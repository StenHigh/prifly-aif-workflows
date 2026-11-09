# Pri-Fly 0.13.89: подтверждённая миграция общих схем

Проверка: 2026-11-09. [Выпуск Core](https://github.com/StenHigh/prifly/releases/tag/v0.13.89).
Исправление для [Core #21](https://github.com/StenHigh/prifly/issues/21) доступно через явное решение владельца.
Обновление бинаря само по себе не снимает `package_not_resolvable` после старого `revoke`.

## Результат проверки

Официальный Linux amd64 binary прошёл проверку двух подписей manifest и SHA-256 архива.
SHA-256 binary: `90e3e37c79a88ae0279a2542e40e34d75afa524b2b3cf7188900830ea7fe2985`.
Source выпуска: `30c3635081f8f012aef3953072dcd45d0807d618`.

Verify прошёл для восьми пакетов, 132 компонентов и 88 шагов.
Compatibility прошёл для пяти launches, четырёх builds и шести trusted packages.
Прежний сценарий без миграции сохраняет seal `core-state/41`.
Обе проверки удалили свои monitor registrations.
Точные результаты: [release JSON](release-0.13.89-results.json).

Native probe проверил четыре независимые временные authority:

| Сценарий | Результат |
|---|---|
| Чистая установка | `succeeded` |
| Старый supplier удалён через remove | `succeeded` |
| Старый supplier отозван через revoke, миграция не выбрана | `package_not_resolvable`, 0 Runs |
| Две общие схемы, явная миграция в той же authority | `succeeded`, сохранён binding обеих схем |

В последнем сценарии используются опубликованные `feature-enabled@1.0.0` и `round-limit@1.1.0`.
Synthetic legacy package содержит только эти схемы. Он не содержит исторический classic code.
Supplier — точный опубликованный `composition-contracts@1.0.0` из declared dependency closure.

Probe также подтвердил read-only prepare, отказ неполного плана и отказ устаревшего плана.
Выбор решения меняет launch review digest. Старый digest получает `project_start_stale_launch`.
Start без выбора решения остаётся заблокированным после apply.
Повтор apply с прежним command ID возвращает прежний receipt.
Последующий revoke делает решение недействительным и запрещает новый Start.
Старый пакет остаётся revoked. Все четыре временные authority и registrations удалены; active claims отсутствуют.

```sh
python3 -B tests/probes/shared_schema_revocation.py \
  --binary /absolute/path/to/released/prifly \
  --output /tmp/shared-schema-migration.json \
  --exercise-migration
```

Binary path — placeholder. Рабочая директория — корень этого репозитория.
[Native JSON](shared-schema-migration-0.13.89.json) содержит точные refs, binding и проверенные отказы.
Без `--exercise-migration` probe сохраняет прежние три контрольных сценария для Core86/88.
Рабочая authority и прикладные задачи не менялись. Полная consumer матрица на Core89 здесь не заявлена.

## Как применить в существующей authority

Authority — хранилище состояния Pri-Fly. Consumer — новый пакет workflow, которому нужны общие схемы.
Supplier — trusted пакет, который непосредственно содержит проверенные схемы.

```text
compile + trust точного consumer
              |
diagnostic prepare -> выбор всех schemas/suppliers -> повторный prepare
                                                          |
                                   проверка владельца -> apply
                                                          |
                                inspect -> prepare launch -> explicit Start
```

Оператор выполняет процедуру в прежней authority. Он сохраняет её Runs, claims и историю отзыва.
Процедура подходит для ошибочного отзыва при обычном обновлении после проверки безопасности схем.
Для действительно небезопасной схемы требуется безопасная новая ревизия.

1. Установите подписанный Pri-Fly `v0.13.89` или совместимый новый выпуск на нужном host.
2. Явно установите зависимости через `tools/install_composition_contracts.py` из установленной версии workflows.
3. Скомпилируйте точный consumer с настройками выбранного launch.
4. Проверьте consumer и suppliers через package list и package inspect.

```sh
python3 .prifly/tools/install_composition_contracts.py --binary PRIFLY_BINARY --project AUTHORITY
prifly --json --project AUTHORITY project compile --repository REPOSITORY --package PACKAGE --host HOST --output BUILD_DIR > compile.json
prifly --json --project AUTHORITY package list > packages.json
```

Здесь `AUTHORITY`, `REPOSITORY`, `PACKAGE`, `HOST` и `BUILD_DIR` — явные placeholders.
`PRIFLY_BINARY` — абсолютный путь к тому же проверенному binary, который вызывается как prifly.
`PACKAGE` — ключ пакета в project profile, а не package Ref.
Добавьте выбранные profile/policy/extension options, если launch их использует.
Сохраните exact consumer Ref из поля `package` файла compile.json.

Если consumer отсутствует, импортируйте `BUILD_DIR` с объяснением доверия.
Неудачный прежний Start может оставить новый consumer в status removed после автоматической очистки.
Тогда проверьте совпадение полного Ref с compile.json и восстановите только этот новый consumer.
Повторный import removed consumer отвечает `package_present` и не восстанавливает его автоматически.

```sh
# Только если нового consumer ещё нет:
prifly --project AUTHORITY package import --dir BUILD_DIR --reason 'Проверен точный новый consumer для миграции общих схем'
# Только для проверенного нового consumer в status removed:
prifly --project AUTHORITY package restore --id CONSUMER_ID --version COMPILED_VERSION --reason 'Новый consumer удалён только очисткой неудачного запуска'
```

Эти ветви не являются последовательностью команд. Старый revoked classic не восстанавливайте.
Consumer и его declared dependencies должны быть trusted/resolvable до применимого плана.

1. Создайте request из точного результата compile.
2. Подготовьте диагностический план с пустым выбором.

```sh
python3 - <<'PY'
import json
from pathlib import Path
consumer = json.loads(Path('compile.json').read_text())['package']
request = {'schema_version': 'schema-migration-request/1', 'consumer_ref': consumer, 'selections': []}
Path('request.json').write_text(json.dumps(request, indent=2) + '\n')
PY
prifly --json --project AUTHORITY package schema-migration prepare --request request.json > diagnostic-plan.json
```

Первый prepare read-only. План показывает exact schema refs, candidates, причины отзыва и затронутые Runs.
Пустой выбор даёт `applicable: false`. Это ожидаемый диагностический результат.

1. Проверьте весь набор `schemas`, включая `revocations`, причины, candidates и byte digests.
2. Запишите для каждой schema проверенный `schema_ref` и выбранный `supplier_ref` в `request.json.selections`.
3. Повторите prepare и проверьте `complete: true`, `applicable: true`.
4. Получите решение владельца для точного полного плана.

```sh
prifly --json --project AUTHORITY package schema-migration prepare --request request.json > plan.json
prifly --json --project AUTHORITY package schema-migration apply --plan plan.json --expected-review-digest REVIEW_DIGEST --reason 'Проверены точные схемы; старую версию отзывали только при обновлении' --command-id command:reviewed-schema-migration > applied.json
prifly --json --project AUTHORITY package schema-migration inspect --id DECISION_ID
```

`REVIEW_DIGEST` — поле review_digest проверенного plan.json.
`DECISION_ID` — поле decision.id из applied.json. Не подставляйте ID решения из другой authority.
Для повтора потерянного ответа используйте тот же plan, digest, reason и command ID.
Для нового решения используйте новый command ID.

1. Подготовьте launch с явным выбором решения и обычными inputs/answers.
2. Проверьте launch summary и его новый review_digest.
3. Выполните Start с тем же выбором и точным новым digest.

```sh
prifly --json --project AUTHORITY project questionnaire --repository REPOSITORY --launch LAUNCH --host HOST --prepare --schema-migration DECISION_ID > launch.json
prifly --json --project AUTHORITY project start --repository REPOSITORY --launch LAUNCH --host HOST --schema-migration DECISION_ID --expected-launch-digest LAUNCH_DIGEST
```

`LAUNCH` — ключ launch в project profile. `LAUNCH_DIGEST` — review_digest из launch.json.
Обе команды требуют обычных inputs, brief, naming inputs и подтверждений конкретного launch.
Пример показывает выбор миграции; он не подменяет конфигурацию прикладной задачи.
Project profile должен иметь версию `/3` или новее.
Проверка готовности миграции не требует запуска уже выполненной прикладной задачи.

## Состояние и отказы

Первый apply переводит package authority в `/2`. Мигрированный Run использует `core-state/45` и `core-read/45`.
Старый binary не должен открывать это новое состояние. Планируйте обновление всех процессов, которые используют одну authority.
Consumer, schema или supplier Ref после изменения bytes может потребовать нового prepare и отдельного решения.
Миграция не переносится автоматически в другой consumer или новые запуски без явного выбора.
Старые revoked executable components и Run pins не получают общий допуск.

При `schema_migration_plan_stale` повторите prepare и проверку плана.
При `schema_migration_decision_invalid` проверьте inspect и новые lifecycle facts.
При `schema_migration_incomplete` заполните весь набор выбора и подготовьте новый план.
Не меняйте SQLite и не убирайте admission gate.
Для обычного вывода старой версии используйте remove; revoke предназначен для security withdrawal.

Shipping packages, contracts и каталоги не менялись. Новые версии workflows для этого механизма не требуются.
Published Core examples: [operations](https://github.com/StenHigh/prifly/blob/v0.13.89/examples/operations/schema-migration.md),
[request и binding](https://github.com/StenHigh/prifly/blob/v0.13.89/examples/authoring/schema-migration-guide.md).
