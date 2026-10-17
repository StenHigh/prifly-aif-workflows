# План изменений workflow после сравнения с Software Factory

Дата: 2026-10-17. W1–W3: **committed/pushed, CI PASS**, с отдельными live observations;
W4: **committed/pushed, pilot qualified, CI PASS**; W5: **пакетная часть завершена, scoped qualification и final CI PASS; v1.52.0**.
Пакеты включены в [выпуск v1.52.0](../releases/v1.52.0.md). Актуальная база совместимости: released Pri-Fly
**0.13.79**, выпуск репозитория **v1.53.0**. Прежние CI/live evidence на
0.13.76 остаются историческими; повторная проверка нового stable записана отдельно.

В этом репозитории нет инициализированного OpenSpec-проекта. Change хранятся
как репозиторная документация: `proposal.md` задаёт объём и критерии приёмки,
`design.md` — решения и границы, `tasks.md` — ещё не выполненные работы.
Документы change описывают scope; executable реализации W1–W3 находятся в отдельных
новых папках, W4 — в standalone project example `examples/verified-integration`.

## Реестр

Отдельно от W1–W6 выпускается
[OpenClaw test audit](add-standalone-test-audit/proposal.md) — самостоятельный
`openclaw-test-audit@1.0.0` в [v1.53.0](../releases/v1.53.0.md), без AI Factory
skills и автоматических вставок в другие workflow. Восемь пакетов репозитория
повторно проверены на0.13.79 (compile/compatibility/contracts); runtime/live
evidence сохраняют исходную версию. [Результаты сверки](engine/release-0.13.79.md).
Семь прежних сохраняют bytes/версии v1.52.0.

| ID | Приоритет | Change | Зависимости | Статус |
|---|---|---|---|---|
| W1 | P1, первым | [Явные доказательства ревью](add-explicit-review-evidence/proposal.md) | Нет; безопасный baseline обязателен там, где используется | committed/pushed, CI PASS / v1.52.0 |
| W2 | P1 | [UI/UX-компоненты](add-ui-ux-review-components/proposal.md) | W1; standalone контракт среды из #2 | committed/pushed, CI + fresh CLI PASS; model/consumer limits / v1.52.0 |
| W3 | P1 | [Короткий workflow для фич](add-bounded-feature-workflow/proposal.md) | W1; W2 для интерфейсного профиля | committed/pushed, CI + live PASS; forced writer cancel deferred / v1.52.0 |
| W4 | P1/P2 | [Приёмка перед интеграцией](document-verified-integration-handoff/proposal.md) | W1; проектный интегратор, #1 при GitLab | committed/pushed, pilot qualified, CI PASS; real provider limits / v1.52.0 |
| W5 | P2 | [Квалификация параллельного ревью](qualify-parallel-implementation-review/proposal.md) | W1, W2, W3; сначала последовательная приёмка | backend opt-in/adapter d515a85; UI/UX qualification0bdc632: local17/CI job PASS для isolated stand, shared limit1 sequential; frontend1.2.3: CLI4 sessions PASS; native1–3 rounds qualified,4–8 refused before writers; final UI/UX35/unit16 и полный exact-SHA CI38848759987 PASS; пакетная часть завершена в указанном scope; App/Claude unqualified / v1.52.0 |
| W6 | P1 после E5 | [Review/UI/UX через call extensions](add-review-uiux-call-extensions/proposal.md) | E5 stable0.13.78+ (probes51 PASS на0.13.79); W1, W2; W3 regression boundary | ready for implementation; consumer qualification не выполнена; classic/profiled неизменны |

Каждый change выпускается отдельно с собственным bump изменённых компонентов,
пакета и зависимых workflow по действующим правилам. Версии здесь не назначены:
их выбирают по фактическому диффу реализации. По уточнению владельца 2026-10-14 classic и производный profiled остаются
эталонными: W1–W6 развиваются отдельно и не правят эти папки. Сначала проверяется latest stable.

## Pri-Fly Light — оставшаяся часть интерфейса

Пакетные W1–W5 выпущены, но отдельный упрощённый интерфейс по образцу Software
Factory ещё не сделан. E1 board/E2 queue в Core не закрывают эту цель.
Оба текущих monitor используют один frontend; отсутствие scan-root не меняет UI.

