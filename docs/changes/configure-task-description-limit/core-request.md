# Связанная задача Core: проектные compile values для prepare/start

Статус: подготовлена к публикации после native-проверки released v0.13.89.
Подтверждённая граница — передача проектного числового значения в сборку штатного запуска.
Package profiles и standalone compile уже умеют параметризовать схему.

Заголовок: `Project-owned compile values for task schema limits in prepare/start`.

## Проблема consumer

Источник: [workflows #3, уточнение владельца](https://github.com/StenHigh/prifly-aif-workflows/issues/3#issuecomment-6751418651).
На Core 0.13.88, project profile `/5` и classic v1.57.0 описание длиной 16 557 символов получает отказ.
`project questionnaire --prepare` возвращает `schema_invalid` по `/description`; схема допускает 12 000 символов.
Проекту нужен настраиваемый предел без изменения upstream-owned файлов.
Пример: предел 32 000 должен принимать полный task.

Проверка released исходников v0.13.89 подтверждает узкую границу `settings`.
`projectSetWorkflowSetting` меняет default объявленного project-scoped input, а не schema keyword.
Вход с числом после старта не меняет первичную валидацию task.
Статические package profiles выбираются из авторских значений; они не дают проекту произвольное целое число.
Native-пример подтверждает положительный profile 32 000 и согласованные refs во всех task-портах.
Он также подтверждает standalone `project compile --value task_description_limit=40000` в source без profiles.
Но prepare/start не объявляют `--value`; без флага они повторяют сборку без этого значения.
Предварительный import ручной сборки не устраняет `project_compile_unresolved_values`.

## Проверенный reproducer

[Driver](../../../tests/probes/task_description_limit.py),
[fixture и команды](../../../tests/fixtures/task-description-limit/README.md),
[native JSON](native-0.13.89-results.json), [разбор результатов](native.md).
Официальный binary v0.13.89 имеет SHA-256
`90e3e37c79a88ae0279a2542e40e34d75afa524b2b3cf7188900830ea7fe2985`.
Восемь проверок длины создали три успешных Run в одной временной authority.
Driver использует синтетические кириллицу/emoji и отвечает worker без модели.
Он проверяет сохранение полных task bytes, единые schema refs, неизменность прежних Run и cleanup.

| Механизм | Результат на v0.13.89 |
|---|---|
| Declared project setting с тем же именем `task_description_limit=32000` | Configuration default меняется; task.maxLength остаётся 12 000; prepare/start отклоняют 16 557. |
| Derived root с той же настройкой | Наследует прежний task.maxLength 12 000. |
| Замена `schema_task` через project references | `project_composition_reference_conflict`. |
| Авторский profile `expanded` | task.maxLength 32 000, root/child/worker пропускают 16 557 и 32 000; 32 001 получает точный отказ. |
| Необъявленный profile `project40000` | `project_compile_unknown_profile`. |
| `compile --value` поверх profile default | `project_compile_profile_value_conflict`. |
| Source без profiles и `compile --value task_description_limit=40000` | Сборка проходит; схема получает 40 000. |
| Prepare/start с тем же `--value` | `invalid_usage`: flag provided but not defined: -value. |
| Prepare/start без флага после import ручной сборки | `project_compile_unresolved_values`. |

Авторские presets могут решить частный случай 32 000 без новой capability.
Запрос относится к поддержанному выбору проектом своего положительного целого числа.
Compiler уже выполняет подстановку; просьба проверить, как использовать её в штатном project launch.

## Требуемое поведение

По возможности использовать существующую подстановку compile values.
Предпочтителен узкий объявленный параметр сборки с типом, диапазоном и default.
Consumer не требует общего разрешения на произвольную замену схем.
Имя YAML-поля и версия authoring contract остаются решением Core.

1. Пакет объявляет разрешённый параметр и default; проект сохраняет значение вне upstream-owned файлов.
2. Compiler применяет значение до проверки task и согласует schema refs всех достижимых потребителей.
3. Prepare и start используют одинаковый контракт и точную сводку запуска.
4. Новый Run сохраняет контракт; смена настройки не переписывает существующий Run.
5. Update сохраняет owner-настройку; несовместимая настройка получает явный отказ.

```text
package declaration + owner value
  -> validate parameter -> compile contract + consumers
  -> prepare -> reviewed start -> immutable Run snapshot
```

## Приёмка Core

| ID | Проверка |
|---|---|
| C1 | Default 12 000: 12 000 pass, 12 001 refuse. Owner value 32 000: 16 557/32 000 pass, 32 001 refuse. |
| C2 | Недопустимые типы и диапазоны получают диагностику настройки до Run. Счёт символов соответствует JSON Schema, включая Unicode. |
| C3 | Превышение возвращает точный pointer, effective limit и actual length в prepare и start. |
| C4 | Корень, child call и worker input используют согласованную схему; длинное описание проходит все передачи целиком. |
| C5 | Изменение параметра инвалидирует прежнюю launch review; старый digest не запускает новую сборку. |
| C6 | Два проекта с разными пределами работают в одной authority без definition drift и конфликта shared refs. |
| C7 | Update сохраняет owner-файлы. Существующий Run сохраняет определения и task; continue использует исходный контракт либо явно отказывает до эффектов. |
| C8 | Необъявленный параметр, неизвестный target и несовместимые bindings получают явный отказ. Чужая схема не подменяется молча. |

Имеющийся fixture содержит root input, child workflow и worker input одной схемы.
Для новой capability дополнительно проверить положительный project-owned consumer и отказ несовместимого binding.
Не использовать частный task или инфраструктуру проекта владельца.
Синтетическое описание длиной 16 557 воспроизводит нужную границу без публикации приватного содержания.

Поставка Core не закрывает workflows #3.
Consumer отдельно проверит classic/profiled, shared task, обновление и документацию по A1–A10.
