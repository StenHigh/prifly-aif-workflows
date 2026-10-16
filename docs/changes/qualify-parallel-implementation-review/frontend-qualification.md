# W5 — квалификация параллельного UI/UX

Решение: **на Pri-Fly 0.13.77 можно параллельно проверять UI и UX в отдельном
тестовом окружении с изолированными browser contexts и данными. Изменения Core
для проверенной композиции не нужны.** Общий стенд с native `resource limit: 1`
остаётся последовательным: этот лимит считает Attempts, включая соседние ветви
одного Run. Повышать лимит вместо проверки владения стендом нельзя.

Это квалификация тестовой композиции, а не включение frontend-режима в пакет.
Все семь устанавливаемых пакетов побайтно прежние, включая `aif-feature`,
`aif-ui-ux`, classic и profiled. В `aif-feature` по-прежнему default sequential
и только ранее квалифицированный opt-in `parallel-backend`; frontend с ним
отвергается. Новых workflow для установки, версий, тега и каталога нет.

## Что исполнено

[Генератор fixture](../../../tests/parallel_product_fixture.py) копирует W2 в
собственную временную папку и меняет только граф композиции. W2 workers,
схемы и bridges сохраняются. Последовательность:

`configure → capture → environment → UI || UX → all-join → exact export → evaluate → release → finalize`.

Оба reader получают один capture, конфигурацию и receipt окружения, разные
requests по lens, Attempts и task workspaces. Repository workspace read-only.
Первый диагностический report не запускает evaluator или cleanup до settlement
второго. Внутренний call/on_error обрабатывает техническую ошибку пары; reviewed
continue повторяет capture, setup и обоих readers. Repair в fixture выполняет
владелец после terminal join и cleanup, автоматического writer здесь нет.

Тестовый controller через публичный `artifact export` читает только точные refs
из native manifest, проверяет digest и переносит исходные report bytes без
редактирования. Provenance сохраняет manifest/ref/raw_base64 каждого reader.
Вердикт формируют прежние program evaluators W1/W2; collector не принимает
решение о качестве. Это test controller, не shipping frontend host adapter.

## Браузер и владение

Зафиксированный Playwright 1.64.1 запускает настоящий Chromium. Два contexts
в одном браузере работают одновременно: UI проверяет desktop/mobile viewport,
overflow, заголовок, label и empty state; UX — keyboard focus, label и состояния
empty/error/loading/success при отправке формы. Сохраняются метрики, screenshot
hashes, context IDs и фактическое перекрытие операций. Барьер готовности исключён
из замера; ускорение и экономия этим замером не устанавливаются.

Каждой Attempt controller выдаёт отдельную анонимную fixture identity. Реальный
loopback API разделяет записи по cookie, отвергает неизвестную identity и
обращения без cookie. Contexts также проверяют отсутствие чужого localStorage.
UX отправляет тестовую запись через форму; UI не получает её данные или DOM state.
Это собственная модель identities для проверки изоляции; реальный login/OAuth,
production backend и произвольные shared services не квалифицированы.

Сервер получает свободный порт у ОС (`port: 0`). Два окружения имеют разные
порты; занятый фиксированный порт даёт `EADDRINUSE`, чужой listener остаётся
жив, неуспешный setup удаляет только свой lease. Cleanup требует точные
owner/session, ждёт остановки своего сервера и проверяет закрытие его порта.
Нативный Git claim не считается доказательством владения сервером или identity.

При отмене workflow **не исполняет автоматический cleanup tail**. В сценарии с
живым браузером controller сначала отменяет Run, видит ещё живые browser/server,
останавливает и дожидается только собственного browser actor, затем освобождает
своё окружение. Native Attempts должны быть settled до продолжения. Неопределённая
очистка сохраняет `reconcile_required` и блокирует gate; последующая операторская
очистка fixture не превращает этот Run в успешный.

## Матрица приёмки

[Native/browser report](frontend-runtime-results.json) содержит 17 сценариев.
Успех матрицы означает совпадение с ожидаемыми исходами, включая отказы, partial
и отмену; это не 17 успешных Runs.

