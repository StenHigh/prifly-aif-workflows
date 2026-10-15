# W5 — результат квалификации

Статус: **qualification recorded; production blocked by cancellation gap**.
Pri-Fly **0.13.76**, официальный Linux AMD64 binary SHA256
`03ac382112a12001ea9e2a86e5a20db2d5e24ec79ce5339f6257c473d0f3322d`.
Новых stable releases на начало работы 2026-10-15 нет.

Квалификация выполнена отдельно от установленных пакетов. Изменений Core,
classic, profiled и остальных семи пакетов нет. В `aif-feature` остаётся
последовательная приёмка. Нового устанавливаемого workflow, parallel profile,
тега или записи каталога этот change не выпускает.

## Что проверено

[Минимальный граф](../../../tests/probes/parallel-review/workflow.yaml)
собирается из неизменённых W1 workers, schemas и bridges. Один capture внутри
quality передаётся двум read-only readers. Они используют один claimed source,
разные Attempts и отдельные каталоги outputs. `all / selection: all /
remainder: wait` сохраняет обе ветви, включая диагностические partial.

После join тестовый controller экспортирует точные sealed refs через публичный
`artifact export`, проверяет digests и сохраняет reader/check/report/evidence.
Одинаковые наблюдения остаются видимыми у обоих readers, но не считаются
дополнительными проверками или независимым подтверждением истинности. Нативный
manifest содержит **ссылки**, а не вложенные JSON-отчёты. Этот controller ещё
не является program-aggregator внутри feature workflow.

Repair проверяется отдельным действием владельца после terminal join: actual
исправление кода и командная проверка, затем reviewed continue с двумя свежими
readers и новым capture. Автоматического repair worker в fixture нет.

| Критерий | Результат и граница |
|---|---|
| A1 — общий candidate/round | PASS в fixture: одинаковые request и candidate у обеих Attempts. Встраивание в W3 с сохранением предварительных checks ещё не выполнено. |
| A2 — all-join | PASS: первый failed/blocked/owner не завершает Run до последнего reader. При timeout одного reader sibling остаётся активен и его отчёт принимается до окончания round. |
| A3 — полнота и provenance | PASS: W1 проверяет каждый report; native schema отвергает malformed и отсутствие обязательного output. Missing/duplicate/чужой round/request не дают successful acceptance. Агрегация точных sealed refs сохраняет происхождение и evidence. |
| A4 — composition/repair | PASS в backend fixture: blocked выше failed, owner выше repairable failed; после owner repair оба readers повторяются. Полная автоматическая W3 composition/repair пока не включена. |
| A5 — прерывания/recovery | **PARTIAL / BLOCKER:** timeout/partial и cancel до первого отчёта поддерживают full-round replay. Cancel после завершения одной ветви застревает в stopping/invalid_input; native claim release и continue отказаны. Это не successful recovery. Две неправильные error compositions также сохранены как named negatives. |
| A6 — среда и ресурсы | Backend: отдельные output workspaces, неизменность source, корректный effect_not_permitted при правке во время reader. Последующая отмена воспроизводит blocker A5. Параллельные UI/UX contexts, порты, identity/shared stands не квалифицированы. |
| A7 — реальное перекрытие | PASS только для двух реальных Codex CLI readers через явный probe dispatcher: четыре разных session IDs в паре sequential/parallel; overlap около 73.6 s. Не доказаны четыре lens, другой model или встроенный автоматический dispatcher host. |
| A8 — неподдержанные hosts | В shipping aif-feature на всех hosts сохраняется sequential review. Таблица ниже отделяет compile/synthetic от live. Параллельный frontend/production mode не объявлен ни для одного host. |
| A9 — необходимость Core | Подготовлен [E4 follow-up](engine-followup.md): native cancel не завершается после settled sibling, даже с правильным error wrapper. Это отдельный gap; ошибки placement on_error исправлены самим пакетом. E3 forced writer cancellation из W3 остаётся отдельным ограничением. |
| A10 — измерения | Один paired sample одинакового code/check scope; время, usage и полнота ниже и в live-results.json. Это наблюдение, не оценка ожидаемой экономии/стоимости/качества. Runtime и live gates разделены. |

