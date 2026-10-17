# Review и UI/UX внутри вашего workflow

Используйте этот пример, когда приёмка должна проверить **незакоммиченную
реализацию текущего Run** и разрешить либо остановить его commit. Он добавляет
native вложенный workflow через проектный `extend.yaml`. Отдельно запускать
`aif-review-evidence` и `aif-ui-ux` для этого не нужно.

| Режим | Зачем включать | Порядок |
| --- | --- | --- |
| `review` | Проверить код по явным критериям и командам | capture → reviewer → gate |
| `uiux` | Проверить интерфейс и пользовательские сценарии в браузере | capture → ensure → UI → UX → gate → release → finalize |
| `combined` | Нужны оба вида приёмки | review → UI/UX; UI/UX начинается после принятого review |

Все режимы завершаются проверкой свежести; дополнительная вставка после commit
сравнивает фактические файлы с принятым candidate. Вложенные стадии выполняются
в том же Run/claim. Если между приёмкой и commit изменятся файлы, итог Run будет
rejected. Локальный commit к этому моменту **может существовать**: вставка не
даёт атомарную блокировку файлов и ничего не откатывает.

Нужны **Pri-Fly ≥0.13.78** (проверено на stable0.13.80), Python3.10+ и
AI Factory2.19.0 skills выбранного host, включая `aif-review`. Для установки
примеров нужен PyYAML6; runtime workers используют stdlib. Первый scope —
последовательная приёмка и изолированная среда (`shared_resource: null`).
Параллельные W5 grants и автоматический repair не подключаются.

## Настроить критерии

Дальнейшие команды выполняются из корня целевого Git-проекта с существующей
`.prifly/project.yaml`. Подставьте абсолютный путь к checkout этого репозитория
вместо `/absolute/path/to/aif-workflows`. Примеры публикуются с main, отдельно
от каталожного выпуска v1.53.0; закрепите выбранный commit примеров у себя.

```sh
python3 -m venv /tmp/w6-tools
/tmp/w6-tools/bin/pip install -r /absolute/path/to/aif-workflows/examples/review-uiux-extensions/requirements.txt
cp /absolute/path/to/aif-workflows/examples/review-uiux-extensions/configurations/combined.json /tmp/w6-settings.json
```

Для `review` или `uiux` скопируйте соответствующий JSON и везде ниже используйте
то же значение `--mode`. Конфигурация содержит ровно `mode`, `review`, `product`;
отсутствующая часть равна `null`. Это вход **установки**, затем его bytes
запечатываются как `project/files/w6-settings.json` внутри workflow.

Review-пример рассчитан на `greeting.py` и `test_greeting.py`; замените description
и checks своими наблюдаемыми критериями и реальными командами проекта. `method`
должен соответствовать свидетельствам: command/code/browser. Нулевой base SHA
заменяется producer-ом на **original base implementation**; он не вычисляется
заново от текущей ветки. `round: 1` — явный логический раунд критериев, continue
не увеличивает его скрытым счётчиком. Новая попытка получит новые artifact refs.

В `product` замените `scope_reason`, owner/profile, setup/cleanup,
`browser_adapter`, test identity и allowed operations настройками проекта.
Значения `fixture ...` — **placeholders тестового стенда**, готовый сервер они
не запускают. Настройте исполняемые ensure/release действия и браузерный adapter
host по [контракту среды](../../docs/product-review-environment.md).
Отредактируйте scenarios: точные paths, viewports, actions, expectations и
соответствующие check_id в UI/UX request. Environment должен обслуживать именно
claimed repository_workspace; внешний старый deployment не подходит.

`optional_policy: ignore` явно допускает неблокирующие warnings, включая
недоступную аттестацию модели. Обязательная недоступная проверка всё равно
останавливает маршрут. `stop` требует решения владельца при warnings.
`require_separate_session: true` требует отдельной reviewer-сессии; другую
модель этот флаг не выбирает и не аттестует.

## Подключить к установленному classic

Это opt-in в **целевом проекте**. Canonical classic этого репозитория не меняется.
Если classic ещё не установлен:

```sh
prifly project workflows add aif-classic --repository .
```

Preview плана установки (без записи):

```sh
/tmp/w6-tools/bin/python /absolute/path/to/aif-workflows/examples/review-uiux-extensions/install.py \
  --repository . --package aif-classic --mode combined --configuration /tmp/w6-settings.json
```

Проверьте extensions и hashes. Затем повторите те же аргументы с **полным**
`review_digest` из preview вместо `INSTALL_DIGEST`:

