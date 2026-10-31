# Примеры workflow

| Задача | Пример | Что нужно настроить |
| --- | --- | --- |
| Пройти полный цикл разработки | [Classic и profiled](classic/README.md) | Task, AI Factory skills, project checks; prepare/start/continue и отдельное opt-in review/UI/UX. |
| Проверить качество изменённых тестов | [OpenClaw test audit](test-audit/README.md) | Исходная база, patterns для Python/Node/monorepo; preview/start/continue. AI Factory skills не нужны. |
| Вставить аудит тестов в свой маршрут | [Test audit через extend.yaml](test-audit-extension/README.md) | Собственный package/launch, producer typed request и evaluate; opt-in. |
| Проверить текущую реализацию внутри своего workflow | [Review/UI/UX через native call в extend](review-uiux-extensions/README.md) | Три opt-in режима, project bundle, критерии и собственная браузерная среда; classic upstream сохраняется. |
| Реализовать небольшую фичу | [Small feature](small-feature/README.md) | Task и критерии checks/security/review; frontend environment при необходимости. |
| Взять небольшую фичу из очереди | [Native queue → aif-feature](native-queue/README.md) | Отдельные queue TaskInput и typed feature input; prepare/start/continue, история Runs и явное complete. Есть изолированная CLI-проверка. |
| Проверить объединённый результат | [Verified integration](verified-integration/README.md) | Точные source/target commits, команды приёмки, явно выбранный режим интеграции. |

Примеры привязаны к указанным в них выпущенным версиям пакетов. Сначала
адаптируйте данные под проект и просмотрите native prepare summary; затем
запускайте с его digest. Данные шаблонов не заменяют наблюдения исполнителя.
