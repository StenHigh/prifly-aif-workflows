# W5: отдельные UI/UX-сессии в aif-feature

В `aif-feature@1.2.3` добавлен явный `parallel-ui-ux`, default sequential сохранён.
Изменений Pri-Fly и классического workflow нет. Другие шесть пакетов остаются
побайтно прежними. Пакет не опубликован в каталоге; установка не подключает
runner автоматически. [Настройка](../../parallel-ui-ux.md).

Этот режим нужен frontend-фиче с собственным изолированным окружением: после
checks/security/code review две свежие CLI-сессии независимо оценивают UI и UX.
Обе получают один candidate, свои criteria и разные browser contexts/identities.
Все read-only Attempts должны завершиться до cleanup/repair; общий quality call
с guard/commit остаётся replay unit. После repair новый candidate, environment,
grants и полный повтор всех проверок. Backend parallel остаётся прежним.

Admission до plan проверяет pinned adapter sources, browser capabilities,
Codex CLI и native quality capacity. Shared resource/limit1 и неподдерживаемый
host отказывают без скрытого sequential fallback. Native App/Claude допускаются
к компиляции, их runtime concurrency не квалифицирована.

Controller сохраняет исходные bytes reports и browser evidence с hashes;
program gate проверяет sealed manifest/ref/digest и прежние W1/W2 правила.
Grant связан с Run/round/candidate/request/configuration/adapter/owner/environment;
observation receipt дополнительно связан с actual Attempt. Reader не получает
sibling grant и не управляет окружением. Source contract охватывает семь Python
файлов; старые незавершённые parallel Runs требуют прежнего companion.

Отдельный error boundary превращает timeout/ошибку pure evaluator в diagnostic
assessment, после которого выполняется cleanup. Owner blocker имеет приоритет
перед repairable defect. Неуспешный cleanup не позволяет commit. Terminal cancel
требует дождаться реальных actors; операторский cleanup сверяет journal с native
accepted environment/configuration/adapter и не меняет исходный outcome.

Unknown ensure/release effect, убитый controller и writer-cancellation E3 требуют
явного осмотра/reconciliation. Это не общее решение внешних effects или OS sandbox.
Доверенный project adapter и визуальное суждение reviewers остаются границами
доверия. Fresh sessions не аттестуют разные модели или экономию времени.

Результаты текущей приёмки записываются отдельными `feature-uiux-*.json`.
Исторические `frontend-*` сохраняют квалификацию прототипа; они не используются
как доказательство новых shipping CLI-сессий.

## Воспроизведение

```sh
python3 -B tests/test_frontend_parallel.py
python3 -B tests/verify.py --binary /absolute/released/prifly
python3 -B tests/probes/feature_uiux_check.py --binary /absolute/released/prifly \
  --browser-library /absolute/node_modules/playwright --jobs 3 \
  --report /tmp/feature-uiux-runtime.json
```

Browser tool установлен по exact lock из `tests/fixtures/product`; CI выполняет
эту matrix отдельно от старой 17-case qualification. Без `--live-skills` все
model reports/session declarations детерминированные, браузер и native Run реальные.
Опциональная квалификация с реальным расходом CLI usage:

```sh
python3 -B tests/probes/feature_uiux_check.py --binary /absolute/released/prifly \
  --browser-library /absolute/node_modules/playwright --case repair-ui \
  --live-skills /absolute/pinned-ai-factory-2.19 \
  --artifacts /absolute/private/fresh-uiux-evidence \
  --report /absolute/private/feature-uiux-live.json
```

Это scoped UI/UX qualification: author, repair writer, checks/security/code review
и commit controller детерминированные. Две независимые CLI-сессии в каждом round
получают прежние upstream review/bridge instructions; controller не выбирает
вердикт и не редактирует их native submissions. Разные thread IDs, overlap,
original report/submission/event/PNG hashes и полнота checks записываются отдельно.
Self-reported screenshot inspection не является машинной аттестацией качества
визуальной оценки; разные модели и UI/UX других hosts не заявляются.

## Подтверждённые результаты

- [Live](feature-uiux-live-results.json): `repair-ui` завершился `succeeded`;
  четыре уникальные CLI thread IDs, две пары с positive overlap197.839s/139.102s.
  Первый UI report обнаружил overflow816px при viewport375px; UX дал pass своего
  check. После детерминированного scoped repair новые UI/UX reports дали pass.
  Оба окружения released, native guard/local commit пройдены. Проверены исходные
  report/submission/event hashes и PNG archives; final native bundle содержит те
  же bytes. Model identity unavailable отражена в отчётах, optional policyignore
  явно разрешена fixture: финальный gate warnings/nonblocking, не model PASS.
- [Compile](feature-uiux-compile-results.json):120 definitions/79 steps/7 packages,
  feature45, три hosts × два профиля. [Compatibility](feature-uiux-compatibility-results.json):
  5 launches/4 builds/4 trusted, state41. Install/update и unit/static результаты:
  [validation](feature-uiux-validation-results.json).