```sh
/tmp/w6-tools/bin/python /absolute/path/to/aif-workflows/examples/review-uiux-extensions/install.py \
  --repository . --package aif-classic --mode combined --configuration /tmp/w6-settings.json \
  --apply --expected-plan-digest INSTALL_DIGEST
```

Installer добавляет `project/` с явно скопированными W1/W2 definitions и
адаптерами, references/execution bindings и две call-вставки в `extend.yaml`.
В classic это `review → w6-quality → commit → w6-committed-quality → done`;
при exclusion review место вставки обрабатывает native compiler.
`workflow.yaml`, shipped steps/contexts/schemas не переписываются. Existing
extensions, profile/exclude сохраняются; конфликты и повторная установка
отказывают. Project profile/2 поднимается до /3; /3 и /4 сохраняются.
Installer сериализует изменённые YAML как JSON (допустимый YAML), поэтому
комментарии в этих двух файлах теряются; исходные bytes сохраняются в выданном
`backup_directory` вне проекта. Сохраните эту копию и preview в своём хранилище.

## Собственный минимальный consumer

Вместо classic можно взять явный пример `write → commit → done`. Он использует
те же W6 вставки, без warmup/plan/repair. Выберите ещё не существующую папку:

```sh
cp -R /absolute/path/to/aif-workflows/examples/review-uiux-extensions/consumer .prifly/workflows/w6-consumer
```

Добавьте записи в существующие mappings `.prifly/project.yaml`, сохранив
остальные поля:

```yaml
packages:
  w6-consumer:
    source: .prifly/workflows/w6-consumer
launches:
  w6-consumer:
    title: Feature with project acceptance
    description: Write, accept and commit one scoped feature.
    kind: workflow
    workflow: .prifly/workflows/w6-consumer/workflow.yaml
```

В обе команды installer из предыдущего раздела передайте
`--package w6-consumer --after write`, сохранив mode/configuration. Для другого
своего графа нужны exact implementation schema и producer output на указанном
ребре, unsuccessful finish и отдельное ребро commit→finish; installer не
переводит произвольные schemas и не импортирует установленные пакеты.

## Compile, preview, start

Ниже `w6-consumer`; для classic замените package/launch на `aif-classic` и
`--consumer minimal` на `--consumer classic`. Classic дополнительно задаёт
обычные ответы preflight в интерактивном questionnaire вашего host.

```sh
prifly project local set --repository . --allow-executable python=/absolute/path/to/python3
prifly project compile --repository . --package w6-consumer --host codex-cli --output /tmp/w6-compiled
python3 -B /absolute/path/to/aif-workflows/examples/review-uiux-extensions/prepare_task.py \
  --repository . --consumer minimal --base HEAD --title 'Greeting feature' \
  --description 'Add greeting(name) returning Hello, <name>! and a unittest in test_greeting.py.' \
  --output /tmp/w6-task.json
```

`--base` — исходная база задачи; helper разрешает её в полный SHA для minimal
consumer и не перезаписывает существующий output. Для classic original base
формируется его штатным producer. Сохраните проектную установку в Git **до**
worktree start; новый worktree не переносит dirty/untracked из другого дерева.
W6 проверяет незакоммиченную реализацию, созданную уже внутри этого Run.

```sh
prifly project questionnaire --repository . --launch w6-consumer --host codex-cli \
  --workspace worktree --input task=/tmp/w6-task.json --allow-execution --prepare
prifly project start --repository . --launch w6-consumer --host codex-cli \
  --workspace worktree --input task=/tmp/w6-task.json --allow-execution \
  --expected-launch-digest START_DIGEST
```

`START_DIGEST` — полный новый review_digest просмотренного questionnaire.
Перед start запустите questionnaire ещё раз, если после preview меняли criteria,
callee, route, policy или другие source files. Host обрабатывает assisted tasks;
один `start` не заменяет работу reviewer-а. `codex-app` и `claude-code` — другие
compile targets; qualification реальных сессий указана отдельно в evidence.

## Остановка и continue

Usable reports с defect/unavailable/stale/owner blocker завершают child как
partial; вставка ведёт родителя в `abandoned`/rejected, без commit. Guaranteed
`assessment` child содержит исходный gate, свежесть и exact report refs/digests;
успешный child также экспортирует original typed reports, gate, receipt и
UI/UX environment/release. Смотрите вложенные стадии Run, а не только root
outcome. Ошибка без usable report не выдаёт фиктивную приёмку.

