# Проверка перед объединением веток

Этот проектный пример нужен, когда фича уже написана и закоммичена, но её ещё
предстоит объединить с целевой веткой. Он проверяет именно объединённый код:
успешные тесты фичи и отсутствие Git-конфликтов могут сопровождаться регрессией
из-за изменений в целевой ветке.

Результат — отчёт с точными candidate и target commits, результатами команд,
финальным ревью и необходимыми решениями владельца. По умолчанию выполняется
только приёмка. Локальное объединение и Draft MR выбираются отдельно.

```text
явный handoff с отчётами W1 и проектной политикой
  → отдельная копия → объединение точных commits → команды приёмки
  → final reader: заданные выборочные проверки объединённого кода
  → проверка актуальности → отчёт
                         → [local_merge: атомарное обновление локальной ветки]
                         → [gitlab_draft: проектный адаптер публикации]
  → освобождение собственной копии
```

Это самостоятельный запускаемый пример `verified-integration`, initial version
**1.0.0**, для адаптации в проекте. Он находится вне опубликованных пакетов.
Требуются Pri-Fly **0.13.76**, POSIX, Python 3.10+, Git с `merge-tree --write-tree`
([Git 2.38+](https://git-scm.com/docs/git-merge-tree/2.38.0)) и host skills `aif-review` с `references/SEVERITY.md`, сверенные с
AI Factory 2.19.0. Python programs используют только стандартную библиотеку.

## Что передать

В [configuration.example.json](configuration.example.json) укажите:

- Полный commit готовой фичи и точный commit целевой ветки. Для этого примера
  цель — отдельный **локальный bare Git repository** и ref `refs/heads/...`.
  Его working checkout не изменяется. Обновление remote tracking ref и получение
  актуальной цели остаются явно выбранным действием проекта перед приёмкой.
- Команды приёмки объединённого кода в виде массивов аргументов, с deadline.
  Они исполняются в собственной копии; shell-строки не подставляются.
  Exit 0 означает pass, 77 — невозможность проверки, остальные коды — дефект.
- Выборочные проверки final reader: например, сохранение поведения вызывающего
  кода при изменении API. В этом примере они используют чтение кода. Полный
  browser/UI/UX-контракт описан отдельно в [W2](../../aif-ui-ux/README.md).
- Проектную политику эскалации: auth/money, migrations, dependencies, deploy
  и business assumptions. Пути задаёт проект; предположения бизнеса перечисляет
  в `declared_risks`. Решение владельца содержит категории, причину, ссылку,
  оба commits и digest точной политики. После изменения этих данных решение
  требуется заново. Модель не подменяет отсутствующее бизнес-решение.
- Режим `assess` (default example), `local_merge` или `gitlab_draft`.
  Для последнего дополнительно требуется конкретный project/branches/identity
  и контракт проектного GitLab adapter; credentials остаются вне artifacts.

Входной handoff также содержит явно названные W1 request/report artifacts.
Скрипт сохраняет **исходные байты request**, чтобы сверить report.request_digest:

```sh
python3 -B examples/verified-integration/files/build_handoff.py \
  --configuration /absolute/project-integration.json \
  --acceptance checks /absolute/w1-request.json /absolute/w1-report.json \
  --output /absolute/handoff.json
# Другие отчёты добавляются повторением --acceptance ROLE REQUEST REPORT.
```

Команды W1 здесь повторно не исполняются: проверяются полный состав отчёта,
его исходные критерии и связь с текущим candidate. Затем исполняются новые
команды **объединённого** кода. Структурная проверка не доказывает истинность
произвольного наблюдения, подписанный origin исходного Run или другую модель.

Candidate должен быть чистым и закоммиченным. Dirty/staged/untracked работа
сохраняется и останавливает интеграцию. Отчёт, полученный до commit, имеет другую
HEAD/index identity: его надо обновить W1-проверкой итогового commit. Это касается
и pre-commit quality evidence из `aif-feature`. Пример не объявляет прежний PASS
действующим после commit и не ищет artifacts по «последнему Run».

## Установка и запуск

Скопируйте папку целиком в `.prifly/workflows/verified-integration/` и добавьте
к **проектному** `.prifly/project.yaml`:

```yaml
packages:
  verified-integration:
    source: .prifly/workflows/verified-integration
launches:
  verified-integration:
    title: Приёмка перед объединением веток
    description: Проверка точного объединённого кода перед отдельно выбранной интеграцией.
    kind: workflow
    workflow: .prifly/workflows/verified-integration/workflow.yaml
```

Позвольте точный Python interpreter и просмотрите подготовленный запуск:

```sh
prifly project local set --repository . --allow-executable python=/absolute/path/python3
prifly project questionnaire --repository . --launch verified-integration \
  --host codex-cli --workspace checkout --input handoff=/absolute/handoff.json \
  --allow-execution --prepare
# Проверить input digest, target, mode и declared effects; затем:
prifly project start --repository . --launch verified-integration \
  --host codex-cli --workspace checkout --input handoff=/absolute/handoff.json \
  --allow-execution --expected-launch-digest DIGEST
```

Для `worktree` исходный отчёт должен соответствовать этому tracked candidate,
а не незакоммиченным файлам другой рабочей копии. Не присваивайте дерево чужого
активного Run: используйте завершённый commit и собственный project claim.

## Результаты и разрешённая запись

| Status в assessment | Значение и следующее действие |
|---|---|
| `ready` | Команды и final spot checks допустили точное объединение. В `assess` возвращается только отчёт. |
| `needs_revision` | Конфликт, семантическая регрессия или находка final reader. Исправить candidate и получить свежую приёмку. |
| `owner_required` | Требуется проектное решение либо локальная CAS-запись отказала. Прочитать risks/findings и фактическую цель. |
| `unavailable` | Приёмка не может судить: устаревшие отчёты, движение candidate/target, изменившая дерево проверка или недоступный инструмент. |
| `reconcile_required` | Внешняя запись могла выполниться или результат очистки неизвестен. Сначала адресно выяснить состояние. |

Process steps создания/проверки копии, локальной интеграции и cleanup объявляют
`external_write / reconcile_required` (StepDefinition 14). Final reader —
read-only assisted step с effects:none. Изолированная копия живёт в собственной
`/tmp/prifly-integration-*`, вне candidate и Attempt scratch; marker связывает
owner, handoff digest и Attempt. Cleanup сверяет marker и удаляет только эту копию.
Имя среды детерминировано digest handoff, а создание — exclusive mkdir. Пока
старый owned session существует, повторная prepare/continue возвращает
`reconcile_required` и не запускает ещё одно ревью или публикацию. Истечение
времени не снимает эту защиту; сначала оператор выясняет исход и освобождает
точную среду. Lease реального provider между разными handoff задаёт проект.
`/tmp` не является production ledger через reboot или системную очистку:
для таких сроков проект сохраняет operation receipts и provider lease в своём
постоянном хранилище. Generic пример квалифицирован в пределах жизни owned среды.
Commands могут писать свои временные данные внутри копии; изменение проверяемого
кода/index после snapshot делает отчёт недоступным. Не запускайте фоновые службы
или произвольные внешние операции вместо объявленных команд приёмки.

`local_merge` импортирует проверенный immutable Git object в локальный bare
repository и выполняет `update-ref NEW OLD`. Движение цели не перезаписывается.
Перед записью повторно измеряются source и integration tree. Это cooperative
freshness, а не блокировка любых внешних редакторов. Объект и целевой ref при
успешной CAS связываются с конкретным проверенным commit. Push здесь не выполняется.

`gitlab_draft` передаёт отдельному assisted executor ровно проектный контракт
публикации. [Reference algorithm](files/publication.py) получает API client от
проекта; generic пример не поставляет production client или credentials.
[Guide](../../docs/verified-integration.md) описывает ownership, один Draft,
повторное использование и reconciliation. Пример не выполняет merge MR или
автоматическое закрытие задач. Offline fixtures не заменяют реальную проверку
вашей версии CLI/API и permission вашего проекта.

## Прерывание и повтор

Обычный `partial` можно продолжить тем же launch после просмотра prepare;
assessment повторяется целиком: новая копия, команды и final reader. Если source
или target изменились, старый handoff станет stale и потребуется новый явно
подготовленный запуск с актуальными artifacts. Input не заменяется через continue.

При отмене final reader хвост cleanup не исполняется автоматически. Сначала
освободите точную среду из сохранённого assessment после проверки marker, затем
используйте reviewed `project continue`. Этот случай проверяется runtime-пробой.

При прерванной локальной записи **сначала прочитайте** журнал этой owned среды:

```sh
python3 -B .prifly/workflows/verified-integration/files/integration.py \
  reconcile --assessment /absolute/exported-assessment.json
```

Команда только читает owner marker, operation journal и текущий ref. При
потерянном подтверждении exact NEW означает applied, exact OLD — not_applied;
другой ref без сохранённого подтверждения означает unknown. Известный CAS отказ
и подтверждённый applied сохраняются как исторические факты. Не повторяйте
update-ref или создание MR до выяснения исхода. Если Core оставил обязательство,
владелец отдельно аттестует осмотр через `run resolve`. Отмена пишущего Attempt
может оставлять границу `recover_source_unsettled`, описанную в
[E3](../../docs/changes/add-bounded-feature-workflow/engine-followup.md): её обход
и успешное возобновление отменённого writer не входят в этот пример.

Не удаляйте журнал неизвестной записи. При `reconcile_required` автоматическая
очистка оставляет owned среду и evidence оператору. После адресной reconciliation
освобождается только она; candidate и чужие изменения остаются на месте.

## Проверка примера

```sh
python3 -B tests/test_integration.py
python3 -B tests/integration_contract.py --binary /absolute/released/prifly
python3 -B tests/probes/integration_check.py --binary /absolute/released/prifly
```

Точные результаты, живое наблюдение final reader и границы квалификации — в
[W4 acceptance](../../docs/changes/document-verified-integration-handoff/acceptance.md).
Несколько inputs у полноценного assessment оформлены явным child graph;
[отдельный пример one-input extension](extensions/extend.yaml) и правила его
подключения описаны в guide. Эталонные classic/profiled не меняются.
