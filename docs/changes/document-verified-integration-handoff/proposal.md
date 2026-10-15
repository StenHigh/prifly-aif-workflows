# W4 — Проверенная передача результата на интеграцию

Статус: **committed/pushed, pilot qualified, CI PASS; unreleased**. Приоритет: **P1/P2**. Дата: 2026-10-15.
База: released Pri-Fly 0.13.76 / пакеты v1.51.2.

## Проблема и результат

Local commit не означает готовность объединения с актуальной целевой веткой.
Отсутствие Git-конфликтов также не доказывает совместимость изменений. Перенять
роль final approver как проектную приёмку и адресное основание эскалации.

Подготовить runnable generic integration example: зафиксированный candidate и
target commit → проверка результата объединения в отдельном дереве → report
и решение → отдельно разрешённая local integration либо external publication.

## Зависимости и границы

Зависит от [W1](../add-explicit-review-evidence/proposal.md). С W3 совместим,
но не ждёт его выпуска: examples имеют собственный authored graph. Для GitLab
использовать [#1](https://github.com/StenHigh/prifly-aif-workflows/issues/1).
Не переносить project workers внутрь canonical classic. Без зависимости на E1/E2.

Не вводить auto-merge/push/MR по умолчанию. Локальный merge — отдельный явно
выбранный режим, а approval report не даёт permission произвольному Bash.
Сложный quality graph не маскируется простым `extend.yaml` шагом.

## Критерии приёмки

- **W4-A1:** Пример связывает acceptance criteria, отчёты W1, candidate identity
  и точный target commit; финальный reader делает declared spot checks.
- **W4-A2:** Тестируется результат объединения в изолированном integration tree.
  Fixture без textual conflict, но с semantic regression, не получает ready.
- **W4-A3:** Движение candidate/target после приёмки инвалидирует её. Исполнитель
  интеграции повторно проверяет identity до записи, сохраняет evidence причины.
- **W4-A4:** Политика эскалации явно включает auth/money, migrations,
  dependencies, deploy и business assumptions; хранится в project contract,
  не в hardcoded core branch. Владелец получает точное решение и evidence.
- **W4-A5:** Local merge и push/MR — отдельные declared effects/режимы. Отказ
  или неопределённый исход публикации не повторяется слепо и не объявляется
  «не создано», когда внешняя запись уже существует.
- **W4-A6:** GitLab repeat/formatting fixtures из #1 не создают второй MR,
  дают один Draft и не перезаписывают чужие изменения. Generic пример не
  зависит от конкретного tracker или credentials.
- **W4-A7:** Released 0.13.76 компилирует пример extension с одним bound input;
  unknown/unavailable producer и несовместимая schema отвергаются. Несколько
  inputs/loop/parallel представлены отдельным явным графом.
- **W4-A8:** Новый standalone пример и его документация корректно описывают
  one-input extension в stable. По уточнению владельца 2026-10-14 файлы
  эталонного classic/profiled не правятся; несовпадение старых комментариев
  объясняется в отдельном integration guide, derive_profiled остаётся прежним.
- **W4-A9:** Проба проходит approval/escalation, moving target, merge conflict,
  failed integrated check и interruption/reconciliation без потери candidate.
  Live host-проверка final reader отделена от offline provider fixtures.

Детали: [design.md](design.md). Работы: [tasks.md](tasks.md).

Реализация — [standalone project example](../../../examples/verified-integration/README.md),
не правка существующего пакета. Default assess; local_merge и gitlab_draft —
отдельные явно выбранные операции. Выпуск и real provider qualification отдельно.
