# E5 — Вложенные workflow через project extend

Статус capability: **выпущена в stable0.13.78, native probes51 PASS на0.13.79**.
[Pri-Fly #9](https://github.com/StenHigh/prifly/issues/9) пока OPEN; Core handoff
и release подтверждают доступность. [Сверка/результаты](release-0.13.79.md).
Пакетный follow-up: [W6](../add-review-uiux-call-extensions/proposal.md), реализация
и consumer qualification ещё впереди. Ниже сохранён исходный issue body на базе
0.13.77: его предложенный syntax не является текущим справочником. Реальный
контракт — marker `prifly-extension/2`, Project profile `/3` и local call refs;
см. [released handoff](https://github.com/StenHigh/prifly/blob/v0.13.79/openspec/changes/archive/2026-10-17-add-project-extension-native-call/handoff-w6.md).

## Проблема

Pri-Fly уже поддерживает native вложенные workflow через authored stage `kind: call`:
в aif-classic так устроены improve/verify/review. Однако project `extend.yaml`
позволяет вставить только StepDefinition. Нельзя подключить переиспользуемый
quality workflow без правки исходного графа или собственного форка маршрута.

Нужна вставка **native call-stage через extend**, чтобы проект мог добавить review
или UI/UX-приёмку, сохранив upstream workflow folder неизменным. Это generic
capability движка; знание пакетов AI Factory в Core не требуется.

База: latest stable **v0.13.77**, проверен 2026-10-16. На этом теге:

- [parser extensions](https://github.com/StenHigh/prifly/blob/v0.13.77/cmd/prifly/project.go#L1845-L1863) допускает `step`, но не call target;
- [applyProjectExtension](https://github.com/StenHigh/prifly/blob/v0.13.77/cmd/prifly/project.go#L2134-L2138) создаёт именно `kind: step`;
- [projectApplyExtensions](https://github.com/StenHigh/prifly/blob/v0.13.77/cmd/prifly/project_compile.go#L1501-L1527) выбирает только step components;
- существующий extension input binding допускает ровно один typed stage output.

Потребители из опубликованного v1.52.0:

- `aif-evidence:workflow/quality@1.0.0`: input request; outputs report/gate;
- `aif-product:workflow/quality@1.0.0`: inputs configuration/ui/ux;
  outputs gate/ui_report/ux_report/environment/release.

## Запрошенный контракт

Добавить отдельную ветвь authoring contract для вставки call. Сохранить текущий
step syntax и его семантику. Точный syntax определить в Core change; пример ниже
**иллюстративный, не поддерживаемый YAML v0.13.77**:

```yaml
extensions:
  - id: product-acceptance
    workflow: consumer
    call: project-product-quality
    between: {from: prepare-product, to: commit}
    input_bindings:
      configuration: $stages.prepare-product.configuration
      ui: $stages.prepare-product.ui
      ux: $stages.prepare-product.ux
    on: {succeeded: commit, partial: stopped, rejected: stopped}
```

`workflow` обозначает расширяемый граф, `call` — отдельную цель. В примере
producer и finish stages уже существуют. Не генерировать из имён новые стадии,
запросы, схемы или полномочия. Нужны:

1. Детерминированное разрешение объявленного дочернего WorkflowRevision с exact
   ref/version/digest в compiled package. Missing/ambiguous/wrong-kind refs —
   named compile refusal; никакого lookup по «последней установленной» версии.
   В первой версии допустим явно вендоренный project bundle: автоматический
   cross-package import через одну установку пакета не требуется этим issue.
2. Несколько typed input bindings у call, штатные проверки существования,
   достижимости producer, обязательных ports и **exact schema refs**. Ограничения
   legacy step extensions не снимать молча.
3. Выходы call доступны последующим стадиям с обычной проверкой guaranteed output
   для каждого исхода. Роутинг проверяет workflow outcomes, а не StepResult
   verdicts. Пропущенные исходы и недопустимые output reads — named refusals.
4. Native дочернее выполнение в том же Run/claim/candidate контексте: не запускать
   `project start` из program/assisted step, не создавать независимый Run и не
   скрывать его в host bridge. Действуют existing effects, resources, trust,
   child depth/steps/transitions/storage budgets и replay semantics.
5. Prepared launch учитывает callee, bindings, routing, resources и declared
   source dependencies. После их правки старый digest не разрешает dispatch.
   Resume сверяет effective accepted prefix штатно и даёт нужную replay boundary
   либо named refusal, без silent reuse чужих accepted outputs.

## Критерии приёмки

- [ ] **E5-A1:** Документированы discriminated step/call syntax, разрешение refs,
  inputs/outputs/outcomes и миграция. Legacy step extension fixtures неизменны.
- [ ] **E5-A2:** Released-CLI compile fixture вставляет call между существующими
  стадиями и исполняет child внутри одного Run. Child с внутренними step/call
  stages работает в пределах обычных limits; root source bytes не правятся.
- [ ] **E5-A3:** Одновходовый review-подобный child и трёхвходовый UI/UX-подобный
  child собираются; downstream получает точные declared outputs. Actual AI или
  browser не требуются engine fixture: это проверка generic runtime wiring.
- [ ] **E5-A4:** Named negative cases: step+call вместе, неизвестный target,
  wrong-kind/ambiguous ref, неизвестный/поздний producer, missing required input,
  exact schema mismatch, incomplete outcomes и output, не гарантированный
  на достигнутом исходе. Никакого частичного исполнения при compile refusal.
- [ ] **E5-A5:** Child succeeded/partial/rejected маршрутизируются по authored
  on. Неполученные outputs не подставляются; partial/blocked assessment не
  превращается в успех родителя по умолчанию. Точные разрешённые outcomes
  определяются самим callee, без hardcoded product policy в Core.
- [ ] **E5-A6:** Cancel/timeout/child error наблюдаемы в native state. Проверены
  settlement, ресурсы и reviewed whole-child replay/continue по обычным правилам.
  Native cancel не выдаётся за доказательство остановки внешнего browser actor.
- [ ] **E5-A7:** Depth/step/transition/resource/effect/trust limits действуют и
  внутри вставленного child. Capability не повышает policy и не обходит budgets;
  insufficient limits дают штатный диагностический отказ.
- [ ] **E5-A8:** Prepare→изменение callee/binding/route→start старым digest
  отказывает до dispatch. Continue после accepted child и изменения его
  контракта не переиспользует stale outputs; replay point/named refusal проверены.
- [ ] **E5-A9:** Исходный upstream graph, sibling workflows и projects без нового
  расширения сохраняют прежнее поведение. Scope target workflow документирован;
  рекурсивная вставка в любой internal graph не подразумевается автоматически.
- [ ] **E5-A10:** Обновлены schema/docs/CLI diagnostics и runner handoff/read
  representation в затронутой части; native harness проходит на поддерживаемых
  hosts с явным отделением synthetic compile/runtime от live host qualification.

## Зависимости и границы

Это следующий слой поверх существующих native call и project extensions,
а не повтор реализации nested execution или запроса одной input binding.
Не зависит от monitor/queue, W5 parallel mode или выбора другой модели.
Перед реализацией оформить Core change (proposal/design/tasks и spec deltas).

Пакетный follow-up: отдельный W6 в StenHigh/prifly-aif-workflows — project-owned
review/UI/UX adapters, complete lifecycle и recipes; зависит от **выпущенного**
stable с этой capability и собственных consumer tests. Закрытие issue само по
себе не является qualification пакетов. Канонические aif-classic/profiled
не редактируются, их версия/контрольные суммы не меняются. В Core не запрашиваются
product-specific repair policy, auto-merge/push/MR или автоматическая установка
проектной среды.
