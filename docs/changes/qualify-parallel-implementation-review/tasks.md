# Tasks W5

Qualification evidence: [acceptance.md](acceptance.md). Backend fixture and real
CLI normal delivery are qualified; **E4 fixed in 0.13.77; production composition pending**.
No Core or shipping package changes or tag/catalog publication. See
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
- [ ] Реализовать reviewed host/project adapter получения raw reports после
  manifest, с детерминированной проверкой каждого digest и W1 gate.
- [ ] Встроить opt-in composition в W3 quality/guard/commit replay unit, сохранить
  preliminary sequential checks и default sequential; автоматический repair
  запускать только после settlement всех включённых readers (A1, A4).
- [ ] Проверить capability/admission до dispatch и native production host loop;
  ручной probe dispatcher не выдавать за автоматическую поддержку host (A8).
- [ ] Квалифицировать параллельный frontend: browser contexts/identity/ports,
  shared stand conflicts, cleanup/cancel, новый candidate после repair (A6).
- [ ] Пройти полную новую приёмку изменённого feature graph и назначить version
  bump по его фактическим bytes; текущий fixture не заменяет эту приёмку.
