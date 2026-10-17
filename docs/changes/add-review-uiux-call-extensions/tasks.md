# W6 — работы

Статус: project recipes реализованы; финальная qualification/CI в работе.
База обновлена до released0.13.80; prerequisite ранее принят на0.13.79; [gates/51 probes](../engine/release-0.13.79.md).
[E5 / Pri-Fly #9](https://github.com/StenHigh/prifly/issues/9).

## До выпуска E5

- [x] Проверить latest stable0.13.77 и existing native call vs step-only extend.
- [x] Открыть отдельный engine issue с generic контрактом/negative cases.
- [x] Описать dependency graph, scope, W6-A1–A10 и план qualification.
- [x] Перечитать released Core handoff: extension/2 + Project/3, exact local
  closure, typed inputs/exports/outcomes, native replay и updated host guidance.

## Gate открытия реализации

- [x] Supporting stable0.13.78+ выпущен; прочитаны0.13.78 и0.13.79 по AGENTS.md.
- [x] Зафиксировать official0.13.79/hash, пройти verify/compatibility и native
  E5 corpus51. Engine prerequisites (A1) подтверждены; consumer A2–A10 впереди.

## Пакетная реализация

- [x] Выбрать explicit bundle/ref layout; проверить provenance, namespace/schema
  collisions и update contract, без неявного cross-package import (A3, A9).
- [x] Создать minimal authored consumer и проектные recipes review-only,
  UI/UX-only, review→UI/UX; classic consumer только через project files/extend,
  upstream canonical и profiled не редактировать (A2–A4).
- [x] Реализовать typed configuration/producer, exact refs и routing/gate
  propagation. Утвердить placement и freshness перед commit (A3–A5).
- [x] Явно подключить environment/cleanup/reconciliation и рассчитать limits,
  resources/effects/host capability; никакой скрытой migration/parallel (A6, A8).

## Qualification и выпуск

- [ ] Пройти матрицу acceptance.md на released binary: positive/negative,
  same-Run/claim, uncommitted candidate, partial/error/cancel/timeout, replay и
  accepted-prefix/prepare drift, реальный браузер (A2–A8).
- [ ] Пройти legacy gates; source hash comparison classic/profiled и untouched
  packages; отдельно scoped live consumer и честная host/model matrix (A9, A10).
- [ ] Обновить README/guide/project examples, minimum stable и migration;
  выбрать bumps по фактическому diff. Проверить final exact-SHA CI (A9, A10).
- [ ] Выпуск/tag/catalog только отдельным release-поручением, с повторной
  сверкой latest stable и обязательными gates по AGENTS.md.
