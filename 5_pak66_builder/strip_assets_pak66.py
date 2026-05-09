r"""strip_assets_pak66.py
==============================================================
Stubs out heavy asset categories beyond particles (voice lines,
music, attack sounds, cosmetic models, etc.) inside
``<dota>/game/dota_<locale>/pak66_dir.vpk`` to cut Dota 2's
map load time.

This is a sibling tool to :mod:`kill_particles_pak66` -- same
pak66 + ``-language <locale>`` mechanism, just operates on
non-particle file types using the blank stubs from
``vendor/dota2-minify/blank-files/``.

Categories
----------
* ``vo``                : ``sounds/vo/**/*.vsnd_c``
                          (~91k files, ~3.7 GB on a stock install)
* ``music``             : ``sounds/music/**/*.vsnd_c``
                          (~1.1 GB)
* ``weapon-sounds``     : ``sounds/weapons/**/*.vsnd_c``
                          (~792 MB)
* ``item-sounds``       : ``sounds/items/**/*.vsnd_c``
* ``ambient-sounds``    : ``sounds/ambient/**/*.vsnd_c``
* ``cosmetics-models``  : ``models/items/**/*.vmdl_c``
                          (~1.5 GB)
* ``cosmetics-mats``    : ``materials/models/items/**/*.vmat_c``
* ``cosmetics-particles``: ``particles/econ/items/**/*.vpcf_c``
* ``all-safe``          : every category above (the recommended
                          'cut load time' bundle - ~7 GB stubbed)

DO NOT USE these categories - they break the game:

* ``models/heroes/**``         (base heroes; no flag, blocked)
* ``materials/models/heroes/**`` (base heroes; no flag, blocked)
* ``sounds/ui/**``             (UI sounds; no flag, blocked)
* ``panorama/**``              (UI; no flag, blocked)

USAGE
-----
::

    python strip_assets_pak66.py --categories all-safe
    python strip_assets_pak66.py --categories vo,music --dry-run
    python strip_assets_pak66.py --categories vo --merge
    python strip_assets_pak66.py --uninstall

After running, add ``-language <locale>`` to Dota 2 launch
options (or run set_launch_option.bat) and restart the game.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "2_particle_killer"))
from vpk_reader import find_dota_install, parse_vpk_dir  # noqa: E402

try:
    import vpk
except ImportError:
    print("ERROR: 'vpk' Python package not installed. Run:  pip install vpk")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
BLANK_FILES_DIR = REPO_ROOT / "vendor" / "dota2-minify" / "blank-files"


# Each category = (pak01 path prefix, expected file extension).
# Blocked categories are listed but raise an error if requested.
CATEGORIES: dict[str, tuple[str, str]] = {
    "vo":                  ("sounds/vo/",                 "vsnd_c"),
    "music":               ("sounds/music/",              "vsnd_c"),
    "weapon-sounds":       ("sounds/weapons/",            "vsnd_c"),
    "item-sounds":         ("sounds/items/",              "vsnd_c"),
    "ambient-sounds":      ("sounds/ambient/",            "vsnd_c"),
    "cosmetics-models":    ("models/items/",              "vmdl_c"),
    "cosmetics-mats":      ("materials/models/items/",    "vmat_c"),
    "cosmetics-particles": ("particles/econ/items/",      "vpcf_c"),
}

ALL_SAFE = list(CATEGORIES.keys())

# These are intentionally NOT user-selectable. They will brick the game.
BLOCKED_CATEGORIES = {
    "heroes-models", "heroes-mats", "ui-sounds", "panorama",
}


def load_blank_stubs() -> dict[str, bytes]:
    stubs: dict[str, bytes] = {}
    for f in sorted(BLANK_FILES_DIR.iterdir()):
        if f.is_file() and f.name.startswith("blank"):
            stubs[f.suffix.lstrip(".")] = f.read_bytes()
    return stubs


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dota", type=Path, default=None,
                    help="Path to '...steamapps/common/dota 2 beta' (auto-detected if omitted)")
    ap.add_argument("--categories", default="all-safe",
                    help="Comma-separated category names, or 'all-safe' / 'list'. "
                         "See module docstring for the full set.")
    ap.add_argument("--list", action="store_true",
                    help="List supported categories and exit.")
    ap.add_argument("--locale", default="minify",
                    help="Output language folder name. The VPK is written into "
                         "<dota>/game/dota_<locale>/. Default: 'minify'.")
    ap.add_argument("--pak-number", type=int, default=66,
                    help="VPK number to write (must be 2-99). Default 66.")
    ap.add_argument("--merge", action="store_true",
                    help="If pak66 already exists, unpack it into staging and add "
                         "stubs on top instead of overwriting. Use this when chaining "
                         "with kill_particles_pak66 / apply_mods.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan but write nothing.")
    ap.add_argument("--uninstall", action="store_true",
                    help="Remove <dota>/game/dota_<locale>/ entirely and exit.")
    args = ap.parse_args()

    if args.list:
        print("Supported categories:")
        for name, (prefix, ext) in CATEGORIES.items():
            print(f"  {name:22s}  ->  {prefix}**/*.{ext}")
        print("  all-safe                 ->  all of the above (recommended)")
        return 0

    if args.pak_number <= 1 or args.pak_number > 99:
        print("ERROR: --pak-number must be between 2 and 99")
        return 1
    if not args.locale or "/" in args.locale or "\\" in args.locale:
        print("ERROR: --locale must be a single folder name (no slashes)")
        return 1

    dota = args.dota or find_dota_install()
    if not dota:
        print("ERROR: Could not locate Dota 2 install. Pass --dota <path>")
        return 1
    print(f"[+] Dota 2 install: {dota}")

    locale_dir = dota / "game" / f"dota_{args.locale}"

    if args.uninstall:
        if locale_dir.exists():
            print(f"[+] Removing {locale_dir} ...")
            if not args.dry_run:
                shutil.rmtree(locale_dir)
            print(f"[+] Done. You can also remove '-language {args.locale}' from Steam launch options.")
        else:
            print(f"[+] Nothing to remove at {locale_dir}")
        return 0

    # Resolve --categories
    raw = [c.strip() for c in args.categories.split(",") if c.strip()]
    if not raw:
        print("ERROR: --categories is empty.")
        return 1
    if "all-safe" in raw:
        if len(raw) != 1:
            print("ERROR: 'all-safe' cannot be combined with other categories.")
            return 1
        selected = list(ALL_SAFE)
    else:
        selected = []
        for c in raw:
            if c in BLOCKED_CATEGORIES:
                print(f"ERROR: category {c!r} is blocked (would brick the game).")
                return 1
            if c not in CATEGORIES:
                print(f"ERROR: unknown category {c!r}. Use --list.")
                return 1
            selected.append(c)

    print(f"[+] Categories ({len(selected)}):")
    for c in selected:
        prefix, ext = CATEGORIES[c]
        print(f"    - {c:22s}  ->  {prefix}**/*.{ext}")

    pak_dir_path = dota / "game" / "dota" / "pak01_dir.vpk"
    if not pak_dir_path.exists():
        print(f"ERROR: pak01_dir.vpk not found under {dota}")
        return 1
    print(f"[+] VPK index:      {pak_dir_path}")

    print("[+] Parsing pak01_dir.vpk...")
    _, entries = parse_vpk_dir(pak_dir_path)
    print(f"[+] Total entries:  {len(entries):,}")

    blank_stubs = load_blank_stubs()
    if not blank_stubs:
        print(f"ERROR: no blank stubs under {BLANK_FILES_DIR}")
        return 1

    # Resolve targets per category, deduplicate
    targets: dict[str, str] = {}  # path -> ext
    cat_counts: list[tuple[str, int, int]] = []  # (cat, n_files, total_bytes)
    for c in selected:
        prefix, ext = CATEGORIES[c]
        if ext not in blank_stubs:
            print(f"[!] No blank stub for .{ext} - skipping {c}")
            continue
        n = b = 0
        for e in entries:
            if e["ext"] != ext:
                continue
            if not e["full"].startswith(prefix):
                continue
            targets[e["full"]] = ext
            n += 1
            b += e["entry_length"]
        cat_counts.append((c, n, b))
        print(f"[+] {c:22s}: {n:>7,} files  ({b/1024/1024:>8.1f} MB original)")

    if not targets:
        print("[!] No matching files. Nothing to do.")
        return 0

    pak_name = f"pak{args.pak_number:02d}_dir.vpk"
    out_path = locale_dir / pak_name
    locale_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Output folder:  {locale_dir}")

    if args.dry_run:
        print()
        print("=" * 60)
        print(f"  DRY RUN - would stub {len(targets):,} files in {pak_name}")
        print(f"  Output would be: {out_path}")
        print("=" * 60)
        return 0

    with tempfile.TemporaryDirectory(prefix="dota10x_strip_assets_") as tmp:
        staging = Path(tmp)
        print(f"[+] Staging dir:    {staging}")

        if args.merge and out_path.exists():
            print(f"[+] Merging existing {out_path.name} into staging...")
            pak = vpk.open(str(out_path))
            n_merged = 0
            for path, _meta in pak.read_index_iter():
                f = pak.get_file(path)
                data = f.read()
                out = staging / path
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(data)
                n_merged += 1
            print(f"[+] Merged {n_merged:,} entries from existing pak66.")

        # Stage all targets
        written = 0
        skipped_existing = 0
        for path, ext in targets.items():
            stub = blank_stubs[ext]
            out = staging / path
            out.parent.mkdir(parents=True, exist_ok=True)
            # If a previous --merge step already gave this path real bytes
            # bigger than our stub, keep them - the user clearly wanted them.
            if out.exists() and out.stat().st_size > len(stub):
                skipped_existing += 1
                continue
            out.write_bytes(stub)
            written += 1
            if written % 20000 == 0:
                print(f"    [{written:,} / {len(targets):,}] staged")
        print(f"[+] Staged {written:,} stubs ({skipped_existing:,} skipped because --merge had bigger bytes).")

        print(f"[+] Building {pak_name}...")
        nv = vpk.new(str(staging))
        nv.read_dir(str(staging))
        tmp_vpk = staging.parent / f"_{pak_name}.tmp"
        nv.save(str(tmp_vpk))
        size = tmp_vpk.stat().st_size
        print(f"[+] Built {pak_name}: {size/1024/1024:.2f} MB")

        if out_path.exists():
            backup = out_path.with_suffix(".vpk.bak")
            print(f"[+] Existing {pak_name} -> {backup.name}")
            shutil.move(str(out_path), str(backup))
        shutil.move(str(tmp_vpk), str(out_path))

    total_n = sum(n for _, n, _ in cat_counts)
    total_b = sum(b for _, _, b in cat_counts)
    print()
    print("=" * 60)
    print(f"  Output VPK:        {out_path}")
    print(f"  Files stubbed:     {total_n:,}")
    print(f"  Original size:     {total_b/1024/1024:.1f} MB  (now ~{written * 2 / 1024:.0f} KB of stubs)")
    print("=" * 60)
    print(f"  REQUIRED: add '-language {args.locale}' to Dota 2 launch options.")
    print("    Run set_launch_option.bat (next to this script) to do it automatically.")
    print(f"  To revert: rerun with --uninstall (or delete {locale_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
