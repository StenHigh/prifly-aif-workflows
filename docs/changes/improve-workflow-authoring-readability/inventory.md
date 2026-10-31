# Inventory shipping packages

Срез: после принятого patch classic, до bump и derived profiled, 2026-10-31.
Сложный mapping — flow mapping с несколькими полями либо вложенной коллекцией.
Длинная инструкция — inline `text/markdown` не короче 500 UTF-8 bytes.
Короткие scalar ports и списки не требуют механического изменения.
Счётчики показывают область review; они не являются обязательной целью обнуления.

| Package | Сложные flow mappings | Длинные inline инструкции | Навигация и решение |
|---|---:|---:|---|
| aif-classic | 145 | 9 | Первая порция: принятые семь файлов и карта root/verify. Остальные readable части сохраняются в этой порции. |
| aif-profiled | 202 | 10 | Первая порция: штатный derive classic, собственная карта и package-local source. Ручные копии запрещены. |
| aif-fanout | 40 | 0 | Следующая порция: раскрыть parallel bindings/join, добавить карту файлов. Короткие инструкции оставить. |
| aif-fix | 160 | 11 | Следующая порция: root/repair bindings и длинные Markdown bridges; добавить карту файлов. |
| aif-feature | 18 | 15 | Следующая порция: quality/parallel bindings и длинные Markdown bridges; текущий flow дополнить картой файлов. |
| aif-review-evidence | 1 | 1 | Следующая порция: coverage bindings и review bridge; текущий flow дополнить картой файлов. |
| aif-ui-ux | 1 | 5 | Следующая порция: environment/reader bindings и Markdown bridges; дополнить карту файлов. |
| openclaw-test-audit | 0 | 2 | Следующая порция: quality bindings и audit bridge; текущий flow дополнить картой файлов. |

Executable Python contexts не переносим в Markdown. Это программные входы, а не инструкции читателя.
Host skill source pointers сохраняем. Их содержание принадлежит внешнему AI Factory.
Самостоятельные examples и project overlays сохраняют собственные pinned версии; обновление source packages не означает их автоматическую замену.
