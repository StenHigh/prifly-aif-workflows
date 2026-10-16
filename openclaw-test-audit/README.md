# Аудит изменённых тестов

Самостоятельный пакет `openclaw:package/test-audit@1.0.0`, launch
**openclaw-test-audit**, для released Pri-Fly **0.13.77** и Python 3 stdlib.
Опубликован в составе [v1.53.0](../docs/releases/v1.53.0.md).

Префикс `openclaw-` отражает источник checklist. Это наша адаптация для Pri-Fly;
AI Factory skills в пакете не используются.

Он проверяет качество тестов текущей задачи: защищаемое поведение, реальную
регрессию, дублирование, зависимость от реализации и корректность моков.
Критерии адаптированы из OpenClaw `test-audit`; [источник и границы](PROVENANCE.md)
закреплены в пакете. Установленный OpenClaw или AI Factory skill не требуется.

```text
configure → quality { select changed test paths
                       → no changes: explicit skip, no AI session
                       → audit → coverage/freshness evaluation }
          → report + gate
```

Другие workflow не подключают этот пакет автоматически. Разработчики выбирают
самостоятельный запуск или включают его компоненты в свой проектный маршрут.
Пакет читает код и выдаёт отчёт. Исправления, удаление тестов, commit и публикация
не входят в него.

## Самостоятельный запуск

Из корня инициализированного проекта:

```sh
prifly project workflows add openclaw-test-audit --repository .
# Или напрямую из release tag:
prifly project workflows add StenHigh/prifly-aif-workflows \
  --path openclaw-test-audit --ref v1.53.0 --repository .
```

Каталог закрепляет tag и точный source commit. Установка объявляет package и
launch, но не запускает код и не устанавливает host skills. Обновление через
`prifly project workflows update openclaw-test-audit --repository .` сохраняет
`extend.yaml` и проектный overlay; локальные правки upstream-файлов требуют
разбора перед update.

Разрешите declared Python programs:

```sh
prifly project local set --repository . \
  --allow-executable python=/absolute/path/to/python3
```

Создайте `config.json` **вне проверяемого дерева**, подставив исходный полный
SHA-1 commit задачи. Он остаётся базой и после промежуточных коммитов/continue:

```json
{
  "base_commit": "0000000000000000000000000000000000000000",
  "round": 1,
  "test_patterns": ["tests/*", "test/*", "*.test.*", "*.spec.*"],
  "require_separate_session": false
}
```

`test_patterns` задаёт проект: универсального способа узнать тестовый файл во
всех языках нет. Используется Python `fnmatchcase` с учётом регистра, пути от
корня через `/`; `*` включает `/`, поэтому `tests/*` охватывает также вложенные
файлы. Для вложенных каталогов вроде `packages/pkg/tests/` добавьте
`*/tests/*`; для pytest вне `tests/` — `test_*.py` и `*/test_*.py`.
Неполные patterns могут пропустить тесты — это явная граница настройки.

Выборка объединяет изменения относительно базы в текущем дереве и index,
а также nonignored untracked файлы. Учитывает новые тесты в существующих файлах,
удаления и переименования. Staged-правка видна и при обратной unstaged-правке.
Проверяется содержимое выбранных файлов и контекст каждого изменённого теста,
а не только названия файлов. Чистые production-правки без тестовых путей дают
skip; последующий production edit делает уже полученный аудит устаревшим.

```sh
prifly project questionnaire --repository . --launch openclaw-test-audit \
  --host codex-cli --workspace checkout --input config=/absolute/path/config.json \
  --allow-execution --prepare
# Проверьте summary и подставьте его review_digest:
prifly project start --repository . --launch openclaw-test-audit \
  --host codex-cli --workspace checkout --input config=/absolute/path/config.json \
  --allow-execution --expected-launch-digest DIGEST
```

