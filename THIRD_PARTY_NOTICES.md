# Third Party Notices

This project incorporates code, mods, and binary stubs from third-party
projects. Each component below retains its original license and is reproduced
in this repository in compliance with that license.

## dota2-minify

- **Project**: <https://github.com/Egezenn/dota2-minify>
- **License**: GNU General Public License v3.0 ([LICENSE](LICENSE))
- **What we use**:
  - All files under `vendor/dota2-minify/blank-files/` (binary blank stubs)
  - All files under `vendor/dota2-minify/mods/` (mod definitions)
  - The `pak66`-side-loaded-VPK approach (architectural)
- **Original authors of vendored mods**:
  - **Egezenn** ([@Egezenn](https://github.com/Egezenn)) — `Minify Spells & Items`, `Minify Base Attacks`, `Remove Hero Renders`, `Remove Showcases`, `Remove Main Menu Background`
  - **robbyz512** ([@robbyz512](https://github.com/robbyz512)) — `Misc Optimization`, `Dark Terrain`, `Remove Foilage`, `Remove River`, `Remove Weather Effects`, `Remove Sprays`, `Mute Ambient Sounds`
- **Modifications by this project**:
  - The mods listed above (with the exception of `Simple Dark Terrain`)
    are copied verbatim from upstream and used as inputs to this project's
    CLI builder.
  - `Simple Dark Terrain` is a derivative of `Dark Terrain` by robbyz512.
    It contains only the 17 `.vmat_c` material-definition files from
    upstream `Dark Terrain/files/materials/`; the ~280 `.vtex_c` texture
    overrides are intentionally omitted. No file content is changed —
    only the file selection differs. The mod remains GPL-3.0 as a
    derivative work.
  - All other modifications would be tracked in commit history under
    `vendor/dota2-minify/`.

The complete GPL-3.0 license text in [`LICENSE`](LICENSE) is the same text
distributed with `dota2-minify` upstream and applies to this entire project
(see "Acknowledgments" / license section below for derivative-work obligation).

## ValvePython/vpk

- **Project**: <https://github.com/ValvePython/vpk>
- **License**: MIT
- **What we use**: imported as a runtime Python dependency (`pip install vpk`).
  Not vendored.

## ValveResourceFormat / Source 2 Viewer

- **Project**: <https://github.com/ValveResourceFormat/ValveResourceFormat>
- **License**: MIT
- **What we use**: documented as a manual user dependency for the optional
  Workshop Tools workflow in `3_workshop_tools_path/`. Not vendored.

## Pillow

- **Project**: <https://python-pillow.org/>
- **License**: HPND (BSD-like)
- **What we use**: imported as a runtime Python dependency for
  `3_workshop_tools_path/downscale_textures.py`. Not vendored.

## Dota 2 game assets

This repository **does not** redistribute any Dota 2 game assets. The toolkit
reads `.vpk` files from the user's local Steam install at runtime. The user
must own a legitimate copy of Dota 2 (free-to-play) for any of these scripts
to be useful.

The 851-byte `null.vpcf_c` particle stub is **not** committed to this
repository — it is read at runtime from the user's own
`pak01_dir.vpk` chunks.
