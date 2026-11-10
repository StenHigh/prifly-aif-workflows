# Обновление candidate classic/profiled/fix 3.0.0

Статус: реализация в main; repository tag и новый каталог не опубликованы.
Проверенный source: `72eb8861263d15079d767c6c6106e8c240f738d0`; PR #16 MERGED, полный CI6/6 SUCCESS.
Для проверки нужен released **Pri-Fly 0.13.90+**, Project profile `/3`–`/5` и точный проверенный source checkout.
Core #22 закрыт; пакетная приёмка проверяется отдельно.

## Новое поведение

Пакет объявляет `task_description_limit` в `compile-parameters.yaml`.
Проект выбирает значение в `.prifly/workflows/NAME/project/compile-values.yaml`:

```yaml
authoring: prifly-compile-values/1
values:
  task_description_limit: 32000
```

Без owner file используется 12 000 Unicode-символов.
Диапазон `1..9007199254740991` следует безопасному целочисленному представлению Core.
Бюджеты входного документа, runtime и модели действуют отдельно.
Число не разрешает произвольную замену схем или подмену ArtifactRef.

```text
новый Core -> новый package -> owner config -> prepare -> reviewed start
                   |              |
                   |              +-> update сохраняет owner bytes
                   +-> существующий Run сохраняет старые definitions/task
```

## Миграция

1. Установите официальный Pri-Fly 0.13.90+ и проверьте его версию.
2. Сохраните исходный пакет и конфигурацию активных или остановленных Run.
3. Обновите выбранный workflow до точного candidate commit.
4. Создайте owner file с нужным пределом.
5. Переведите task consumers проекта на `{{schema_task}}`.
6. Выполните compile, prepare и reviewed start из [готового примера](../../../examples/task-description-limit/README.md).

Для обновления уже установленного workflow используйте его реальный origin и новый commit:

```sh
PRIFLY_BIN=/absolute/path/to/prifly-v0.13.90
REPOSITORY=/absolute/path/to/project
SOURCE_COMMIT=72eb8861263d15079d767c6c6106e8c240f738d0
"$PRIFLY_BIN" project workflows update aif-classic \
  --repository "$REPOSITORY" --ref "$SOURCE_COMMIT"
```

Подставьте настоящий commit из origin этого workflow. Для profiled/fix замените имя workflow.
Source checkout с contracts/tools должен соответствовать проверенному candidate.
Явная установка общих схем остаётся обязательной; native manifest composition-contracts1.2.0 и frozen1.0.0 не меняются.
Update сохраняет `extend.yaml` и `project/`; он не переводит старые project worker definitions на новый alias.
Не редактируйте upstream-owned `schemas/task.yaml` ради настройки проекта.

## Совместимость task

Classic/profiled/fix используют owned source `aif:schema/task@1.2.0` с параметром.
Compiler создаёт exact ref для выбранной сборки.
Внешний frozen task1.1.0 сохраняется для прежних public consumers и не получает эту настройку.
Поэтому версии трёх пакетов повышены до 3.0.0.

Project-owned consumers используют `{{schema_task}}` из своего source owner.
Положительный пример входит в native-приёмку; несовместимый frozen consumer получает отказ compilation.
W6 project-copy bundle3.0.0 использует этот alias. Старые copies требуют явного обновления по инструкции W6.
UI/UX, feature и остальные независимые shipping packages сохраняют свои bytes и контракты.

## Continue

Для поддерживаемого остановленного Run сохраните исходный package source, profile и owner value.
Сначала выполните `project continue --prepare` с его реальным `--source-run`.
Несовместимая сборка получает отказ до нового Run и эффектов.
Верните исходный owner value и получите новую сводку продолжения.
Новый start с другим пределом не изменяет старый Run и не мигрирует его.
После отмены writer требуется штатное разрешение его эффектов.

## Каталог и выпуск

Текущие опубликованные catalog pins остаются на v1.57.0.
[catalog.draft.yaml](catalog.draft.yaml) описывает три candidate пакета для будущего v1.58.0.
`REPLACE_WITH_RELEASE_SOURCE_COMMIT` — обязательный placeholder; такой каталог нельзя публиковать без подстановки проверенного commit.
Перед тегом повторно проверьте latest stable, полный CI точного source и public install/update.
Публикация тега, merge и центральный каталог требуют отдельного этапа.
