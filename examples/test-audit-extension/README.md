# Test audit через extend.yaml

Это отдельный opt-in пример. Он использует компоненты `openclaw-test-audit`, но
связывает их своим корневым графом и вставляет assisted-шаг через overlay.
В существующие пакеты репозитория ничего не вставляется.

В локальной копии пакета для эксперимента:

1. Скопируйте папку `openclaw-test-audit` в отдельную проектную папку.
2. Замените её `workflow.yaml` и `extend.yaml` файлами из этого примера.
3. Поместите получившуюся папку в `.prifly/workflows/my-test-audit` своего
   тестового проекта и объявите package/launch `my-test-audit` по образцу
   README пакета. Не изменяйте установленный upstream-пакет ради примера.
4. Используйте config и команды запуска из [README пакета](../../openclaw-test-audit/README.md),
   указав свой launch `my-test-audit`.

Исходное ребро prepare → evaluate заменяется prepare → audit → evaluate.
Prepare выдаёт bundle config/candidate/paths. Вставленный шаг получает его
единственным `input_bindings`, а evaluate проверяет весь отчёт и свежесть дерева.
При пустой выборке prepare возвращает `no_work` и обходит assisted-шаг.

`on` направляет usable `pass`, `needs_revision` и `blocked` в evaluate, потому
что диагностический отчёт нужен при любом исходе. Ошибки без отчёта дают
`rejected`. Evaluate даёт `partial` при дефекте, недоступности или stale evidence.
Пример без overlay намеренно некомплектен: его evaluate читает отчёт вставки.
Это проверяемая пара graph + extend, а не готовый graph без настройки.

Вставки разрешают только шаги текущего пакета по коротким именам; installation
другого пакета не добавляет такой import. В существующем своём workflow
разместите нужные step/schema/context/program components в проектной области
и объявите producer exact request schema. Проверьте доступность output на
каждом входящем пути и свои лимиты. Для repair-цикла нужен явный graph; эта
forward-вставка сама не создаёт повторный аудит после исправлений.

`tests/verify.py` компилирует эту пару на трёх хостах; native probe исполняет
clean/defect/empty-selection сценарии с синтетическим reviewer.
