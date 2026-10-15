# Приёмка перед интеграцией

Используйте [standalone пример](../examples/verified-integration/README.md), когда
готовый commit надо объединить с конкретной целью. Он подготавливает отдельное
дерево, исполняет проектные команды и передаёт final reader заранее заданные
spot checks. Ready описывает проверенный результат; разрешение на запись задаёт
отдельно выбранный режим и reviewed executor contract.

## Одна привязка в extend.yaml

Released Pri-Fly **0.13.76** поддерживает **один** `input_bindings` у inserted
step. Остальные required inputs недопустимы для такой вставки. Binding берёт
существующий output producer, уже исполнившегося на каждом входящем пути, с
**той же exact schema reference**. Short workflow/step names — хвост `id` после
последнего `/`, даже когда имя YAML-файла другое.

В комментариях эталонных classic/profiled и прежней документации встречалось
ограничение «у вставки вообще нет inputs». Оно не описывает текущий stable;
эталонные файлы по решению владельца сохраняются без правок. Пример и compile
negative cases находятся здесь, а не в canonical graph.

```yaml
extensions:
  - id: inspect-handoff
    workflow: one-input-example
    step: extension
    between: {from: configure, to: done}
    input_bindings: {handoff: $stages.configure.handoff}
    on: {pass: done, needs_revision: abandoned, fail: abandoned, no_work: abandoned}
    impossible_verdicts: [blocked]
```

В отдельной тестовой/проектной копии `verified-integration` замените
`workflow.yaml` содержимым
[one-input-workflow.yaml](../examples/verified-integration/extensions/one-input-workflow.yaml),
а `extend.yaml` — [extensions/extend.yaml](../examples/verified-integration/extensions/extend.yaml).
Это самостоятельный маленький graph: configure производит typed handoff, inserted
extension читает его. Он демонстрирует передачу входа и не выполняет интеграцию.

Проба подтверждает положительную компиляцию и следующие реальные отказы:

- Несуществующий producer: `project_extension_unknown_stage`.
- Producer, исполняющийся позднее: `unavailable_output`.
- Несуществующий output: `unknown_port`.
- Другая exact schema: `port_type_mismatch`.
- Две привязки: `project_extension_invalid`, с указанием ровно одного input.

Для нескольких reports, target и повторных проверок используйте явный workflow,
как [assessment.yaml](../examples/verified-integration/workflows/assessment.yaml),
или заранее произведённый typed bundle. Источник bundle должен быть явным
producer; «последний Run» и память host conversation не заменяют binding.

## Проектная публикация в GitLab

Основание — [issue #1](https://github.com/StenHigh/prifly-aif-workflows/issues/1):
после создания MR оформление может оказаться неверным, хотя внешняя запись уже
произошла. Offline fixture моделирует описанное в issue поведение glab1.119.0:
`--draft` добавляет собственный `Draft: `. Поэтому formatter и CLI должны иметь
одного владельца префикса. С готового заголовка снимается ровно один префикс при
передаче `--title` вместе с `--draft`. Заголовок с двумя готовыми префиксами требует
reconciliation, а не нового create.

Project adapter должен реализовать операции reference client protocol:

| Операция | Обязательные проверки |
|---|---|
| `inspect(spec)` | Реальный current target commit, точный source ref и все MR для project/branches/ownership identity. Несколько результатов означают неоднозначность. |
| `ensure_source_branch(spec, expected_old)` | Проверка ownership и CAS по old commit. Чужая/изменившаяся ветка сохраняется. |
| `create(spec, title, draft=True)` | Один Draft для exact candidate/target/identity. Тело содержит проектную связь и evidence, без credentials. |
| `update_title(url, title, expected_revision)` | Отдельно разрешённая адресная reconciliation только своего MR; revision и observed body digest совпадают с записанным receipt. |

После любого write считайте реальное состояние заново. Target должен совпадать
с принятым commit до **и после** записи. Если он сдвинулся, MR может существовать,
но прошлая приёмка не становится проверкой новой цели. GitLab API не даёт этому
примеру атомарно зафиксировать remote target на всё время приёмки/создания;
production adapter должен объявлять эту границу и свою concurrency policy.
В частности, lookup/create/read-after-write выполняются под одной owned
publication lease проекта; два параллельных создателя не должны оба увидеть
«нет MR» и начать create. Последовательные offline fixtures такой lease или
атомарность реального provider не аттестуют.

Matching MR повторно используется с сохранением human title/body. Для исправления
формата после записи применяйте `repair_owned_title(client, spec, previous_receipt)`:
предыдущий URL, revision и body digest защищают чужие и intervening edits.
Reference algorithm не переписывает тело. Исчезнувшая связь, неоднозначный lookup,
переместившаяся ветка или изменившийся MR требуют owner action.
Если revision отсутствует или реальный API/client не обеспечивает conditional
update, adapter отказывает в автоматической правке. Обычный unconditional
`glab mr update` не заменяет требуемую защиту intervening edits.

Timeout после create не означает «не создано». Разрешена повторная **read-only
inspect**: она может обнаружить один уже созданный MR и вернуть reused с его URL.
Если состояние всё ещё неизвестно, возвращается `reconcile_required` без повторного
create. Такой же порядок нужен после неизвестного push исходной ветки.

Generic W4 не выбирает GitLab account, glab version или project credentials.
Выполнены offline provider fixtures; реальная GitLab-публикация и её permission
требуют отдельной проектной квалификации. Issue #1 сохраняет production scope;
этот пример покрывает generic contract/regression portion и не закрывает issue.

## Политика владельца и остановка

Пути auth/money, migrations, dependencies и deploy и явные business assumptions
содержатся в handoff.policy. Required decision сообщает категории, конкретные
изменённые пути/причины, candidate/target commits и digest политики. Решение по
старой цели или прежним правилам не переносится на новые условия. Число reviewers
не заменяет такое решение и не становится hardcoded веткой Pri-Fly.

Default `assess` не обновляет target branch, не делает push и не создаёт MR.
Создание/cleanup собственной integration copy всё равно являются declared external
effects. Local merge и GitLab Draft — разные режимы и отдельные executor boundaries.
Ни один из них не означает разрешение на deployment, release или tracker sync.

При отмене/unknown write оператор получает точную owned session и journal/receipt.
Сначала reconciliation, затем reviewed continuation или новый handoff с новой
целью. Автоматический cleanup сохраняет uncertain journal. Работа candidate,
индекс, файлы и HEAD не восстанавливаются через reset/checkout/stash.
В пределах exact handoff owned integration session создаётся эксклюзивно по
детерминированному digest. Сохранившаяся среда блокирует повторную prepare/continue
до адресной reconciliation/release; новый Run не теряет эту память об unknown
write. Для разных handoff одного remote publication identity всё ещё нужна
project-owned provider lease и реальная проверка внешнего состояния.
