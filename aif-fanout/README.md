# AI Factory fan-out workflow

Этот optional package дорабатывает существующий plan одним parallel pass:
независимые ракурсы `coverage` и `risk` → выбор разработчика → применение
принятых предложений. Он намеренно отделён от `aif-classic`.

Названия ветвей — ракурсы review, не имена моделей. Текущий assisted-session
adapter закрепляет instruction contexts, но **не** выбирает provider, model или
reasoning level. Этот package не является model routing: для этого нужен
будущий model-profile protocol.

## Карта файлов

Сначала прочитайте `workflow.yaml`, затем `workflows/improve-pass.yaml`.
Root передаёт JSON plan одному проходу. Improve-pass запускает coverage/risk и ждёт обе ветви.
`workflows/improve-branch.yaml` вызывает `steps/improve.yaml` для каждого ракурса.
Join возвращает исходный plan при succeeded. Иначе choose/apply обрабатывают предложения.
`steps/choose.yaml` закрепляет выбор; `steps/apply.yaml` возвращает новый plan.
`contexts/select.yaml` короткий, поэтому инструкция остаётся рядом с metadata.
`contexts/aif-improve.yaml` закрепляет внешний host skill, без копирования его текста.
Схемы и короткие scalar ports сохранены: их связи видны без раскрытия.

```text
workflow → improve-pass → [coverage | risk] → join → done
                                              └─ choose → apply → changed
```

[Готовые входы, prepare/start и границы continue](../examples/fanout-fix/README.md).

Прежний root не обрабатывает no_work дочернего improve-pass: отказ unhandled_child_outcome сохраняется.
Это ограничение относится к остановке choose/apply; readability-порция его не исправляет.
