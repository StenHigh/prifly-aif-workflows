# Примеры workflow

| Задача | Пример | Что нужно настроить |
| --- | --- | --- |
| Проверить версии перед выпуском и вывести старую сборку | [Compiled versions](compiled-versions/README.md) | Official Core0.13.90, полный checkout и PyYAML; сравнение compiled ID/version/SHA-256 и отдельный `package remove`. |
| Настроить предел длинного task | [Task description limit](task-description-limit/README.md) | Classic/profiled/fix3.0.0 из exact source, Core0.13.90, owner config; compile/prepare/start/continue. |
| Пройти полный цикл разработки | [Classic и profiled](classic/README.md) | Task, AI Factory skills, project checks; prepare/start/continue и отдельное opt-in review/UI/UX. |
| Проверить качество изменённых тестов | [OpenClaw test audit](test-audit/README.md) | Исходная база, patterns для Python/Node/monorepo; preview/start/continue. AI Factory skills не нужны. |
| Вставить аудит тестов в свой маршрут | [Test audit через extend.yaml](test-audit-extension/README.md) | Собственный package/launch, producer typed request и evaluate; opt-in. |
| Проверить текущую реализацию внутри своего workflow | [Review/UI/UX через native call в extend](review-uiux-extensions/README.md) | Три opt-in режима, project bundle, критерии и собственная браузерная среда; classic upstream сохраняется. |
| Реализовать небольшую фичу | [Small feature](small-feature/README.md) | Task и критерии checks/security/review; frontend environment при необходимости. |
| Взять небольшую фичу из очереди | [Native queue → aif-feature](native-queue/README.md) | Отдельные queue TaskInput и typed feature input; prepare/start/continue, история Runs и явное complete. Есть изолированная CLI-проверка. |
| Проверить объединённый результат | [Verified integration](verified-integration/README.md) | Точные source/target commits, команды приёмки, явно выбранный режим интеграции. |

Каждый пример указывает опубликованный tag или проверенный source commit.
Tag v1.58.0 пока не опубликован; установка из обычного каталога сохраняет v1.57.0. Сначала
адаптируйте данные под проект и просмотрите native prepare summary; затем
запускайте с его digest. Данные шаблонов не заменяют наблюдения исполнителя.

- [Самостоятельные fanout/fix](fanout-fix/README.md): JSON-входы, preview/start и поддерживаемый fix continue.

- [Самостоятельные review/UI/UX](review-ui-ux/README.md): request/configuration, preview/start/continue и отдельный opt-in.

## Unified composition `/5` — v1.57.0

[Public imports и scoped points](unified-composition/README.md) показывают
public UI/UX2.0.0 и собственный consumer на выпущенном Core0.13.90. Общие схемы требуют
явной установки. Пример task-aware Call содержит task, implementation,
applicability и optional configuration. UI/UX2.0.0 опубликован в v1.57.0;
общая зависимость устанавливается отдельно из точного checkout.

## Проектный предел task.description

[Task description limit](task-description-limit/README.md) даёт owner config32000, Unicode task16557,
полные source install/compile/prepare/start и поддерживаемый continue для classic/profiled/fix3.0.0 на Core0.13.90.
Opt-in project consumers подключаются отдельно через schema_task.