## Где должен находиться error boundary

Поддержанный путь:

```text
root configure → call round
                   └─ call quality [on_error → rejected]
                        └─ capture → parallel {reader → W1 evaluate} → all-join
root: normal rejected outcome of call round → finish rejected
reviewed continue → repeat the whole root call round
```

Один timeout сначала оставляет Run running, пока sibling держит Attempt.
Controller принимает его точный отчёт; только после settlement обрабатывается
ошибка. При общем timeout внутренняя обёртка тоже возвращает normal rejected.
Внешний root call имеет однозначный обработанный outcome и подходит для replay.
Лимит timeout при продолжении не удаляется, source/state не переписываются.

**Отмена после первого результата остаётся блокером.** Без правок кода первый
reader/evaluate/branch завершается; второй отменяется. Все Attempts settled,
но Run остаётся stopping, повторный drive возвращает invalid_input. Claim release
отказан как claim_run_active, reviewed continue — recover_source_ineligible.
При owner edit native effect_not_permitted работает, затем cancel даёт тот же
отказ. Нельзя заменить это вымышленным unavailable report или сбросом состояния.
[Минимальное воспроизведение и acceptance E4](engine-followup.md).

Без error boundary получается `recover_frontier_unsupported`; один только
`on_error` внешнего root call приводит к `resume_frontier_ambiguous`. Эти
варианты нельзя переносить в feature. Проверенный внутренний boundary решает
проблему **timeout replay** средствами released Core. Reopen и late submission не используются
для обхода recovery. Existing W3 E3 относится к отменённому **writer** и остаётся
отдельным ограничением.

## Host matrix

| Host | Compile | Runtime с synthetic reports | Actual independent reader overlap | Доступный режим |
|---|---|---|---|---|
| codex-cli | PASS | Полная matrix | PASS: 2 fresh CLI sessions через opt-in probe | Probe backend; shipping feature sequential |
| codex-app | PASS | Direct pass | Не квалифицировано: нет проверенного dispatcher для независимых app sessions | Shipping sequential |
| claude-code | PASS | Direct pass | Не квалифицировано: live Claude dispatcher/session matrix не запускалась | Shipping sequential |

Compile для host не означает, что его bridge автоматически запустит несколько
readers. Prototype dispatcher вызывает `codex exec` в отдельных task workspaces
с sandbox/automatic review и точным grant своего source. Модель задают настройки
host; `independent-review` mapping unavailable сохранён как видимое warning.
Ни свежий session ID, ни значение model_profile не доказывают другой model.

## Живой замер

Scope: `calc.total(values)`, сумма чисел и ноль для пустого списка. Два readers
проверяют один и тот же code criterion; это **один уникальный критерий**, а не
две разные проверки. В обоих режимах каждый report содержит его один раз,
executed/passed; native W1 gates — warnings из-за unavailable model mapping,
Run succeeded при явно заданном ignore. Source и authority не менялись readers.

| Наблюдение | Sequential | Parallel |
|---|---:|---:|
| Fresh reader sessions | 2 | 2 |
| Wall span reader turns, s | 250.669 | 90.830 |
| Overlap reader turns, s | 0 | 73.615 |
| Reported input tokens | 772694 | 462767 |
| В том числе cached input | 708224 | 400640 |
| Reported output tokens | 8420 | 6064 |
| Полнота | 1/1 у каждого | 1/1 у каждого |

CLI 0.162.1, одинаковые pinned AI Factory 2.19.0 review/severity, code bytes и
check scope. Метрики охватывают только reader turns, включая действия tools;
не весь feature cycle. Это по одному запуску без рандомизации порядка. Cache,
число tool calls, scheduling и поведение модели различались. Во время разработки
исправлен error wrapper вокруг quality; сами W1 reader/bridge/skills и timed
normal review path не менялись. Замер не сравнивает две полные версии feature
graph и не обосновывает ускорение, экономию денег или равенство качества.
Input/cache/output — отдельные поля usage CLI; денежная стоимость не вычислялась.

