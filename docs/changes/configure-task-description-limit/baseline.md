# Первичная проверка исходного состояния

Дата: 2026-11-10. Эта проверка сопровождает подготовку change.
Рабочая ветка: `codex/diagnose-revoked-shared-schemas`, HEAD `1a84177`.
До подготовки change дерево было чистым.
Shipping packages в этой задаче не меняются.

## Сверка Core

`gh release list -R StenHigh/prifly --exclude-pre-releases -L 5` вернул latest stable `v0.13.89`.
Шапка `CONTEXT_STATE.md` уже указывает ворота на той же версии.
Новых stable нет; повторный запуск verify/compatibility для документации не выполнялся.
Прежняя проверка восьми пакетов: [released 0.13.89 evidence](https://github.com/StenHigh/prifly-aif-workflows/blob/ea80f4730deb0e4ec4d166d68b2fb3d189491c6a/docs/changes/engine/release-0.13.89-results.json).

Проверен исходник тега `v0.13.89`, а не рабочее дерево Core после этого тега:

1. [Extension reference](https://github.com/StenHigh/prifly/blob/v0.13.89/examples/authoring/extension-authoring-reference.yaml) описывает settings для объявленных project-scoped inputs.
2. [project_compile.go](https://github.com/StenHigh/prifly/blob/v0.13.89/cmd/prifly/project_compile.go) содержит `projectSetWorkflowSetting` и запись `configuration["default"] = value`.
3. [Project profile reference](https://github.com/StenHigh/prifly/blob/v0.13.89/examples/authoring/project-profile-authoring-reference.yaml) отделяет naming inputs от workflow inputs.

Naming input — проектные данные для имени рабочей ветки или worktree.
Он не меняет compiled refs и не решает эту задачу.
Вывод о недостаточности settings основан на опубликованном исходнике.
Общий вывод о невозможности всех существующих композиций пока не заявлен.

## Проверка пакетов

`aif-classic`, `aif-profiled` и `aif-fix` содержат одинаковую схему `aif:schema/task@1.1.0`.
В каждой схеме `description` имеет `minLength: 1` и `maxLength: 12000`.
В classic общий alias используется в root, plan и четырёх nested verify/review workflows.
Настройка корневого входа без этих потребителей не удовлетворяет A7.

Python `jsonschema.Draft202012Validator` проверил каждую из трёх исходных схем:

| Длина description | Результат для каждой схемы |
|---|---|
| 12 000 | valid |
| 12 001 | error: path `/description`, validator `maxLength` |
| 16 557 | error: path `/description`, validator `maxLength` |

Проверка использовала строку из повторяемой кириллической буквы `я`.
Она не использовала приватное описание владельца.
`python3 -B tools/derive_profiled.py --check` завершился с кодом 0.

## Пределы доказательства

Отказ native prepare на 0.13.88 взят из сообщения владельца.
В этой подготовке он не воспроизводился через CLI.
Здесь не выполнялись новые native prepare/start/continue, обновление установленного workflow или живые модели.
Новый YAML-синтаксис не проверялся, поскольку механизм ещё не выбран.
Оставшиеся работы явно перечислены в [tasks.md](tasks.md).

После этой первичной проверки выполнена отдельная [native-проверка v0.13.89](native.md).
Она проверяет prepare/start, profiles, settings, composition и compile values на generic fixture.
Исторический scope первичной проверки выше сохранён; новый результат не является приёмкой shipping workflows.
