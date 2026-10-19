# Native feature queue — работы

- [x] Проверить latest stable:0.13.80, новее базы ворот нет; скачать official
  asset отдельно, сверить binary SHA256 с предыдущей принятой базой.
- [x] Создать CLI-only consumer probe с private HOME/repository/authority,
  real programs/Git и отдельным full-monitor read listener.
- [x] Добавить TaskInput JSON, команды opt-in prepare/start/continue/complete,
  различие intake и typed task; связать README/index/release guide.
- [x] Пройти Q1–Q8 на official stable; записать outcomes, ограничения и cleanup.
- [x] Проверить неизменность всех8 shipping packages, включая classic/profiled;
  пройти обязательные статические ворота и compile/compatibility.
- [x] Добавить regression step и сохранение JSON результата в existing CI.
- [x] Сохранить результаты и обновить исходный план/CONTEXT_STATE.
- [x] Commit/push source679e2a1, принять полный exact-SHA CI39250210672 и
  скачанный native queue artifact; сохранить CI evidence и финальный статус.

Результат:3 cases /5 Runs, local и remote CI PASS; [приёмка](acceptance.md),
[local evidence](results.json), [CI evidence](ci-results.json).

Full exact-SHA CI39250210672 SUCCESS для679e2a1a9da2a15fdff6e23c8f13d60a0610f9ec:
verify/parallel-ui-ux/call-review-uiux. Docs/evidence follow-up [skip ci] не меняет
tested code, inputs, CI и shipping packages. Новый tag/catalog release не требуется.
