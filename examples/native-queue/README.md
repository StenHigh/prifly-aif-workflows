# Небольшая фича из native queue

Пример проверяет связь **Task → Run → отчёты → продолжение → решение о завершении
Task** для `aif-feature@1.2.3` и выпущенного readability-пакета1.3.0. Очередь принадлежит Pri-Fly: отдельной базы задач,
планировщика или нового workflow здесь нет. Минимум native queue —0.13.77;
актуальная проверенная база — официальный stable **0.13.82**.
CI41207313038 повторно проверил три native queue cases на source42e60de.

## Полностью изолированная проверка

Из checkout этого репозитория, на Linux с Python3, Git и официальным Pri-Fly:

```sh
python3 -B tests/probes/feature_queue_check.py \
  --binary /absolute/path/to/released/prifly \
  --report /tmp/aif-feature-queue-results.json
```

`--binary` — абсолютный путь к скачанному release asset, не dev-сборка.
`--report` — файл результата; существующий файл будет заменён. Можно выбрать
один сценарий через `--case backend`, `--case blocked-resume` или
`--case cancel-resume`.

Скрипт сам создаёт временные repository, authority, HOME и конфигурацию,
копирует локальный пакет и fixture skills, выполняет реальный unit-тест и
локальный Git commit. Native prepare/start/continue и export работают через
публичный CLI. Отдельный временный full monitor проверяется через HTTP.
Runs/claims, собственные monitor processes и временное дерево очищаются;
JSON сохраняет команды, ответы, срезы очереди и исходные typed отчёты.
При ошибке итог FAIL, ненаблюдённые сценарии не считаются пройденными.

Assisted actors детерминированы: это проверка интеграции пакета с очередью,
а не живая квалификация AI Factory skills, моделей или независимых LLM-сессий.
UI/UX и браузерная приёмка в backend-примере не включены. Проверка HTTP полного
monitor не означает приёмку его интерфейса или Pri-Fly Light.

## Явное использование в своём проекте

Это opt-in: установка `aif-feature` не включает очередь автоматически. Сначала
подготовьте отдельный проект, skills и `backend` extend по
[small-feature](../small-feature/README.md). Дальнейшие команды выполняет
владелец/проектный runner для этого проекта. Они не заменяют исполнение
выданных assisted Attempts хостом.

Здесь **два разных входа**:

- [queue.task.json](queue.task.json) — исходный `task-input/1`, сохраняемый
  очередью без переформулировки;
- [backend.task.json](../small-feature/backend.task.json) — отдельный typed input
  workflow: scope и критерии checks/security/review. Его нужно согласовать с
  исходной задачей. Автоматического преобразования между форматами нет.

Замените абсолютные пути ниже. `queue_files` — каталог вне tracked candidate,
`queue_repo` — подготовленный проект; источник примеров — checkout этого repo.
Адаптируйте оба JSON под задачу и обновите source metadata перед `add`.

```sh
queue_prifly=/absolute/path/to/released/prifly
queue_repo=/absolute/path/to/prepared-project
queue_authority=/absolute/path/to/project-authority
queue_source=/absolute/path/to/aif-workflows
queue_files=/absolute/path/to/queue-inputs
mkdir "$queue_files"
cp "$queue_source/examples/native-queue/queue.task.json" "$queue_files/queue.task.json"
cp "$queue_source/examples/small-feature/backend.task.json" "$queue_files/feature.task.json"

"$queue_prifly" --json project queue add --repository "$queue_repo" \
  --input "$queue_files/queue.task.json" --priority 10 --command-id command:greeting-add
"$queue_prifly" --json project queue claim-next --repository "$queue_repo" \
  --owner session:greeting-owner --command-id command:greeting-claim > "$queue_files/claim.json"
```

`claim-next` берёт следующую доступную задачу по native порядку. В проекте с
другими задачами сначала прочитайте `claim.json` и убедитесь, что это нужная
задача; не подставляйте greeting input к произвольной полученной задаче.
Получение задачи ещё не создаёт Run или workspace claim.

Следующие команды для Bash получают **записанные** идентификаторы:

```sh
queue_task_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["result"]["id"])' "$queue_files/claim.json")
queue_revision=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["result"]["revision"])' "$queue_files/claim.json")
queue_generation=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["result"]["claim"]["generation"])' "$queue_files/claim.json")
queue_selection=(--task-id "$queue_task_id" --task-owner session:greeting-owner \
  --task-revision "$queue_revision" --task-claim-generation "$queue_generation")
queue_launch=(--repository "$queue_repo" --launch aif-feature --host codex-cli \
  --workspace worktree --input "task=$queue_files/feature.task.json" \
  --decision-policy autonomous --preflight-answer plan_tests=true \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'plan_retention="capture"' \
  --allow-execution "${queue_selection[@]}")

"$queue_prifly" --json project questionnaire "${queue_launch[@]}" --prepare > "$queue_files/prepare.json"
```

