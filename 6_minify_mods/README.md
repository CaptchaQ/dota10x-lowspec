# 6_minify_mods — vendored dota2-minify mods

Applies a curated subset of [dota2-minify](https://github.com/Egezenn/dota2-minify)
mods into `<dota>/game/dota_<locale>/pak66_dir.vpk` (default locale:
`minify`, configurable via `--locale`). The folder is only mounted by Dota 2
when Steam launch options contain `-language <locale>` — use
[`../5_pak66_builder/set_launch_option.bat`](../5_pak66_builder/set_launch_option.bat)
to add it. CLI-only.

## Available mods

```bat
apply_mods.bat --list
```

| Mod | Mechanism | Effect |
|-----|-----------|--------|
| **Minify Spells & Items** | blacklist (~5,400 paths) | replaces spell/item particles with blank stubs (the canonical "disable particles" list from minify itself) |
| **Minify Base Attacks** | blacklist (~250 paths) | replaces base-attack particles with blank stubs |
| Misc Optimization | blacklist | broad cvar pack + ambient particle blanks |
| Dark Terrain | blacklist + files/ | dark/black terrain (depends on Remove Foilage) |
| Remove Foilage | blacklist | removes grass and trees |
| Remove River | blacklist + files/ | removes the river |
| Remove Weather Effects | blacklist | removes rain/snow/fog |
| Remove Sprays | blacklist | removes player sprays |
| Mute Ambient Sounds | blacklist | mutes wind, water, etc. |
| Remove Hero Renders | css | requires Workshop Tools (skipped by CLI) |
| Remove Showcases | css | requires Workshop Tools (skipped by CLI) |

### How particle disabling works

The two `Minify *` mods are minify's own hand-curated lists of particle paths.
Each line in their `blacklist.txt` is a real `.vpcf_c` path that exists in
`pak01_dir.vpk`; we stage a blank `.vpcf_c` stub at every one of those paths
and pack the result into `pak66_dir.vpk`. When Source 2 mounts
`dota_<locale>/pak66_dir.vpk` after `pak01`, the blank stubs win and the
particles render as nothing. This is exactly the same mechanism (and the same
files) that minify itself ships.

## Usage

```bat
REM 1) Apply every supported mod (default; writes dota_minify\pak66_dir.vpk).
apply_mods.bat

REM 2) Apply specific mods (comma-separated).
apply_mods.bat "Misc Optimization,Dark Terrain,Remove River"

REM 3) Dry run (don't write any VPK).
apply_mods.bat all --dry-run

REM 4) Particle disabling “as in minify” only (no other visual mods).
apply_mods.bat "Minify Spells & Items,Minify Base Attacks"

REM 5) Combine with kill_particles_pak66 for a fully-optimized pak66.
REM    Order matters — build mods first, then merge wildcard nuke on top.
apply_mods.bat all
..\5_pak66_builder\kill_particles_pak66.bat total

REM 6) Use a different language folder (e.g. dota_russian\).
apply_mods.bat all --locale russian

REM 7) Activate the override in Steam (must be done once after building).
..\5_pak66_builder\set_launch_option.bat

REM 8) Remove dota_minify\ entirely (without touching launch options).
apply_mods.bat --uninstall
```

`--merge` unpacks the existing `pak66_dir.vpk` into staging before adding new
mod files, so particle stubs from `kill_particles_pak66.py` and minify mod
overrides end up in the same VPK.

### After running this script

1. Run `..\5_pak66_builder\set_launch_option.bat` — this adds
   `-language minify` to your Dota 2 launch options (it requires Steam to be
   closed because Steam rewrites `localconfig.vdf` on exit).
2. Restart Steam, launch Dota 2. Source 2 will mount
   `<dota>/game/dota_minify/` as a language overlay **on top of** the base
   game, so the override always wins.

## Uninstall

Same as everything else in this repo:

```bat
..\5_pak66_builder\uninstall_pak66.bat
```

This removes `<dota>\game\dota_minify\` and (after a confirmation) drops
`-language minify` from your Steam launch options.

Manual uninstall: just delete `<dota>\game\dota_minify\` and remove
`-language minify` from Dota 2's Steam launch options. The base `game/dota/`
is never touched, so Steam's "Verify integrity of game files" stays clean.

## Workshop-Tools mods (CSS)

`Remove Hero Renders` and `Remove Showcases` ship a `styling.css` that needs
to be compiled to a `.vcss_c` by the Dota 2 Workshop Tools panorama compiler.
The CLI skips them with a warning. If you need these specifically, use the
[upstream dota2-minify GUI](https://github.com/Egezenn/dota2-minify) — it
will detect Workshop Tools and compile them automatically.

## Attribution

All mods under `vendor/dota2-minify/mods/` are GPL-3.0 from upstream. See
[`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).
