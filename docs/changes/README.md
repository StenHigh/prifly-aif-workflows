# План изменений workflow после сравнения с Software Factory

Дата: 2026-10-14. W1: **реализован и проверен локально**, остальные change: **proposed**. Выпуск не выполнен.
База: released Pri-Fly **0.13.76**, пакеты этого репозитория **v1.51.2**.
Stable проверен перед оформлением: новых выпусков нет. Это не новый прогон ворот.

В этом репозитории нет инициализированного OpenSpec-проекта. Change хранятся
как репозиторная документация: `proposal.md` задаёт объём и критерии приёмки,
`design.md` — решения и границы, `tasks.md` — ещё не выполненные работы.
Эти документы не являются executable workflow и не меняют действующие контракты.

## Реестр

| ID | Приоритет | Change | Зависимости | Статус |
|---|---|---|---|---|
| W1 | P1, первым | [Явные доказательства ревью](add-explicit-review-evidence/proposal.md) | Нет; безопасный baseline обязателен там, где используется | local implementation accepted / unreleased |
| W2 | P1 | [UI/UX-компоненты](add-ui-ux-review-components/proposal.md) | W1; контракт среды из #2 | proposed |
| W3 | P1 | [Короткий workflow для фич](add-bounded-feature-workflow/proposal.md) | W1; W2 для интерфейсного профиля | proposed |
| W4 | P1/P2 | [Приёмка перед интеграцией](document-verified-integration-handoff/proposal.md) | W1; проектный интегратор, #1 при GitLab | proposed |
| W5 | P2 | [Квалификация параллельного ревью](qualify-parallel-implementation-review/proposal.md) | W1, W2, W3; сначала последовательная приёмка | proposed |

Каждый change выпускается отдельно с собственным bump изменённых компонентов,
пакета и зависимых workflow по действующим правилам. Версии здесь не назначены:
их выбирают по фактическому диффу реализации. По уточнению владельца 2026-10-14 classic и производный profiled остаются
эталонными: W1–W5 развиваются отдельно и не правят эти папки. Сначала проверяется latest stable.

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
5. E1 — обзор Runs в monitor. E2 — очередь после подтверждённой потребности.

W1–W4 не зависят от E1/E2. Не добавляем обязательный набор четырёх reviewers
каждому запуску. Auto-merge, push/MR и tracker sync не становятся поведением
пакетов по умолчанию. Native skills и канонический classic сохраняют назначение.

## Задачи движка

- [E1: Pri-Fly #4 — обзор Runs](https://github.com/StenHigh/prifly/issues/4),
  [сохранённый issue body](engine/E1-run-board.md). Статус: open, P2.
- [E2: Pri-Fly #5 — локальная очередь](https://github.com/StenHigh/prifly/issues/5),
  [сохранённый issue body](engine/E2-task-queue.md). Статус: open, P3.
- E3 пока не создаётся: основание — только результаты W5, если stable не
  предоставляет нужную передачу независимых Attempts, join, cancel или recovery.

В Pri-Fly 0.13.76 уже есть monitor, title задачи, `parallel`/join, ресурсы,
model-profile reports и одна типизированная привязка входа extension. Не
заказывать эти возможности повторно. Сложные repeat/parallel и более одной
привязки пишутся явным графом. Несовпадение наших старых комментариев о полном запрете inputs с actual stable
разъясняется отдельным guide W4; эталонные templates не правятся.

## Источники

- [Исходный Software Factory, закреплённый commit](https://github.com/zazencodes/zazencodes-season-3/tree/555467c365e6750278efba09349369109f62f65f/src/software-factory-claude-code).
- [Released Pri-Fly 0.13.76](https://github.com/StenHigh/prifly/tree/v0.13.76).
- [Пакеты v1.51.2](https://github.com/StenHigh/prifly-aif-workflows/tree/v1.51.2).

Заимствуем устройство процесса, не обещание качества: synthetic host проверяет
wiring и effects; отдельная живая приёмка проверяет поведение host/model.
Проверка схемы не доказывает истинность наблюдения. Сравнительных замеров
экономии пока нет; непроверенные случаи должны оставаться явно непроверенными.
