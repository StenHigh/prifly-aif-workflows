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

Один root quality call содержит bounded repeat body. Readers только читают
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
