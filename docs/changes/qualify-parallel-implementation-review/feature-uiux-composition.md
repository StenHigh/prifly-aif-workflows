# W5: отдельные UI/UX-сессии в aif-feature

В `aif-feature@1.2.0` добавлен явный `parallel-ui-ux`, default sequential сохранён.
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

Полная новая matrix33 и CI пока выполняются; их PASS этим не заявляется.
