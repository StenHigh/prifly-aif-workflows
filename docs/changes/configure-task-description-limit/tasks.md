# Задачи

## Подготовка change

- [x] Прочитать уточнение владельца в issue #3 и критерии приёмки.
- [x] Проверить latest stable: Pri-Fly v0.13.89; новых выпусков нет.
- [x] Проверить исходные task schemas и общие ссылки classic/profiled/fix.
- [x] Проверить границу settings по исходникам released Core v0.13.89.
- [x] Проверить границы 12 000/12 001 и длину 16 557 через JSON Schema validator.
- [x] Подготовить proposal/design, критерии A1–A10 и черновик задачи Core.
- [x] Проверить штатное соответствие profiled через `derive_profiled.py --check`.
- [x] Проверить 40 локальных ссылок, формат diff и отсутствие изменений shipping bytes.

## Проверка механизма

- [x] Повторно проверить latest stable перед исследованием: v0.13.89; новых выпусков нет.
- [x] Подготовить generic fixture с корневым, дочерним и step потребителями одной схемы task.
- [x] Проверить profiles/settings/composition и compile values: presets работают, проектное число не достигает prepare/start.
- [x] Получить 8 length cases / 3 succeeded Runs; проверить exact refs, полные task bytes, неизменность прежних Runs и cleanup.
- [x] Сохранить native JSON с checksum binary, fixture и driver; versions/folders/derive PASS.
- [x] Опубликовать Pri-Fly #22 из core-request.md с pinned source ea80f473, native evidence и точными отказами.
- [x] Связать Core #22 с consumer #3 через исходный комментарий; consumer остаётся открытым до пакетной приёмки.
- [x] Проверить published v0.13.90: signatures/binary/gates, sidecars /1 и Project profile3–5.

## Пакетная реализация

- [x] Объявить task_description_limit с default12 000 и safe integer range1..9007199254740991.
- [x] Перевести все task refs classic и применимые project consumers на owned schema_task.
- [x] Получить одинаковый owned task1.2.0 и parameter sidecar в classic/profiled/fix; frozen contracts сохранить.
- [x] Получить profiled штатной генерацией; все три профиля компилируются на трёх hosts.
- [x] Повысить classic/profiled/fix до3.0.0 и версии изменённых steps/workflows.
- [x] Проверить port_type_mismatch для несовместимого frozen task consumer.

## Приёмка на released Pri-Fly

- [x] A1: установить прежний пакет, сохранить owner-настройку, обновить пакет и сравнить owner-файлы.
- [x] A2: без настройки проверить12 000 pass и12 001 refuse через prepare/start для всех трёх пакетов.
- [x] A3: при32 000 проверить16 557/32 000 pass и32 001 refuse для всех трёх пакетов.
- [x] A4: проверить0, -1,1.5, строку, boolean, null, unsafe integer, object и array.
- [x] A5: проверить /description, effective limit, actual length, кириллицу и emoji.
- [x] A6: сменить только32000→40000 между prepare/start; прежний digest получает project_start_stale_launch.
- [x] A7: передать полный task через plan, nested verify/review и repair/repeat в classic/profiled.
- [x] A7: проверить совместимое opt-in расширение, которое получает task.
- [x] A8: запустить два проекта с разными пределами в одной authority без definition drift.
- [x] A8: сравнить refs, сохранённый контракт, task bytes и историю существующего Run после смены настройки.
- [x] A9: проверить поддерживаемый continue после смены настройки либо документированный ранний отказ совместимости.
- [x] Проверить отсутствие новых Run, claims и изменений дерева после отказов и read-only prepare.
- [x] Проверить standalone fix, если изменён его task-контракт; независимый feature остаётся вне scope.
- [x] Сохранить machine-readable результаты, binary provenance, source commit и границы synthetic/live приёмки.
- [x] Удалить временные roots, claims и monitor registrations.

## Документация и выпуск

- [x] A10: обновить package README, release guide, draft catalog и готовые examples на released синтаксисе.
- [x] Дать полные команды установки, настройки, prepare/start и continue с явными placeholders и profile answers.
- [x] Разделить самостоятельный запуск и opt-in composition; проверить оба заявленных сценария.
- [x] Выполнить versions/folders/derive и требуемые unit/contract/native checks.
- [x] Выполнить verify.py/compatibility.py на official v0.13.90:8/132/88 и5/4/6trusted PASS.
- [x] Получить CI на точном source commit и проверить артефакты приёмки:6 jobs SUCCESS,10 ZIP digests/22 JSON reports.
- [x] Записать реализацию, ограничения и результаты в CONTEXT_STATE.md.
- [x] Подготовить reviewable PR: #16 MERGED. Публикация выпуска и обновление каталога идут отдельным этапом.

Локальная native-приёмка A1–A9 завершена:16 cases /31 Runs.
Документация A10 и exact-source CI PASS. PR #16 влит; repository release и каталог остаются отдельным этапом.
Живые модели и приватная инфраструктура в эту приёмку не входят.
