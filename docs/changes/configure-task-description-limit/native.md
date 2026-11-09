# Native-проверка механизма на Pri-Fly v0.13.89

Проверка: 2026-11-10. Latest stable перед работой — `v0.13.89`; новых выпусков нет.
Core уже умеет подставлять число в схему при сборке.
Не хватает проектной передачи произвольного числа в сборку штатных prepare/start.
Это узкая граница конфигурации запуска, а не отсутствие параметризации схем вообще.

## Среда и пример

Использован официальный Linux amd64 binary из ранее проверенного выпуска.
SHA-256: `90e3e37c79a88ae0279a2542e40e34d75afa524b2b3cf7188900830ea7fe2985`.
Source выпуска: `30c3635081f8f012aef3953072dcd45d0807d618`.
Подписи manifest и архив проверены в [приёмке выпуска](../engine/release-0.13.89.md).
В этой проверке версия и checksum binary сверены повторно.

[Fixture](../../../tests/fixtures/task-description-limit/README.md) содержит root, child workflow и один worker.
[Driver](../../../tests/probes/task_description_limit.py) передаёт синтетический task и возвращает те же bytes.
Шесть task-портов имеют одинаковый exact schema ref внутри каждой сборки.
Описание содержит кириллицу и emoji; длина учитывает символы, а не байты UTF-8.
Project profile использует `/5`; extension и наследование используют `/5`.

```text
package profile -> task.maxLength -> root input -> child input -> worker input
                                                                    |
                                                 root output <- те же bytes

settings.task_description_limit -> configuration.default
                                  task.maxLength остаётся прежним

compile --value -> новая схема доступна при ручной сборке
prepare/start  -> собственной сборке это значение не передают
```

## Результат

| Сценарий | Наблюдение |
|---|---|
| Default 12 000, длина 12 000 | Prepare проходит; Run завершается `succeeded`; task возвращается целиком. |
| Default 12 000, длины 12 001 и 16 557 | Prepare и start возвращают `schema_invalid` по `/description` с пределом и фактической длиной. |
| `settings.root.task_description_limit: 32000` | Configuration default становится 32 000. `maxLength` остаётся 12 000; prepare/start отклоняют 16 557. |
| Настройка необъявленного input | `project_option_unknown_input`. |
| Попытка настроить обычный input task | `project_option_not_project_scoped`. |
| Замена package alias `schema_task` через project references | `project_composition_reference_conflict`. |
| Авторский package profile `expanded` | `maxLength` становится 32 000 во всех потребителях. Длины 16 557 и 32 000 проходят до `succeeded`. |
| Profile `expanded`, длина 32 001 | Prepare/start возвращают точный `schema_invalid`. |
| Проект выбирает необъявленный profile `project40000` | `project_compile_unknown_profile`. |
| Derived root с project setting 32 000 | Наследует схему 12 000. Prepare/start отклоняют 16 557. |
| `compile --value task_description_limit=40000` поверх package profile | `project_compile_profile_value_conflict`. |
| Тот же compile value в source без preset profiles | Сборка проходит; схема получает 40 000 во всех потребителях. |
| `prepare/start --value task_description_limit=40000` | Оба возвращают `invalid_usage`: флаг `--value` не объявлен. |
| Prepare/start source без profiles после ручного import сборки 40 000 | Оба возвращают `project_compile_unresolved_values`: запускают собственную компиляцию без этого значения. |

Восемь проверок длины создали три успешных Run.
Дополнительные compile-проверки не создавали Run.
Каждый успешный Run передал полный task через child и worker; digest root output совпал с входом worker.
Prepare и проверенные отказы сохранили файлы проекта, package inventory, Runs и claims.
Последующие изменения конфигурации не изменили полное сохранённое состояние трёх прежних Run.
Временный root и одна monitor registration удалены; active claims — 0.

Точный отчёт: [native-0.13.89-results.json](native-0.13.89-results.json).
Он содержит compiled definitions, actual Problem envelopes, digests fixture и driver.
Versions — 4 теста PASS; folders — 7 тестов PASS; derive `--check` — PASS.
Shipping packages и Core в этой проверке не менялись.

## Воспроизведение

Из корня checkout выполните:

```sh
PRIFLY_BIN=/absolute/path/to/released/prifly-v0.13.89
"$PRIFLY_BIN" --json version
sha256sum "$PRIFLY_BIN"
python3 -B tests/probes/task_description_limit.py \
  --binary "$PRIFLY_BIN" --output /tmp/task-description-limit-results.json
```

`PRIFLY_BIN` — placeholder для официального binary с указанным SHA-256.
Нужен Python 3; AI Factory skills и живая модель не требуются.
Driver самостоятельно готовит profile, inputs, prepare и reviewed start успешных случаев.
Приватный task владельца не нужен: синтетическая длина 16 557 воспроизводит ту же границу.

## Вывод для Core

Авторские profiles уже позволяют предложить конечный набор пределов без нового Core.
Это частичный вариант для заранее выбранных значений, включая 32 000.
Он требует сочетать предел с уже существующими `fast/full/ultra` layouts.
Он не выполняет требование этого change: проект задаёт своё положительное целое число через конфигурацию.

`project compile --value` уже обеспечивает нужную числовую подстановку при ручной сборке.
Новая capability должна по возможности использовать этот механизм с объявленным типом, default и owner-конфигурацией.
Точный синтаксис и безопасная область подстановки остаются решением Core.
Запрос Core не должен утверждать, что существующие схемы нельзя параметризовать.

Приёмка shipping classic/profiled, обновление установленных пакетов и continue остаются следующими этапами.
Успех synthetic worker не доказывает работу живой модели с увеличенным контекстом.
