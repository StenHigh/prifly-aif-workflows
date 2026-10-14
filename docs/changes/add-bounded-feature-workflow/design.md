# Design W3

## Отдельный пакет

Новый launch сохраняет разделение feature/bug/canonical development. Profile
package определяет layout/check composition, а model_profile — требование
к сессии; эти сущности не смешиваются. Working name aif-feature проверяется
на catalog identity до выпуска. Ref/component versions назначаются по bytes.

Plan — native fast artifact pinned skill, а не Markdown copy из чужой Factory.
Criteria передаются явно (native manifest плюс report/catalog W1 в точной
композиции, выбранной при реализации). Нет исполнения чужого существующего
плана по догадке. Fresh worktree setup объявляет проект, не pinned prompt.

## Quality и repair

Один root acceptance call (stage quality) содержит bounded repeat body,
candidate guard и local commit. При partial commit default continuation
повторяет quality перед новой записью, а не переносит старый PASS. Readers только читают
candidate, отдельный workspace-write repair возвращает актуальную implementation
и diagnosis. Следующий round начинается с checks; все enabled readers повторяются.
Repair skill выбирается после сверки upstream и предмета работы: new feature
implementation нельзя молча подменить bug skill. Из aif-fix заимствуется
контроль rounds/blocked, не контракт исполнения любого нового требования.

При missing dependency сначала diagnostic partial, при подтверждённом дефекте —
repair, при owner-only blocker — остановка. Status gate имеет приоритет над
удобным verdict отчёта. W1 evaluator не принимает старый candidate.

## Resume и приёмка

Объявить root resumable stages и проверить stopped calls как replay units;
не обещать выбор nested step через root `--from-stage`. Prepare не изменяет
source Run или tree. Ранняя принятая работа переносится только при effective
contract match. Native plan replay/cleanup отдельно проверяется после cancel.

Backend и frontend profiles можно квалифицировать по отдельности. Объявлять
frontend поддержанным только после W2, не заменяя UI/UX молчаливыми bypass.
Published install и complete Run входят в release evidence; LLM-observations
не подменяются skill stubs. Existing workflows сохраняют назначение.

## Реализованная композиция и native scheduling

Separate aif-feature initial1.0.0, profiles backend/frontend. W1/W2 program,
schema/bridge copies byte-identical; child W2 graph получил новое имя
product-quality для независимых option aliases. Typed task seal-ит scope,
assumptions и checks/security/review; frontend включает required UI+UX scenarios.
Nested product policy/session choices должны совпадать с общей task policy;
base/round материализуются от immutable warmup base и текущего quality counter.

Native plan Tasks — код и выполнимые unit/static tests. Command/security/code/UI/UX
acceptance и owned browser setup назначены более позднему quality этапу; browser
criteria остаются обязательными, но не становятся зависимостью implementation
от ещё не поднятой среды. В ready/pass нет заявления о выполненном quality.

Released Core captures declared workspace_tree also on non-pass. Если native
planner остановился без ready plan, W3 сохраняет только явно non-executable
BLOCKED native snapshot с диагнозом, без executable Tasks. Typed result и
verdict не допускают его в implement. Retain сохраняет tracked owned progress;
default capture сохраняет blob bytes и освобождает only untracked owned path.

Forced writer cancellation — воспроизведённый deferred E3 boundary: after
inspected applied/not_applied resolve core still refuses recover_source_unsettled.
No flag reset or fake continuation. Graceful writer partial и read-only quality
cancel/chained/commit-stop continuation поддерживаются без core changes.
