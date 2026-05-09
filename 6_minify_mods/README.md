# 6_minify_mods — vendored dota2-minify mods

Applies a curated subset of [dota2-minify](https://github.com/Egezenn/dota2-minify)
mods to `<dota>/game/dota/pak66_dir.vpk`. CLI-only.

## Available mods

```bat
apply_mods.bat --list
```

| Mod | Mechanism | Effect |
|-----|-----------|--------|
| Misc Optimization | blacklist | broad cvar pack + ambient particle blanks |
| Dark Terrain | blacklist + files/ | dark/black terrain (depends on Remove Foilage) |
| Remove Foilage | blacklist | removes grass and trees |
| Remove River | blacklist + files/ | removes the river |
| Remove Weather Effects | blacklist | removes rain/snow/fog |
| Remove Sprays | blacklist | removes player sprays |
| Mute Ambient Sounds | blacklist | mutes wind, water, etc. |
| Remove Hero Renders | css | requires Workshop Tools (skipped by CLI) |
| Remove Showcases | css | requires Workshop Tools (skipped by CLI) |

## Usage

```bat
REM 1) Apply every supported mod (default).
apply_mods.bat

REM 2) Apply specific mods (comma-separated).
apply_mods.bat "Misc Optimization,Dark Terrain,Remove River"

REM 3) Dry run (don't write any VPK).
apply_mods.bat all --dry-run

REM 4) Combine with kill_particles_pak66 for a fully-optimized pak66.
..\5_pak66_builder\kill_particles_pak66.bat total
apply_mods.bat all --merge
```

`--merge` unpacks the existing `pak66_dir.vpk` into staging before adding new
mod files, so particle stubs from `kill_particles_pak66.py` and minify mod
overrides end up in the same VPK.

## Uninstall

Same as everything else in this repo:

```bat
..\5_pak66_builder\uninstall_pak66.bat
```

Or manually delete `<dota>\game\dota\pak66_dir.vpk`.

## Workshop-Tools mods (CSS)

`Remove Hero Renders` and `Remove Showcases` ship a `styling.css` that needs
to be compiled to a `.vcss_c` by the Dota 2 Workshop Tools panorama compiler.
The CLI skips them with a warning. If you need these specifically, use the
[upstream dota2-minify GUI](https://github.com/Egezenn/dota2-minify) — it
will detect Workshop Tools and compile them automatically.

## Attribution

All mods under `vendor/dota2-minify/mods/` are GPL-3.0 from upstream. See
[`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).
