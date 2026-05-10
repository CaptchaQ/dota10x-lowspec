<!-- LANG:EN -->
Stubs all 312 tree / bush / foliage `.vmdl_c` model files in
`pak01_dir.vpk` with a 3 KB blank model. Trees, bushes, mushrooms,
flowers, lily pads and other ground props **physically disappear** from
the screen instead of being rendered as broken / pink error textures
(which is what the older `Remove Foilage` mod does — that one only
stubs materials, not models).

Gameplay is **unaffected**: tree collision, line of sight, vision
blocking and Tango / Quelling Blade chopping are all server-side and
do not depend on the client model. Hero abilities that interact with
trees (Furion Sprout, Tinker rearm bushes, Treant ult) work exactly
the same.

Scope:

- All 174 vanilla tree props in `models/props_tree/**.vmdl_c` (oak,
  pine, palm, dire, desert, bamboo, cypress, snow, autumn, spring
  variants + destruction / inspector / sfm sub-models + stumps).
- 138 event-map foliage models — Cavern, Journey, Jungle, Reef,
  Summer, TI10 and Crownfall side-buildings (bushes, mushrooms,
  plants, flowers, lily pads, topiary).

Use this together with the upstream `Remove Foilage` and `Tree Mod`
for the strongest effect, or alone if you want trees gone but the
ground texture untouched.

This is a derivative work — original concept and approach from
Egezenn / robbyz512 (`dota2-minify`, GPL-3.0). The blacklist itself
was generated from the file index of `pak01_dir.vpk`.

<!-- LANG:RU -->
Стабит все 312 файлов моделей деревьев / кустов / листвы (`.vmdl_c`)
в `pak01_dir.vpk` пустой 3-килобайтной заглушкой. Деревья, кусты,
грибы, цветы, кувшинки и прочие наземные объекты **физически исчезают**
с экрана, а не рендерятся как сломанные розовые текстуры (что делает
старый мод `Remove Foilage` — он стабит только материалы, не модели).

Геймплей **не страдает**: коллизия деревьев, линия видимости, блок
обзора и руб Tango / Quelling Blade — всё серверное и не зависит от
клиентской модели. Способности, взаимодействующие с деревьями
(Furion Sprout, Tinker, Treant ult) работают как обычно.

Что покрывается:

- Все 174 ванильных tree-prop в `models/props_tree/**.vmdl_c` (oak,
  pine, palm, dire, desert, bamboo, cypress, snow, autumn, spring +
  destruction / inspector / sfm-подмодели + пни).
- 138 моделей листвы из event-карт — Cavern, Journey, Jungle, Reef,
  Summer, TI10 и Crownfall (кусты, грибы, растения, цветы, кувшинки,
  topiary).

Можно использовать вместе с `Remove Foilage` и `Tree Mod` для
максимального эффекта, или отдельно — если хочется убрать деревья,
но не трогать текстуру земли.

Это derivative — исходная концепция и подход от Egezenn / robbyz512
(`dota2-minify`, GPL-3.0). Сам blacklist собран из файлового индекса
`pak01_dir.vpk`.
