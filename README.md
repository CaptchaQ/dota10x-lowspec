# dota10x-lowspec

A Dota 2 client-side optimizer focused on running multiple instances simultaneously
(10-box farm, scripted bots, account warming) on modest hardware. CLI + .bat scripts.

> ⚠️ Visual / client-side only. No gameplay advantage. No injected DLLs, no memory
> patches, no online services. Everything runs locally against the user's own
> Dota 2 install. **Use at your own risk** — Valve's stance on cosmetic client
> mods has historically been permissive but not formally guaranteed.

## What this does

Builds a side-loaded VPK archive (`pak66_dir.vpk`) inside a **language-overlay
folder** (`<dota>/game/dota_minify/`, by default), then flips the Steam launch
options for Dota 2 to include `-language minify` so the game mounts that folder.

This is the exact same mechanism the well-known
[dota2-minify](https://github.com/Egezenn/dota2-minify) project uses, and that
this project borrows several mods from. Why not put the VPK directly into
`game/dota/`? Two reasons:

1. **Steam's "Verify integrity of game files"** wipes any non-vanilla pak
   inside `game/dota/`. Language overlays (`game/dota_<locale>/`) are left
   alone.
2. Source 2 mounts language overlays **after** the base game, so an asset
   inside `dota_<locale>/pak66_dir.vpk` is guaranteed to win over the same
   path in `dota/pak01_*.vpk`. The previously documented
   `game/dota/pak66_dir.vpk` approach can be ignored / not loaded by Source 2
   on some installations — the language-overlay path is reliable.

The VPK we build can contain any combination of:

- **Particle null-stubs** — replaces every (or only matched) `.vpcf_c` with
  Valve's empty 851-byte `null.vpcf_c`. Spell visuals disappear, gameplay is
  unaffected (cooldowns, damage, hitboxes, projectile travel time all normal).
- **Asset stubs (load-time killer)** — replaces heavy categories beyond
  particles (hero voice lines, music, attack sounds, cosmetic models) with
  blank stubs. ~7 GB of assets become ~2 KB of stubs, which dramatically cuts
  Dota 2's map load time. See [Cut map load time](#cut-map-load-time) below.
- **Vendored minify mods** — a curated subset of the
  [dota2-minify](https://github.com/Egezenn/dota2-minify) mod catalog
  (see [Mods included](#mods-included) below).

Reverting is one command (deletes the `dota_<locale>/` folder and drops
`-language <locale>` from launch options).

## Mods included

All vendored from [dota2-minify](https://github.com/Egezenn/dota2-minify) under
GPL-3.0. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for full
attribution to original mod authors.

| Mod | Effect | Original author |
|-----|--------|-----------------|
| **Minify Spells & Items** | replaces ~5,400 hand-curated spell/item particles with blank stubs (the canonical “disable particles” list from minify) | [Egezenn](https://github.com/Egezenn) |
| **Minify Base Attacks** | replaces ~250 hand-curated base-attack particles with blank stubs | [Egezenn](https://github.com/Egezenn) |
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
├── 2_particle_killer/           # Loose-file override path (legacy / unreliable)
├── 3_workshop_tools_path/       # Workshop Tools downscale/strip pipeline
├── 4_overrides_helpers/         # install/uninstall for the loose-file path
├── 5_pak66_builder/             # ★ Particle/asset nukes + Steam launch-option helper
│   ├── kill_particles_pak66.{py,bat}    # particle .vpcf_c -> null stubs
│   ├── strip_assets_pak66.{py,bat}      # voice/music/cosmetics -> blank stubs (load-time)
│   ├── set_launch_option.{py,bat}       # adds/removes -language <locale>
│   └── uninstall_pak66.bat              # removes folder + launch option
├── 6_minify_mods/               # ★ Apply vendored minify mods into pak66
│   └── apply_mods.{py,bat}              # builds dota_<locale>/pak66_dir.vpk
├── data/                        # VPK listings + heaviest-files reports
├── vendor/dota2-minify/         # Upstream mods + blank stubs (GPL-3.0)
├── LICENSE                      # GPL-3.0 (required because we vendor minify)
├── README.md                    # this file
├── README_RU.md                 # Russian readme
└── THIRD_PARTY_NOTICES.md       # Attribution
```

## Quickstart

### Requirements

- Windows 10/11 with a normal Dota 2 install
- Python 3.7+ (3.10+ recommended). Add to PATH.
- Python packages: `pip install vpk vdf` (the `.bat` wrappers install them on
  first run if missing)
- ~100 MB free disk for `pak66_dir.vpk`

### Two ways to disable particles

This project ships **both** of minify's particle-disable approaches:

1. **Curated list (recommended, identical to minify):** the new
   `Minify Spells & Items` and `Minify Base Attacks` mods ship hand-picked
   blacklists of ~5,600 particle paths that minify itself uses. Every entry
   is a real path that exists in `pak01_dir.vpk`, so the override is
   guaranteed to bind. Visuals for spells / items / base attacks disappear,
   ambient and UI particles stay.
2. **Pattern-matching wildcard nuke:** the older `kill_particles_pak66.bat`
   matches every `.vpcf_c` in `pak01_dir.vpk` against substring patterns and
   stubs them out. This is the “nuclear” option (`total` preset stubs all
   ~80,700 `.vpcf_c` files).

### Disable EVERY particle (nuclear)

This nukes all ~80,700 `.vpcf_c` files in `pak01_dir.vpk` (every spell, item,
attack, ambient, UI, ward, courier, etc.). Close Steam first, then:

```bat
REM Step 1 — build dota_minify\pak66_dir.vpk with EVERY particle stubbed
5_pak66_builder\kill_particles_pak66.bat total

REM Step 2 — add "-language minify" to Dota 2 Steam launch options
5_pak66_builder\set_launch_option.bat
```

Kill-particles presets: `safe` (~19,700), `aggressive` (~30,400),
`nuclear` (~39,400), `total` (~80,700 — all).

### One-shot: total particle nuke + all visual mods (recommended)

Order matters: `kill_particles_pak66.bat` writes a fresh `pak66_dir.vpk`,
so it must run first. `apply_mods.bat all --merge` then unpacks that pak66,
layers the visual mods (dark terrain, no river, no foliage, etc.) on top,
and repacks.

```bat
REM Step 1 — fresh pak66 with all 80,700 particles stubbed
5_pak66_builder\kill_particles_pak66.bat total

REM Step 2 — extend it with all visual mods (dark terrain, no river, no foliage, ...)
6_minify_mods\apply_mods.bat all --merge

REM Step 3 — add "-language minify" to Dota 2 Steam launch options
5_pak66_builder\set_launch_option.bat
```

Now relaunch Steam, start Dota — no spell visuals, no fountain fire, no
trails, dark terrain, no river, no weather, no menu hero renders. Gameplay
(cooldowns, damage, hitboxes, projectile travel time) is **unchanged**.

### Minify-style particle disabling only (curated list)

Identical to what dota2-minify ships — ~5,600 hand-picked spell/item/base-attack
particle paths. Smaller and more targeted than the wildcard `total` preset:

```bat
6_minify_mods\apply_mods.bat "Minify Spells & Items,Minify Base Attacks"
5_pak66_builder\set_launch_option.bat
```

The locale name is configurable via `--locale <name>` on every script
(default: `minify`). Use a different locale only if you want to keep an
existing `dota_minify/` folder around or you already use minify itself.

### Apply only specific minify mods

```bat
6_minify_mods\apply_mods.bat "Misc Optimization,Dark Terrain,Remove Foilage,Remove River"
5_pak66_builder\set_launch_option.bat
```

### Cut map load time

Particles are not the heaviest thing Dota 2 loads. On a stock install
`pak01_dir.vpk` contains:

| Category | Files | Original size | Brick risk |
|----------|-------|---------------|------------|
| `sounds/vo/**/*.vsnd_c` (hero voice lines) | 91,020 | **3,773 MB** | safe |
| `models/items/**/*.vmdl_c` (cosmetics) | 12,245 | **1,483 MB** | safe |
| `sounds/music/**/*.vsnd_c` | 876 | **1,130 MB** | safe |
| `sounds/weapons/**/*.vsnd_c` (attack sfx) | 2,639 | **792 MB** | safe |
| `materials/models/items/**/*.vmat_c` | 13,317 | **131 MB** | safe |
| `particles/econ/items/**/*.vpcf_c` | 39,945 | **102 MB** | safe |
| `sounds/items/**/*.vsnd_c` | 184 | 81 MB | safe |
| `sounds/ambient/**/*.vsnd_c` | 242 | 158 MB | safe |
| **TOTAL `all-safe`** | **160,468** | **~7.6 GB** | safe |
| `models/heroes/**` (base heroes) | 1,705 | 513 MB | **DO NOT** — game crashes |
| `sounds/ui/**` | 556 | 153 MB | **DO NOT** — menu breaks |

Replace every `all-safe` file with the minimal blank stub from
`vendor/dota2-minify/blank-files/` (1.5 KB per `.vsnd_c`, 3 KB per `.vmdl_c`):

```bat
REM Step 1 — stub all 160k+ heavy assets (saves ~7.6 GB of disk reads at load)
5_pak66_builder\strip_assets_pak66.bat all-safe

REM Step 2 — add "-language minify" to Steam launch options
5_pak66_builder\set_launch_option.bat
```

Finer-grained category control (no spaces between names):

```bat
5_pak66_builder\strip_assets_pak66.bat vo,music
5_pak66_builder\strip_assets_pak66.bat --list
```

It stacks with the particle nuke and the visual mods — `kill_particles_pak66`
writes a fresh `pak66_dir.vpk`, so it goes first; `strip_assets_pak66 --merge`
and `apply_mods --merge` then layer onto the same VPK:

```bat
5_pak66_builder\kill_particles_pak66.bat total
5_pak66_builder\strip_assets_pak66.bat all-safe --merge
6_minify_mods\apply_mods.bat all --merge
5_pak66_builder\set_launch_option.bat
```

Result: every particle stubbed, every voice line / music / cosmetic / attack
sound stubbed, every visual mod applied. **Tradeoff:** heroes will be silent
(no voice lines, no attack sounds) and cosmetic models render as nothing —
base hero models / animations / UI / spell mechanics all still work.

### Uninstall

```bat
5_pak66_builder\uninstall_pak66.bat
```

This deletes `<dota>/game/dota_minify/` and (after a confirmation) removes
`-language minify` from your Steam launch options. Vanilla restored — no
touches to `game/dota/`, no risk of triggering Steam's "Verify integrity".

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