Точные events, prompts, reports и submissions сохранены приватно в
`/tmp/w5-live-readers`; controller отправлял исходные submissions без правок.
Публичный [live-results.json](live-results.json) — производная сводка с hashes
исходных bytes, session IDs и timings, не сами приватные event logs.

## Решение о переносе

**Не добавлять parallel profile в aif-feature в этом change.** Возможность двух
параллельных backend readers доказана, но native cancellation blocker не позволяет
пройти A5/A6. Перед включением нужны:

1. Исправление и повторная released qualification [E4 cancellation](engine-followup.md),
   включая вариант без source edits и effect_not_permitted, native release/continue.
2. Получение и проверка raw reports после manifest внутри reviewed host/project
   adapter, без подмены детерминированного W1 evaluator модельным решением.
3. Встраивание в W3 whole quality/guard/commit replay unit, сохранение sequential
   checks до веера и repair только после settlement всех включённых readers.
4. Явная capability/admission host до dispatch; qualifier controller не считать
   встроенным production dispatcher. Сначала разрешать только проверенные hosts.
5. Для frontend — отдельные browser contexts/identity/resources и live проверки
   shared stand/port conflicts, cleanup, cancel и нового candidate после repair.
6. Новая полная приёмка изменённого feature graph; текущие наблюдения не выдавать
   за evidence этой ещё не существующей версии.

E4 — работа Core; этот change движок не меняет. Остальное относится к пакетам,
проектным adapters и host qualification. Версии семи
пакетов не меняются; собственные fixture graphs имеют initial 1.0.0 и не
публикуются. Миграции пользовательских проектов нет.

## Воспроизведение и gates

```sh
python3 -B tests/parallel_contract.py --binary /absolute/released/prifly
python3 -B tests/probes/parallel_check.py --binary /absolute/released/prifly --report /tmp/w5-runtime.json
```

Runtime matrix проверяет реальные Run/Git/evaluator/public export, но reports
синтетические. Live probe отдельно расходует настоящий host usage:

```sh
python3 -B tests/probes/parallel_live.py --binary /absolute/released/prifly \
  --skills /absolute/pinned-ai-factory-2.19-review-files \
  --artifacts /private/fresh-w5-evidence --report /private/w5-live.json
```

В skills нужны `aif-review.md` и `severity.md` с закреплёнными upstream bytes.
Не подставлять stubs для live. Owned Runs/claims освобождаются на поддержанных
путях; cancellation negatives сохраняют refusal native release. Default harness
удаляет только весь свой временный sandbox после фиксации evidence; это не native
release и не инструкция для consumer project. `--keep --case cancel-after-first`
оставляет собственный stand для чтения. Только собственная monitor registration
удаляется во всех случаях. Браузеры и внешние providers здесь не создаются.
Compile/native matrix добавлены в CI; live LLM не входит в CI. Итог точного
implementation commit и полного CI записывается отдельно после push.

## Записанные результаты

- [compile-results.json](compile-results.json): 8 sealed definitions на каждом
  из трёх hosts; reader/workers/schemas W1 byte-identical.
- [runtime-results.json](runtime-results.json): 24 сценария (22 CLI и два direct
  synthetic на app/Claude). Четыре terminal named negatives включают два Core
  cancellation blockers и две ошибки placement error boundary. Завершение
  matrix означает совпадение с этими результатами, не общий W5 PASS.
- [live-results.json](live-results.json): четыре настоящие fresh CLI sessions,
  исходные report/submission hashes, timings/usage и отдельная полнота checks.
- [source-boundaries.json](source-boundaries.json): все 310 существующих package
  files совпадают с baseline 942269b; закреплены собственные qualification sources.
- [validation-results.json](validation-results.json): static7/version3/derive и
  parse новых entry points. Exact implementation/full CI result следует отдельно.
