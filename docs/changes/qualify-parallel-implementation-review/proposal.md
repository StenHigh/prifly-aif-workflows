# W5 — Квалификация параллельного ревью реализации

Статус: **proposed**. Приоритет: **P2**. Дата: 2026-10-14.
База: released Pri-Fly 0.13.76 / пакеты v1.51.2.

## Проблема и результат

Исходный Factory запускает security/code/UI/UX одновременно и ждёт всех перед
repair. Pri-Fly уже поддерживает authored parallel/join; существующий fanout
дорабатывает план и не является квалификацией параллельных readers реализации.
Проверить доступное исполнение и добавить opt-in режим review нового feature
workflow, только когда фактические результаты это позволяют.

## Зависимости и границы

Зависит от [W1](../add-explicit-review-evidence/proposal.md),
[W2](../add-ui-ux-review-components/proposal.md) и последовательной приёмки
[W3](../add-bounded-feature-workflow/proposal.md). W3 не ждёт W5.
Не создавать новый core operator/model router и не менять canonical classic.
Host-specific ограничения фиксируются, не выдаются за параллельный pass.

## Критерии приёмки

- **W5-A1:** Один sealed candidate/round поступает всем выбранным readers.
  Sequential checks до веера и quality composition сохраняют смысл W3.
- **W5-A2:** Join ждёт terminal результатов всех включённых ветвей; ранний
  CHANGES/blocked не допускает repair, пока reader может продолжать чтение.
- **W5-A3:** Missing/malformed/stale report не закрывает round как successful.
  Findings агрегируются с происхождением, дубликаты не теряют evidence.
- **W5-A4:** Mixed pass/failed/blocked/owner cases дают правильную остановку
  или repair после join; все readers после repair читают новый candidate.
- **W5-A5:** Cancel/crash/late result не смешивают rounds, не теряют работу
  и не создают слепой повтор неизвестной Attempt. Resume имеет проверенный frontier.
- **W5-A6:** Resources/browser sessions/ports разделены; конфликт shared
  стенда не приводит к чтению чужой страницы. Candidate во время round не меняется.
- **W5-A7:** На каждом объявленном как parallel-supported host evidence
  подтверждает перекрытие времени реальных независимых reader-сессий. Compile
  `parallel` и scripted simultaneous reports не заменяют host observation.
- **W5-A8:** Неподдержанный host получает явный sequential mode либо named
  limitation до опасного dispatch; UI не обещает параллельность этому Run.
- **W5-A9:** Если stable блокирует нужный сценарий, сохранены minimal package,
  версия, команды, diagnostics и expected/actual. Только тогда открыть E3 с
  конкретным contract gap; existing operator/ресурсы не заказывать повторно.
- **W5-A10:** Released probes до finish и live host matrix разделены. Записаны
  время/токены/полнота checks для сравнимых sequential/parallel tasks; отсутствие
  measurements не заменяется заявлением об экономии.

Детали: [design.md](design.md). Работы: [tasks.md](tasks.md).
