# W6 — работы

Статус: **реализовано; начальная consumer qualification и полный CI PASS**.
Source f4e40e7; исходные package bytes прежние. Расширенные границы ниже.
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
  E5 corpus51. Engine prerequisite (A1) принят; consumer qualification теперь описана ниже.

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

- [x] Начальная матрица на official0.13.80:27 native CI cases,18 compiles/8
  refusals; same Run/claim, dirty/untracked candidate, diagnostic routing, real
  Chromium. Дополнительно direct cancel→continue2 и deadline/process timeout2;
  Core51 controls/limits/replay отдельно. Подробнее acceptance.md (A2–A8).
- [x] Локальные legacy gates, shipping8 tree comparison с v1.53.0; scoped
  live combined classic3 fresh Codex CLI readers, original reports/receipts и
  screenshots. App/Claude runtime synthetic, live не квалифицированы (A9,A10).
- [x] Обновить README/guide/project examples, minimum stable и migration;
  shipping8 прежние, bump не нужен; final exact-SHA CI39038596555 SUCCESS (A9,A10).
- [ ] Выпуск/tag/catalog только отдельным release-поручением, с повторной
  сверкой latest stable и обязательными gates по AGENTS.md.


## Расширенная квалификация и границы

- [x] Direct W6 corpus7 root limits/trust/effects, finite8MiB storage отказ с
  сохранением10 Attempts и explicit owner recovery; capacity1 отказ с нулём
  queued Attempts. Дополнительные custom loops/resources требуют своей приёмки (A8).
- [ ] Private project environment и произвольные варианты interrupted/unknown
  external actor reconciliation; fixture не заменяет admission из issue#2.
- [ ] Actual App/Claude/model qualification при необходимости. Generic Core
  controls и synthetic host results не выдаются за эти наблюдения.

W5 parallel/UIUX shared resource не входят в первую W6 версию; installer
принимает только isolated shared_resource:null. Catalog release не требуется:
shipping package bytes/versions прежние; project examples поставляются с main.