После обычного partial UI/UX cleanup выполняется до остановки. После cancel,
timeout или прерванного ensure/release граф **не гарантирует cleanup tail**:
остановите внешнего actor, сверяйте exact owner/session, завершите reconciliation
и дождитесь settlement. `cancelled` само по себе не доказывает освобождение среды.
Не делайте blind retry и не удаляйте чужие ресурсы.

Для поддерживаемых rejected/partial/cancelled исходов обоих показанных parents:

```sh
prifly project continue --repository . --launch w6-consumer --source-run SOURCE_RUN_ID \
  --host codex-cli --allow-execution --prepare
prifly project continue --repository . --launch w6-consumer --source-run SOURCE_RUN_ID \
  --host codex-cli --allow-execution --expected-launch-digest CONTINUE_DIGEST
```

В classic используйте его launch. Не добавляйте новый input/workspace: continue
сохраняет original base, критерии, дерево и claim. При остановке внутри W6
повторяется весь call с capture, отчётами и собственной средой. После принятого
child и отказа commit native accepted-prefix продолжение сохраняет receipt;
post-commit guard всё равно проверяет актуальные файлы. При изменённом candidate
владелец должен выбрать **reviewed replay приёмки** по prepare summary; рецепт
не добавляет автоматический repair/выбор replay point. Source/config drift
после принятого prefix обрабатывается native refusal/явным replay, не reset.
Импорт произвольных отчётов и repair-loop этим примером не предоставляются.

## Обновление и удаление

`bundle/manifest.json` фиксирует source и generated file hashes; installer
проверяет их и сохраняет provenance. Это project-owned копия компонентов W1/W2,
а не cross-package import. Обновление standalone пакетов **не обновляет** эти
копии. Новый bundle требует review и повторной квалификации вашего consumer.

Сохраните весь project/overlay и project.yaml перед обновлением workflow.
`project workflows update` может отказать из-за добавленных project files;
`remove` удаляет их целиком. Для удаления W6 сверяйте сохранённый план: удалите
только его две extensions, references, execution bindings и перечисленные
project files, сохранив чужие additions. Восстановление всего backup допустимо
только если после установки никто не менял эти файлы. Затем compile/preview.
Для обновления upstream выполните этот reviewed removal, обычный update и
новую preview/apply установку; автоматической миграции нет.

Root budgets recipe не повышает. У classic max steps200/transitions1000/depth4;
своя минимальная версия задаёт32/120/4. Для combined линейная приёмка добавляет
12 шагов, post-commit guard1; вложенность child wrappers до2 относительно root.
Проект с дополнительными loops/extensions должен отдельно проверить общий
budget/capacity/trust. Environment/release сохраняют исходную effect policy W2.

[Критерии и фактическая квалификация W6](../../docs/changes/add-review-uiux-call-extensions/acceptance.md).

Для автоматизированного classic launch сначала получите текущий каталог:

```sh
prifly project questionnaire --repository . --package aif-classic --package-profile fast
```

Для greeting-примера ниже CATALOG_DIGEST — полный catalog_digest из этой
команды; START_DIGEST — новый review_digest из следующего preview.
Сначала создайте task helper-ом с `--consumer classic` и проверьте ответы:

```sh
prifly project questionnaire --repository . --launch aif-classic --host codex-cli \
  --workspace worktree --input task=/tmp/w6-task.json --allow-execution --package-profile fast \
  --preflight-answer 'plan_profile="fast"' --preflight-answer 'plan_tests=true' \
  --preflight-answer 'plan_constraints="Implement only the declared greeting feature; no push."' \
  --preflight-answer 'gate_checks="python3 -B -m unittest test_greeting"' \
  --preflight-answer 'gate_warnings="fix"' --expected-decision-catalog-digest CATALOG_DIGEST --prepare
prifly project start --repository . --launch aif-classic --host codex-cli \
  --workspace worktree --input task=/tmp/w6-task.json --allow-execution --package-profile fast \
  --preflight-answer 'plan_profile="fast"' --preflight-answer 'plan_tests=true' \
  --preflight-answer 'plan_constraints="Implement only the declared greeting feature; no push."' \
  --preflight-answer 'gate_checks="python3 -B -m unittest test_greeting"' \
  --preflight-answer 'gate_warnings="fix"' --expected-decision-catalog-digest CATALOG_DIGEST \
  --expected-launch-digest START_DIGEST
```

Required fields зависят от profile и ваших decisions. `gate_warnings` здесь
относится к штатным classic gates; W6 policy остаётся в settings.json.
Не переносите greeting-ответы на другой проект без review.
