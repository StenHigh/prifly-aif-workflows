# Test audit через extend.yaml

Это отдельный opt-in пример. Он использует компоненты `openclaw-test-audit`, но
связывает их своим корневым графом и вставляет assisted-шаг через overlay.
В существующие пакеты репозитория ничего не вставляется.
Пакет1.1.0 из v1.55.0 сохраняет эти bindings; extension native cases повторены на official0.13.82.

Для обычного отдельного запуска есть
[готовые config и команды preview/start/continue](../test-audit/README.md).
Ниже — сборка собственного маршрута. Нужны Pri-Fly ≥0.13.77 и Python 3;
AI Factory skills не нужны.

Из корня инициализированного тестового проекта выберите новую, ещё не существующую
папку `my-test-audit`. Подставьте путь к checkout репозитория с примерами:

```sh
cp -R /absolute/path/to/aif-workflows/openclaw-test-audit .prifly/workflows/my-test-audit
cp /absolute/path/to/aif-workflows/examples/test-audit-extension/workflow.yaml .prifly/workflows/my-test-audit/workflow.yaml
cp /absolute/path/to/aif-workflows/examples/test-audit-extension/extend.yaml .prifly/workflows/my-test-audit/extend.yaml
```

Добавьте элементы в существующие mappings `.prifly/project.yaml`, сохранив
остальные packages и launches:

```yaml
packages:
  my-test-audit:
    source: .prifly/workflows/my-test-audit
launches:
  my-test-audit:
    title: Project test audit
    description: Test audit inserted through the project overlay.
    kind: workflow
    workflow: .prifly/workflows/my-test-audit/workflow.yaml
```

Создайте config с исходной базой задачи через
[prepare_config.py](../test-audit/prepare_config.py), разрешите Python программы
и проверьте компиляцию:

```sh
prifly project local set --repository . --allow-executable python=/absolute/path/to/python3
prifly project compile --repository . --package my-test-audit --host codex-cli \
  --output /tmp/my-test-audit-compiled
prifly project questionnaire --repository . --launch my-test-audit --host codex-cli \
  --workspace worktree --input config=/tmp/openclaw-audit-config.json \
  --allow-execution --prepare
```

После проверки summary:

```sh
prifly project start --repository . --launch my-test-audit --host codex-cli \
  --workspace worktree --input config=/tmp/openclaw-audit-config.json \
  --allow-execution --expected-launch-digest REVIEW_DIGEST
```

Сохраните установку и изменения задачи в commits до отдельного worktree запуска.
Этот проектный пример поддерживает сам проект; обновление установленного
`openclaw-test-audit` не синхронизирует скопированные компоненты автоматически.

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
clean/defect/empty-selection сценарии с синтетическим reviewer. Пример завершает
Run при partial и не объявляет resumable; команды continue из standalone
примера относятся к исходному launch `openclaw-test-audit`. Для собственного
repair/continue маршрута проект должен явно объявить и проверить его граф.
