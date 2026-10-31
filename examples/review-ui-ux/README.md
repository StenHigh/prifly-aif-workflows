# Самостоятельные review evidence и UI/UX

Нужны Pri-Fly0.13.82, Python3.10+, Git и AI Factory2.19.0 review skill выбранного host.
Примеры используют codex-cli и существующий Git-проект с начальным commit.
`SOURCE` — абсолютный путь к checkout этого репозитория.
Кандидаты1.1.0 готовятся для v1.55.0; до выпуска устанавливайте указанную ветку.

```text
request → capture → review → evaluate → report + gate
configuration → capture → environment → UI → UX → evaluate → release → finalize
```

## Подготовка

```sh
SOURCE=/absolute/path/to/aif-workflows
prifly project init --repository . --host codex-cli
prifly project workflows add StenHigh/prifly-aif-workflows --path aif-review-evidence --ref codex/issue-6-remaining-readability --repository .
prifly project workflows add StenHigh/prifly-aif-workflows --path aif-ui-ux --ref codex/issue-6-remaining-readability --repository .
prifly project local set --repository . --allow-executable python=/absolute/path/to/python3
cp "$SOURCE/examples/review-ui-ux/request.json" /tmp/review-request.json
cp "$SOURCE/aif-ui-ux/examples/configuration.json" /tmp/uiux-configuration.json
```

Для существующего проекта пропустите init. Установите только нужный пакет.
Путь Python должен указывать на ваш исполняемый файл. Сохраните установленные файлы в Git.
В обоих JSON замените нулевой base_commit исходным полным SHA задачи; в configuration обновите также ui/ux.base_commit.
Используйте `git rev-parse TASK_BASE_COMMIT_OR_REF` для получения SHA.
База не сдвигается после промежуточных commits или continue.
Request содержит code check; адаптируйте scope и критерии проекта.

Configuration — полный шаблон полей, включая scenarios, setup/cleanup и test identity.
Замените URL, команды, пути, критерии и ownership contract настройками вашего тестового проекта.
Пакет не запускает произвольный сервер сам. Просмотрите [контракт среды](../../docs/product-review-environment.md).
Input/evidence не должны содержать секреты. Конфиги храните вне проверяемого дерева.

## Review: preview и start

```sh
prifly project questionnaire --repository . --launch aif-review-evidence --host codex-cli --workspace checkout --input request=/tmp/review-request.json --allow-execution --prepare
prifly project start --repository . --launch aif-review-evidence --host codex-cli --workspace checkout --input request=/tmp/review-request.json --allow-execution --expected-launch-digest REVIEW_DIGEST
```

`REVIEW_DIGEST` — точное поле review_digest просмотренной сводки.
Checkout проверяет текущие tracked, staged и untracked изменения.
Runner исполняет assisted task; отсутствие независимой сессии отражается в отчёте.
Пакет возвращает evidence/gate, без repair и commit.

## UI/UX: preview и start

```sh
python3 -B .prifly/workflows/aif-ui-ux/files/preview.py --configuration /tmp/uiux-configuration.json
prifly project questionnaire --repository . --launch aif-ui-ux --host codex-cli --workspace checkout --input configuration=/tmp/uiux-configuration.json --allow-execution --prepare
prifly project start --repository . --launch aif-ui-ux --host codex-cli --workspace checkout --input configuration=/tmp/uiux-configuration.json --allow-execution --expected-launch-digest REVIEW_DIGEST
```

Просмотрите native summary, permissions и digest. Preview не исполняет setup.
`--allow-execution` разрешает declared programs; среда использует собственный declared effect contract.
UI/UX readers проверяют готовый интерфейс. Они не исправляют код.

## Поддерживаемый continue

Для partial/rejected или settled cancellation с принятым root prefix выберите исходный launch:

```sh
prifly project continue --repository . --launch aif-review-evidence --source-run SOURCE_RUN --host codex-cli --allow-execution --prepare
prifly project continue --repository . --launch aif-review-evidence --source-run SOURCE_RUN --host codex-cli --allow-execution --expected-launch-digest CONTINUE_DIGEST
prifly project continue --repository . --launch aif-ui-ux --source-run SOURCE_RUN --host codex-cli --allow-execution --prepare
prifly project continue --repository . --launch aif-ui-ux --source-run SOURCE_RUN --host codex-cli --allow-execution --expected-launch-digest CONTINUE_DIGEST
```

Выполняйте только пару команд нужного launch. SOURCE_RUN — исходный Run; CONTINUE_DIGEST — digest просмотренной сводки.
Не переопределяйте input/workspace. Quality заново измеряет candidate и получает свежие reports.
После прерванного environment effect сначала выполните требуемое reconcile; resume не заменяет cleanup.
Остановка до accepted prefix может дать resume_prefix_empty.

## Отдельное opt-in подключение

[W6 recipe](../review-uiux-extensions/README.md) добавляет project-owned calls в существующий маршрут.
Standalone add не создаёт import и не добавляет readers в classic.
Update сохраняет extend.yaml/project; изменённый author prefix может потребовать reviewed replay.
