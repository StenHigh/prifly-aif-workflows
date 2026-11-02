# Передача в Core-сессию

Дата: 2026-11-01. Целевая сессия: «Load project context», `/srv/projects/prifly/core`.
Владелец согласовал полный автоматический цикл и создание отдельного Core issue.
Issue создан. Сообщение в сессию не отправлено: доступные tools не содержат send/handoff.

Готовый текст для Core-сессии:

> Возьми https://github.com/StenHigh/prifly/issues/14.
> Это согласованная задача от consumer prifly-aif-workflows#9.
> Сначала прочитай issue, правила Core и pinned generic reproducer из consumer PR#12.
> Проверь минимальную композицию существующих native calls перед добавлением нового механизма.
> Нужен project-owned measurement до reader на первом и повторном входах после child repair.
> Его новый output должен стать input следующего reader через явные typed bindings.
> Одна поддержка nested anchor без этой передачи недостаточна.
> Reader остаётся read-only; project measurement сохраняет declared effects и execution consent.
> Не добавляй application logic, runner/cache или догадки о применимости отчётов в Core.
> Проверь C1–C8, подготовь change по правилам Core и выпущенный generic example.
> Consumer qualification classic/profiled/fix остаётся отдельной частью aif-workflows#9.

Основа: released Pri-Fly0.13.82, binary SHA-256 прежний.
Fixture/driver pinned на consumer source95ea2cb77b69570c24891694e8e23bcf2d9102cb.
Focused CI41229072017 и полный CI41229071851 завершились SUCCESS.

```text
Core #14: порядок + typed bindings -> выпуск capability или доказанный existing path
                                              |
Consumer #9: report refs + bridges + routes + examples + native qualification
```
