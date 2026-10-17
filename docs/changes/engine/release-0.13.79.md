# Pri-Fly0.13.79 — совместимость пакетов и обновление сервера

Дата: 2026-10-17. Прочитаны оба новых stable releases:
[v0.13.78](https://github.com/StenHigh/prifly/releases/tag/v0.13.78) и
[v0.13.79](https://github.com/StenHigh/prifly/releases/tag/v0.13.79).
[Команды/результаты и source boundaries](release-0.13.79-results.json).

## Изменения движка

0.13.78 исправляет claim ownership scan (#8), добавляет reviewed finite authority
storage budget recovery (#7) и native call extensions (#9). Последние требуют
Project profile `/3` и marker `authoring: prifly-extension/2`; несколько typed
inputs, exports/outcomes, error routes и exact local dependency closure работают
внутри родительского Run/claim. Legacy step extensions сохранены. Editor schemas
и generated runner guidance обновлены.

Storage setting — явная операция владельца с prepare/review digest; запись
использует storage version10 и требует совместимых writers после миграции.
Это не новый default limit и не изменение authoring workflow. В этой задаче
storage budget set не вызывался и проектные limits не повышались.

0.13.79 не меняет runtime после0.13.78: опубликованы scoped Codex app/CLI
acceptance и [W6 handoff](https://github.com/StenHigh/prifly/blob/v0.13.79/openspec/changes/archive/2026-10-17-add-project-extension-native-call/handoff-w6.md).
Live Claude и наша browser/product qualification этим не закрыты.

## Проверено

На official linux/amd64 binary
`sha256:d19a97274675f5762d45c550865183d28c30af545cca4c1de35a3fae5c202443`:
version/folder/derive, compile126 definitions/83 steps/8 packages,
compatibility5 launches/4 builds/4 trusted (core-state41), integration/backend/
UI/UX contracts и OpenClaw audit contract — PASS.
Public E5 corpus51/51 PASS: synthetic native CLI, не новый live host run.
Static scope string оригинального harness сохранена; происхождение фактического
released executable проверено отдельно по manifest/archive/binary SHA256.

Серверный managed CLI обновлён штатным signed updater **0.13.76 →0.13.79**,
старый binary сохранён в локальной резервной копии. Два действующих monitor
перезапущены; оба HTTP200, executable hashes совпадают с tested release.
Project runner files, inputs и workflow configurations этой операцией не обновлялись.

Все восемь package trees побайтно равны v1.53.0. Classic/profiled, их шаблоны
и маршруты не менялись. Полная предыдущая runtime CI qualification на0.13.77
остаётся исторической; здесь не заявлен её полный повтор на0.13.79.

## Статус исходного плана

W1–W5 выпущены в согласованном scope: explicit review, UI/UX, small feature,
project integration example и opt-in parallel review. E1/E2 native board/queue
уже в stable0.13.77. Scoped qualification не означает поддержку всех hosts,
моделей и приватных окружений; E3 forced writer cancellation остаётся deferred.

[W6](../add-review-uiux-call-extensions/proposal.md) ещё не реализован. Его
engine prerequisite теперь выполнен: supporting stable0.13.78+ и повтор51 E5
probes на0.13.79 подтверждены. Следующий отдельный implementation change —
три project recipes review-only/UI/UX-only/combined и настоящая consumer приёмка,
с unchanged upstream classic/profiled. Issue#9 при наблюдении ещё OPEN;
наличие released capability подтверждено независимо от административного статуса.

Новые возможности storage recovery не снимают current frontend parallel guard:
1–3 quality rounds qualified,4–8 refused before writers. Более широкая поддержка
потребует отдельного budget/consumer qualification; скрытого повышения лимита нет.