На released 0.13.77 старт с `checkout` требует чистого репозитория
(`checkout_dirty` иначе). Самостоятельный запуск проверяет сохранённые в commit
изменения относительно исходной базы. Новый `worktree` также начинается с tracked
состояния своего commit. Staged/dirty/untracked изменения, возникшие уже в дереве
Run до аудита, учитываются программой. Для проверки незакоммиченной реализации
живого Run используйте композицию внутри него; отдельный запуск не должен
обходить чужой claim. Codex App и Claude Code также компилируются;
наличие отдельной сессии и выбор модели зависят от хоста.

## Результат и повторный запуск

`report` содержит candidate, digest доставленного запроса, round и по одной
записи на каждый выбранный путь: behavior, regression, existing_proof, evidence,
findings и status. Внутри записи reviewer должен разобрать все изменённые тесты.
Программа проверяет полноту списка **путей**, но не доказывает истинность prose
или семантическую полноту разбора каждого assertion. При skip request digest
вычисляется для canonical config/candidate/empty-paths bundle: assisted-запрос
не доставлялся. Отсутствие динамического
baseline proof сообщается явно: статический аудит не заявляет выполненный тест.

`gate.status`:

| Status | Outcome | Значение |
| --- | --- | --- |
| `skipped` | `succeeded` | Нет изменений по объявленным patterns; `session: not_run`, причина в отчёте. |
| `passed` | `succeeded` | Полный актуальный отчёт без найденных дефектов. |
| `failed` | `partial` | Есть конкретные дефекты тестов; исправление остаётся вызывающему маршруту. |
| `blocked` | `partial` | Недоступны обязательные данные/сессия либо отчёт неполный, чужой или устарел. |

`blocking` означает остановку приёмки для `failed` и `blocked`; различать
исправимый дефект и недостаток данных нужно по status. Ошибка подготовки
(невалидная база, unmerged index, submodule, лимит) даёт `rejected`, без
сфабрикованного успешного отчёта. Максимум 200 изменённых тестовых путей и 10000
путей candidate; большие задачи надо разделять.

Candidate измеряется до аудита и перед приёмкой: HEAD, logical index, байты и
режимы tracked/nonignored untracked файлов. Symlinks не разыменовываются;
ignored caches/dependencies не входят в basis. Это cooperative Git freshness,
а не атомарная блокировка внешнего редактора. Отчёт перестаёт быть актуальным
после последующей записи; вызывающий workflow отвечает за guard до commit.

После исправления или восстановления доступности данных:

```sh
prifly project continue --repository . --launch openclaw-test-audit \
  --source-run RUN --host codex-cli --allow-execution --prepare
# Используйте новый review_digest для запуска той же команды.
```

Весь quality повторяется: новая выборка, новая сессия, новая оценка. Исходная
база, config/round и дерево наследуются. Изменение уже принятого configure
контракта может отказать `recover_prefix_changed`; это не способ незаметно
поменять критерии аудита в существующем Run. Сам workflow repair-цикла не имеет.

## Подключение разработчиками

`extend.yaml` вставляет **шаг** в корневое ребро своего пакета. Он не импортирует
другой установленный workflow по имени и не добавляет собственный repeat.
Шаг `openclaw:step/audit` имеет один typed input `request`, поэтому подходит для
такой вставки, когда проект уже подготовил bundle exact schema.

Полный [opt-in пример](../examples/test-audit-extension/README.md) показывает
prepare → вставленный audit → evaluate. Он компилируется и исполняется как
отдельный проектный маршрут; никакой classic workflow ради примера не меняется.
Для существующего проекта нужны зарегистрированные в его пакете компоненты,
producer запроса и обработка результатов. Сам факт установки двух пакетов не
связывает их. Не используйте «последний Run» или память host вместо artifact.
Если аудит должен повторяться после repair, включите его в явный quality graph.

## Проверки

```sh
python3 -B tests/test_test_audit.py
python3 -B tests/verify.py --binary /path/to/released/prifly
python3 -B tests/probes/test_audit_check.py --binary /path/to/released/prifly \
  --report /tmp/openclaw-test-audit-results.json
```

Unit tests используют настоящий Git. Native probe исполняет реальные
программы/CLI с синтетическим reviewer: это проверка маршрутизации, артефактов,
skip и freshness, без заявления о качестве LLM-аудита или другой модели.
