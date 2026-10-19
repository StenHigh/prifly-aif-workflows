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

Результат:3 cases /5 Runs, локальный PASS; [приёмка](acceptance.md),
[evidence](results.json). Remote CI не запускался.

Remote CI будет принят только после наблюдённого прогона конкретного commit;
локальный PASS не называется CI PASS. Новый tag/catalog release не требуется.
