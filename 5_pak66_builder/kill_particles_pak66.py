r"""kill_particles_pak66.py
==============================================================
Builds a ``pak66_dir.vpk`` inside ``<dota>/game/dota_<locale>/``
(default locale: ``minify``) that overrides every preset-matched
particle with Valve's empty ``null.vpcf_c`` stub (851 bytes).

The target folder is mounted by Dota 2 only when Steam launch
options contain ``-language <locale>``. This is the same
mechanism dota2-minify uses. Putting the override in a language
folder rather than in ``game/dota/`` directly:

  - bypasses Steam's 'verify integrity of game files', which
    deletes any non-vanilla pak in ``game/dota/`` but leaves
    language folders alone.
  - lets you toggle the whole override on/off by adding/removing
    ``-language minify`` from Steam launch options, no rebuild
    needed.
  - on Source 2, language overlays mount AFTER the base, so
    ``dota_<locale>/pak66_dir.vpk`` is guaranteed to win over
    ``dota/pak01_dir.vpk`` for the same paths.

USAGE:
    python kill_particles_pak66.py --preset total
    python kill_particles_pak66.py --preset aggressive --dry-run
    python kill_particles_pak66.py --uninstall

After running, add ``-language <locale>`` to Dota 2 launch options
(or run set_launch_option.bat next to this script) and restart Dota 2.

"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Vendored vpk_reader (same as 2_particle_killer)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "2_particle_killer"))
from vpk_reader import find_dota_install, parse_vpk_dir, read_entry_bytes  # noqa: E402

try:
    import vpk  # ValvePython/vpk
except ImportError:
    print("ERROR: 'vpk' Python package not installed.")
    print("       Install it with:   pip install vpk")
    sys.exit(1)


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
    ap.add_argument("--preset", default="total",
                    choices=["safe", "aggressive", "nuclear", "total"],
                    help="Aggressiveness of culling. Default 'total' = kill every particle.")
    ap.add_argument("--preset-file", type=Path, default=None,
                    help="Custom preset .txt file (overrides --preset)")
    ap.add_argument("--pak-number", type=int, default=66,
                    help="VPK number to write (must be > 01). Default 66 (matches dota2-minify convention).")
    ap.add_argument("--locale", default="minify",
                    help="Output language folder name. The VPK is written into "
                         "<dota>/game/dota_<locale>/. Steam launch options must "
                         "contain '-language <locale>' for the override to mount. "
                         "Default: 'minify'.")
    ap.add_argument("--uninstall", action="store_true",
                    help="Remove <dota>/game/dota_<locale>/ entirely and exit.")
    ap.add_argument("--dry-run", action="store_true", help="Print what WOULD be done, don't write")
    ap.add_argument("--stub-from-file", type=Path, default=None,
                    help="Use these raw bytes as the null stub instead of reading from pak01_NNN.vpk "
                         "(useful for testing without full VPK chunks)")
    args = ap.parse_args()

    if args.pak_number <= 1 or args.pak_number > 99:
        print("ERROR: --pak-number must be between 2 and 99")
        sys.exit(1)
    if not args.locale or "/" in args.locale or "\\" in args.locale:
        print("ERROR: --locale must be a single folder name (no slashes)")
        sys.exit(1)

    # --- locate Dota ---
    dota = args.dota or find_dota_install()
    if not dota:
        print("ERROR: Could not locate Dota 2 install. Pass --dota <path>")
        sys.exit(1)
    print(f"[+] Dota 2 install: {dota}")

    locale_dir = dota / "game" / f"dota_{args.locale}"

    # --uninstall does not need pak01_dir.vpk to be present; let users
    # clean up even if Dota was uninstalled or the pak is broken.
    if args.uninstall:
        if locale_dir.exists():
            print(f"[+] Removing {locale_dir} ...")
            if not args.dry_run:
                shutil.rmtree(locale_dir)
            print(f"[+] Done. You can also remove '-language {args.locale}' from Steam launch options.")
        else:
            print(f"[+] Nothing to remove at {locale_dir}")
        return

    pak_dir = dota / "game" / "dota" / "pak01_dir.vpk"
    if not pak_dir.exists():
        print(f"ERROR: pak01_dir.vpk not found under {dota}")
        sys.exit(1)
    print(f"[+] VPK index:      {pak_dir}")

    # --- load preset ---
    here = Path(__file__).parent
    preset_dir = here.parent / "2_particle_killer" / "presets"
    preset_file = args.preset_file or (preset_dir / f"{args.preset}.txt")
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
    print(f"[+] Null stub:      {NULL_PARTICLE} ({null_entry['entry_length']} bytes)")

    if args.stub_from_file:
        null_bytes = args.stub_from_file.read_bytes()
        print(f"[+] Stub bytes (from --stub-from-file {args.stub_from_file}): {len(null_bytes)} bytes")
    else:
        try:
            null_bytes = read_entry_bytes(null_entry, pak_dir)
        except FileNotFoundError as e:
            print(f"ERROR: missing pak01 archive chunk: {e}")
            print("       (You need a full Dota 2 install, not just pak01_dir.vpk)")
            sys.exit(1)
        print(f"[+] Read null bytes: {len(null_bytes)} bytes")

    # --- find target particles ---
    targets = [
        e for e in entries
        if e["ext"] == "vpcf_c"
        and e["full"] != NULL_PARTICLE
        and matches_any(e["full"].lower(), patterns)
    ]
    print(f"[+] Particles to override: {len(targets):,}")

    pak_name = f"pak{args.pak_number:02d}_dir.vpk"
    out_path = locale_dir / pak_name
    locale_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Output folder:  {locale_dir}")

    if args.dry_run:
        print()
        print("=" * 60)
        print(f"  DRY RUN - would write VPK with {len(targets):,} entries")
        print(f"  Output would be: {out_path}")
        print("=" * 60)
        return

    # --- build a staging tree, then pack into VPK ---
    with tempfile.TemporaryDirectory(prefix="dota10x_pak66_") as tmp:
        staging = Path(tmp)
        print(f"[+] Staging dir:    {staging}")

        # Write null bytes under each target path
        written = 0
        for e in targets:
            f = staging / e["full"]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(null_bytes)
            written += 1
            if written % 10000 == 0:
                print(f"    [{written:,} / {len(targets):,}] staged")
        print(f"[+] Staged {written:,} files. Total ~{written * len(null_bytes) / 1024 / 1024:.1f} MB")

        # Build the VPK
        print(f"[+] Building {pak_name}...")
        nv = vpk.new(str(staging))
        nv.read_dir(str(staging))

        # Write to a temp location first, then move atomically
        tmp_vpk = staging.parent / f"_{pak_name}.tmp"
        nv.save(str(tmp_vpk))
        size = tmp_vpk.stat().st_size
        print(f"[+] Built {pak_name}: {size / 1024 / 1024:.2f} MB")

        # Move to final location
        if out_path.exists():
            backup = out_path.with_suffix(".vpk.bak")
            print(f"[+] Existing {pak_name} -> {backup.name}")
            shutil.move(str(out_path), str(backup))
        shutil.move(str(tmp_vpk), str(out_path))

    print()
    print("=" * 60)
    print(f"  Output VPK:       {out_path}")
    print(f"  Particles killed: {len(targets):,}")
    print("=" * 60)
    print(f"  REQUIRED: add '-language {args.locale}' to Dota 2 launch options:")
    print("    Steam -> Library -> Dota 2 -> right-click -> Properties -> Launch Options")
    print("    Or run set_launch_option.bat (next to this script) to do it automatically.")
    print("  Then restart Dota 2.")
    print(f"  To revert:        rerun with --uninstall (or delete {locale_dir})")


if __name__ == "__main__":
    main()
