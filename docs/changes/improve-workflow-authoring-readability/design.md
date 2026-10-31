# Решения и границы

## Закреплённые входы

- Repository baseline: `v1.53.0` / `c85306050df060dc4b381ba7512173806250b3a6`.
- Начальный HEAD: `7260962d02285607d50a01389e5b6fd85dbfb1e2`; GitHub main совпадает.
- Принимаемый handoff: Pri-Fly `d010dd3ed4a4e6fb2af05a3ba7455fe256ab408d`.
- Product patch SHA-256: `d91952033fd67f59098d9eb0ae6b9bcba05f1afa148cc9ccadc91a229df48cf2`.
- Released runtime: Pri-Fly `0.13.82`; binary SHA-256 `3b073126921bca3e9d78b7649b51bd20527fd70cf4de44e0d440b5428b7712e5`.

Семь файлов patch раскрывают 64 сложных mappings, выносят verify bridge через существующий `context.source` и добавляют README-карту.
Decoded UTF-8 bytes инструкции сохраняются вместе с завершающим LF.
Прежние build keys требуются только до повышения author versions.
После bump меняется identity; итоговые сборки и маршруты проверяются заново.

## Производные пакеты

`aif-profiled` порождается из `aif-classic` инструментом `tools/derive_profiled.py`.
Копии общих компонентов сохраняют ID и одинаковые bytes.
Изменение classic должно попасть в profiled в той же проверяемой порции.
Остальные пакеты получают собственную оценку; случайное сходство не создаёт зависимости.

## Известный дефект

`verify fail/no_work → verify-once.stopped → verify-batch.unstarted → root.verify`
не имеет handler и даёт `unhandled_child_outcome`.
Patch сохраняет этот дефект. Исправление относится к отдельной задаче с согласованным terminal outcome.

## Runtime 0.13.82

Выпуск исправляет concurrent package install и блокировку реестра Git worktree.
Authoring contract, API и сохранённые Runs не меняются.
Изменение пакетов ради этих исправлений не требуется.
Официальный archive проверен по release manifest перед выполнением ворот.
