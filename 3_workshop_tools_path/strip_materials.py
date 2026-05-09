"""strip_materials.py
==============================================================
Walks through extracted/ and rewrites .vmat files into work/
with a much cheaper shader and minimal parameters.

Replaces:
    Shader "hero.vfx"          -> "global_lit_simple.vfx"
    Shader "vr_complex.vfx"    -> "vr_simple.vfx"
    Shader "csgo_complex.vfx"  -> "csgo_simple.vfx"
    Shader "complex.vfx"       -> "simple.vfx"

Strips expensive parameters:
    g_flCubeMapBlend, g_vCubeMapTint, g_flSelfIllumScale,
    g_flSpecularExponent, g_vEnvMapTintColor, g_flClothScale,
    F_CLOTH_SHADING, F_CLOTH_NORMAL, F_DETAIL_TEXTURE,
    F_NORMAL_MAP, F_SPECULAR, F_FANCY_BLENDING,
    F_TINT_MASK, F_TRANSLUCENT, F_SUBSURFACE_SCATTER,
    F_FLOW_SEPARATE_TRANSPARENCY, F_REFRACTION,
    g_flBumpStrength, g_flMetalness

USAGE:
    python strip_materials.py --input extracted --output work
    python strip_materials.py --input extracted --output work --shader simple.vfx
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

DEFAULT_REPLACEMENTS = {
    "hero.vfx": "global_lit_simple.vfx",
    "vr_complex.vfx": "vr_simple.vfx",
    "csgo_complex.vfx": "csgo_simple.vfx",
    "complex.vfx": "simple.vfx",
    "hero_underlords.vfx": "global_lit_simple.vfx",
    "hero_for_arcanas.vfx": "global_lit_simple.vfx",
}

EXPENSIVE_PARAMS_RE = re.compile(
    r"^\s*(?:F_CLOTH_SHADING|F_CLOTH_NORMAL|F_DETAIL_TEXTURE|F_DETAIL_TEXTURE_TRANSFORM|"
    r"F_NORMAL_MAP|F_SPECULAR|F_FANCY_BLENDING|F_TINT_MASK|F_TRANSLUCENT|"
    r"F_SUBSURFACE_SCATTER|F_FLOW_SEPARATE_TRANSPARENCY|F_REFRACTION|"
    r"F_RIM_LIGHTING|F_LAYERS|F_OVERBRIGHT_FACTOR|F_FLESH|F_BLEND_MODE|"
    r"g_vCubeMapTint|g_flCubeMapBlend|g_flSelfIllumScale|g_flSpecularExponent|"
    r"g_vEnvMapTintColor|g_flClothScale|g_flBumpStrength|g_flMetalness|"
    r"g_flRoughnessScale|g_flDetailBlendFactor|g_flRefractScale|"
    r"g_flFleshSubsurfaceScatter|g_flRimLightScale|g_flRimLightExponent|"
    r"g_flAmbientOcclusionDirectDiffuse|g_flAmbientOcclusionDirectSpecular)\s+",
    re.IGNORECASE,
)


def transform_vmat(text: str, replacements: dict[str, str]) -> str:
    out_lines = []
    for line in text.splitlines():
        # Replace shader
        m = re.match(r'^(\s*shader\s+")([^"]+)("\s*)$', line, re.IGNORECASE)
        if m:
            old = m.group(2)
            new = replacements.get(old, old)
            line = f"{m.group(1)}{new}{m.group(3)}"
            out_lines.append(line)
            continue
        # Drop expensive parameter lines entirely
        if EXPENSIVE_PARAMS_RE.match(line):
            continue
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--shader", default=None,
                    help="Force replace ALL shader names with this one (overrides defaults)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repl = dict(DEFAULT_REPLACEMENTS)
    if args.shader:
        repl = {k: args.shader for k in repl}

    vmats = list(args.input.rglob("*.vmat"))
    print(f"Found {len(vmats):,} .vmat files")
    rewritten = 0
    for src in vmats:
        rel = src.relative_to(args.input)
        dst = args.output / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = src.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"[err] {rel}: {e}")
            continue
        new_text = transform_vmat(text, repl)
        if new_text == text:
            if not args.dry_run:
                shutil.copy2(src, dst)
            continue
        if args.dry_run:
            print(f"[mod] {rel}")
        else:
            dst.write_text(new_text, encoding="utf-8")
        rewritten += 1
    print(f"Rewrote {rewritten} materials, copied {len(vmats) - rewritten} unchanged")


if __name__ == "__main__":
    main()
