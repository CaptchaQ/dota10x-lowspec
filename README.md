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
| Dark Terrain | dark/black terrain, reduces visual noise (~300 files, full texture pack) | [robbyz512](https://github.com/robbyz512) |
| **Simple Dark Terrain** | lite version: only the 17 `.vmat_c` material overrides from Dark Terrain, no texture pack — much smaller VPK, faster build | derivative of [robbyz512](https://github.com/robbyz512)'s Dark Terrain |
| Remove Foilage | removes grass and trees | [robbyz512](https://github.com/robbyz512) |
| Remove River | removes the river / replaces water with flat plane | [robbyz512](https://github.com/robbyz512) |
| Remove Weather Effects | removes rain/snow/fog | [robbyz512](https://github.com/robbyz512) |
| Remove Hero Renders | removes hero renders in main menu (panorama) | [Egezenn](https://github.com/Egezenn) |
| Remove Showcases | removes cosmetic showcases (panorama) | [Egezenn](https://github.com/Egezenn) |
| **Remove Main Menu Background** | hides the dashboard background image / front-page contents (panorama) | [Egezenn](https://github.com/Egezenn) |
| Remove Sprays | removes sprays | [robbyz512](https://github.com/robbyz512) |
| Mute Ambient Sounds | mutes ambient world sounds (wind, water, etc.) | [robbyz512](https://github.com/robbyz512) |

> **Note:** "Remove Hero Renders", "Remove Showcases", and
> "Remove Main Menu Background" rely on `styling.css` modifications
> which require Workshop Tools to compile to `.vcss_c`. They are
> vendored for completeness but the CLI **skips them with a warning**
> (it can't compile CSS); for full effect on these three specific mods,
> use the original [dota2-minify GUI](https://github.com/Egezenn/dota2-minify)
> with Workshop Tools installed.

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

### Easiest way: the GUI (`dota10x_gui.bat`)

If you prefer click-to-build over typing CLI commands, double-click
**`dota10x_gui.bat`** at the repo root. It auto-detects Python, auto-installs
`vpk` + `vdf` on first run, then opens a small window where you can:

- Pick the **particle preset** (off / safe / aggressive / total).
- Pick the **asset-strip bundle** (off / all-safe / all-aggressive /
  all-extreme / all-nuclear / all-suicide).
- Pick **visual mods** — either tick "Apply all available mods" or pick
  individually. Mods that need Workshop Tools (CSS compilation) are shown
  greyed out so you don't accidentally pick something that won't take effect.
- Toggle **auto-set Steam launch option** (`-language <locale>`).

Then hit **Build pak66**. The GUI runs the four scripts in the right order
(particles → assets → mods → launch flag), passing `--merge` automatically
from step 2 onwards so each step adds to the same `pak66_dir.vpk` instead of
overwriting it. Output streams live to the log pane. **Uninstall** removes
the language-overlay folder and drops `-language <locale>` from launch
options.

> Steam must be CLOSED before you click Build / Uninstall — otherwise Steam
> overwrites `localconfig.vdf` on exit and the launch flag edit is lost.

The GUI is just a frontend — it calls the same `5_pak66_builder/` and
`6_minify_mods/` scripts described below, with the same arguments. Use the
CLI directly if you prefer scripting.

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

Particles are not the heaviest thing Dota 2 loads. The biggest disk reads at
load come from voice lines, music, cosmetic models/textures, and panorama
images. `strip_assets_pak66` replaces them with minimal blank stubs from
`vendor/dota2-minify/blank-files/` (1.5 KB per `.vsnd_c`, 3 KB per `.vmdl_c`,
1×1 px per `.vtex_c`).

There are **five tiers**, picking how aggressive you want to go. Each tier
includes everything from the previous one. Numbers are measured against a
real `pak01_dir.vpk` (371,479 entries):

| Bundle | Categories | Files stubbed | Original size | Visual cost |
|---|---:|---:|---:|---|
| **`all-safe`**       | 8  | 160,468 | ~7.6 GB  | **none** — gameplay & UI identical |
| **`all-aggressive`** | 19 | 221,931 | ~37.6 GB | menu loses hero portraits / icons / loading-screen art; heroes still look normal in-game |
| **`all-extreme`**    | 23 | 284,738 | ~55.6 GB | heroes / creeps / props render as flat error textures, but hitboxes / animations / HP bars / mechanics all work |
| **`all-nuclear`**    | 32 | 288,361 | ~57.1 GB | + legacy Flash UI gone (~1.1 GB), event teaser videos, VS-screen models, couriers / pets / profile cards become placeholders. **No gameplay impact.** |
| **`all-suicide`**    | 42 | 290,035 | ~58.3 GB | + 3D hero-pick previews, map textures, event-map content (Cavern Crawl, Reef Bender, Diretide). **Likely breaks event game modes / hero-pick UI.** |

Pick one bundle (do **not** combine bundle names). Close Steam first, then:

```bat
REM Tier 1 — zero visual impact (recommended baseline)
5_pak66_builder\strip_assets_pak66.bat all-safe
5_pak66_builder\set_launch_option.bat

REM Tier 2 — main menu loses portraits / icons
5_pak66_builder\strip_assets_pak66.bat all-aggressive
5_pak66_builder\set_launch_option.bat

REM Tier 3 — heroes are flat colors. Useful for headless 10-box bot farms.
5_pak66_builder\strip_assets_pak66.bat all-extreme
5_pak66_builder\set_launch_option.bat

REM Tier 4 — also kills legacy Flash UI, event videos, VS-screen, couriers.
5_pak66_builder\strip_assets_pak66.bat all-nuclear
5_pak66_builder\set_launch_option.bat

REM Tier 5 — also kills 3D hero-pick previews + event-map assets. May break events.
5_pak66_builder\strip_assets_pak66.bat all-suicide
5_pak66_builder\set_launch_option.bat
```

#### Tier 1 — `all-safe` (8 categories, ~7.6 GB)

Voice lines, music, attack sounds, ambient sfx, item sounds, and pure cosmetic
models / materials / particles. Everything here is invisible to gameplay:
heroes still look normal, the UI is untouched, hitboxes / damage / cooldowns
unchanged. Recommended for everyone, including 1-instance "I just want faster
loads" users.

#### Tier 2 — `all-aggressive` (+11 categories, ~+30 GB)

On top of `all-safe`, also stubs panorama images (~17.8 GB), stickers
(~11 GB), particle textures, cosmetic textures, event content, loading-screen
backgrounds, skybox, tournament fan content, and structural prop models.

**Tradeoff:** the main menu / dashboard loses most of its hero portraits,
item icons, loading-screen art, and item-shop preview images. **In actual
gameplay** heroes still look normal — only menu / inventory / shop visuals
degrade.

#### Tier 3 — `all-extreme` (+4 categories, ~+18 GB)

On top of `all-aggressive`, also stubs hero textures (~3 GB), every
`materials/models/` texture (~14 GB), creep textures, and unit models.

**Tradeoff:** heroes / illusions / creeps / units render as **flat error
colors / checkerboards** during gameplay. The game is still 100 % playable —
hitboxes, animations, HP bars, spell mechanics all work — but you literally
cannot tell heroes apart by looking. Suitable for autopilot 10-box / bot
farms / scripted account warming where you don't actually look at the screen.

#### Tier 4 — `all-nuclear` (+9 categories, ~+1.5 GB)

On top of `all-extreme`, also stubs:

- `resource/flash3/` PNG assets (~1.14 GB) — legacy Flash UI replaced
  long ago by Panorama; pure dead weight.
- `scripts/workshop_import_templates/` (~98 MB) — dev-only Workshop
  import templates.
- `models/versus/` (~133 MB) — pre-match VS-screen models.
- `materials/overlays/` (~85 MB) — terrain decals (Aegis logos, motifs).
- `models/courier/` + `models/pets/` (~70 MB) — courier / pet models.
- `materials/portraits_card/` (~35 MB) — profile portrait cards.

**Tradeoff:** main menu loses some legacy banners and event teaser videos;
couriers / pets become placeholders; pre-match VS-screen has no portraits.
**Zero gameplay impact.**

#### Tier 5 — `all-suicide` (+10 categories, ~+1.2 GB)

On top of `all-nuclear`, also stubs:

- `models/ui/` (~567 MB) — 3D hero-pick / loadout previews.
- `materials/maps/` (~97 MB) — terrain texture atlas.
- `materials/nature/` (~142 MB) — terrain nature decals.
- `maps/{reef,cavern,jungle,journey,ti10}_assets/` (~410 MB) —
  event-mode map content.

**Tradeoff:** hero-pick / loadout previews are empty boxes; event modes
(Cavern Crawl, Reef Bender, Diretide-style mini-games) may **fail to load
or crash**. Use only if you don't play any event mode and don't care about
3D hero previews.

#### Finer-grained category control

```bat
5_pak66_builder\strip_assets_pak66.bat --list
5_pak66_builder\strip_assets_pak66.bat vo,music
5_pak66_builder\strip_assets_pak66.bat panorama-images,stickers
```

Categories that are **intentionally blocked** because they brick the game:
`heroes-models` (hero meshes), `heroes-mats` (hero materials), `ui-sounds`
(menu / event audio), `panorama` (UI definitions), `localization`,
`scripts` (npc / item / ability logic), `vsndevts` (sound event
definitions). The script will refuse with an error if you ask for any of
these.

#### Stacking with particle nuke + visual mods

`strip_assets_pak66` stacks with `kill_particles_pak66` and `apply_mods`
via `--merge`. `kill_particles_pak66` writes a fresh `pak66_dir.vpk`, so it
goes first; everything afterwards uses `--merge` to layer onto the same VPK:

```bat
5_pak66_builder\kill_particles_pak66.bat total
5_pak66_builder\strip_assets_pak66.bat all-extreme --merge
6_minify_mods\apply_mods.bat all --merge
5_pak66_builder\set_launch_option.bat
```

Result: every particle stubbed, every voice line / music / cosmetic / attack
sound / panorama image / hero texture stubbed, every visual mod applied
(dark terrain, no river, no foliage, no weather, etc.). About **the most
aggressive client-side cut** you can do without modifying `game/dota/`
itself.

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
