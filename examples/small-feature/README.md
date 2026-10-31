# Одна небольшая фича

Примеры подходят для выпущенного `aif-feature@1.2.3` и выпущенного readability-пакета1.3.0.
Пакет1.3.0 опубликован в [v1.55.0](../../docs/releases/v1.55.0.md).
Прямая установка: `prifly project workflows add StenHigh/prifly-aif-workflows --path aif-feature --ref v1.55.0 --repository .`.
Нужны Pri-Fly ≥0.13.77, Python 3 и skills AI Factory (квалификация на2.19.0).
Workflow пишет локальный commit; push, merge и MR в него не входят.

Для запуска из существующей native queue есть
[отдельный пример Task → Run → ревью → continue](../native-queue/README.md).
Очередь подключается явно и не меняет этот workflow; её TaskInput не заменяет
typed input с критериями фичи.

| Задача | Task | Настройка extend | Дополнительная подготовка |
| --- | --- | --- | --- |
| Функция greeting с тестом | [backend](backend.task.json) | [backend](backend.extend.yaml) | Команда unit-теста и критерии code/security соответствуют проекту. |
| Изменение интерфейса | [frontend](frontend.task.json) | [frontend](frontend.extend.yaml) | Указать точные routes, UI/UX scenarios, браузер, setup/cleanup среды. |
| Backend с отдельными ревьюерами | backend task | [parallel-backend](parallel-backend.extend.yaml) | Подключить reviewed Codex CLI host helper к runner. |
| Frontend с параллельными UI/UX | frontend task | [parallel-ui-ux](parallel-ui-ux.extend.yaml) | Подключить CLI helper и pinned owned-loopback browser adapter; отдельные contexts/identities, capacity≥2. |

Установите пакет из каталога:

```sh
prifly project workflows add aif-feature --repository .
```

Скопируйте выбранный task в файл проекта и замените объём и критерии на свои.
В `.prifly/workflows/aif-feature/extend.yaml` перенесите нужные настройки,
сохранив уже добавленные проектные extensions. Примеры не копируются поверх
существующей конфигурации автоматически.

Для backend примера проверьте input и подготовьте запуск (замените абсолютные пути):

```sh
python3 -B .prifly/workflows/aif-feature/files/preview.py \
  --task /absolute/backend.task.json --profile backend
prifly project local set --repository . --allow-executable python=/absolute/python3
prifly project questionnaire --repository . --launch aif-feature --host codex-cli \
  --workspace worktree --input task=/absolute/backend.task.json --package-profile backend \
  --decision-policy autonomous --preflight-answer plan_tests=true \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'plan_retention="capture"' \
  --allow-execution --prepare
```

Просмотрите summary и используйте его `review_digest` в том же запуске:

```sh
prifly project start --repository . --launch aif-feature --host codex-cli \
  --workspace worktree --input task=/absolute/backend.task.json --package-profile backend \
  --decision-policy autonomous --preflight-answer plan_tests=true \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'plan_retention="capture"' \
  --allow-execution --expected-launch-digest 'sha256:<review_digest>'
```

Digest preview и native launch digest различаются; для start нужен второй.
Для frontend замените profile и task, подготовьте среду по
[environment guide](../../docs/product-review-environment.md). JSON содержит
примерные пути/команды, а не готовый сервер вашего приложения.

[Параллельные UI/UX](../../docs/parallel-ui-ux.md) требуют input `browser_adapter`
с exact hashes проверенного bundle. Само изменение review_mode не устанавливает
adapter и не запускает отдельные CLI actors. Квалифицированы1–3 круга;
4–8 явно отказывают до writers. По умолчанию используйте sequential.

Критерии и сценарии определяет проект. Required unavailable даёт диагностическую
остановку; дефект запускает scoped repair с полным повтором приёмки. При
неизвестном внешнем эффекте нужна reconciliation, а не повтор setup/cleanup.

## Продолжение после отмены пишущего шага

Для этого маршрута нужен **Pri-Fly ≥0.13.81**. Проверка consumer описана в
[E3](../../docs/changes/add-bounded-feature-workflow/engine-followup.md).
Root, inputs и `extend.yaml` сохраняются; новый workflow не устанавливается.
Сам `run resolve` подтверждает осмотр эффектов, а новый reviewed Run повторяет
writer и последующие checks/security/review.

Сначала дождитесь остановки actor, проверьте его файлы и внешние эффекты.
Замените абсолютные пути и IDs ниже на записанные у своего Run/Attempt.
`not_applied` в этом примере относится к consumer, остановленному **до actor
write**. Выберите `applied` только если осмотр подтверждает применившиеся
эффекты; завершённость реализации из этого не следует. Пока эффект неизвестен,
продолжение остаётся недоступным.

```sh
e3_binary=/absolute/path/to/released/prifly
e3_authority=/absolute/path/to/project-authority
e3_repository=/absolute/path/to/project
e3_source_run=run:REPLACE_WITH_RECORDED_RUN_ID
e3_attempt=attempt:REPLACE_WITH_RECORDED_ATTEMPT_ID
e3_resolution=not_applied

"$e3_binary" --project "$e3_authority" run resolve "$e3_source_run" \
  --attempt "$e3_attempt" --outcome "$e3_resolution" \
  --reason 'Осмотрены эффекты остановленного actor; выбран исход по фактическому состоянию'
"$e3_binary" --project "$e3_authority" run drive "$e3_source_run"
"$e3_binary" --json --project "$e3_authority" project continue \
  --repository "$e3_repository" --launch aif-feature --source-run "$e3_source_run" \
  --host codex-cli --allow-execution --prepare
```

Просмотрите `recovery.frontier_action: execute`, frontier, переносимый prefix,
claim и **верхний** `review_digest`. Prepare не должен менять source, дерево
или список Runs. После принятия этого review запишите его digest:

```sh
e3_review_digest=sha256:REPLACE_WITH_REVIEWED_DIGEST
"$e3_binary" --json --project "$e3_authority" project continue \
  --repository "$e3_repository" --launch aif-feature --source-run "$e3_source_run" \
  --host codex-cli --allow-execution --expected-launch-digest "$e3_review_digest"
```

Далее runner обслуживает новый Run. Исходный Run сохраняет cancellation facts;
для последующего продолжения source — текущий владелец claim.

Если producer оставил partial `.ai-factory/PLAN.md`, новый start может получить
`workspace_tree_output_exists` до выдачи writer. Этот файл сохраняется. Владелец
проверяет принадлежность файла и явно переносит его в выбранное место **вне
candidate**, сохраняя bytes; автоматического удаления здесь нет. После такого
решения повторите prepare/start от последнего failed Run, которому start уже
передал claim, с новым review digest. Можно освободить путь до первого start,
если это уже явно решил владелец.

Для backend-стенда воспроизводимые проверки без живой модели:

```sh
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly \
  --case implement-cancel --report /tmp/e3-implement-81.json
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly \
  --case plan-cancel --report /tmp/e3-plan-81.json
python3 -B tests/probes/feature_check.py --binary /absolute/released/prifly \
  --case cancel-resume --report /tmp/e3-read-only-81.json
```

Эти команды запускаются из checkout этого репозитория; current writer probes
требуют0.13.81+. На0.13.80 остались исторические negative probes в source081931f.
Fixture сам выполняет осмотр и перенос только своего временного partial PLAN;
это не автоматическая операция над планами реального проекта.
