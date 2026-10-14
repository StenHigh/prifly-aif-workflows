# Design W2

## Применимость и композиция

UI и UX — разные readers и разные reports W1. Финальный gate принимает их
по закреплённому составу. Общий `gate-result` сейчас допускает verify/security/
review; не расширять enum молча: ui/ux lens остаётся в report, aggregate —
обычный review gate либо новый явно версионированный контракт.

Компоненты сначала собираются в тестовом явном графе. При W3 определить их
установочные source boundaries: необходимые компоненты должны реально попадать
в устанавливаемую папку или приходить по exact dependency. Не ссылаться на
соседние неустановленные каталоги. Classic остаётся canonical.

Requiredness и applicability задаёт reviewed configuration/scenario catalog.
Reader обязан обосновать not_applicable; изменение scope требует решения,
а не изменения состава проверки на ходу. Если сложная логика требует нескольких
inputs, использовать authored workflow graph, не обход `extend.yaml`.

## Среда и эффекты

Fresh checkout setup — проектный declared executor; браузер читает проверяемое
дерево через соответствующую dev/test среду. Installation, env provisioning и
release не прячутся внутри `effects: none`. Использовать existing execution
bindings/resource contracts, а не hardcoded Docker/npm.

Для flows с auth/формами нужны явно тестовые identities, данные и разрешённые
операции. По умолчанию production sign-in/submission не выполняются. Это
ограничение test adapter, не замена проверки сценария: непроверенное остаётся
видимым. Shared artifacts не содержат credentials и приватные project IDs.

Cancellation/recovery сохраняют evidence и candidate; cleanup проверяет
принадлежность среды и выполняется declared lifecycle executor.

## Реализованная первая композиция

Standalone aif-ui-ux содержит byte-identical W1 schemas/helper/bridge под их
исходными IDs; compile gate проверяет равенство source bytes. Собственные
configuration/environment/release schemas и steps имеют aif-product IDs.
Установка папки самодостаточна; ссылок на неустановленный sibling нет.

configure проецирует lens/scenarios/environment в descriptions typed W1
requests. Quality capture → environment → UI → UX → evaluate → release →
finalize возвращает два reports, environment/release receipts и review gate.
Evaluate проверяет scenario IDs/viewport/test URL и actual current Git basis;
finalize повторяет basis после release и связывает exact cleanup owner/session.
Quality call повторяется при continue; авторского repair/commit нет.

Среда — project-assisted adapter с external_write ensure/release и read-only
candidate; default общий compatible profile, transition не спрятан в reviewers.
Engine resource сериализует Attempts; lease project runner защищает жизненный
цикл между Attempts. Cancellation требует predeclared operator reconciliation.
Generic contract описан в ../../product-review-environment.md, actual private
consumer qualification остаётся issue #2. Native prepare отображает immutable
input digest; package preview отдельно показывает предметные choices.
