# Проектный предел описания задачи

Пример предназначен для candidate classic/profiled/fix **3.0.0** и released Pri-Fly **0.13.90+**.
Публикация repository tag ещё не выполнена. Устанавливайте точный проверенный candidate commit.
Project profile должен иметь версию `/3`, `/4` или `/5`.
Рабочий проект должен содержать начальный Git commit и реальные AI Factory skills выбранного host.

Готовый [task.json](task.json) содержит 16 557 Unicode-символов в description.
[compile-values.yaml](compile-values.yaml) выбирает предел 32 000.
Без owner file остаётся 12 000; строка длиной 12 001 получает отказ.
Недопустимое значение получает `project_compile_parameter_invalid` до Run.
Диапазон `1..9007199254740991` соответствует безопасным целым числам Core; бюджеты документа и host действуют отдельно.

```text
package compile-parameters.yaml + project/compile-values.yaml
  -> effective schema_task -> prepare -> reviewed start
  -> планирование -> вложенные verify/review -> repair/repeat
  -> stop -> reviewed continue с исходной настройкой
```

## Подготовка и самостоятельный запуск

Замените три абсолютных пути. `WORKFLOW_SOURCE` — Git checkout проверенного candidate, включая contracts и tools.
`PRIFLY_BIN` — официальный released binary; `REPOSITORY` — целевой Git-проект.
Команды ниже предназначены для нового проекта. В существующем проекте пропустите `project init`.
`SOURCE_COMMIT` фиксирует текущий commit checkout; незакоммиченные изменения в установку не попадут.

```bash
PRIFLY_BIN=/absolute/path/to/prifly-v0.13.90
WORKFLOW_SOURCE=/absolute/path/to/aif-workflows-candidate
REPOSITORY=/absolute/path/to/project
FLOW=aif-classic
PLAN_PROFILE=fast
PLAN_ANSWERS=()
if [ "$PLAN_PROFILE" != fast ]; then
  PLAN_ANSWERS=(--preflight-answer 'plan_logging="standard"' --preflight-answer plan_docs=false)
fi
SOURCE_COMMIT=$(git -C "$WORKFLOW_SOURCE" rev-parse HEAD)

"$PRIFLY_BIN" project init --repository "$REPOSITORY" --host codex-cli
"$PRIFLY_BIN" project workflows add "$WORKFLOW_SOURCE" \
  --path "$FLOW" --name "$FLOW" --ref "$SOURCE_COMMIT" --repository "$REPOSITORY"
```

Подставьте state root, который вернула команда `project init`, в `AUTHORITY`.
Настройка authority относится к проекту, а не к папке source.
Подключите общие неизменяемые схемы явно:

```bash
AUTHORITY=/absolute/path/to/project-authority
python3 "$WORKFLOW_SOURCE/tools/install_composition_contracts.py" \
  --binary "$PRIFLY_BIN" --project "$AUTHORITY"
mkdir -p "$REPOSITORY/.prifly/workflows/$FLOW/project"
cp "$WORKFLOW_SOURCE/examples/task-description-limit/compile-values.yaml" \
  "$REPOSITORY/.prifly/workflows/$FLOW/project/compile-values.yaml"
```

Команда `cp` предназначена для первого создания owner file. Существующий файл измените после просмотра его значений.
При необходимости отредактируйте task, сохранив его вне целевого Git-дерева.
Просмотрите и закоммитьте конфигурацию проекта перед запуском в worktree.
Замените команду `gate_checks` реальной командой проверок проекта в обоих вызовах.

```bash
"$PRIFLY_BIN" --project "$AUTHORITY" project questionnaire \
  --repository "$REPOSITORY" --launch "$FLOW" --host codex-cli --prepare \
  --workspace worktree --package-profile "$PLAN_PROFILE" "${PLAN_ANSWERS[@]}" \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/task.json" \
  --decision-policy attended --preflight-answer plan_tests=true \
  --preflight-answer 'gate_warnings="ignore"' \
  --preflight-answer 'gate_checks="python3 -m unittest discover -s tests"' \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'roadmap_linkage="skip"'
```

Просмотрите сводку. `REVIEW_DIGEST` — точное поле `review_digest` этой сводки.

```bash
REVIEW_DIGEST=sha256:REPLACE_WITH_REVIEWED_DIGEST
"$PRIFLY_BIN" --project "$AUTHORITY" project start \
  --repository "$REPOSITORY" --launch "$FLOW" --host codex-cli \
  --workspace worktree --package-profile "$PLAN_PROFILE" "${PLAN_ANSWERS[@]}" \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/task.json" \
  --decision-policy attended --preflight-answer plan_tests=true \
  --preflight-answer 'gate_warnings="ignore"' \
  --preflight-answer 'gate_checks="python3 -m unittest discover -s tests"' \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'roadmap_linkage="skip"' \
  --expected-launch-digest "$REVIEW_DIGEST"
```