- [Source boundaries](feature-uiux-source-boundaries.json):233 tracked файла
  остальных шести пакетов совпадают с baseline f95f2c4. Core не менялся.

[Native/browser результаты](feature-uiux-runtime-results.json):32 из33 индивидуальных
assertions PASS, включая admission negatives, freshness, cleanup/cancel/timeout и
commit replay. Это исторические cases до admission guard; отказ8 зафиксирован ниже.
Их не называют35-case matrix последней версии. Прерванный тест в эту сумму не включён. Test-only finalizer получил
exact current-session lease guard и регрессию13 (commit98665bc); CLI/browser/lifecycle
functions после7f2f57a не менялись; последующие admission/begin guards описаны ниже.

## Уточнение приёмки1.2.1: storage envelope

Первый CI на7f2f57a выявил `storage_budget_exhausted` у UI/UX max-budget8.
Это native refusal, не PASS и не timeout теста. Log SHA и точная причина
сохраняются отдельно. Публичного CLI override не найдено; Core не меняется.
В1.2.1 explicit admission проверяет public sealed
`workflow_configurations[...].inputs.limit.value` для exact quality workflow:
разрешает1–3, отказывает4–8 до writers, не меняя запрос владельца. Отсутствующая
или неоднозначная configuration также отказывает. Sequential/backend1–8 прежние.
Теперь max-budget8 — early-refusal assertion, parallel-budget3 — настоящий Run
с тремя полными quality-кругами, двумя repairs и тремя released environments.
[Budget cases](feature-uiux-budget-results.json) PASS:8 rejected до writers,
3 native rounds завершились partial на последнем дефекте без лишнего repair,
все три окружения released. Unit14 и compile120/79/7 PASS.
[Source lineage](feature-uiux-admission-delta.json) подтверждает неизменность
reader/lifecycle functions и остальных шести pinned Python modules. Полная
34-case matrix на8c92cf6 прошла: [exact-SHA CI evidence](feature-uiux-ci-results.json).
Это зелёный parallel-ui-ux job, не полный CI последнего hard-guard patch.

CLI reader dispatch/observe/environment/release/cleanup и report transport после
live checkpoint7f2f57a не менялись. Повторный расход LLM для admission-only guard
не требуется: source lineage фиксируется отдельно, новый admission проверяется
unit14 и native cases. Старые live bytes/context hashes сохраняются как история,
не переписываются под новый source contract.

## 1.2.2: защита начала каждого круга

Pure program begin получает typed limit из quality-round и повторно проверяет
1–3 до checks/browser work. Это защищает внутренние вызовы и reviewed continuation,
даже если host отдал устаревший/неправильный admission. Обычный fresh launch
отказывает4–8 ещё до plan/implement; программа кругов не доверяет одному этому
заявлению. Unit15 проверяет limit8 refusal и прежний begin8 для sequential/backend.
Native limit-guard с намеренно подставленным capability остановился rejected
после writer, до checks/environment/repair/commit; это test-only forged/cached
host response, не production bypass option. Обычный frontend path также PASS; [native results](feature-uiux-round-guard-results.json).
CI38847358894 на5ac14a3: UI/UX job35 SUCCESS, все35 original case lines
проверены в [CI evidence](feature-uiux-ci-results.json); полный verify отдельно.

## 1.2.3: неопределённость при ошибке CLI

Unexpected CLI error/timeout до полного evidence callback не маркирует actors
settled: journal остаётся unknown, operator cleanup блокируется до фактического
осмотра/остановки собственных actors и reconciliation. Callback устанавливает
settled только после возврата обоих CLI actors и проверки original browser
receipts/PNG files. Поэтому последующий native submit refusal сохраняет уже
подтверждённое settlement. Unit16 проверяет оба исхода и отказ cleanup для unknown.
Это уточнение error bookkeeping; reader process/prompt construction, observe и
browser/report/lifecycle functions не менялись, кроме состояния dispatch errors.
Исторические live delivery bytes не переписываются. Source lineage дополнена
точным сравнением prefix инструкций dispatcher с live checkpoint7f2f57a.

Final source f43eb43 pushed, package1.2.3. Его [CI38848759987](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38848759987)
завершился **SUCCESS** на exact SHA `f43eb4389adde5aa6adc1c18228fc70cb0549354`:
оба jobs `parallel-ui-ux` и `verify` зелёные. Проверены35 original native/browser
case lines (все cleanup завершены),16 unit tests и17 прежних browser fixture cases.
В `verify` прошли default feature35/backend24, compile120/79/7, Classic
compatibility и все остальные gates. Terminal job steps, SHA256 полных logs и
original35 rows сохранены в [CI evidence](feature-uiux-ci-results.json),
поле `final_error_refinement`. CI использует deterministic actors, без live LLM.

Пакетная часть W5 завершена в заявленном scope: explicit Codex CLI, reviewed
owned isolated loopback adapter,1–3 quality rounds;4–8 отказ до writers.
App/Claude live concurrency, независимые модели и unknown external-write recovery
не квалифицированы. Пакет1.2.3 остаётся unpublished; tag/catalog не выпускались.
Pri-Fly и классический workflow не менялись.