**E6/P1 — [Pri-Fly #11](https://github.com/StenHigh/prifly/issues/11)**:
отдельная компактная доска задач/очереди и результатов ревью, с переходом в полный
monitor. [Scope и E6-A1–A10](engine/E6-prifly-light.md). Статус: requested,
не реализован/не развёрнут; ожидаемый deployment — `prify-light.stenhigh.net`.
Полный `prifly.stenhigh.net`, classic/profiled и defaults не меняются.
Core delivery и actual browser/domain acceptance — разные обязательные этапы.

## Предпосылки P0

- [#5: baseline adapter сохраняет candidate](https://github.com/StenHigh/prifly-aif-workflows/issues/5).
  Проверять baseline в отдельной копии предпочтительнее подстановки файлов в
  candidate. При необходимости restore должен сохранять HEAD, index, dirty и
  untracked файлы, удаления и modes, включая прерванный путь. Это работа
  проектного adapter; upstream содержит обобщённый контракт и fixtures.
- [#2: жизненный цикл приватной среды](https://github.com/StenHigh/prifly-aif-workflows/issues/2).
  До живой браузерной приёмки согласовать общий профиль или объявленный переход
  между профилями; различать `release_required` и `reconcile_required`.
- [#1: повторная GitLab-публикация](https://github.com/StenHigh/prifly-aif-workflows/issues/1)
  используется в W4, без переноса проектных workers в canonical classic.

## Порядок

1. Предпосылки P0 в применимых интеграциях; W1.
2. W2, затем W3 с последовательными quality readers и живой приёмкой.
3. W4 и измерение времени, токенов, пропусков проверок и repair-кругов.
4. W5: квалификация released runtime и hosts; изменение core только при
   воспроизводимом недостающем контракте.
5. E1/E2 выпущены в Pri-Fly 0.13.77: применять native monitor board и явно
   выбранную native queue; отдельную очередь или доску в workflow не создавать.
6. E6: Light UI в Core поверх этих native sources; после released delivery —
   отдельная проверка domain rollout. E1/E2 release не является Light acceptance.

W1–W4 не зависят от E1/E2. Не добавляем обязательный набор четырёх reviewers
каждому запуску. Auto-merge, push/MR и tracker sync не становятся поведением
пакетов по умолчанию. Native skills и канонический classic сохраняют назначение.

## Задачи движка

- [E1: Pri-Fly #4 — обзор Runs](https://github.com/StenHigh/prifly/issues/4),
  [сохранённый issue body](engine/E1-run-board.md). Статус: closed,
  реализован в stable 0.13.77; свежая браузерная приёмка со стороны пакетов не заявлена.
- [E2: Pri-Fly #5 — локальная очередь](https://github.com/StenHigh/prifly/issues/5),
  [сохранённый issue body](engine/E2-task-queue.md). Статус: closed,
  реализована native queue в stable 0.13.77; живой запуск наших пакетов из очереди
  ещё не квалифицирован. Claim задачи сам по себе не запускает Run.
- [E3: prepared writer-cancellation follow-up](add-bounded-feature-workflow/engine-followup.md)
  воспроизведён в W3: resolved cancelled writer ещё не допускает reviewed continue
  (`recover_source_unsettled`). Issue body подготовлен локально, issue не опубликован;
  ordinary partial/read-only cancellation W3/W4 эту возможность не требуют.
  Дополнительные engine issues по W5 нужны только при воспроизводимом отсутствии
  контракта independent Attempts, join, cancel или recovery.
- [E4: Pri-Fly #6 — parallel cancellation](https://github.com/StenHigh/prifly/issues/6),
  [reproducer](qualify-parallel-implementation-review/engine-followup.md):
  closed, исправлен в stable 0.13.77. Старые stopping/invalid_input остаются
  историческим reproducer; актуальная проверка требует terminal cancel, native
  release и полного reviewed replay. Не смешивать с E3 writer cancellation
  или исправленным placement on_error. См. [повторную квалификацию](qualify-parallel-implementation-review/release-0.13.77.md).

- [E5: Pri-Fly #9 — nested workflow call через extend](https://github.com/StenHigh/prifly/issues/9),
  [сохранённый issue body](engine/E5-nested-workflow-extensions.md): capability
  выпущена в stable0.13.78, проверена E5 corpus51 на0.13.79. Issue пока OPEN;
  Core handoff готов. W6 ждёт реализации project recipes/consumer qualification,
  engine release больше не блокирует. [Результаты](engine/release-0.13.79.md).

- [E6: Pri-Fly #11 — отдельный Pri-Fly Light](https://github.com/StenHigh/prifly/issues/11),
  [сохранённый issue body](engine/E6-prifly-light.md): open/P1, UI gap поверх
  existing E1/E2. Native tasks/Runs/review provenance, настоящий отдельный
  frontend и production browser acceptance; текущие два monitor не считаются Light.

В Pri-Fly0.13.77 уже есть monitor board, native queue, title, `parallel`/join,
resources/model-profile reports и одна typed input binding legacy step extension.
С0.13.78 call extension допускает несколько typed bindings и exports; сложный
quality/repeat/parallel остаётся явно authored child graph. Эти возможности
повторно не заказываем. Старые ограничения0.13.77 — историческая база;
legacy step и новые call extensions различаются. Эталонные templates не правятся.

## Источники

- [Исходный Software Factory, закреплённый commit](https://github.com/zazencodes/zazencodes-season-3/tree/555467c365e6750278efba09349369109f62f65f/src/software-factory-claude-code).
- [Released Pri-Fly 0.13.77](https://github.com/StenHigh/prifly/tree/v0.13.77).
- [Пакеты v1.51.2](https://github.com/StenHigh/prifly-aif-workflows/tree/v1.51.2).

Заимствуем устройство процесса, не обещание качества: synthetic host проверяет
wiring и effects; отдельная живая приёмка проверяет поведение host/model.
Проверка схемы не доказывает истинность наблюдения. Сравнительных замеров
экономии пока нет; непроверенные случаи должны оставаться явно непроверенными.
