r"""apply_mods.py
==============================================================
Builds (or extends) ``pak66_dir.vpk`` inside
``<dota>/game/dota_<locale>/`` (default locale: ``minify``) by
applying selected vendored dota2-minify mods.

The target folder is mounted by Dota 2 only when Steam launch
options contain ``-language <locale>``. This is the same
mechanism dota2-minify uses (it edits ``localconfig.vdf`` to
add ``-language minify`` automatically). To turn the override
off, simply remove ``-language <locale>`` from launch options.

Each mod can contribute via two mechanisms:

1. ``blacklist.txt`` -- a list of asset paths inside ``pak01_dir.vpk``
   that should be replaced with empty/blank stubs of the matching
   extension. Lines support these prefixes:

   - ``>>path/``  / ``**path/``  -- directory pattern (every file under
     this directory, recursive).
   - ``*-path/``                 -- directory-pattern exclusion.
   - ``--path/file.ext``         -- exact-path exclusion.
   - ``# comment`` or empty      -- ignored.
   - other                       -- exact path; must end with one of the
     blank-file extensions (``.vpcf_c``, ``.vmat_c``, ``.vtex_c`` etc.).

2. ``files/`` -- a directory tree of pre-compiled override files. The
   relative path from ``files/`` becomes the path inside the produced
   VPK. Used for mods that need real compiled resources (Dark Terrain,
   Remove River).

USAGE
-----
::

    # Apply all 9 vendored mods, overwriting pak66_dir.vpk
    python apply_mods.py --mods all

    # Apply specific mods
    python apply_mods.py --mods "Misc Optimization,Dark Terrain,Remove River"

    # See what would happen, write nothing
    python apply_mods.py --mods all --dry-run

    # Combine particle-killer + mods into the same pak66
    #   1) build pak66 with kill_particles_pak66.py first
    #   2) then run this with --merge to extend it instead of overwrite
    python apply_mods.py --mods all --merge

    # Use a different locale folder name (must match -language X in Steam)
    python apply_mods.py --mods all --locale russian

    # List all available mods
    python apply_mods.py --list

    # Remove the entire dota_<locale>/ folder
    python apply_mods.py --uninstall

After running, add ``-language <locale>`` to Dota 2 launch options
in Steam (Properties -> Launch Options) and restart the game.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Vendored vpk_reader (re-used from 2_particle_killer)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "2_particle_killer"))
from vpk_reader import find_dota_install, parse_vpk_dir  # noqa: E402

try:
    import vpk  # ValvePython/vpk
except ImportError:
    print("ERROR: 'vpk' Python package not installed.")
    print("       Install it with:   pip install vpk")
    sys.exit(1)


# Mods that we cannot fully apply without Workshop Tools (require .vcss_c
# compilation). They are vendored for completeness but skipped here with a
# warning.
WORKSHOP_TOOLS_REQUIRED = {
    "Remove Hero Renders",
    "Remove Showcases",
    "Remove Main Menu Background",
}


REPO_ROOT = Path(__file__).resolve().parent.parent
VENDOR_ROOT = REPO_ROOT / "vendor" / "dota2-minify"
MODS_ROOT = VENDOR_ROOT / "mods"
BLANK_FILES_DIR = VENDOR_ROOT / "blank-files"


# ---------------------------------------------------------------------------
# Mod loading
# ---------------------------------------------------------------------------


def list_available_mods() -> list[str]:
    if not MODS_ROOT.is_dir():
        return []
    return sorted(p.name for p in MODS_ROOT.iterdir() if p.is_dir())


def load_blank_stubs() -> dict[str, bytes]:
    """Load blank.* stubs into a {".ext": bytes} map."""
    stubs: dict[str, bytes] = {}
    for f in sorted(BLANK_FILES_DIR.iterdir()):
        if f.is_file() and f.name.startswith("blank"):
            ext = f.suffix  # ".vpcf_c", ".vmat_c", ".txt", ...
            stubs[ext] = f.read_bytes()
    return stubs


def load_dependencies(mod_name: str) -> list[str]:
    """Read modcfg.json dependencies field. Returns [] if no deps."""
    cfg = MODS_ROOT / mod_name / "modcfg.json"
    if not cfg.exists():
        return []
    import json

    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception:
        return []
    return list(data.get("dependencies", []))


def resolve_mods(selected: list[str]) -> list[str]:
    """Add transitive dependencies, preserving order, de-duped."""
    available = set(list_available_mods())
    out: list[str] = []
    seen: set[str] = set()

    def add(name: str):
        if name in seen:
            return
        if name not in available:
            print(f"[!] Unknown mod: {name!r}")
            return
        for dep in load_dependencies(name):
            add(dep)
        seen.add(name)
        out.append(name)

    for m in selected:
        add(m)
    return out


# ---------------------------------------------------------------------------
# Blacklist parsing
# ---------------------------------------------------------------------------


def parse_blacklist(path: Path) -> tuple[list[str], list[str], set[str], set[str]]:
    """Returns (exact_includes, dir_includes, exact_excludes, dir_excludes).

    Lines:
        >>foo/bar          -> dir include   "foo/bar"
        **foo/bar          -> dir include   "foo/bar"
        *-foo/bar          -> dir exclude   "foo/bar"
        --foo/bar.vpcf_c   -> exact exclude "foo/bar.vpcf_c"
        # ...              -> comment
        (blank)            -> ignored
        else               -> exact include
    """
    exact_inc: list[str] = []
    dir_inc: list[str] = []
    exact_exc: set[str] = set()
    dir_exc: set[str] = set()

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(">>"):
            dir_inc.append(line[2:].strip().rstrip("/"))
        elif line.startswith("**"):
            dir_inc.append(line[2:].strip().rstrip("/"))
        elif line.startswith("*-"):
            dir_exc.add(line[2:].strip().rstrip("/"))
        elif line.startswith("--"):
            exact_exc.add(line[2:].strip())
        else:
            exact_inc.append(line)
    return exact_inc, dir_inc, exact_exc, dir_exc


def expand_blacklist(
    bl: tuple[list[str], list[str], set[str], set[str]],
    entry_paths: set[str],
) -> set[str]:
    """Resolve patterns into a concrete set of pak01 paths."""
    exact_inc, dir_inc, exact_exc, dir_exc = bl
    matched: set[str] = set()

    # Exact includes
    for p in exact_inc:
        matched.add(p)

    # Directory includes - any entry whose path starts with "<dir>/"
    if dir_inc:
        prefixes = tuple(d + "/" for d in dir_inc)
        for p in entry_paths:
            if p.startswith(prefixes):
                matched.add(p)

    # Directory excludes
    if dir_exc:
        ex_prefixes = tuple(d + "/" for d in dir_exc)
        matched = {p for p in matched if not p.startswith(ex_prefixes)}

    # Exact excludes
    matched -= exact_exc

    return matched


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def stage_blacklist_files(
    paths: set[str],
    blank_stubs: dict[str, bytes],
    staging: Path,
    mod_name: str,
    entry_paths: set[str],
) -> tuple[int, int, int]:
    """Write blank stubs at each path. Returns (written, skipped_unknown_ext, missing_in_vpk)."""
    written = skipped = missing = 0
    for p in paths:
        ext = "." + p.rsplit(".", 1)[-1] if "." in p else ""
        stub = blank_stubs.get(ext)
        if stub is None:
            skipped += 1
            continue
        if p not in entry_paths:
            # File listed in blacklist but not in pak01 - harmless,
            # the mod was probably written for a slightly different
            # version of Dota.
            missing += 1
            continue
        out = staging / p
        out.parent.mkdir(parents=True, exist_ok=True)
        # Don't overwrite if a previous mod already provided real bytes
        if out.exists() and out.stat().st_size > len(stub):
            continue
        out.write_bytes(stub)
        written += 1
    if missing:
        print(f"      [{mod_name}] {missing} listed paths not in current pak01 (ignored)")
    if skipped:
        print(f"      [{mod_name}] {skipped} entries skipped (no blank stub for extension)")
    return written, skipped, missing


def stage_override_files(files_dir: Path, staging: Path, mod_name: str) -> int:
    """Copy every file under <mod>/files/ into staging at the same relpath."""
    written = 0
    for src in files_dir.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(files_dir).as_posix()
        out = staging / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        # files/ overrides win over blacklist stubs even if a stub was
        # already staged
        out.write_bytes(src.read_bytes())
        written += 1
    if written:
        print(f"      [{mod_name}] {written} override files copied from files/")
    return written


def build_vpk(staging: Path, out_path: Path) -> int:
    print(f"[+] Building {out_path.name}...")
    nv = vpk.new(str(staging))
    nv.read_dir(str(staging))
    tmp_vpk = staging.parent / f"_{out_path.name}.tmp"
    nv.save(str(tmp_vpk))
    size = tmp_vpk.stat().st_size

    if out_path.exists():
        backup = out_path.with_suffix(".vpk.bak")
        print(f"[+] Existing {out_path.name} -> {backup.name}")
        shutil.move(str(out_path), str(backup))
    shutil.move(str(tmp_vpk), str(out_path))
    return size


def merge_existing_into_staging(out_path: Path, staging: Path) -> int:
    """If --merge was passed and pak66 already exists, unpack it into staging
    so that subsequent build picks up both old + new entries."""
    if not out_path.exists():
        return 0
    print(f"[+] Merging existing {out_path.name} into staging...")
    pak = vpk.open(str(out_path))
    count = 0
    for path, _meta in pak.read_index_iter():
        # Use pak.get_file to extract bytes
        f = pak.get_file(path)
        data = f.read()
        out = staging / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        count += 1
    print(f"[+] Merged {count:,} entries from existing pak66.")
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dota", type=Path, default=None,
                    help="Path to '...steamapps/common/dota 2 beta' (auto-detected if omitted)")
    ap.add_argument("--mods", default="all",
                    help='Comma-separated mod names, or "all". Use --list to see options.')
    ap.add_argument("--list", action="store_true", help="List available mods and exit.")
    ap.add_argument("--locale", default="minify",
                    help="Output language folder name. The VPK is written into "
                         "<dota>/game/dota_<locale>/. Steam launch options must "
                         "contain '-language <locale>' for the override to mount. "
                         "Default: 'minify'.")
    ap.add_argument("--pak-number", type=int, default=66,
                    help="VPK number to write (must be 2-99). Default 66.")
    ap.add_argument("--merge", action="store_true",
                    help="If pak66_dir.vpk already exists, unpack it into staging "
                         "and add new mod files on top. Otherwise pak66 is overwritten.")
    ap.add_argument("--dry-run", action="store_true", help="Print what WOULD happen, write nothing.")
    ap.add_argument("--uninstall", action="store_true",
                    help="Remove <dota>/game/dota_<locale>/ entirely and exit.")
    args = ap.parse_args()

    available = list_available_mods()
    if args.list:
        print("Available mods (vendored from dota2-minify):")
        for m in available:
            tags = []
            if m in WORKSHOP_TOOLS_REQUIRED:
                tags.append("requires Workshop Tools")
            if (MODS_ROOT / m / "blacklist.txt").exists():
                tags.append("blacklist")
            if (MODS_ROOT / m / "files").is_dir():
                tags.append("files/")
            tag_str = f"  [{', '.join(tags)}]" if tags else ""
            print(f"  - {m}{tag_str}")
        return 0

    if not available:
        print(f"ERROR: no mods found under {MODS_ROOT}")
        return 1

    if args.mods.strip().lower() == "all":
        selected_raw = available
    else:
        selected_raw = [m.strip() for m in args.mods.split(",") if m.strip()]

    selected = resolve_mods(selected_raw)
    # Filter out WT-required mods with a warning
    final: list[str] = []
    for m in selected:
        if m in WORKSHOP_TOOLS_REQUIRED:
            print(f"[!] Skipping {m!r} - requires Workshop Tools to compile .vcss_c.")
            print("    See README.md, this mod is panorama-CSS only and the CLI cannot compile it.")
            continue
        final.append(m)
    if not final:
        print("ERROR: no applicable mods selected.")
        return 1

    print(f"[+] Mods to apply ({len(final)}):")
    for m in final:
        print(f"    - {m}")

    if args.pak_number <= 1 or args.pak_number > 99:
        print("ERROR: --pak-number must be between 2 and 99")
        return 1

    if not args.locale or "/" in args.locale or "\\" in args.locale:
        print("ERROR: --locale must be a single folder name (no slashes)")
        return 1

    # --- locate Dota
    dota = args.dota or find_dota_install()
    if not dota:
        print("ERROR: Could not locate Dota 2 install. Pass --dota <path>")
        return 1
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
        return 0

    pak_dir_path = dota / "game" / "dota" / "pak01_dir.vpk"
    if not pak_dir_path.exists():
        print(f"ERROR: pak01_dir.vpk not found under {dota}")
        return 1
    print(f"[+] VPK index:      {pak_dir_path}")

    # --- parse VPK
    print("[+] Parsing pak01_dir.vpk...")
    _, entries = parse_vpk_dir(pak_dir_path)
    entry_paths = {e["full"] for e in entries}
    print(f"[+] Total entries:  {len(entries):,}")

    # --- load blank stubs
    blank_stubs = load_blank_stubs()
    if not blank_stubs:
        print(f"ERROR: no blank stubs found under {BLANK_FILES_DIR}")
        return 1
    print(f"[+] Blank stubs:    {len(blank_stubs)} extensions ({', '.join(sorted(blank_stubs))})")

    # --- compute final action plan
    pak_name = f"pak{args.pak_number:02d}_dir.vpk"
    out_path = locale_dir / pak_name
    locale_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Output folder:  {locale_dir}")

    # --- stage and build
    if args.dry_run:
        print()
        print("=" * 60)
        print(f"  DRY RUN - {pak_name} would be written to {out_path}")
        print("=" * 60)

    total_blank = total_override = 0
    with tempfile.TemporaryDirectory(prefix="dota10x_apply_mods_") as tmp:
        staging = Path(tmp)
        print(f"[+] Staging dir:    {staging}")

        if args.merge and not args.dry_run:
            merge_existing_into_staging(out_path, staging)

        # Pass 1: all blacklists (blank stubs).
        for mod in final:
            mod_dir = MODS_ROOT / mod
            bl_path = mod_dir / "blacklist.txt"
            if not bl_path.exists():
                continue
            bl = parse_blacklist(bl_path)
            paths = expand_blacklist(bl, entry_paths)
            print(f"[+] {mod}: blacklist matches: {len(paths):,}")
            if not args.dry_run:
                w, _s, _m = stage_blacklist_files(
                    paths, blank_stubs, staging, mod, entry_paths
                )
                total_blank += w

        # Pass 2: all files/ overrides. These always win over blacklist
        # blank stubs, so they must be staged after pass 1.
        for mod in final:
            files_dir = MODS_ROOT / mod / "files"
            if not files_dir.is_dir():
                continue
            file_count = sum(1 for _ in files_dir.rglob("*") if _.is_file())
            print(f"[+] {mod}: files/ overrides: {file_count}")
            if not args.dry_run:
                total_override += stage_override_files(files_dir, staging, mod)

        if args.dry_run:
            print()
            print("=" * 60)
            print("  DRY RUN complete - nothing written.")
            print("=" * 60)
            return 0

        total_size = sum(f.stat().st_size for f in staging.rglob("*") if f.is_file())
        print(f"[+] Staged {total_blank:,} blank-stubs + {total_override:,} overrides "
              f"= ~{total_size / 1024 / 1024:.1f} MB")

        size = build_vpk(staging, out_path)

    print()
    print("=" * 60)
    print(f"  Output VPK:   {out_path}")
    print(f"  Size:         {size / 1024 / 1024:.2f} MB")
    print(f"  Entries:      {total_blank + total_override:,}")
    print("=" * 60)
    print(f"  REQUIRED: add '-language {args.locale}' to Dota 2 launch options:")
    print("    Steam -> Library -> Dota 2 -> right-click -> Properties -> Launch Options")
    print("    Or run set_launch_option.bat (5_pak66_builder/) to do it automatically.")
    print("  Then restart Dota 2.")
    print(f"  To revert:    rerun with --uninstall (or delete {locale_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
