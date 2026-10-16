# W5 — пакетный backend-режим aif-feature

Дата: 2026-10-16. Пакет `aif-feature` переходит с подготовленной 1.0.0 на
**1.1.0**. Выпуск/тег/центральный каталог не входят в это изменение.
Implementation [d515a856b985](https://github.com/StenHigh/prifly-aif-workflows/commit/d515a856b985a12b2dbb6c519b0f1b13348003a9)
committed/pushed main. [Полный exact-SHA CI](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38833536583)
выполняется; локальная приёмка ниже завершена, полный CI PASS пока не заявлен.
[CI status](feature-ci-results.json) и [сводка проверки](feature-validation-results.json).
Pri-Fly **0.13.77** используется как выпущенный бинарник, Core не меняется.
Classic/profiled и остальные workflow вне feature не меняются.

## Объём и устройство

Корневой project input `review_mode` по умолчанию равен `sequential`.
`settings.feature.review_mode: parallel-backend` включает только backend,
с отдельной host admission до plan/implement. При frontend конфигурация
отвергается до writer; при неподдержанном host admission возвращает явную
недоступность. Автоматического fallback на sequential нет.

```text
warmup → configure → mode → [parallel host admission] → native plan → implement
  → quality call {
      repeat whole round {
        begin → capture → sequential checks → mode
          ├─ sequential: security → review → [frontend product quality]
          └─ parallel: call {security reader || code reader → all/wait manifest}
                       → collect original bytes → verify refs/digests + W1
        → owner/unavailable stop | accepted | scoped repair after both settled
      }
      → current-candidate guard → local commit
    }
```

Веер — отдельный child workflow. Две ветви сохраняют read-only StepDefinitions
и получают один captured candidate, свои request refs и разные Attempt workspaces.
Даже диагностический report завершает ветвь; содержание проверяется после
all-join. Missing report/technical error не становится PASS. Inner call/on_error
возвращает обработанный исход через round/repeat в replayable root quality call;
продолжение повторяет checks, оба reader, aggregation, guard и commit.

Parallel round требует до восьми StepInstances; default frontend — по-прежнему
до 14. При limit8 conservative acceptance budget114/root128 сохраняется,
depth увеличен до5, parallelism до2. Последний неуспешный круг не ремонтирует код.
Existing whole-quality resume после диагностического commit сохранён.

## Report adapter

Native aggregate-manifest содержит refs, а не bytes JSON reports. Assisted
`collect-reviews` — транспортный handoff существующему host controller.
`files/parallel_host.py` читает только точные refs через публичный `artifact export`.
Transport handoff не получает repository workspace. Это не ослабляет native
none-effects guard: правка кода во время активного reader по-прежнему получает
`effect_not_permitted`, после остановки actor нужны native cancel/reviewed continue.
Raw report не пересериализуется: canonical base64 сохраняет пробелы, порядок
ключей и исходный SHA256. Manifest digest связывает bundle с текущим join.

`files/parallel_reports.py` не имеет доступа к authority. Программный
`aggregate-parallel` проверяет native branch order/status/outcome, отсутствие
waivers, selection all, exact artifact IDs/revisions/digests и исходные bytes;
после этого **заново** выполняет W1 для каждого request/report/current candidate.
Подпись «ready» и session verdict не заменяют эту проверку. Missing/duplicate/
stale/substituted/invalid JSON/unavailable export блокируют repair/commit.

Evidence содержит исходный manifest, bundle с ref/raw_base64, каждый reader report,
полные критерии и итоговый gate. Наблюдения двух readers не объединяются и не
суммируются как дополнительные критерии. Предел транспорта4MiB/report объявлен
явно: отказ диагностический, bytes не усекаются.

## Host boundary

Поставляемый opt-in controller обслуживает только admission, точную пару readers
и collection. Обычные этапы остаются существующему host. Controller не делает
start/drive/continue, не исполняет writers, не меняет настройки и не запускается
скрыто при установке пакета. Подключение к runner явное; [команда и настройка](../../../aif-feature/README.md).

Проверяются наличие CLI dispatcher, released runtime>=0.13.77 и source hashes
трёх helper modules из sealed `parallel-adapter-contract`. Только явный
codex-cli backend dispatcher может сообщить ready. Native App/Claude dispatch и
parallel UI/UX этим не квалифицируются. Готовность инструментов не доказывает
будущую успешную работу модели, поэтому отказ/timeout оставляют настоящий
диагноз и реальные obligations.

Dispatcher проверяет common claim/candidate/round, раздельные Attempts/workspaces,
запускает два fresh CLI actors с sandbox/automatic review и ждёт обоих, прежде
чем отправлять их неизменённые submissions. Source snapshot контролируется до
и после actors. Разные session IDs не объявляются другой моделью; unavailable
model mapping остаётся видимым. W1 requests двух readers требуют separate session.

Exclusive marker в собственной Attempt workspace предотвращает blind duplicate
dispatch даже при другом пути evidence. Каждая Attempt имеет свой каталог
events/submission/report. После ошибки controller не отменяет Run автоматически
и не выдумывает unavailable от имени незавершённого actor: сначала устанавливают
фактическую остановку, затем native cancellation/recovery. Это cooperative
host contract, не новое доказательство изоляции со стороны ОС.

## Приёмка

Unit trust-boundary tests проверяют исходные bytes, неверный digest/ref/manifest,
пропущенные/дублированные ветви, waived/unsettled join, invalid encoding/JSON,
stale report и shared session, а также drift installed adapter/pinned contract.

`feature_parallel_check.py` использует **полный feature graph**, штатный report
adapter и программный evaluator. Его synthetic matrix отделена от live CLI:
direct, repair каждого backend lens, required unavailable, owner stop, limit/
max budget, cancel после первой ветви, owner edit/cancel, timeout replay,
partial/commit replay, intervening edit, unsupported host/frontend и malformed
transport не являются утверждением о настоящем host/model.

Live mode оставляет fixture author/checks синтетическими и выполняет только
security/review в настоящих свежих CLI sessions через **поставляемый** dispatcher.
Ожидается overlap, неизменённые submissions, exact raw export, native W1 gate,
guard и успешный local commit. Это другая граница, чем прежний W5 fixture/live
sample; сравнение стоимости или качества с classic не заявляется.

Фактические результаты на official Linux AMD64 Pri-Fly0.13.77:

| Проверка | Результат и граница |
|---|---|
| Native full feature graph | **24/24 assertions PASS**, grouped local qualification. Включая limit8 (восемь полных rounds, семь repairs), complete report transport, owner/unavailable priority и отказ stale/shared/missing evidence. [Отчёт](feature-runtime-results.json). |
| Cancel/timeout/replay | После первого **завершённого** security sibling review остаётся активным; cancel, owner edit/cancel и timeout завершаются, reviewed continue повторяет весь quality call. Один timeout также ждёт живой sibling и принимает его report. |
| Intervening edit | Правка между обоими принятыми отчётами и следующим handoff сохраняется; W1 возвращает blocked/partial, repair и commit отсутствуют. Fixture сортирует delivered tasks только для целевых first/last сценариев; API не обещает branch order. |
| Raw trust boundary | **12 unit tests PASS**: exact bytes/ref/digest, completeness, invalid JSON/base64, stale/shared reports, sealed/installed adapter source drift. |
| Compile/compatibility | **PASS**: 106 definitions/70 source steps в семи пакетах, feature profiles на трёх hosts; прежние пять launches/четыре builds/четыре trusted packages и legacy state41. [Compile](feature-compile-results.json), [compatibility](feature-compatibility-results.json). |
| Install/update | **PASS** в local unpublished catalog: exact bytes, сохранены extend/project overlays, local upstream edit отказан. [Отчёт](feature-install-results.json). |
| Default sequential regression | **35 ожидаемых сценариев PASS**, включая frontend, bounded repairs, read-only continuation, два synthetic hosts и сохранённые named writer negatives. Actual browser/Claude LLM этим не заявляются. [Отчёт](feature-sequential-results.json). |
| Actual shipped CLI adapter | **PASS**: две новые session IDs, overlap **100.940 s**, native collection/W1 gate/guard/local commit succeeded. Author/checks в fixture synthetic; security/review действительно выполнены CLI. [Отчёт](feature-live-results.json). |
| Model declaration | Model mapping unavailable остаётся явным warning при выбранном ignore; другая модель не аттестована. Это не оценка ожидаемой экономии или качества. |
| Protected source | **233 файла шести других пакетов неизменны**, включая classic/profiled. [Граница исходников](feature-source-boundaries.json). |

Exact events/prompts/submissions двух actual actors сохранены в owned
`/tmp/aif-w5-feature-live-shipping`; public live results содержат SHA256,
IDs/timing/usage и исходные report bytes внутри exported evidence. Native
assertions используют synthetic reports и не объявляются LLM observations.

## Оставшиеся границы

Параллельный frontend требует отдельной qualification browser contexts,
identity/ports/shared resources, cancel/cleanup и нового candidate после repair.
App/Claude остаются sequential до отдельного подтверждения host adapter.
E3 cancelled writer и реальные GitLab/private-project adapters не входят в scope.
Existing live W3 frontend observations не переносятся на новую версию без проверки.

Migration: task JSON и три product decisions прежние; default sequential
сохраняется. После обновления source нужен новый reviewed prepare с текущим
contract. Старые Runs/evidence не переписываются; переход существующего sealed
Run на новую closure требует штатного reviewed replay и сохранения его work/claim.
Initial1.0.0 у новых компонентов, 1.1.0 у изменённых existing components и пакета;
версии W1/W2 и canonical folders прежние.
