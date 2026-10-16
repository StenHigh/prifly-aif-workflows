# Небольшая новая фича

Самостоятельный `aif-feature:package/feature@1.2.1`, launch **aif-feature**.
Требует released Pri-Fly **0.13.77**, Python 3 stdlib для declared programs
и AI Factory skills (контракт сверён с **2.19.0**). Пакет пока не выпущен.

```text
warmup → configure → native fast plan → implement
  → quality {begin → capture → checks → security → code review
                → [frontend: environment → UI → UX → evaluate → cleanup → finalize]
                → aggregate → clean / diagnostic stop / scoped repair → next full round
              → candidate guard → local commit} → finish
```

Маршрут предназначен для одной связной фичи, обычно до четырёх native tasks
вместе с тестами. Миграция, существенная архитектура, неоднозначный бизнес scope
или слишком широкий repair дают `partial` с конкретной причиной и сохранённой
работой. Автоматического запуска classic нет. Это ограничение planning bridge,
а не машинное доказательство сложности проекта. `aif-fix` остаётся маршрутом
конкретного бага; classic/profiled/fanout/fix не меняются.

## Приёмка и профили

Task — JSON по [schema](schemas/task.yaml): title, exact description, scope,
явные assumptions и три каталога W1 `checks/security/review`. Каждый check имеет
стабильный ID, описание проверки, method, required, enabled, applicable.
`checks` требует хотя бы одну включённую обязательную command-проверку;
`review` — code-проверку. Security включается/исключается явно в каталоге, с
видимым report. Каждая command должна описывать реальную проверку и условия её
выполнения; package не устанавливает инструменты и не поднимает скрытую baseline.
Если baseline требует переключить/reset candidate, проект должен предоставить
отдельную безопасную копию, сохранив Run tree (см. repository issue #5).

**backend** требует `product:null` и обходит все браузерные этапы. **frontend**
требует W2 configuration с обязательными UI **и** UX scenarios и явным контрактом
project environment. [Environment guide](../docs/product-review-environment.md)
описывает owned sessions, cleanup/reconcile и реальные внешние effects. Backend
нельзя выбрать, чтобы скрыть недоступный браузер у интерфейсной фичи. Родительский
input `surface` — project configuration; profile задаёт default. Configure
проверяет его согласованность с task. Модельный `independent-review` — отдельное
требование сессии, не profile пакета.

Примеры: [backend](examples/backend.json), [frontend](examples/frontend.json).
В frontend example setup/cleanup/browser_adapter заменить точным контрактом
проекта. Вложенные product base_commit/round — placeholders: begin каждого
круга устанавливает original warmup base и текущий номер. Criteria и environment contract сохраняются; вложенные UI/UX policy/session
choices обязаны совпадать с общей политикой task, иначе preview/configure откажут; projected W1 requests запечатаны
точными digest, aggregate evidence также содержит digest исходного task.

После каждого repair повторяются **все** enabled readers с нового snapshot.
W1 проверяет request digest, round, candidate и полный список checks. W2
проверяет scenarios/viewport/origin и cleanup того же owner/session. Общий
aggregate повторно измеряет candidate; program guard делает это перед commit,
commit bridge — после доставки writer. Это cooperative Git freshness, не
атомарный lock против внешних редакторов, не аттестация истинности prose/browser
или другой модели. Read-only actors не ремонтируют код и не управляют средой.

Required unavailable/stale/invalid evidence → diagnostic `partial`, без repair.
Owner-only stop имеет приоритет даже при дефекте в другой проверке. Confirmed
defect → отдельный scoped writer `aif-implement --without-plan`, в пределах
его upstream inline guard; никакого универсального bug-fix skill. Optional
warnings/skips и unavailable model mapping следуют task.optional_policy
`ignore/stop`; fresh session и другая модель отчётливо различаются.

`settings.quality.limit` в [extend.yaml](extend.yaml) — число **полных quality
кругов**, default3. Диапазон1–8 для sequential/backend, **1–3** для
`parallel-ui-ux` (проверяется до writers). Limit=1 означает проверить без repair.
Последний неуспешный круг не редактирует код; возвращает последний gate/evidence.
Для нового UI/UX round требуется до 15 StepInstances, включая диагностический
путь; quality budget122, root128, child depth7, parallelism2. Sequential/backend
используют прежние ветви в том же bounded graph; default limit3, максимум8.
Это budget одного Run; reviewed continuation даёт новый bounded acceptance call.

## Как выбрать режим ревью

| Режим | Когда нужен | Что выполняется одновременно |
| --- | --- | --- |
| `sequential` (default) | Обычный запуск, существующий host runner, общий тестовый стенд | Ничего |
| `parallel-backend` | Backend-фича и подключённый Codex CLI dispatcher | Security и code review после checks |
| `parallel-ui-ux` | Frontend-фича, Codex CLI dispatcher и проверенный browser adapter проекта | UI и UX после checks/security/code review |

## Параллельные UI и UX

`parallel-ui-ux` выполняет одновременно два продуктовых ревью небольшой
интерфейсной фичи. Каждый reviewer запускается в новой CLI-сессии, получает
свои критерии и отдельные browser context/test identity; candidate и окружение
общие. Workflow ждёт оба отчёта и освобождает своё окружение перед repair или
commit. После repair повторяются все проверки, UI/UX получают новые grants и
окружение. Другую модель новая сессия не гарантирует.

Это явное подключение проекта: выбрать `profile: frontend`, задать
`settings.feature.review_mode: parallel-ui-ux` и project configuration input
`browser_adapter`. Последний — JSON descriptor с точными source hashes и
настройками проверенного адаптера. Подробная настройка и протокол:
[guide](../docs/parallel-ui-ux.md). Пример адаптера для квалификации:
[fixture](../tests/fixtures/feature-browser/adapter.py); его нельзя переносить
в проект без проверки и настройки сценариев.

В этом режиме `quality.limit` допускает **1–3** полных круга; 4–8 отвергаются
до writers. Это явная граница квалификации storage footprint на released0.13.77;
sequential/backend сохраняют1–8, budget Core не меняется.

До plan/implement проверяются доступность browser adapter и двух изолированных
contexts/identities, Codex CLI и достаточная native capacity. Только owned
loopback environment, `shared_resource: null`; quality resource `limit: 1`
отвергается. Requested parallel не переключается молча на sequential.
Нужен явный вызов shipped host helper из существующего runner; одна установка
пакета этого не делает. Native App/Claude пока не квалифицированы.

## Опциональное параллельное backend-ревью

По умолчанию проверки, безопасность и ревью идут последовательно. Если проект
хочет запустить два независимых reader одновременно, можно явно выбрать
`parallel-backend` в своём `extend.yaml`:

```yaml
profile: backend
settings:
  feature:
    review_mode: parallel-backend
  quality:
    limit: 3
exclude: []
extensions: []
```

Маршрут: `checks → {security || review} → ожидание обеих ветвей → aggregate`.
Каждый reader получает общий candidate и свой каталог критериев. Для этих двух
отчётов отдельная сессия обязательна независимо от общего
`task.require_separate_session`. Другая модель этим не обещается. Даже первый
неуспешный отчёт не запускает repair, пока вторая ветвь не завершена. После repair
повторяются checks и оба reader; guard и commit остаются в общей replay unit.

Режим требует **явного host adapter**. Перед plan хост отвечает на
`parallel-admission`: без подходящего dispatcher маршрут останавливается.
В этом варианте поставляется только dispatcher независимых Codex CLI sessions;
App/Claude concurrency не квалифицирована. `parallel-backend` допускается только
для backend; для frontend предусмотрен отдельный режим ниже.

Контроллер существующего host loop после `run drive` может обработать один
готовый batch поставляемой командой:

```sh
python3 -B .prifly/workflows/aif-feature/files/parallel_host.py \
  --binary /absolute/released/prifly --project /absolute/selected/authority \
  --run run:<ID> --host codex-cli --artifacts /absolute/owned/evidence
```

Команда обслуживает только capability admission, пару security/review и сбор
их отчётов. `handled:false` возвращает обычный этап основному хосту: writers,
checks, выбор workflow и управление Run остаются в существующем runner.
Папка evidence должна находиться вне claimed репозитория. Эту команду хост
вызывает явно; новая версия пакета сама не меняет installed
runner и не включает фоновый запуск. Для другой среды до opt-in нужен собственный
проверенный adapter. Корневая папка evidence принадлежит запуску; внутри каждая
Attempt получает отдельный каталог. Повторный запуск той же Attempt блокируется
локальным marker; после неизвестного результата сначала останавливают и сверяют
реального actor, затем применяют штатные cancel/recovery и новые Attempts.

Collector использует публичный `artifact export`, переносит исходные bytes в
base64 и не принимает решения о качестве. Программный aggregate сверяет exact
refs/digests/полноту, затем заново применяет W1. Источник каждого отчёта и его
исходные bytes сохраняются в evidence; одинаковые observations не исчезают и
не становятся дополнительными критериями. Ошибка экспорта, stale/missing/bad
digest → diagnostic partial без repair/commit. Предел транспорта — 4 MiB на
отчёт; превышение даёт явную недоступность без усечения.

Исходники адаптера закреплены hashes в sealed context. Несовпадение установленного
helper с reviewed Run запрещает его использование. После обновления пакета
нужно заново просмотреть prepare; источник старого Run не переписывается.
[Приёмка и ограничения W5](../docs/changes/qualify-parallel-implementation-review/feature-composition.md).

## Native plan и решения

Используются `aif-plan fast` и явный `aif-implement @.ai-factory/PLAN.md`,
native TASK-FORMAT и progress checkboxes. Native Tasks включают код и доступные
unit/static проверки; независимые quality readers и browser environment — позже.
Их критерии остаются обязательными в плане, но не создают зависимость implementation
от ещё не поднятой quality-среды. implemented означает завершённые native Tasks,
а итоговую приёмку допускает только quality gate. Pri-Fly capture/materialisation
переносит exact plan bytes; не используется копия чужого spec format.
Declared preflight: `plan_tests`, `plan_constraints`, `plan_retention`.
Fast route задаёт Docs:no и roadmap:none; docs могут быть явной задачей в scope.
На released Core capture исполняется также на non-pass. Если upstream остановился
без ready plan, bridge создаёт только **BLOCKED diagnostic snapshot** в native
формате, без executable tasks; result не ready, root не допускает implement.
Это явно названная адаптация границы capture, не успешный upstream plan.

Owner/business conflicts не превращаются в ordinary automatic decisions:
attended host спрашивает владельца; autonomous останавливается с диагнозом.

`plan_retention=capture` — default: свой untracked PLAN запечатывается и
освобождает staging path; bytes остаются в artifact store. `retain` stage-ит
только созданный owned PLAN: native engine сохраняет tracked document, его
progress проходит quality/commit. Package никогда не удаляет tracked PLAN.
Следующий Run откажет на занятом пути: владелец отдельно архивирует retained
план. Имеющийся чужой PLAN не выполняется/не заменяется; native refusal —
`workspace_tree_output_exists`. Нестандартный project config paths.plan требует
согласовать capture отдельным project change, не переписать config молча.
Принудительная отмена workspace-write planner/implement даёт `recovery_required`.
После остановки host оператор осматривает bytes и отдельно `run resolve`
аттестует результат, без blind retry. В 0.13.76 такой Run затем остаётся failed
с cancel_requested:true, и reviewed continue отказывает `recover_source_unsettled`.
Это проверенная граница текущего Core: работа/план сохранены, resume не объявлен
успешным. [Engine follow-up](../docs/changes/add-bounded-feature-workflow/engine-followup.md)
предлагает отдельное улучшение. Где host ещё может вернуть результат, normal
blocked/diagnostic partial позволяет корректный reviewed continue. Ни сброс флага
отмены, ни reset/clean, ни замена source Run здесь не выполняются. Native занятый
путь даже после отдельной адресной архивации должен проверяться на reviewed replay.

## Локальная установка и reviewed запуск

Скопировать папку целиком в `.prifly/workflows/aif-feature/`, добавить к project:

```yaml
packages:
  aif-feature:
    source: .prifly/workflows/aif-feature
launches:
  aif-feature:
    title: Small feature
    description: Native fast plan and bounded sequential acceptance.
    kind: workflow
    workflow: .prifly/workflows/aif-feature/workflow.yaml
```

До start просмотреть scope/criteria и точные bytes input:

```sh
python3 -B .prifly/workflows/aif-feature/files/preview.py --task /absolute/task.json --profile backend
prifly project local set --repository . --allow-executable python=/absolute/python3
prifly project questionnaire --repository . --launch aif-feature --host codex-app \
  --workspace worktree --input task=/absolute/task.json --package-profile backend \
  --decision-policy autonomous --preflight-answer plan_tests=true \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'plan_retention="capture"' \
  --allow-execution --prepare
# После просмотра summary передать его review_digest с теми же arguments:
prifly project start --repository . --launch aif-feature --host codex-app \
  --workspace worktree --input task=/absolute/task.json --package-profile backend \
  --decision-policy autonomous --preflight-answer plan_tests=true \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'plan_retention="capture"' \
  --allow-execution --expected-launch-digest sha256:<review_digest>
```

Для frontend выбрать frontend profile и frontend task. Preview digest input и
native review_digest принадлежат разным доменам; подставлять один вместо другого
нельзя. Runner recommendation — совет; этот пакет сам не стартует другой Run.

## Продолжение и границы

Root resumable: partial/rejected/cancelled. `project continue --launch
aif-feature --source-run RUN --prepare` сначала проверяет текущий контракт,
затем reviewed digest допускает Run. Сохраняются исходный base, claim, ответы и
работа. Stopped **acceptance call** объединяет quality, guard и commit в одну единицу
replay; все readers в новом круге повторяются также после partial commit.
Таким образом intervening edit не оставляет continuation на старом PASS. Не обещается root `--from-stage` для nested UI/checks. Перед
continue после отменённого frontend Run оператор адресно reconciles/cleans
owned environment: cancellation может обойти нормальный cleanup tail.

Изменённый effective accepted prefix даёт `recover_prefix_changed`; версия
или текст вне effective контракта сами по себе не доказывают такой отказ.
Никаких reset/clean/recreate для обхода. При большой фиче или required blocker
owner выбирает дальнейший reviewed launch отдельно, учитывая уже сохранённую
работу; automatic classic escalation отсутствует.

Commit только local в claimed tree, exact task paths, original base и actual
HEAD. Native implementation checkpoints могут уже сделать local commits;
пустой final commit нормален. Package не пушит, не создаёт MR и не merge-ит.
Неразрешённое чужое staged work требует владельца.

## Проверки и публикация

[W3 acceptance](../docs/changes/add-bounded-feature-workflow/acceptance.md)
разделяет synthetic runtime, actual browser и реальные LLM observations.
Self-contained folder вендорит неизменённые W1/W2 workers/contexts/schemas;
ссылок на установленную sibling folder нет. Existing graphs/bytes сохранены.
Catalog — [unpublished draft](../docs/changes/add-bounded-feature-workflow/catalog.draft.yaml);
local catalog add/update проверяет сохранение extend/project overlays и отказ
при local upstream edits. Tag, catalog publication и published install требуют
отдельного release поручения. Экономия времени/токенов против classic пока
не доказана: fixture timings не являются сопоставимым benchmark.
