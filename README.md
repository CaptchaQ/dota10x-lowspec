# dota10x-lowspec

A Dota 2 client-side optimizer focused on running multiple instances simultaneously
(10-box farm, scripted bots, account warming) on modest hardware. CLI + .bat scripts.

> ⚠️ Visual / client-side only. No gameplay advantage. No injected DLLs, no memory
> patches, no online services. Everything runs locally against the user's own
> Dota 2 install. **Use at your own risk** — Valve's stance on cosmetic client
> mods has historically been permissive but not formally guaranteed.

## What this does

Builds a side-loaded VPK archive (`pak66_dir.vpk`) that gets mounted alongside
Valve's `pak01_dir.vpk`. Source 2 mounts every `pak*_dir.vpk` in numerical order,
so `pak66` overrides `pak01` for the same asset paths. This is the same mechanism
that the well-known [dota2-minify](https://github.com/Egezenn/dota2-minify) project
uses, and that this project borrows several mods from.

The VPK we build can contain any combination of:

- **Particle null-stubs** — replaces every (or only matched) `.vpcf_c` with
  Valve's empty 851-byte `null.vpcf_c`. Spell visuals disappear, gameplay is
  unaffected (cooldowns, damage, hitboxes, projectile travel time all normal).
- **Vendored minify mods** — a curated subset of the
  [dota2-minify](https://github.com/Egezenn/dota2-minify) mod catalog
  (see [Mods included](#mods-included) below).

Reverting is one command (or one file deletion).

## Mods included

All vendored from [dota2-minify](https://github.com/Egezenn/dota2-minify) under
GPL-3.0. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for full
attribution to original mod authors.

| Mod | Effect | Original author |
|-----|--------|-----------------|
| Misc Optimization | broad cvar pack + hundreds of ambient particle blanks | [robbyz512](https://github.com/robbyz512) |
| Dark Terrain | dark/black terrain, reduces visual noise | [robbyz512](https://github.com/robbyz512) |
| Remove Foilage | removes grass and trees | [robbyz512](https://github.com/robbyz512) |
| Remove River | removes the river / replaces water with flat plane | [robbyz512](https://github.com/robbyz512) |
| Remove Weather Effects | removes rain/snow/fog | [robbyz512](https://github.com/robbyz512) |
| Remove Hero Renders | removes hero renders in main menu (panorama) | [Egezenn](https://github.com/Egezenn) |
| Remove Showcases | removes cosmetic showcases (panorama) | [Egezenn](https://github.com/Egezenn) |
| Remove Sprays | removes sprays | [robbyz512](https://github.com/robbyz512) |
| Mute Ambient Sounds | mutes ambient world sounds (wind, water, etc.) | [robbyz512](https://github.com/robbyz512) |

> **Note:** "Remove Hero Renders" and "Remove Showcases" rely on `styling.css` /
> `xml_mod.json` modifications which require Workshop Tools to recompile.
> They are vendored for completeness but **only the panorama-style hooks**
> are applied by this CLI; for full effect on these two specific mods, use
> the original [dota2-minify GUI](https://github.com/Egezenn/dota2-minify).

## Repository layout

```
dota10x-lowspec/
├── 1_settings/                  # autoexec.cfg, launch options, in-game settings
├── 2_particle_killer/           # Loose-file override path (legacy fallback)
├── 3_workshop_tools_path/       # Workshop Tools downscale/strip pipeline
├── 4_overrides_helpers/         # install/uninstall for the loose-file path
├── 5_pak66_builder/             # ★ VPK-based particle override (recommended)
├── 6_minify_mods/               # ★ Apply vendored minify mods into pak66.vpk
├── data/                        # VPK listings + heaviest-files reports
├── vendor/dota2-minify/         # Upstream mods + blank stubs (GPL-3.0)
├── LICENSE                      # GPL-3.0 (required because we vendor minify)
├── README.md                    # this file
├── README.ru.md                 # Russian readme
└── THIRD_PARTY_NOTICES.md       # Attribution
```

## Quickstart

### Requirements

- Windows 10/11 with a normal Dota 2 install
- Python 3.7+ (3.10+ recommended). Add to PATH.
- 100 MB free disk for `pak66_dir.vpk`

### One-shot: kill every particle in the game

```bat
5_pak66_builder\kill_particles_pak66.bat total
```

This produces `<dota>/game/dota/pak66_dir.vpk` (~70 MB) containing 80,731
`null.vpcf_c` stubs. Restart Dota — no spell visuals, no fountain fire, no
trails. Gameplay unchanged.

Other presets: `safe`, `aggressive`, `nuclear` (less aggressive cuts).

### Apply minify mods

```bat
6_minify_mods\apply_mods.bat all
```

Or a curated set:

```bat
6_minify_mods\apply_mods.bat "Misc Optimization,Dark Terrain,Remove Foilage,Remove River"
```

This appends mod assets to the pak66 build (or builds a fresh one if none
exists). Final `pak66_dir.vpk` contains particles+mods together.

### Uninstall

```bat
5_pak66_builder\uninstall_pak66.bat
```

Or just delete `<dota>/game/dota/pak66_dir.vpk`. One file. Vanilla restored.

## Multi-instance / 10-box

`1_settings/autoexec.cfg` and `1_settings/launch_options.txt` cover:

- `engine_no_focus_sleep 50` — background windows drop to ~5% CPU
- `snd_mute_losefocus 1` — sound only on focused window
- `fps_max 120` — caps cap GPU per instance
- `r_low 1`, `r_particle_quality 0`, `r_postprocess_enable 0` — global visual cuts

Combine with [Sandboxie-Plus](https://sandboxie-plus.com/) (or 10 Windows users)
to actually launch 10 isolated clients.

## License

[GPL-3.0](LICENSE). This project derives from
[dota2-minify](https://github.com/Egezenn/dota2-minify) (GPL-3.0) and copies
mod content from it; under GPL-3.0 copyleft, derivative works must remain
GPL-3.0. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

No Dota 2 game assets are committed. The toolkit reads files from the user's
own local Dota 2 install (Steam) and produces a `pak66_dir.vpk` that the user
places into their own install.

## Acknowledgments

This project would not exist without the work of:

- [**dota2-minify**](https://github.com/Egezenn/dota2-minify) — Egezenn,
  robbyz512, MeGaNeKoS, and contributors. The pak66 mechanism, blank-file
  stubs, and most mods are theirs.
- [**ValveResourceFormat**](https://github.com/ValveResourceFormat/ValveResourceFormat) —
  Source 2 file formats, used to inspect VPKs.
- [**ValvePython/vpk**](https://github.com/ValvePython/vpk) — Python library
  that builds the actual VPK archive.

If you want a polished GUI experience instead of CLI scripts, **use
[dota2-minify](https://github.com/Egezenn/dota2-minify) directly**. This
project is a CLI-focused subset for batch / scripted use cases (10-box, CI,
fresh-install scripted setup).