| Сценарии | Проверяемый результат |
|---|---|
| pass | Оба реальных browser contexts работают одновременно, exact reports проходят W1/W2; предупреждение об отсутствии model mapping остаётся видимым. |
| defect-repair | UI замечает overflow, UX — сломанный success; partial, cleanup, owner repair, новый candidate/environment и две свежие Attempts, затем принятие. |
| cancel-before / cancel-after-first | Terminal cancel, отсутствие раннего cleanup, отказ поздней сдачи после первого report, полный reviewed replay. |
| cancel-during-browser | Native cancel не выдаёт живой браузер/сервер за очищенные; actor остановлен до cleanup, replay создаёт новое окружение. |
| one-timeout | UI истекает, UX остаётся активен, его report принимается; затем rejected, поздний UI report отвергается, оба readers повторяются. |
| intervening-edit | Изменение владельца после reports сохраняется, старый candidate не принимается. |
| stale-report-after-repair | Старый UI report вместе со свежим UX после repair даёт blocked, а не принятие нового candidate. |
| wrong-origin | Наблюдение с чужим origin не принимается. |
| shared-stand | Второму Run отказывает native resource, второму внешнему owner — lease; capacity-one отказывает и второму reader того же Run. Пара не dispatch-ится, Run явно отменяется, свой lease освобождается и доступен новому owner. |
| ports / port-conflict | Разные свободные порты, отказ на занятом порту, чужой listener и собственное основное окружение сохранены. |
| shared-context-refused / shared-identity-refused | Небезопасная конфигурация adapter отвергается до запуска браузера и изменения данных; отчёты не выдумываются. |
| wrong-cleanup-owner / cleanup-interrupted | Чужая очистка не выполняется; неоднозначный исход даёт blocked/reconcile_required, оператор сверяет точное владение. |
| missing-browser | Required browser check unavailable, gate blocked; код не подставляется вместо браузера. |

[Compile report](frontend-compile-results.json): 14 definitions на каждом из
трёх hosts, read-only readers, общий candidate/environment, all/wait и неизменные
W2 workers. Native browser matrix исполнена на `codex-cli` с детерминированным
test controller. Compile для App/Claude не объявляет их независимые сессии
квалифицированными. [Границы исходников](frontend-source-boundaries.json)
закрепляют shipping bytes и собственные qualification sources.

## Что эта проверка не закрывает

Это A6 и связанные A1–A5 для указанной fixture. Отчёты строятся из фактических
browser observations детерминированно. Модель не выносит визуальную оценку,
другая модель и отдельные LLM-сессии не заявляются. `require_separate_session`
в этой test matrix не включается: report содержит `session: shared` и
`model_profile: unavailable`;
model mapping остаётся warning при явно заданной fixture policy `ignore`.
Production policy или требования backend opt-in этим не ослабляются.
Reviewed continue этой W2 fixture сохраняет исходную configuration и её `round`;
проверены новые native Attempts/environment и свежий capture. Нумерация новых
feature rounds и их request identity остаются частью полной feature-приёмки.

Для подключения UI/UX к `aif-feature` отдельным пакетным изменением ещё нужны:

1. Admission до writers: только проверенный host/browser/environment adapter,
   отдельные identities и изолированный стенд. Capacity-one shared stand — явный
   отказ параллельному режиму; существующий sequential выбирается отдельно.
2. Shipping frontend report transport с закреплёнными исходниками, browser
   lifecycle и точным manifest, затем W2 evaluator внутри полного feature round.
3. Проверка двух настоящих независимых UI/UX reader-сессий с browser tools и
   screenshots; host capability нельзя выводить из успешного test controller.
4. Приёмка всего изменённого feature graph: preliminary checks, security/review,
   UI/UX, repair только после settlement, guard и commit после cleanup; полное
   повторение quality после repair/continue. Здесь security/review не исполнялись
   одновременно с UI/UX, четырёхсторонний веер не квалифицирован.

Новых issues Pri-Fly по этим результатам не требуется: проверенная композиция
работает, а `resource_busy` соответствует существующему Attempt-limit contract.
Проект с общим стендом может отдельно определить lease/identity protocol;
текущая fixture не разрешает его по умолчанию и не заменяет его большим лимитом.

## Повторение

```sh
python3 -B tests/parallel_product_contract.py --binary /absolute/released/prifly
npm ci --ignore-scripts --no-audit --no-fund --prefix tests/fixtures/product
tests/fixtures/product/node_modules/.bin/playwright install chromium
python3 -B tests/probes/parallel_product_check.py --binary /absolute/released/prifly \
  --browser-library "$PWD/tests/fixtures/product/node_modules/playwright" \
  --jobs 3 --report /tmp/aif-parallel-product-results.json
```

`--case` и `--cases` позволяют повторить сценарий или набор; с `--jobs` каждый
сценарий работает в отдельном процессе с собственными HOME/config/authority.
Для своего browser cache задайте одинаковый `PLAYWRIGHT_BROWSERS_PATH` при
установке и запуске. Удаляются только собственные временные Runs/claims,
регистрация monitor, browser actors, окружения и leases. Synthetic identities
и standalone fixture не публикуются как пользовательский workflow.