Просмотрите весь summary: выбранный launch, inputs, исполняемые программы,
`queue_task` и `review_digest`. Без полного typed input получите `missing_input`,
даже если задача успешно получена из очереди. После принятия review:

```sh
queue_digest=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["review_digest"])' "$queue_files/prepare.json")
"$queue_prifly" --json project start "${queue_launch[@]}" \
  --expected-launch-digest "$queue_digest" --command-id command:greeting-start > "$queue_files/start.json"
queue_run=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_id"])' "$queue_files/start.json")
"$queue_prifly" --json project queue show --repository "$queue_repo" --task-id "$queue_task_id"
```

Далее проектный runner обслуживает именно `queue_run` по сгенерированной
инструкции выбранного хоста. Результаты читаются в `run status` и full monitor;
`output_artifacts.gate` и `output_artifacts.evidence` содержат точные refs.
Сохраните ref в JSON и используйте `artifact export --ref /absolute/ref.json
--output /absolute/report.json` против authority этого проекта. Смотрите
`gate.status` и отдельные reports: технический verdict `pass` сам по себе не
означает успешной приёмки.

## Продолжение остановленного Run

Поддержанный этим примером маршрут — `partial` из-за недоступной обязательной
проверки или отмена на read-only quality step. Сначала владелец устраняет
названную причину; неизвестные внешние эффекты требуют своей reconciliation.
Принудительная отмена writer этим примером не квалифицируется.

Если revision/ownership не менялись, используйте ту же `queue_selection`.
Если менялись — перечитайте native queue и её контракт, не подбирайте значения.
Без queue selection продолжение связанного source откажет
`queue_source_identity_conflict`.

```sh
queue_continue=(--repository "$queue_repo" --launch aif-feature --host codex-cli \
  --source-run "$queue_run" --allow-execution "${queue_selection[@]}")
"$queue_prifly" --json project continue "${queue_continue[@]}" --prepare > "$queue_files/continue-prepare.json"
```

Просмотрите recovery boundary и новый summary, затем:

```sh
queue_continue_digest=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["review_digest"])' "$queue_files/continue-prepare.json")
"$queue_prifly" --json project continue "${queue_continue[@]}" \
  --expected-launch-digest "$queue_continue_digest" --command-id command:greeting-continue > "$queue_files/continue.json"
queue_next_run=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_id"])' "$queue_files/continue.json")
"$queue_prifly" --json project queue show --repository "$queue_repo" --task-id "$queue_task_id"
```

Runner обслуживает новый `queue_next_run`. Continuation создаёт новый Run,
сохраняя прежний в истории той же Task и исходную рабочую копию. В проверенных
сценариях quality повторяется полностью; plan/implement повторно не выполняются.
После изменения candidate прежние результаты не заменяют новую приёмку.

Для чтения результатов укажите authority, записанную при `project init`,
а не authority другого проекта. После обслуживания нужного Run:

```sh
queue_result_run=${queue_next_run:-$queue_run}
"$queue_prifly" --json --project "$queue_authority" run status "$queue_result_run" > "$queue_files/result-state.json"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); json.dump(d["run"]["output_artifacts"]["evidence"],open(sys.argv[2],"w"))' \
  "$queue_files/result-state.json" "$queue_files/evidence.ref.json"
"$queue_prifly" --json --project "$queue_authority" artifact export \
  --ref "$queue_files/evidence.ref.json" --output "$queue_files/evidence.json"
```

Если Run ещё не дошёл до aggregate, output `evidence` может отсутствовать;
прочитайте status и текущий Attempt, не создавайте фиктивный ref/отчёт.

## Завершение задачи

Успешный Run не переводит Task в `done` автоматически. После просмотра свежих
отчётов и локального commit владелец отдельно принимает локальное завершение:

```sh
"$queue_prifly" --json project queue complete --repository "$queue_repo" \
  "${queue_selection[@]}" --command-id command:greeting-complete \
  --reason 'Проверены свежие отчёты и локальный commit; публикация не выполнялась'
```

Повтор **той же операции с теми же аргументами** использует прежний command-id.
Новая операция требует нового ID. Не заменяйте новый start повторным claim-next.
`done` — решение локальной очереди; merge, deploy и закрытие внешней задачи
из него не следуют. Это пример работы с native queue, не поставка Light UI.
