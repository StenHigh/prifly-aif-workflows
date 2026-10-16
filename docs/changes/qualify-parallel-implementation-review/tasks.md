# Tasks W5

Qualification evidence: [acceptance.md](acceptance.md). Backend fixture and real
CLI normal delivery are qualified; **E4 fixed in 0.13.77; backend composition implemented**.
Package portion changes aif-feature1.2.2 only, with default sequential and
explicit codex-cli backend adapter. No Core/classic/profiled changes or tag/catalog publication. See
[feature composition](feature-composition.md) and
[released requalification](release-0.13.77.md); the old named cancellation
negatives below describe the original 0.13.76 qualification.

- [x] Завершить последовательную приёмку W3 и report/components W1/W2.
- [x] Создать minimal released-runtime fixture; проверить admission, read-only
  claim и separate Attempt workspaces; actual CLI independent delivery (A1, A7).
- [x] Зафиксировать решение: backend qualification prototype; не добавлять
  production parallel mode до проверки оставшихся границ (A8).
- [x] Проверить all-join/точные sealed refs/W1 identity/completeness в fixture;
  сохранить provenance и duplicate evidence (A1–A3).
- [x] Проверить mixed failed/blocked/owner, missing/malformed/stale/duplicate,
  delayed sibling и owner repair после terminal join (A2–A4).
- [x] Проверить read-only cancel, late rejection, intervening edit, общий timeout,
  один timeout при активном sibling и full-round replay с внутренним error
  boundary. Timeout/early cancel проходят; cancel после settled sibling остаётся
  named blocking negative, не successful recovery (A5).
- [x] Проверить, требуется ли Core: timeout wrapper реализуется в пакете;
  отдельный cancellation blocker воспроизводится без source edits. Подготовить
  E4, не смешивая его с W3 writer-cancellation E3 (A9). Открыт
  [Pri-Fly #6](https://github.com/StenHigh/prifly/issues/6).
- [x] Разделить three-host compile/synthetic и actual CLI observations. App/Claude
  live concurrency и browser matrix отметить unqualified, не PASS (A7, A8).
- [x] Снять paired reader time/usage/completeness; не заявлять ожидаемую экономию.
  Заполнить A1–A10 и version/migration notes с явными deferred portions (A10).
- [x] Добавить отдельные compile/native CI gates; live LLM остаётся opt-in.
- [x] Полный [CI38721905656](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38721905656)
  success на implementation7767464878593481818d9f3a7f84017485e42391;
  результат/steps/head/log hash и все24 W5 case lines записаны в ci-results.json.

До включения в aif-feature (отдельная production часть W5):

- [x] Исправление existing native parallel cancellation в Pri-Fly (E4) и новая
  qualification на released binary: terminal stop, native release и full-round
  reviewed continue. PASS на 0.13.77, включая owner edit/effect_not_permitted;
  отдельный abandon case проверяет native claim release. В рамках W5 пакетов
  Core не меняется (backend portion A5/A6; frontend остаётся ниже).
- [x] Реализовать reviewed host/project adapter получения raw reports после
  manifest, с детерминированной проверкой каждого digest и W1 gate.
- [x] Встроить opt-in composition в W3 quality/guard/commit replay unit, сохранить
  preliminary sequential checks и default sequential; автоматический repair
  запускать только после settlement всех включённых readers (A1, A4).
- [x] Проверить capability/admission до dispatch и native production host loop
  для явного codex-cli backend adapter; final actual two-reader loop прошёл
  через shipped helper, raw collection, W1/guard/commit. Native App/Claude
  concurrency этим не заявляются; установка не меняет existing runner (A8).
- [x] Квалифицировать параллельный UI/UX в отдельной native/browser fixture:
  contexts/identity/ports, shared stand conflicts, cleanup/cancel, новый candidate
  после repair (scoped A6). Изолированный owned stand работает на0.13.77 без Core
  changes; shared stand с native limit1 даёт named resource_busy внутри того же
  Run и остаётся sequential. См. [границы и результаты](frontend-qualification.md).
- [ ] Завершить полную приёмку уже реализованной frontend composition: admission до writers, pinned
  host/browser/report adapter, две actual independent UI/UX reader-сессии и
  приёмка полного aif-feature quality/repair/guard/commit. Browser fixture с
  детерминированными reports эту работу и A7/A8/A10 для frontend не заменяет.
- [x] Пройти новую backend приёмку actual feature graph: 24 native scenarios,
  unit12, three-host compile и scoped actual CLI observation; feature1.1.0.
  Старый fixture не заменяет эту приёмку. Default/full CI отражаются отдельно;
  полный W5 A1–A10 для всех hosts/frontend этим не объявляется.

Frontend1.2.0 implementation checkpoint: pinned host/browser adapter и scoped
actual CLI repair-ui PASS (4 sessions/2 rounds), compile120/79, critical8 native
cases PASS. Полная matrix33 и новый CI ещё выполняются; checklist выше не
выдаёт их за общий frontend PASS. [Evidence](feature-uiux-composition.md).

Patch1.2.1: native storage refusal8 rounds сохранён как negative; admission
явно разрешает1–3, не снижая4–8. Native3 rounds/2 repairs/3 releases PASS,
reject8 до writers PASS, unit14/compile120/79 PASS. Final34-case CI ещё pending.

1.2.2 pure begin повторяет typed limit guard для replay/internal calls. Unit15
и native forged/cached-admission guard PASS; final35-case CI остаётся отдельным.
