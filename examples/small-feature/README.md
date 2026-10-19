# Одна небольшая фича

Примеры для `aif-feature@1.2.3` из [v1.52.0](../../docs/releases/v1.52.0.md).
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
  --allow-execution --expected-launch-digest sha256:<review_digest>
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
