r"""kill_particles.py
==============================================================
Reads pak01_dir.vpk + pak01_NNN.vpk on disk, finds every particle
that matches a preset pattern, and writes Valve's own null
particle (`particles/error/null.vpcf_c`) under those paths into
  <dota>/game/dota/particles/<...>
to act as an override.

That override is loaded by Dota 2 at runtime *instead of* the real
particle - so the particle effectively becomes a no-op.

This does NOT modify the original VPKs - it only writes new files
into game/dota/. To revert, run uninstall.bat or simply delete the
created override files.

USAGE:
    python kill_particles.py --dota "C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta" --preset safe
    python kill_particles.py --preset aggressive --dry-run
    python kill_particles.py --preset nuclear

Presets are .txt files in ./presets/. Every line is a substring
pattern. A particle is killed if any pattern matches its full path.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vpk_reader import find_dota_install, parse_vpk_dir, read_entry_bytes


NULL_PARTICLE = "particles/error/null.vpcf_c"


def load_preset(preset_path: Path) -> list[str]:
    pats = []
    for line in preset_path.read_text(encoding="utf-8").splitlines():
        s = line.split("#", 1)[0].strip()
        if s:
            pats.append(s.lower())
    return pats


def matches_any(full_lower: str, patterns: list[str]) -> bool:
    return any(p in full_lower for p in patterns)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dota", type=Path, default=None,
                    help="Path to '...steamapps/common/dota 2 beta' (auto-detected if omitted)")
    ap.add_argument("--preset", default="safe", choices=["safe", "aggressive", "nuclear", "total"],
                    help="Aggressiveness of culling. 'total' = kill every particle in the VPK.")
    ap.add_argument("--preset-file", type=Path, default=None,
                    help="Custom preset .txt file (overrides --preset)")
    ap.add_argument("--dry-run", action="store_true", help="Print what WOULD be done, don't write")
    ap.add_argument("--out-suffix", default="", help="Optional suffix appended to override dir name")
    ap.add_argument("--stub-from-file", type=Path, default=None,
                    help="Use these raw bytes as the null stub instead of reading from pak01_NNN.vpk "
                         "(useful if you only have pak01_dir.vpk available, e.g. for testing)")
    args = ap.parse_args()

    # --- locate Dota ---
    dota = args.dota or find_dota_install()
    if not dota:
        print("ERROR: Could not locate Dota 2 install. Pass --dota <path>")
        sys.exit(1)
    pak_dir = dota / "game" / "dota" / "pak01_dir.vpk"
    if not pak_dir.exists():
        print(f"ERROR: pak01_dir.vpk not found under {dota}")
        sys.exit(1)
    print(f"[+] Dota 2 install: {dota}")
    print(f"[+] VPK index:      {pak_dir}")

    # --- load preset ---
    here = Path(__file__).parent
    preset_file = args.preset_file or (here / "presets" / f"{args.preset}.txt")
    if not preset_file.exists():
        print(f"ERROR: preset not found: {preset_file}")
        sys.exit(1)
    patterns = load_preset(preset_file)
    print(f"[+] Preset:         {preset_file.name}  ({len(patterns)} patterns)")

    # --- parse VPK ---
    print("[+] Parsing pak01_dir.vpk...")
    _, entries = parse_vpk_dir(pak_dir)
    print(f"[+] Total entries:  {len(entries):,}")

    # --- find null particle stub ---
    null_entry = next((e for e in entries if e["full"] == NULL_PARTICLE), None)
    if not null_entry:
        print(f"ERROR: {NULL_PARTICLE} not found in VPK. Cannot proceed.")
        sys.exit(1)
    print(f"[+] Null stub found: {NULL_PARTICLE} ({null_entry['entry_length']} bytes, "
          f"archive_index={null_entry['archive_index']})")

    if not args.dry_run:
        if args.stub_from_file:
            null_bytes = args.stub_from_file.read_bytes()
            print(f"[+] Stub bytes (from --stub-from-file {args.stub_from_file}): {len(null_bytes)} bytes")
        else:
            try:
                null_bytes = read_entry_bytes(null_entry, pak_dir)
            except FileNotFoundError as e:
                print(f"ERROR: missing pak01 archive chunk: {e}")
                sys.exit(1)
            print(f"[+] Read null bytes: {len(null_bytes)} bytes")

    # --- find target particles ---
    targets = [
        e for e in entries
        if e["ext"] == "vpcf_c"
        and e["full"] != NULL_PARTICLE  # never override the stub itself
        and matches_any(e["full"].lower(), patterns)
    ]
    print(f"[+] Particles matched by preset: {len(targets):,}")

    override_root = dota / "game" / "dota"
    backup_log = override_root / "_dota10x_overrides.txt"

    written = 0
    skipped = 0
    for e in targets:
        out_path = override_root / e["full"]
        if out_path.exists():
            skipped += 1
            continue
        if args.dry_run:
            written += 1
            continue
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(null_bytes)
        written += 1

    # log what we wrote so uninstall can clean up
    if not args.dry_run:
        with open(backup_log, "a", encoding="utf-8") as f:
            for e in targets:
                f.write(e["full"] + "\n")

    print()
    print("=" * 60)
    print(f"  Particles overridden:   {written:>6}")
    print(f"  Skipped (already exist): {skipped:>6}")
    if args.dry_run:
        print("  (DRY RUN - no files written)")
    else:
        print(f"  Override log:           {backup_log}")
    print("=" * 60)
    if not args.dry_run:
        print("  Restart Dota for changes to take effect.")
        print("  To revert: run uninstall.bat or delete the override files.")


if __name__ == "__main__":
    main()
