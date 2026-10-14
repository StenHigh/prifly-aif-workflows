# W3 — Короткий workflow для небольшой новой фичи

Статус: **proposed**. Приоритет: **P1**. Дата: 2026-10-14.
Рабочее имя нового package/launch: **aif-feature**.
База: released Pri-Fly 0.13.76 / пакеты v1.51.2.

## Проблема и результат

Classic включает обязательную последовательность планирования и доработки;
aif-fix предназначен для конкретного неправильного поведения, а не новой фичи.
Добавить отдельный компактный development launch: краткий native plan с
проверяемыми критериями → реализация → полный включённый quality-круг → commit.

```text
warmup → native fast plan → implement → quality → commit → finish
                                        │   ↑
                                        └ repair → новый полный quality-круг
```

Quality в первой версии последовательный: checks, enabled security, code review,
применимые UI/UX. Ordinary improve и второй challenge reader не обязательны.

## Зависимости и границы

Зависит от [W1](../add-explicit-review-evidence/proposal.md); интерфейсный профиль
также от [W2](../add-ui-ux-review-components/proposal.md). Backend profile может
быть принят отдельно без объявления frontend profile готовым. Никакой
зависимости на E1/E2/W5. Baseline/environment prerequisites применяются по составу.

Использовать pinned AI Factory skills, прежде всего plan/implement; до design
сверить их фактический authoring contract. Не сочинять альтернативный spec
format, не запускать bug-fix skill как универсальную реализацию новой фичи.
Classic/profiled/fanout/fix не получают auto-selector или новый граф молча.

## Критерии приёмки

- **W3-A1:** Отдельный installable package и точный launch ID, input task и
  declared decisions; совет runner остаётся советом, start — reviewed выбором.
- **W3-A2:** Native plan содержит проверяемые criteria, scope и assumptions;
  business/scope-changing решения ждут владельца. Capture/materialisation
  выполняются existing protocol; чужой PLAN не выполняется/не удаляется.
- **W3-A3:** Прямой backend и frontend paths доходят до local commit/finish;
  обязательные checks соответствуют profile, пропуски видны по W1.
- **W3-A4:** После repair из любого quality reader все включённые checks
  повторяются на новом candidate. Старые PASS не переносятся через новую правку.
- **W3-A5:** Declared bounded limit и budgets согласованы с nested graph;
  исчерпание оставляет partial с последними gate/evidence и сделанной работой.
- **W3-A6:** Required unavailable check и owner-only blocker не запускают
  бессмысленный repair/commit; безопасно сохраняют diagnostic и candidate.
- **W3-A7:** Если короткого пути недостаточно, вернуть reason и выполненную
  работу. Не создавать classic Run автоматически; дальнейший launch и перенос
  работы требуют отдельного reviewed выбора.
- **W3-A8:** Same-version partial/cancelled/chained resume сохраняет исходный
  base, claim, ответы и работу; повторяет нужный quality-круг. Changed contract
  даёт фактический named refusal/replay boundary без reset/clean.
- **W3-A9:** Tracked plan policy и cleanup объявлены; default capture не теряет
  bytes. Package не пушит и не создаёт MR; чужие project documents сохраняются.
- **W3-A10:** Compile/negative fixtures на трёх hosts и synthetic runtime до
  finish плюс отдельные live direct/repair/resume observations. Existing gates
  и derive_profiled остаются зелёными; install/update/catalog проверены.

Экономия времени/токенов — измеряемая гипотеза, не критерий по неподтверждённому
проценту. Записать размеры/сложность задач и ограничения сравнения с classic.

Детали: [design.md](design.md). Работы: [tasks.md](tasks.md).
