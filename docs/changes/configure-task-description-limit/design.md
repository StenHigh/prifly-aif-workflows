# Проектный параметр task.description

## Принятое решение

Реализация использует released Pri-Fly0.13.90 и capability `project_compile_parameters`.
Core #22 закрыт; исходная граница0.13.89 сохраняется в [historical native evidence](native.md).
Пакет объявляет параметр в `compile-parameters.yaml` с marker `prifly-compile-parameters/1`.
Проект задаёт значение в `project/compile-values.yaml` с marker `prifly-compile-values/1`.
Оба файла относятся к выбранному source owner — пакету, который определяет схему.

Параметр `task_description_limit` имеет type integer, minimum1 и default12 000.
Maximum9 007 199 254 740 991 соответствует безопасному целочисленному представлению Core.
Пакет не вводит новый произвольный потолок описания поверх этой числовой границы.
Бюджеты документа, runtime и host действуют отдельно.
Binding называет только owned alias `schema_task` и pointer `/properties/description/maxLength`.

```text
package compile-parameters.yaml + owner project/compile-values.yaml
  -> проверка integer / range / binding
  -> maxLength в owned task1.2.0
  -> все достижимые workflow и step inputs
  -> prepare -> reviewed start -> immutable Run
```

Compiler проверяет параметр до проверки task.
Compile, prepare и start читают один owner file через общий resolver Core.
Смена значения меняет build key и требует нового launch review.
Недопустимое значение возвращает `project_compile_parameter_invalid` до Run.
Превышение длины возвращает `schema_invalid` по `/description`, выбранный предел и фактическую длину.
Длина измеряется Unicode code points, включая кириллицу и emoji.

## Ownership и версии

Прежний task1.1.0 был внешней frozen схемой composition-contracts.
Core разрешает параметризовать только схему выбранного source owner.
Поэтому classic/profiled/fix получают owned task1.2.0 с placeholder вместо literal maxLength.
Все их потребители используют `{{schema_task}}`.
Внешний `contract_schema_task` удалён из package.references этих трёх пакетов.

Это изменение exact type для внешних потребителей; версии трёх пакетов повышены до3.0.0.
Profiled получен штатной генерацией classic.
Изменённые steps и вложенные workflows получают новые версии по действующим правилам.
`compile-parameters.yaml` и task source одинаковы во всех трёх пакетах.
Остальные пять shipping packages сохраняют прежние bytes.

Генератор composition contracts исключает schemas с объявленными compile bindings из inert exports.
Текущий bindings lock отражает оставшиеся внешние aliases.
Native contracts1.2.0, frozen1.0.0, их manifests и schema bytes не меняются.
Старые public imports по task1.1.0 сохраняют прежний контракт.

## Проектные потребители

Project-owned worker использует `{{schema_task}}` из устанавливаемого source owner.
Он получает тот же exact compiled ref, что root, plan и вложенные verify/review workflow.
Opt-in task reader из native-примера проверяет полный task перед каждым verify/review, включая повтор после repair.
Несовместимый frozen consumer получает отказ compilation.
Compiler не подменяет его ref и не отрезает description.

W6 project-copy bundle3.0.0 переводит task-aware copies на `schema_task`.
Минимальный собственный W6 consumer уже определяет owned task и также компилируется.
Старые установленные copies требуют явного reviewed обновления; installer не обновляет их скрыто.
Standalone public UI/UX exports с frozen task не получают проектный предел автоматически.

## Update и продолжение

Owner file расположен в `project/`, который workflow update сохраняет.
Native-приёмка проверяет переход с v1.57.0 на candidate и последующее обновление изменённого source.
Она сравнивает owner config, extend.yaml и произвольный project sentinel по bytes.
Обновлённый пакет компилируется с прежними32 000 и принимает длинный task.

Существующий Run хранит прежние definitions, lock и task.
Два проекта с разными пределами используют одну authority без смешивания compiled refs.
Изменение source или owner file не меняет сохранённое состояние предыдущего Run.

Для reviewed continue поддерживайте исходную сборку, package profile и owner value.
Сужение32 000 →12 000 отклоняет carried task16 557 через `schema_invalid` до нового Run и effects.
Возврат32 000 позволяет продолжить с принятого prefix и завершить quality/repair маршрут.
Новый task или новый review digest не мигрируют старый Run.
После отмены writer действуют прежние требования разрешить его эффекты.

```text
Run(32000) -> stop(partial)
  owner12000 -> continue prepare: schema_invalid, новый Run не создан
  owner32000 -> новый reviewed continue -> verify/repair -> review/repair -> succeeded
```

## Документация и выпуск

Готовые owner config и task16 557 находятся в `examples/task-description-limit/`.
README трёх пакетов, W6, реестр examples и [release guide](release-guide.md) описывают один синтаксис.
[Draft catalog](catalog.draft.yaml) содержит будущие descriptions и явный placeholder commit.
Публичные pins v1.57.0 не переводятся на неопубликованный tag.
Планируемый repository release — v1.58.0; tag и Release не публикуются в этой реализации.

[Пакетная приёмка](acceptance.md) сопоставляет результаты с A1–A10.
Синтетические actors проверяют wiring и сохранение bytes; живые модели и приватная инфраструктура не квалифицируются.
