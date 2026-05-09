# dota10x-lowspec

Тулкит для оптимизации клиента Dota 2 под мульти-инстанс
(10 окон, фарм, прогрев акков, скриптовые боты) на слабом железе. CLI + .bat.

> ⚠️ Только визуал, только клиент. Никаких DLL-инжектов, патчей памяти или
> онлайн-сервисов. Всё работает локально на твоей собственной установке Dota 2.
> **Используешь на свой риск** — Valve по поводу косметических клиентских модов
> исторически нейтральна, но формальных гарантий нет.

## Что делает тулкит

Собирает рядом с `pak01_dir.vpk` ещё один VPK — `pak66_dir.vpk`. Source 2
монтирует все `pak*_dir.vpk` по возрастанию номера, поэтому `pak66`
переопределяет `pak01` для тех же путей. Это тот же механизм, что использует
популярный [dota2-minify](https://github.com/Egezenn/dota2-minify), и моды
которого этот проект частично заимствует (с лицензией GPL-3.0).

В собираемый pak66 можно положить:

- **Партикл-стабы** — заменяет каждый (или только подходящий под пресет)
  `.vpcf_c` на пустой `null.vpcf_c` Valve (851 байт). Спелл-визуал
  пропадает, геймплей не меняется (кулдауны, урон, хитбоксы, время полёта
  снарядов — всё на месте).
- **Моды из minify** — куратированный набор модов из
  [dota2-minify](https://github.com/Egezenn/dota2-minify)
  (см. [Моды](#моды) ниже).

Откат — одна команда (или удалить один файл).

## Моды

Все взяты из [dota2-minify](https://github.com/Egezenn/dota2-minify) под
лицензией GPL-3.0. Полная атрибуция авторов в
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

| Мод | Что делает | Автор оригинала |
|-----|------------|-----------------|
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
├── 2_particle_killer/           # Loose-file путь (легаси, может не работать)
├── 3_workshop_tools_path/       # Workshop Tools downscale/strip пайплайн
├── 4_overrides_helpers/         # install/uninstall для loose-file пути
├── 5_pak66_builder/             # ★ VPK-based партикл-килл (рекомендуется)
├── 6_minify_mods/               # ★ Применение модов minify в pak66.vpk
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
- ~100 МБ свободного места под `pak66_dir.vpk`

### Один шаг: убить все партиклы в игре

```bat
5_pak66_builder\kill_particles_pak66.bat total
```

Создаст `<dota>\game\dota\pak66_dir.vpk` (~70 МБ) с 80,731 стабом
`null.vpcf_c`. Перезапусти Dota — нет визуала спеллов, нет огня в фонтане,
нет трейлов снарядов. Геймплей не меняется.

Другие пресеты: `safe`, `aggressive`, `nuclear` (менее агрессивные).

### Применить моды minify

```bat
6_minify_mods\apply_mods.bat all
```

Или конкретный набор:

```bat
6_minify_mods\apply_mods.bat "Misc Optimization,Dark Terrain,Remove Foilage,Remove River"
```

Скрипт собирает pak66 со всеми указанными модами. Если хочешь объединить
партикл-килл + моды в одном pak66:

```bat
5_pak66_builder\kill_particles_pak66.bat total
6_minify_mods\apply_mods.bat all --merge
```

`--merge` распакует существующий pak66 в стейджинг и добавит моды поверх.

### Откат

```bat
5_pak66_builder\uninstall_pak66.bat
```

Или просто удали `<dota>\game\dota\pak66_dir.vpk`. Всё, ванилла вернулась.

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
