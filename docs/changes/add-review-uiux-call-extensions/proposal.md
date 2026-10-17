# W6 — Подключение review/UI/UX через вложенные workflow в extend

Статус: **ready for implementation; supporting stable E5 и native probes подтверждены**.
Пакетные recipes и consumer qualification ещё не реализованы.
Приоритет: **P1**. Обновлено: 2026-10-17. База проверки: Pri-Fly0.13.79,
пакеты v1.53.0 (review-evidence1.0.0, ui-ux1.0.0, feature1.2.3 unchanged).
[Prerequisite evidence](../engine/release-0.13.79.md): official binary, gates и51 E5 probes.
Текущая задача создаёт документы, без executable изменений, bump, tag или публикации пакетов.

## Проблема и результат

Пользователю нужна review/UI/UX-приёмка внутри своего workflow, в том же Run и
на том же candidate. Отдельные standalone launches не связывают её автоматически
с родительскими guards/commit. Исторически в v0.13.77 project extend вставлял только step.
С0.13.78 поддержан native call-extension, но наших consumer recipes ещё нет.

Предоставить project-owned adapters поверх released E5 и документированные
рецепты трёх подключений: review evidence, sequential UI/UX, review→UI/UX.
Отчёты, точный gate и cleanup влияют на продолжение родителя. Подключение
явно выбирает проект; default существующих workflow не меняется.

## Зависимости

1. **E5 / [Pri-Fly #9](https://github.com/StenHigh/prifly/issues/9)**: native call через extend, typed multiple inputs,
   exact callee refs, outputs/outcomes и continuation. Gate открытия реализации:
   capability опубликована в stable и необходимые native positive/negative
   probes пройдены. Gate выполнен на0.13.79: E5 corpus51 PASS. Closed issue
   или dev binary сами по себе недостаточны.
2. **[W1](../add-explicit-review-evidence/proposal.md)**: request/candidate/report/
   gate и explicit coverage. Published1.0.0 — исходная база переиспользования.
3. **[W2](../add-ui-ux-review-components/proposal.md)**: sequential UI/UX,
   project-owned environment, exact owner/session cleanup и reconciliation.
   Для реального проекта применим [контракт среды](../../product-review-environment.md)
   и [consumer issue #2](https://github.com/StenHigh/prifly-aif-workflows/issues/2).
4. **[W3](../add-bounded-feature-workflow/proposal.md)** — regression boundary
   и пример candidate/freshness, не обязательный standalone запуск.
   W5 parallel mode не требуется: первое подключение UI/UX последовательное.

W6 не зависит от E1/E2 queue/board. Независимая работа по аудиту тестов не добавляет зависимость:
её интеграция сюда не входит.

## Границы

В репозитории **не изменять ни одного файла aif-classic/ и aif-profiled/**,
включая их extend templates. Рецепт для classic живёт отдельно в examples и
применяется владельцем только к проектному extend/overlay установленного workflow.
Проверить upstream package bytes отдельно от намеренно изменённой project configuration.

Не заменять native child самостоятельным Run, CLI start из worker или host
conversation. Не включать автоматически parallel/другую модель/repair, push,
merge или MR. Не обещать consumer qualification приватного стека результатами
нашего fixture. Standalone launches W1/W2 остаются доступными.

## Критерии приёмки

- **W6-A1 — Release gate:** зафиксированы supporting stable version, release
  notes, official binary hash и native E5 probes. На0.13.77 рецепты помечены
  недоступными; документация не выдаёт предложенный syntax за работающий.
- **W6-A2 — Три рецепта:** в project examples исполнимы review-only, UI/UX-only
  и review→UI/UX. Минимальный собственный graph и отдельный classic consumer
  fixture проходят через project extend; upstream classic/profiled bytes прежние.
- **W6-A3 — Явные входы:** producer формирует request/configuration/ui/ux из
  явно заданных критериев, original base/round и текущей реализации. Все bindings
  exact-typed и callee/version/digests разрешены детерминированно. Старая schema,
  missing/late producer, неявный cross-package lookup и source drift отказывают.
- **W6-A4 — Native child:** приёмка идёт в том же parent Run и claimed candidate;
  видны child stages/Attempts, исходные report refs/digests и gate. Нет второго
  Run/claim или обхода workspace ownership; тест включает незакоммиченный candidate.
- **W6-A5 — Честная маршрутизация:** succeeded/partial/rejected и доступные outputs
  обрабатываются по callee contract. Required unavailable, defect, invalid/stale
  evidence и owner-only stop не ведут к commit/успешному finish. Политика допуска
  warnings явна. Ошибочный output binding/outcome отказывает до исполнения.
- **W6-A6 — UI/UX lifecycle:** actual Chromium проверяет объявленные scenarios;
  ensure/release принадлежат проекту. Cleanup exact owner/session предшествует
  продолжению/commit на обычных исходах; cleanup failure/unknown effects блокируют
  продолжение и требуют operator reconciliation. Отмена не подменяет cleanup.
- **W6-A7 — Replay:** tested partial/cancel/timeout + reviewed continue. Повтор
  приёмки получает fresh candidate/round/reports/environment по agreed boundary;
  intervening edit инвалидирует старое evidence. Callee/route/config drift после
  prepare или accepted child даёт штатный named refusal/replay, без reset/clean.
- **W6-A8 — Limits/permissions:** callee учитывает parent depth/step/transition/
  resource/storage budgets и effect/trust policy. Недостаток полномочий, capacity
  или бюджета диагностируется; установка рецепта не увеличивает limits молча.
- **W6-A9 — Регрессия и versions:** standalone W1/W2, sequential/parallel feature
  и classic без extension проходят прежние ворота. Hash comparison доказывает
  неизменность classic/profiled и остальных не затронутых shipping packages.
  Любые фактические package/component changes получают собственный bump и migration.
- **W6-A10 — Документы и наблюдения:** README объясняет component vs launch,
  установку project bundle, inputs/outcomes, minimum stable и removal/update.
  Native fixture matrix + actual browser PASS отделены от live host/model claims;
  проведён scoped live consumer run на заявленном host. Остальные hosts/models
  остаются unqualified до своих наблюдений. CI подтверждён на final exact SHA.

## Приёмка и порядок работ

[Design](design.md) задаёт границы компоновки. [Tasks](tasks.md) разделяет
подготовку до E5 и реализацию после stable. Базовые сценарии и доказательства —
[qualification plan](acceptance.md). Реализация по этому change пока не начата.
