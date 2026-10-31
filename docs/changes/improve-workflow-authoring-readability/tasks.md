# Задачи

## Подготовка

- [x] Прочитать AGENTS.md и CONTEXT_STATE.md.
- [x] Выполнить fetch/pull --ff-only; GitHub уже синхронизирован.
- [x] Прочитать issue #6 и release notes Pri-Fly 0.13.82.
- [x] Скачать official binary, сверить archive SHA-256 по manifest.
- [x] Скачать pinned handoff и сверить SHA-256 patch.
- [x] Сверить изменения после baseline и выполнить git apply --check.
- [x] Завершить verify/compatibility на новом stable и записать результаты.

## Первая порция: classic + derived profiled

- [x] Применить patch и проверить hashes семи файлов.
- [x] Проверить YAML/bridge bytes до bump.
- [x] Выполнить 12 пар сборок и восемь пар маршрутов до bump.
- [x] Повысить версии classic с распространением зависимостей.
- [x] Перегенерировать profiled штатным инструментом.
- [x] Актуализировать guards, если они зависят от inline-формы.
- [x] Обновить README/release guide/catalog/examples и evidence.
- [x] Выполнить локальные ворота, финальные восемь пар и install/update smoke.
- [x] Получить exact-commit CI.
- [x] Повторно проверить latest stable перед тегом.
- [x] Выпустить порцию и обновить каталог.
- [x] Проверить published add/update с сохранением extend.yaml.

## Остальные пакеты

- [x] Составить inventory восьми shipping packages.
- [x] Подготовить отдельные проверяемые изменения для принятых кандидатов.
- [ ] Проверить семантику, instruction bytes и маршруты каждой порции.
- [ ] Выпустить порции; записать причины для неизменённых пакетов.

## Отдельный дефект

- [x] Оформить задачу verify fail/no_work с reproducer: issue #7.
- [ ] Согласовать terminal outcome с владельцем до отдельного исправления.

Порция оставшихся6: [remaining acceptance](remaining-acceptance.md), candidate v1.55.0.
