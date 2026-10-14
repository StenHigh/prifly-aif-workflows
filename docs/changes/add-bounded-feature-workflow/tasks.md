# Tasks W3

- [x] Завершить W1 и W2 для frontend; перечитать точный upstream skills tag и
  inventory, определить package profiles и решения (A1–A3).
- [x] Описать authored root/quality graph, native plan lifecycle, implementation
  и round artifacts, skill для repair и все verdict handlers (A2, A4–A7, A9).
- [x] Рассчитать max steps/transitions/child depth для полного repair limit;
  проверить start с максимальной конфигурацией (A5).
- [x] Реализовать отдельную installable папку и catalog draft, не меняя
  canonical graph; compile three-host/profile negative cases (A1, A10).
- [x] Прогнать до finish direct backend/frontend и repair каждого quality lens,
  missing dependency, owner decision, exhaustion и insufficient scope (A3–A7).
- [x] Прогнать native plan conflicts/capture, blocked/cancelled/chained resume,
  intervening edit и contract-change prepare/replay (A2, A8, A9).
- [x] Проверить install/update и source boundaries компонентов; выполнить
  static/version/derive/compile/compatibility/runtime gates (A10).
- [x] Провести live direct/repair/resume; собрать сопоставимые measurements без
  обещания экономии; заполнить matrix A1–A10 и deferred cases.
- [x] Подготовить отдельный package/repository bump, migration и pilot guide;
  публикацию/каталог выполнять только в рамках отдельного release поручения.


Реализован separate package1.0.0; repository release bump/tag/catalog остаются
отложенными до отдельного release поручения. Implementation commit
`b7e071e25fd52b9347f52b12adfa2990885a4786` отправлен в main. A8 partial/read-only cancellation
и reviewed configure replay выверены; forced writer cancellation после resolve
остаётся честным negative/deferred E3 (engine-followup.md), не successful resume.
Backend actual direct/repair/graceful writer continuation наблюдены; final
frontend scheduling/explicit-scope qualification и quality continuation PASS;
final-live-observations.json содержит исходные unedited отчёты и 19 fresh sessions.
Экономия против classic без одинаковой задачи/настроек не заявляется.

Полный [CI](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38653153795)
для implementation commit завершился success на latest stable Pri-Fly0.13.76;
existing gates и новые W3 unit/install/runtime35/actual-browser3 прошли.
Итог — [ci-results.json](ci-results.json). Публикация пакета остаётся отдельной задачей.
