"""downscale_textures.py
==============================================================
Walks through extracted/ (the output of extract.bat) and produces
a parallel tree under work/ where every PNG with side > MAX_SIZE
is downscaled. The accompanying .vtex file is copied as-is so
Workshop Tools' resourcecompiler will recompile a smaller .vtex_c.

USAGE:
    python downscale_textures.py --input extracted --output work --max-size 256
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Install Pillow first:  pip install pillow")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--max-size", type=int, default=256,
                    help="Max texture side; anything larger is shrunk")
    ap.add_argument("--quality", type=int, default=85)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    in_root: Path = args.input
    out_root: Path = args.output
    out_root.mkdir(parents=True, exist_ok=True)

    pngs = list(in_root.rglob("*.png"))
    print(f"Found {len(pngs):,} PNG files. Max side: {args.max_size}")
    shrunk = 0
    copied = 0
    for src in pngs:
        rel = src.relative_to(in_root)
        dst = out_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(src) as im:
                w, h = im.size
                if max(w, h) > args.max_size:
                    ratio = args.max_size / max(w, h)
                    new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
                    if args.dry_run:
                        print(f"[shrink] {rel}  {w}x{h} -> {new_size}")
                    else:
                        im.thumbnail((args.max_size, args.max_size), Image.LANCZOS)
                        im.save(dst, optimize=True)
                    shrunk += 1
                else:
                    if not args.dry_run:
                        shutil.copy2(src, dst)
                    copied += 1
        except Exception as e:
            print(f"[err]   {rel}: {e}")

    # also copy .vtex source files (text format) so resourcecompiler picks them up
    vtex_files = list(in_root.rglob("*.vtex"))
    for src in vtex_files:
        rel = src.relative_to(in_root)
        dst = out_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not args.dry_run:
            shutil.copy2(src, dst)

    print(f"Done. shrunk={shrunk}, copied={copied}, vtex files={len(vtex_files)}")


if __name__ == "__main__":
    main()
