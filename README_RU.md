# dota10x-lowspec

Тулкит для оптимизации клиента Dota 2 под мульти-инстанс
(10 окон, фарм, прогрев акков, скриптовые боты) на слабом железе. CLI + .bat.

> ⚠️ Только визуал, только клиент. Никаких DLL-инжектов, патчей памяти или
> онлайн-сервисов. Всё работает локально на твоей собственной установке Dota 2.
> **Используешь на свой риск** — Valve по поводу косметических клиентских модов
> исторически нейтральна, но формальных гарантий нет.

## Что делает тулкит

Собирает `pak66_dir.vpk` **внутри отдельной папки-оверлея языка**
(`<dota>\game\dota_minify\` по умолчанию) и переключает Steam launch
options на `-language minify`, чтобы Dota 2 эту папку подхватила.

Это **тот же** механизм, что использует [dota2-minify](https://github.com/Egezenn/dota2-minify),
и моды которого этот проект заимствует (под GPL-3.0). Почему не класть VPK
прямо в `game/dota/`? Две причины:

1. **Steam «Verify integrity of game files»** удаляет любой не-ванильный
   pak в `game/dota/`. Папки-оверлеи языка (`game/dota_<locale>/`) Steam
   не трогает.
2. Source 2 монтирует оверлеи языка **после** базы, т.е. ассет внутри
   `dota_<locale>/pak66_dir.vpk` гарантированно перебивает тот же путь в
   `dota/pak01_*.vpk`. Старый подход «`game/dota/pak66_dir.vpk`» на части
   установок просто **не загружается** — путь через `-language` надёжен.

В собираемый pak66 можно положить:

- **Партикл-стабы** — заменяет каждый (или только подходящий под пресет)
  `.vpcf_c` на пустой `null.vpcf_c` Valve (851 байт). Спелл-визуал
  пропадает, геймплей не меняется (кулдауны, урон, хитбоксы, время полёта
  снарядов — всё на месте).
- **Моды из minify** — куратированный набор модов из
  [dota2-minify](https://github.com/Egezenn/dota2-minify)
  (см. [Моды](#моды) ниже).

Откат — одна команда (удаляет папку `dota_<locale>/` и снимает
`-language <locale>` из launch options).

## Моды

Все взяты из [dota2-minify](https://github.com/Egezenn/dota2-minify) под
лицензией GPL-3.0. Полная атрибуция авторов в
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

| Мод | Что делает | Автор оригинала |
|-----|------------|-----------------|
| **Minify Spells & Items** | заменяет ~5,400 вручную отобранных партиклов спеллов/предметов на пустые стабы (это и есть «канонический» список отключения партиклов из minify) | [Egezenn](https://github.com/Egezenn) |
| **Minify Base Attacks** | заменяет ~250 вручную отобранных партиклов базовых атак на пустые стабы | [Egezenn](https://github.com/Egezenn) |
| Misc Optimization | широкий cvar-pack + сотни ambient-партикл-стабов | [robbyz512](https://github.com/robbyz512) |
| Dark Terrain | тёмный/чёрный террейн, меньше визуального шума | [robbyz512](https://github.com/robbyz512) |
| Remove Foilage | убирает траву и деревья | [robbyz512](https://github.com/robbyz512) |
| Remove River | убирает реку (плоская плоскость вместо воды) | [robbyz512](https://github.com/robbyz512) |
| Remove Weather Effects | убирает дождь/снег/туман | [robbyz512](https://github.com/robbyz512) |
| Remove Hero Renders | убирает рендеры героев в главном меню (panorama) | [Egezenn](https://github.com/Egezenn) |
| Remove Showcases | убирает витрины косметики (panorama) | [Egezenn](https://github.com/Egezenn) |
| Remove Sprays | убирает спреи | [robbyz512](https://github.com/robbyz512) |
| Mute Ambient Sounds | глушит ambient-звуки мира (ветер, вода и т.д.) | [robbyz512](https://github.com/robbyz512) |

> **Важно:** "Remove Hero Renders" и "Remove Showcases" построены на
> модификации `styling.css` / `xml_mod.json` и требуют Workshop Tools для
> компиляции в `.vcss_c`. Они вендорятся для полноты, но **CLI их пропускает**;
> для полного эффекта используй [GUI dota2-minify](https://github.com/Egezenn/dota2-minify).

## Структура репо

```
dota10x-lowspec/
├── 1_settings/                  # autoexec.cfg, launch options, in-game settings
├── 2_particle_killer/           # Loose-file путь (легаси, ненадёжно)
├── 3_workshop_tools_path/       # Workshop Tools downscale/strip пайплайн
├── 4_overrides_helpers/         # install/uninstall для loose-file пути
├── 5_pak66_builder/             # ★ Партикл-килл + правка Steam launch options
│   ├── kill_particles_pak66.{py,bat}    # билдит dota_<locale>/pak66_dir.vpk
│   ├── set_launch_option.{py,bat}       # включает/убирает -language <locale>
│   └── uninstall_pak66.bat              # удаляет папку + launch option
├── 6_minify_mods/               # ★ Применение модов minify в pak66.vpk
│   └── apply_mods.{py,bat}              # билдит dota_<locale>/pak66_dir.vpk
├── data/                        # VPK listings + heaviest-files отчёты
├── vendor/dota2-minify/         # Upstream моды + blank stubs (GPL-3.0)
├── LICENSE                      # GPL-3.0 (обязательно — мы вендорим minify)
├── README.md                    # English
├── README_RU.md                 # этот файл
└── THIRD_PARTY_NOTICES.md       # Атрибуция
```

## Быстрый старт

### Что нужно

- Windows 10/11 с обычной установкой Dota 2
- Python 3.7+ (рекомендую 3.10+). При установке поставь галку "Add to PATH".
- Python-пакеты: `pip install vpk vdf` (`.bat`-обёртки сами их доставят при
  первом запуске)
- ~100 МБ свободного места под `pak66_dir.vpk`

### Два способа отключить партиклы

Проект поддерживает **оба** подхода minify:

1. **Курированный список (рекомендуется, 1-в-1 как в minify)**:
   новые моды `Minify Spells & Items` и `Minify Base Attacks` — это
   вручную подобранные блэклисты на ~5,600 партикл-путей, именно
   их использует сам minify. Каждый путь в списке — реальный файл
   в `pak01_dir.vpk`, поэтому оверрайд гарантированно срабатывает.
   Визуал спеллов/предметов/базовых атак исчезает, ambient/UI
   партиклы остаются.
2. **Нук-по-паттерну**: старый `kill_particles_pak66.bat` проходит
   по всем `.vpcf_c` в `pak01_dir.vpk` и стабит те, что совпадают с
   substring-паттернами пресета. «Ядерный» вариант (пресет
   `total` стабит все ~80,700 `.vpcf_c`).

### Отключить ВСЕ партиклы (ядерный вариант)

Нукает все ~80,700 `.vpcf_c` из `pak01_dir.vpk` (все спеллы, предметы, атаки,
ambient, UI, варды, курьеры — вообще всё). **Закрой Steam**, потом:

```bat
REM Шаг 1 — собрать dota_minify\pak66_dir.vpk с ВСЕМИ партиклами-стабами
5_pak66_builder\kill_particles_pak66.bat total

REM Шаг 2 — добавить "-language minify" в Steam launch options Dota 2
5_pak66_builder\set_launch_option.bat
```

Пресеты `kill_particles`: `safe` (~19,700), `aggressive` (~30,400),
`nuclear` (~39,400), `total` (~80,700 — все).

### Один проход: ядерный партикл-нук + все визуал-моды (рекомендуется)

Порядок важен: `kill_particles_pak66.bat` пишет `pak66_dir.vpk` с нуля —
значит он идёт ПЕРВЫМ. `apply_mods.bat all --merge` потом распаковывает
этот pak66, кладёт визуал-моды (тёмная карта, без реки, без травы …) сверху
и собирает обратно.

```bat
REM Шаг 1 — свежий pak66 со всеми 80,700 партиклами-стабами
5_pak66_builder\kill_particles_pak66.bat total

REM Шаг 2 — расширяем его всеми визуал-модами (тёмная карта, без реки, без травы, …)
6_minify_mods\apply_mods.bat all --merge

REM Шаг 3 — добавить "-language minify" в Steam launch options Dota 2
5_pak66_builder\set_launch_option.bat
```

Запускай Steam, заходи в Dota — никаких визуалов спеллов, фонтанного огня,
трейлов; тёмная карта, нет реки, нет погоды, нет рендеров героев в меню.
Геймплей (кулдауны, урон, хитбоксы, время полёта снарядов) — **без изменений**.

### Отключение партиклов «как в minify» (курированный список)

1-в-1 список из dota2-minify — ~5,600 вручную подобранных партикл-путей
(спеллы, предметы, базовые атаки). Меньше и более точно чем пресет `total`:

```bat
6_minify_mods\apply_mods.bat "Minify Spells & Items,Minify Base Attacks"
5_pak66_builder\set_launch_option.bat
```

Название локали меняется флагом `--locale <name>` у любого скрипта
(по умолчанию: `minify`). Свою локаль имеет смысл задать, только если
ты уже используешь сам minify или хочешь несколько профилей.

### Применить только конкретные моды

```bat
6_minify_mods\apply_mods.bat "Misc Optimization,Dark Terrain,Remove Foilage,Remove River"
5_pak66_builder\set_launch_option.bat
```

### Сократить время загрузки карты

Партиклы — не самое тяжёлое, что Dota грузит. Главные тяжи на загрузке —
войсы героев, музыка, косметические модели/текстуры и panorama-картинки.
`strip_assets_pak66` заменяет их на минимальные blank-стабы из
`vendor/dota2-minify/blank-files/` (1.5 KB на `.vsnd_c`, 3 KB на `.vmdl_c`,
1×1 px на `.vtex_c`).

Есть **три уровня агрессии**, выбирай насколько глубоко резать. Каждый
следующий уровень включает всё из предыдущего. Цифры — реальный замер по
твоему `pak01_dir.vpk` (371,479 entries):

| Bundle | Категорий | Файлов | Исходный размер | Что теряешь визуально |
|---|---:|---:|---:|---|
| **`all-safe`**       | 8  | 160,468 | ~7.6 GB | **ничего** — игра и UI выглядят 1-в-1 как ванилла |
| **`all-aggressive`** | 19 | 221,931 | ~37.6 GB | в меню пропадают портреты героев / иконки / loading-screen картинки; в самой игре герои выглядят нормально |
| **`all-extreme`**    | 23 | 284,738 | ~55.6 GB | герои / крипы / пропсы рендерятся плоскими error-текстурами, но хитбоксы / анимации / HP-бары / механика работают |

Выбирай **один** bundle (не комбинируй имена). Закрой Steam, потом:

```bat
REM Уровень 1 — нулевая визуальная цена (рекомендуемая база)
5_pak66_builder\strip_assets_pak66.bat all-safe
5_pak66_builder\set_launch_option.bat

REM Уровень 2 — главное меню теряет портреты / иконки
5_pak66_builder\strip_assets_pak66.bat all-aggressive
5_pak66_builder\set_launch_option.bat

REM Уровень 3 — герои = плоские цвета. Под автопилот / 10 ботов / прогрев акков.
5_pak66_builder\strip_assets_pak66.bat all-extreme
5_pak66_builder\set_launch_option.bat
```

#### Уровень 1 — `all-safe` (8 категорий, ~7.6 GB)

Войсы героев, музыка, звуки атак, ambient, item-sounds + чисто косметические
модели/материалы/партиклы. Всё это невидимо для геймплея: герои выглядят
как обычно, UI не трогается, хитбоксы / урон / кулдауны без изменений.
Подходит вообще всем, в том числе если ты играешь в одно окно и просто
хочешь чтобы карта быстрее грузилась.

#### Уровень 2 — `all-aggressive` (+11 категорий, ~+30 GB)

Поверх `all-safe` стабит ещё panorama-картинки (~17.8 GB), стикеры
(~11 GB), particle-текстуры, текстуры косметики, ивент-контент,
loading-screen фоны, скайбокс, tournament fan content, структурные модели
зданий.

**Цена:** в главном меню / дашборде пропадают портреты героев, иконки
предметов, loading-screen арт, превью предметов в магазине. **В самой
игре** герои выглядят нормально — деградирует только меню / инвентарь /
магазин.

#### Уровень 3 — `all-extreme` (+4 категории, ~+18 GB)

Поверх `all-aggressive` стабит текстуры героев (~3 GB), все
`materials/models/`-текстуры (~14 GB), текстуры крипов и модели юнитов.

**Цена:** герои / иллюзии / крипы / юниты на поле боя рендерятся
**плоскими error-цветами / клетчатыми текстурами**. Игра при этом
**полностью играбельна** — хитбоксы, анимации, HP-бары, механика спеллов
работают — но визуально героев друг от друга не отличишь. Подходит для
автопилот-сценариев / 10-окон-фарм / прогрева акков, когда ты в экран не
смотришь.

#### Точечный контроль по категориям

```bat
5_pak66_builder\strip_assets_pak66.bat --list
5_pak66_builder\strip_assets_pak66.bat vo,music
5_pak66_builder\strip_assets_pak66.bat panorama-images,stickers
```

Категории, которые **намеренно заблокированы** (ломают игру):
`heroes-models` (меши героев), `heroes-mats` (материалы героев),
`ui-sounds` (меню / звуки кликов), `panorama` (определения UI),
`localization` (тексты), `scripts` (npc / item / ability логика),
`vsndevts` (определения звуковых событий). Скрипт ругнётся ошибкой, если
ты их попросишь.

#### Стак с партикл-нуком и визуал-модами

`strip_assets_pak66` стакается с `kill_particles_pak66` и `apply_mods`
через `--merge`. `kill_particles_pak66` пишет `pak66_dir.vpk` с нуля,
значит он идёт первым; всё остальное — с `--merge`, чтобы дописать в тот
же VPK:

```bat
5_pak66_builder\kill_particles_pak66.bat total
5_pak66_builder\strip_assets_pak66.bat all-extreme --merge
6_minify_mods\apply_mods.bat all --merge
5_pak66_builder\set_launch_option.bat
```

Результат: все партиклы стабы, все войсы / музыка / косметика / звуки атак /
panorama-картинки / hero-текстуры стабы, все визуал-моды применены
(тёмная карта, без реки, без травы, без погоды, …). По сути **самый
агрессивный клиентский cut**, который можно сделать без модификации
самой `game/dota/`.

### Откат

```bat
5_pak66_builder\uninstall_pak66.bat
```

Удаляет `<dota>\game\dota_minify\` и (по подтверждению) убирает
`-language minify` из Steam launch options. Ванилла. `game/dota/` мы
не трогали — "Verify integrity" в Steam не сорвётся.

## 10 окон / Multi-box

Положи содержимое `1_settings/autoexec.cfg` в
`<dota>\game\dota\cfg\autoexec.cfg` и добавь в свойства Steam launch options
из `1_settings/launch_options.txt`. Главные cvar-ы:

- `engine_no_focus_sleep 50` — фоновые окна жрут ~5% CPU
- `snd_mute_losefocus 1` — звук только в активном окне
- `fps_max 120` — кап FPS на каждое окно
- `r_low 1`, `r_particle_quality 0`, `r_postprocess_enable 0` — глобальный low

Сверху — [Sandboxie-Plus](https://sandboxie-plus.com/) (или 10 пользователей
Windows) для реальной изоляции 10 клиентов.

## Лицензия

[GPL-3.0](LICENSE). Проект — производная работа от
[dota2-minify](https://github.com/Egezenn/dota2-minify) (GPL-3.0); по
копилефту GPL-3.0 любая производная обязана оставаться GPL-3.0. Подробности
в [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

Никакие игровые ассеты Dota 2 не коммитятся в репо. Тулкит читает файлы
из твоей локальной установки Dota 2 (Steam) и собирает `pak66_dir.vpk`,
который ты сам кладёшь обратно в свою установку.

## Спасибо

Без этих ребят проекта бы не было:

- [**dota2-minify**](https://github.com/Egezenn/dota2-minify) — Egezenn,
  robbyz512, MeGaNeKoS и контрибьюторы. Механизм pak66, blank-стабы и
  большинство модов — их работа.
- [**ValveResourceFormat**](https://github.com/ValveResourceFormat/ValveResourceFormat) —
  парсинг Source 2 форматов.
- [**ValvePython/vpk**](https://github.com/ValvePython/vpk) — Python-библиотека,
  которой собирается VPK.

Если тебе нужен GUI вместо CLI — **используй
[dota2-minify](https://github.com/Egezenn/dota2-minify) напрямую**. Этот
проект — CLI-сабсет под батч/скриптовые сценарии (10 окон, CI, скриптовая
настройка свежих установок).
