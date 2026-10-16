# Примеры workflow

| Задача | Пример | Что нужно настроить |
| --- | --- | --- |
| Проверить качество изменённых тестов | [OpenClaw test audit](test-audit/README.md) | Исходная база, patterns для Python/Node/monorepo; preview/start/continue. AI Factory skills не нужны. |
| Вставить аудит тестов в свой маршрут | [Test audit через extend.yaml](test-audit-extension/README.md) | Собственный package/launch, producer typed request и evaluate; opt-in. |
| Реализовать небольшую фичу | [Small feature](small-feature/README.md) | Task и критерии checks/security/review; frontend environment при необходимости. |
| Проверить объединённый результат | [Verified integration](verified-integration/README.md) | Точные source/target commits, команды приёмки, явно выбранный режим интеграции. |

Примеры привязаны к указанным в них выпущенным версиям пакетов. Сначала
адаптируйте данные под проект и просмотрите native prepare summary; затем
запускайте с его digest. Данные шаблонов не заменяют наблюдения исполнителя.
