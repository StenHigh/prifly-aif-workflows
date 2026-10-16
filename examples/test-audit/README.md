# Самостоятельный OpenClaw test audit

Примеры для выпущенного `openclaw-test-audit@1.0.0` из
[v1.53.0](../../docs/releases/v1.53.0.md). Нужны Pri-Fly ≥0.13.77, Python 3
и coding host. AI Factory и установленный OpenClaw skill не требуются.

| Проект | Шаблон | Какие пути выбрать |
| --- | --- | --- |
| Python / pytest | [python.config.json](python.config.json) | `tests/`, вложенные tests, `test_*.py`, `*_test.py`. |
| Node / TypeScript | [node.config.json](node.config.json) | test/tests, `*.test.*`, `*.spec.*`, `__tests__/`. |
| Monorepo packages/apps | [monorepo.config.json](monorepo.config.json) | Корневые tests и тесты внутри packages/apps. |

Patterns — исходная настройка, которую нужно сверить со структурой проекта.
Используется Python `fnmatchcase`: `*` включает `/`. Весь изменённый test/helper/
fixture файл, подходящий под pattern, попадает в аудит. Неподходящий путь
программа не обнаружит сама по синтаксису языка. Нулевой SHA в JSON — placeholder;
подготовьте рабочий config с явной исходной базой задачи.

## Подготовить вход

Из корня целевого инициализированного проекта установите пакет:

```sh
prifly project workflows add openclaw-test-audit --repository .
prifly project local set --repository . --allow-executable python=/absolute/path/to/python3
```

Команды ниже предполагают checkout этого репозитория с примерами в
`/absolute/path/to/aif-workflows`. Подставьте свой путь и исходный commit/ref
задачи вместо `TASK_BASE_COMMIT_OR_REF`. Например, `origin/main` подходит, если
именно он задаёт нужную базу вашей ветки. Сохранённый SHA после этого не сдвигается.

```sh
python3 -B /absolute/path/to/aif-workflows/examples/test-audit/prepare_config.py \
  --repository . --base TASK_BASE_COMMIT_OR_REF --template python \
  --output /tmp/openclaw-audit-config.json
```

Для Node или monorepo измените `--template`. Скрипт читает Git, подставляет полный
локальный SHA, записывает новый файл вне целевого дерева и сохраняет выбранные
patterns. Существующий config он не перезаписывает. Проверьте результат и при
необходимости отредактируйте patterns. `--require-separate-session` делает
отдельную reviewer-сессию обязательной; её недоступность даст blocked/partial.
Этот флаг не устанавливает и не подтверждает другую модель.

## Просмотреть и запустить

Сохраните изменения задачи и проектную установку workflow в обычных commits
перед отдельным запуском. В `checkout` новый Run требует чистого дерева;
`worktree` начинается с tracked состояния HEAD и не переносит dirty/untracked
файлы другого Run. Аудит незакоммиченной реализации живого Run подключается
внутри него через [проектный маршрут](../test-audit-extension/README.md).

```sh
prifly project questionnaire --repository . --launch openclaw-test-audit \
  --host codex-cli --workspace worktree --input config=/tmp/openclaw-audit-config.json \
  --allow-execution --prepare
```

Просмотрите summary. Подставьте его **полный** `review_digest` вместо
`REVIEW_DIGEST`, сохранив остальные аргументы:

```sh
prifly project start --repository . --launch openclaw-test-audit \
  --host codex-cli --workspace worktree --input config=/tmp/openclaw-audit-config.json \
  --allow-execution --expected-launch-digest REVIEW_DIGEST
```

`codex-app` и `claude-code` — другие поддерживаемые host names. Host runner
обрабатывает выданный assisted task по sealed bridge; после отчёта program
evaluator проверяет coverage и candidate. Сам пример не заполняет отчёт за AI.
При пустой выборке Run завершается без assisted task.

## Разобрать результат

| Изменения / наблюдения | Gate | Outcome |
| --- | --- | --- |
| Относительно базы изменён только production-файл, test paths прежние | `skipped` | `succeeded`, AI-сессии нет. |
| Добавлен тест в существующий test-файл, полный актуальный отчёт без дефектов | `passed` | `succeeded`. |
| Reviewer нашёл конкретный дефект теста | `failed` | `partial`, с findings. |
| Не хватает обязательных данных/сессии или код изменился после инспекции | `blocked` | `partial`, с диагностикой. |

Успех означает приёмку этого отчёта для измеренного состояния дерева.
Он не запускает исправления, commit или отдельный test suite. Reviewer обязан
различать вывод по коду и фактически наблюдавшийся pre-fix/post-fix proof.

## Продолжить после partial

Исправление выполняется отдельно в принадлежащем этому Run дереве. Сначала
просмотрите продолжение, подставив исходный Run ID:

```sh
prifly project continue --repository . --launch openclaw-test-audit \
  --source-run SOURCE_RUN_ID --host codex-cli --allow-execution --prepare
```

Затем используйте **новый** review_digest:

```sh
prifly project continue --repository . --launch openclaw-test-audit \
  --source-run SOURCE_RUN_ID --host codex-cli --allow-execution \
  --expected-launch-digest NEW_REVIEW_DIGEST
```

Continue сохраняет исходные config/base/round и дерево; весь quality повторяется
с новой выборкой и отчётом. Не подставляйте `--workspace` или новый input,
чтобы перенести чужое дерево или незаметно поменять критерии принятого prefix.
Отменённый Run должен быть settled перед продолжением.

[Полный контракт пакета](../../openclaw-test-audit/README.md) ·
[Подключение шага через extend.yaml](../test-audit-extension/README.md).