Для profiled выберите `FLOW=aif-profiled` до установки и используйте те же команды.
Команды используют Bash. Для `full` или `ultra` выберите `PLAN_PROFILE` до подготовки.
В этих профилях `PLAN_ANSWERS` явно выбирает standard logging и docs warning.
При необходимости замените эти ответы решениями проекта.
Профили меняют layout плана, сохраняя независимую настройку длины.

## Самостоятельный fix

Для fix установите `FLOW=aif-fix` и повторите подготовку owner file.
Fix использует собственные package profiles и ответы:

```bash
"$PRIFLY_BIN" --project "$AUTHORITY" project questionnaire \
  --repository "$REPOSITORY" --launch aif-fix --host codex-cli --prepare \
  --workspace worktree --package-profile default \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/fix-task.json" \
  --preflight-answer 'short_checks=""' --preflight-answer 'gate_warnings="ignore"' \
  --runtime-answer fix_plan_execution=true
REVIEW_DIGEST=sha256:REPLACE_WITH_REVIEWED_FIX_DIGEST
"$PRIFLY_BIN" --project "$AUTHORITY" project start \
  --repository "$REPOSITORY" --launch aif-fix --host codex-cli \
  --workspace worktree --package-profile default \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/fix-task.json" \
  --preflight-answer 'short_checks=""' --preflight-answer 'gate_warnings="ignore"' \
  --runtime-answer fix_plan_execution=true --expected-launch-digest "$REVIEW_DIGEST"
```

Для настоящего bug task замените готовый synthetic task содержанием ошибки и задайте настоящие `short_checks`.
Ответ `fix_plan_execution=true` явно разрешает исполнение созданного fix-plan.

## Поддерживаемый continue

Для поддерживаемого `partial/rejected` Run сохраните пакет, profile и owner value исходного запуска.
`SOURCE_RUN` — реальный ID исходного Run. Не передавайте новый task при продолжении.

```bash
SOURCE_RUN=run:REPLACE_WITH_SOURCE_RUN_ID
"$PRIFLY_BIN" --project "$AUTHORITY" project continue \
  --repository "$REPOSITORY" --launch "$FLOW" --source-run "$SOURCE_RUN" \
  --host codex-cli --prepare
CONTINUE_DIGEST=sha256:REPLACE_WITH_REVIEWED_CONTINUE_DIGEST
"$PRIFLY_BIN" --project "$AUTHORITY" project continue \
  --repository "$REPOSITORY" --launch "$FLOW" --source-run "$SOURCE_RUN" \
  --host codex-cli --expected-launch-digest "$CONTINUE_DIGEST"
```

Изменение owner value требует нового review. Несовместимая сборка может отказать до создания Run.
Для продолжения прежнего контракта верните исходный owner value и выполните новый prepare.
Старый Run сохраняет исходный task и definitions. После отмены writer сначала разрешите его эффекты штатным способом.

## Opt-in project consumer

Самостоятельный запуск выше не добавляет project worker.
Проектный step, который получает task через объявленную extension point, должен использовать:

```yaml
inputs:
  task: {schema_ref: "{{schema_task}}"}
```

Старая внешняя ссылка `aif:schema/task@1.1.0` имеет другую идентичность даже при совпадении предела 12 000.
Не заменяйте ссылки на Core артефакты вручную.
Project-owned W6 bundle версии 3.0.0 использует новый alias; старые установленные copies требуют явного обновления.
[Полный opt-in W6 example](../review-uiux-extensions/README.md) описывает подготовку, execution consent и собственные inputs.
Frozen public imports с task1.1.0 сохраняют свой контракт; эта настройка не меняет их автоматически.

## Проверка примера

Готовые YAML и оба JSON проверены на official Pri-Fly0.13.90 через prepare/start для classic/profiled/fix.
Экспорт сохранённого task совпал с исходным JSON-значением целиком.
Эта проверка останавливается после read-only warmup; живые skills и прикладная логика не выполняются.
Полная synthetic native matrix отдельно проверяет repair, review, continue и update.

```bash
python3 -B tests/probes/task_limit_examples.py \
  --binary /absolute/path/to/released/prifly-v0.13.90 \
  --output /tmp/aif-task-limit-examples.json
```
