# W2 — UI/UX-компоненты приёмки

Статус: **proposed**. Приоритет: **P1**. Дата: 2026-10-14.
База: released Pri-Fly 0.13.76 / пакеты v1.51.2.

## Проблема и результат

Текущие пакеты не поставляют самостоятельную пару UI/UX readers с проверкой
выполнения браузерного сценария. Добавить компоненты для применимых задач:
UI оценивает визуальную согласованность, UX — поведение пользователя и состояния.
Первое включение — интерфейсный профиль нового feature workflow W3.

## Объём

- Read-only UI/UX steps, bridges, reports и последовательная fixture их вызова.
- UI: existing design system, desktop/mobile, overflow, hierarchy и contrast.
- UX: declared flows, loading/empty/error, keyboard/focus, labels/alt и copy.
- Проект задаёт browser adapter, setup, URLs, viewport/scenarios и test identity.
- Доступная среда и применимость checks закрепляются до их исполнения.

## Зависимости и границы

Зависит от [W1](../add-explicit-review-evidence/proposal.md). Живая browser
приёмка требует согласованного lifecycle среды по [#2](https://github.com/StenHigh/prifly-aif-workflows/issues/2).
Baseline-пути выполняют #5. W3 — потребитель, а не prerequisite: до него
компоненты проходят самостоятельные authored fixtures; текущие графы не меняются.

Не добавляем четыре reviewers каждому Run, browser CLI в engine, полный audit
доступности или production form submissions. Инструмент выбирает проект.

## Критерии приёмки

- **W2-A1:** Prepare показывает выбранные UI/UX checks, requiredness, scenarios
  и среду. Исключение reviewer — явный проектный выбор, не скрытый PASS.
- **W2-A2:** На frontend fixture реально выполнены desktop/mobile UI и
  пользовательский UX-сценарий; evidence связано с candidate и check IDs W1.
- **W2-A3:** Нет browser/tool/server — required check даёт blocked/partial с
  причиной, optional следует declared policy. Diff review не выдаётся за browser.
- **W2-A4:** Backend-only задача получает not_applicable с основанием. Изменение
  интерфейса не объявляется неприменимым только потому, что нет browser.
- **W2-A5:** Внедрённый overflow или сломанный flow даёт finding с evidence;
  отдельный repair и новый проход подтверждают исправление текущего candidate.
- **W2-A6:** Два jobs не делят browser session/ports по умолчанию. Shared
  стенд сериализуется объявленным resource, ownership виден и cleanup адресный.
- **W2-A7:** Setup/transition/cleanup имеют согласованные effects; reviewers
  не меняют candidate. Cancellation не освобождает чужой стенд/worktree.
- **W2-A8:** Compile/negative fixtures покрывают три hosts; отдельно живая
  browser-приёмка на реально доступных hosts, остальные помечены непроверенными.

Детали: [design.md](design.md). Работы: [tasks.md](tasks.md).
