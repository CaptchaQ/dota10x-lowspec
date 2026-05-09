# Workshop Tools path — настоящая оптимизация (heavy lift)

Этот путь **по-настоящему** уменьшает нагрузку: ужимаем текстуры героев и карты,
упрощаем шейдеры, и компилируем результат в `_c` через официальный
**Dota 2 Workshop Tools**.

> Если хочется быстро — используй `2_particle_killer/`. Этот путь —
> для тех, кто готов один раз потратить ~30–60 минут и получить максимум.

## Что нужно установить

1. **Steam → Library → Tools → Dota 2 Workshop Tools** (бесплатно).
2. **Source 2 Viewer (CLI)** — для распаковки/декомпиляции `_c` файлов:
   - https://github.com/ValveResourceFormat/ValveResourceFormat/releases
   - Скачать `Source2Viewer-CLI.zip` (Windows). Распаковать в `tools_bin\`.
3. **Python 3.10+** + `Pillow` (`pip install pillow`).

## Структура папок workflow

```
3_workshop_tools_path\
├── tools_bin\               <- Source2Viewer-CLI.exe + DLLs (распаковать сюда)
├── extracted\               <- сюда распакуем нужные ресурсы из VPK
├── work\                    <- редактируем текстуры/материалы здесь
├── content_addon\           <- структура аддона Workshop Tools
└── compiled_overrides\      <- готовые _c файлы для game/dota/
```

## Шаги (one-by-one)

### 1. Скачать ресурсы из VPK

Запусти `extract.bat` — он вытащит из `pak01_dir.vpk` все:

- `materials/models/heroes/**/*.vtex_c` (текстуры героев)
- `materials/models/heroes/**/*.vmat_c` (материалы героев)
- `materials/maps/**/*.vtex_c` (текстуры карты)
- `materials/maps/**/*.vmat_c`
- `models/heroes/**/*.vmdl_c` (опционально, для редактирования геометрии)

Параллельно `Source2Viewer-CLI` декомпилирует их в исходники (`.png`, `.vmat`).

### 2. Уменьшить текстуры

```
python downscale_textures.py --input extracted --output work --max-size 256
```

Понизит все PNG с >256px стороной до 256px. Можно поставить 128 или 64
для сверх-low-spec режима.

### 3. Упростить материалы

```
python strip_materials.py --input extracted --output work
```

Заменяет в `.vmat`:

- `shader "hero.vfx"` → `shader "global_lit_simple.vfx"`
- Удаляет `cloth`, `subsurface`, `detail`, `normal`, `flow` параметры
- Убирает `g_flCubeMapBlend`, `g_flSelfIllumScale` и подобные

### 4. Положить в content_addon и собрать

```
copy_to_content.bat
```

Скопирует `work/*` в правильный путь:
```
<dota>/content/dota_addons/lowspec/<...>
```

Затем запусти Workshop Tools → Asset Browser → Build (или из CLI):

```
build.bat
```

вызовет:
```
"<dota>\game\bin\win64\resourcecompiler.exe" -i "content/dota_addons/lowspec/**/*"
```

Скомпилированные `_c` лягут в `<dota>/game/dota_addons/lowspec/`.

### 5. Перенести в override-папку

```
collect_compiled.bat
```

Скопирует `_c` из `game/dota_addons/lowspec/` в `compiled_overrides/`,
а `4_overrides_helpers/install.bat` зальёт их в `<dota>/game/dota/`.

## Что РЕАЛЬНО надо ужимать (приоритет)

В порядке падения отдачи:

1. **Текстуры героев** — `materials/models/heroes/` — суммарно >5 ГБ.
   Хитер на VRAM при 10 окнах. Жми до 256–512.
2. **Текстуры карты** — `materials/maps/` — почти 700 МБ.
   Жми до 256.
3. **Текстуры арканов** (опционально) — `materials/models/items/` для
   героев, которые часто мейн-пикают.
4. **Скайбокс** — `materials/skybox/` — там 4K кубмапы. Жми до 512.
5. **Декали/блад** — `materials/decals/` — заменить на 4×4 пустышки.
6. **Шейдеры героев** — `vmat` → `global_lit_simple.vfx`.

## Что НЕ трогать

- `models/heroes/*.vmdl_c` — поломает анимации, если не пересобирать.
- `panorama/*` — UI рендерится дёшево; правка может только сломать.
- `scripts/` — это игровая логика, мы не трогаем.
- `sounds/*.vsnd_c` — лучше через `volume 0.05` cvar.
- Любые particles в этой папке — для них есть `2_particle_killer/`.

## Что предоставлено в этой папке

- `extract.bat`           — распаковка нужных ресурсов из VPK
- `downscale_textures.py` — массовый ресайз PNG
- `strip_materials.py`    — упрощение `.vmat` файлов
- `copy_to_content.bat`   — раскладка в content/dota_addons/lowspec/
- `build.bat`             — вызов resourcecompiler
- `collect_compiled.bat`  — сбор скомпилированных _c в override_pack
