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
- [ ] При нехватке механизма опубликовать связанную Core issue из core-request.md с pinned reproducer и точными отказами.
- [ ] Связать Core issue с consumer issue #3; не закрывать consumer по одной поставке Core.
- [ ] Проверить опубликованный механизм Core и зафиксировать точный YAML-синтаксис и поддерживаемые версии.

## Пакетная реализация

- [ ] Объявить параметр с default 12 000, типом integer и проверкой диапазона.
- [ ] Применить эффективный контракт ко всем task refs classic и его выбранной композиции.
- [ ] Согласовать shared schema bytes/версии с aif-fix, если меняется общий авторский контракт.
- [ ] Получить profiled штатной генерацией и проверить fast/full/ultra.
- [ ] Повысить версии изменённых компонентов, пакетов и зависимых workflow по фактическому диффу.
- [ ] Проверить явный отказ несовместимой project extension при сборке.

## Приёмка на released Pri-Fly

- [ ] A1: установить прежний пакет, сохранить owner-настройку, обновить пакет и сравнить owner-файлы.
- [ ] A2: без настройки проверить 12 000 pass и 12 001 refuse через prepare/start.
- [ ] A3: при 32 000 проверить 16 557 pass, 32 000 pass и 32 001 refuse через prepare/start.
- [ ] A4: проверить 0, -1, 1.5, строку, boolean, null и неподдерживаемое большое целое число.
- [ ] A5: проверить точный pointer, effective limit и actual length; включить кириллицу и emoji.
- [ ] A6: сменить только настройку между prepare/start; прежний digest должен получить отказ.
- [ ] A7: передать полный task через plan, nested verify/review и repair/repeat в classic/profiled.
- [ ] A7: проверить совместимое opt-in расширение, которое получает task.
- [ ] A8: запустить два проекта с разными пределами в одной authority без definition drift.
- [ ] A8: сравнить refs, сохранённый контракт, task bytes и историю существующего Run после смены настройки.
- [ ] A9: проверить поддерживаемый continue после смены настройки либо документированный ранний отказ совместимости.
- [ ] Проверить отсутствие новых Run, claims и изменений дерева после отказов и read-only prepare.
- [ ] Проверить standalone fix, если изменён его task-контракт; независимый feature остаётся вне scope.
- [ ] Сохранить machine-readable результаты, binary provenance, source commit и границы synthetic/live приёмки.
- [ ] Удалить временные roots, claims и monitor registrations.

## Документация и выпуск

- [ ] A10: обновить package README, release guide, каталог и готовые examples на реальном синтаксисе.
- [ ] Дать полные команды установки, настройки, preview/start и поддерживаемого continue с явными placeholders.
- [ ] Разделить самостоятельный запуск и opt-in composition; проверить оба заявленных сценария.
- [ ] Выполнить versions/folders/derive и требуемые unit/contract/native checks.
- [ ] Выполнить verify.py и compatibility.py с `--binary` на latest stable.
- [ ] Получить CI на точном source commit и проверить артефакты приёмки.
- [ ] Записать реализацию, ограничения и результаты в CONTEXT_STATE.md.
- [ ] Подготовить reviewable PR; публикация выпуска и обновление каталога идут отдельным этапом.

Подготовка change не означает прохождение runtime-критериев A1–A10.
Проверка схем через Python не заменяет native prepare/start/continue.
