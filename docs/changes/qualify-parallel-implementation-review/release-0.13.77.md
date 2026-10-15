# W5 — повторная проверка на Pri-Fly 0.13.77

Дата: 2026-10-16. [Выпуск](https://github.com/StenHigh/prifly/releases/tag/v0.13.77)
закрыл [E4 / #6](https://github.com/StenHigh/prifly/issues/6).
Native cancellation blocker снят; production parallel profile ещё не включён.

## Что изменилось

В 0.13.76 два сценария намеренно подтверждали старый дефект: после первого
завершённого reader отмена sibling оставляла Run в stopping; drive, release и
continue отказывали. На 0.13.77 прежний assertion падает, потому что drive
успешен и Run достигает cancelled. Сохранять этот assertion означало бы требовать
возврата исправленного дефекта. Старые runtime/CI/live JSON сохранены как история.

Актуальный `tests/probes/parallel_check.py` требует:

- Cancel после первого результата → cancelled, без outcome, активных Attempts
  и unresolved effects; все Attempts settled.
- Поздний отчёт не принимается; повторный drive не меняет RunVersion и candidate.
- При сохранённом claim reviewed continue повторяет весь quality call:
  новый capture, две новые Attempts, общий новый candidate, прежний claim,
  сохранённая работа владельца и итог succeeded.
- Отдельный `cancel-after-first-release` освобождает claim штатной командой
  после terminal stop. Удаление временного каталога не считается native release.
- При owner edit во время reader исходный `effect_not_permitted` сохраняется;
  последующие cancel и full-round replay должны проходить по тем же правилам.

Две ошибочные error compositions остаются отрицательными сценариями:
`recover_frontier_unsupported` без wrapper и `resume_frontier_ambiguous` при
wrapper только на внешнем call. Это не новый запрос к движку.

## Проверки и границы

Официальный Linux AMD64 архив проверен по SHA256 из release-manifest:
`fa4b40eb0b13e0b5862f9c8c89707f31aa16fb0d545f3ad5f1419d5aaf02220b`.
SHA256 исполняемого binary:
`d0848b299c49206aa59a069cc7e924b36f52b883067180018be7fdd4ee85b6aa`.

Compile всех семи пакетов: PASS, 100 definitions / 67 source steps.
Compatibility: PASS, пять launches / четыре builds / четыре trusted packages,
прежний legacy state41. W5 compile: восемь definitions на каждом из трёх hosts.
Статические проверки: семь folder tests, три version tests и derive check PASS.
Runtime matrix: **25/25 assertions PASS** (23 CLI cases и direct pass на двух
других hosts). Две неправильные error compositions — ожидаемые named negatives,
не successful recovery. Cancel после settled sibling, owner-edit cancel/replay
и abandon/native release — успешные положительные проверки.
[Полный локальный отчёт](release-0.13.77-results.json) содержит runtime/compile
results, отдельный E3 recheck, source/binary hashes и границы заявлений;
исторический `runtime-results.json` описывает только 0.13.76.

В этом повторе используются synthetic reports и настоящий released runtime,
Git, evaluator и public artifact API. Нового live LLM, браузерного board/queue
pilot или полного CI на 0.13.77 эта локальная проверка не утверждает.
Все 310 защищённых файлов семи пакетов совпадают с прежним source-boundaries;
Core/classic/profiled/feature не изменяются. Нового тега или версии пакета нет.

## Что дальше

E1 (board) и E2 (queue) тоже выпущены в 0.13.77 и закрыты upstream. Они доступны
нативно, без отдельного workflow и без изменения classic. Их применение на
реальном потребителе и queue-bound запуск наших пакетов требуют отдельного pilot.
Queue selection передаёт Task ID, owner, revision и claim generation; claim
сам по себе не запускает работу и не заменяет reviewed prepare/start/reconcile.

Для W5 остались reviewed report adapter с проверкой raw bytes/digests,
opt-in composition в W3 quality/guard/commit, capability/admission и production
host loop, parallel browser isolation/cleanup и полная приёмка нового graph.
По умолчанию review остаётся последовательным. Полный W5 A1–A10 PASS и перенос
живых замеров с 0.13.76 на новую версию не заявляются. E3 отменённого writer
проверен отдельно: `feature_check.py --case implement-cancel` на 0.13.77
всё ещё воспроизводит `recover_source_unsettled` после inspected not_applied
resolve, сохраняя work/claim и очищая собственный stand. Это negative PASS,
не успешное восстановление; plan-cancel в этом повторе не запускался.

```sh
python3 -B tests/verify.py --binary /absolute/released/prifly
python3 -B tests/compatibility.py --binary /absolute/released/prifly
python3 -B tests/parallel_contract.py --binary /absolute/released/prifly
python3 -B tests/probes/parallel_check.py --binary /absolute/released/prifly --report /tmp/w5-runtime-0.13.77.json
```
