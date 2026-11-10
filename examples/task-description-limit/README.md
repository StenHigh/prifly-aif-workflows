# Проектный предел описания задачи

Пример предназначен для classic/profiled/fix **3.0.0** из main и released Pri-Fly **0.13.90+**.
[PR #16](https://github.com/StenHigh/prifly-aif-workflows/pull/16) смёржен; tag v1.58.0 ещё не опубликован.
Проверенный source: `72eb8861263d15079d767c6c6106e8c240f738d0`. Обычный каталог пока устанавливает прежний v1.57.0.
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

Замените три абсолютных пути. `WORKFLOW_SOURCE` — новая папка для checkout проверенного source, включая contracts и tools.
`PRIFLY_BIN` — официальный released binary; `REPOSITORY` — целевой Git-проект.
Команды ниже предназначены для нового проекта. В существующем проекте пропустите `project init`.
`SOURCE_COMMIT` фиксирует проверенную реализацию. Существующий checkout просмотрите перед использованием.

```bash
PRIFLY_BIN=/absolute/path/to/prifly-v0.13.90
WORKFLOW_SOURCE=/absolute/path/to/aif-workflows-source
REPOSITORY=/absolute/path/to/project
FLOW=aif-classic
PLAN_PROFILE=fast
PLAN_ANSWERS=()
if [ "$PLAN_PROFILE" != fast ]; then
  PLAN_ANSWERS=(--preflight-answer 'plan_logging="standard"' --preflight-answer plan_docs=false)
fi
NAMING_ARGS=()
# Если профиль проекта объявляет naming input worktree, задайте:
# NAMING_ARGS=(--naming-input worktree=/absolute/path/to/project-valid-naming.json)
SOURCE_COMMIT=72eb8861263d15079d767c6c6106e8c240f738d0
git clone --no-checkout https://github.com/StenHigh/prifly-aif-workflows.git "$WORKFLOW_SOURCE"
git -C "$WORKFLOW_SOURCE" checkout --detach "$SOURCE_COMMIT"

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
Настройка предела принадлежит каждому workflow отдельно. Установка profiled не копирует настройку из classic.
При необходимости отредактируйте task, сохранив его вне целевого Git-дерева.
Просмотрите конфигурацию и сохраните выбранный workflow в Git:

```bash
git -C "$REPOSITORY" diff -- .prifly .codex/skills/prifly-run
git -C "$REPOSITORY" add -- .prifly .codex/skills/prifly-run
git -C "$REPOSITORY" commit -m "Configure task description limit"
```

При наличии других изменений сначала отделите их при просмотре и фиксации.
Новый worktree использует committed snapshot. AI Factory skills выбранного host также должны быть доступны в нём.
Если проект объявляет naming input, создайте JSON по его собственной схеме и задайте `NAMING_ARGS` до prepare.
Подставьте новую пустую папку `SCRATCH` и выполните отдельную компиляцию.
Она использует профиль по умолчанию из `extend.yaml`. Prepare ниже собирает профиль, выбранный через `PLAN_PROFILE`.

```bash
SCRATCH=/absolute/path/to/fresh-scratch
mkdir -p "$SCRATCH"
"$PRIFLY_BIN" project compile --repository "$REPOSITORY" --package "$FLOW" \
  --host codex-cli --output "$SCRATCH/compiled"
```

Замените команду `gate_checks` реальной командой проверок проекта в обоих вызовах.

```bash
"$PRIFLY_BIN" --project "$AUTHORITY" project questionnaire \
  --repository "$REPOSITORY" --launch "$FLOW" --host codex-cli --prepare \
  --workspace worktree --package-profile "$PLAN_PROFILE" "${PLAN_ANSWERS[@]}" "${NAMING_ARGS[@]}" \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/task.json" \
  --decision-policy attended --preflight-answer plan_tests=true \
  --preflight-answer 'gate_warnings="ignore"' \
  --preflight-answer 'gate_checks="python3 -m unittest discover -s tests"' \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'roadmap_linkage="skip"' \
  --json > "$SCRATCH/prepare.json"
cat "$SCRATCH/prepare.json"
```

Просмотрите сводку. `REVIEW_DIGEST` — точное поле `review_digest` этой сводки.

```bash
REVIEW_DIGEST=sha256:REPLACE_WITH_REVIEWED_DIGEST
"$PRIFLY_BIN" --project "$AUTHORITY" project start \
  --repository "$REPOSITORY" --launch "$FLOW" --host codex-cli \
  --workspace worktree --package-profile "$PLAN_PROFILE" "${PLAN_ANSWERS[@]}" "${NAMING_ARGS[@]}" \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/task.json" \
  --decision-policy attended --preflight-answer plan_tests=true \
  --preflight-answer 'gate_warnings="ignore"' \
  --preflight-answer 'gate_checks="python3 -m unittest discover -s tests"' \
  --preflight-answer 'plan_constraints=""' --preflight-answer 'roadmap_linkage="skip"' \
  --expected-launch-digest "$REVIEW_DIGEST" --json > "$SCRATCH/start.json"
cat "$SCRATCH/start.json"
```

Для profiled выберите `FLOW=aif-profiled` до установки и используйте те же команды.
Команды используют Bash. Для `full` или `ultra` выберите `PLAN_PROFILE` до подготовки.
В этих профилях `PLAN_ANSWERS` явно выбирает standard logging и docs warning.
При необходимости замените эти ответы решениями проекта.
Профили меняют layout плана, сохраняя независимую настройку длины.

## Обновление существующего проекта

Для установленного classic выполните update вместо повторного add:

```bash
"$PRIFLY_BIN" project workflows update "$FLOW" --repository "$REPOSITORY" --ref "$SOURCE_COMMIT"
```

`FLOW` должен совпадать с реальным именем установленного workflow и его origin.
Update сохраняет `extend.yaml` и `project/`; проверьте их до следующего compile.
Переведите project-owned task consumers с `{{contract_schema_task}}` на `{{schema_task}}`.
Сохраните прежний source и проектные файлы для старых Run.
При подключённом frozen public UI/UX сначала выберите совместимую композицию по [руководству миграции](../../docs/changes/configure-task-description-limit/release-guide.md).

## Самостоятельный fix

Для fix установите `FLOW=aif-fix` и повторите установку, подготовку owner file, фиксацию и compile.
Fix использует собственные package profiles и ответы:

```bash
"$PRIFLY_BIN" --project "$AUTHORITY" project questionnaire \
  --repository "$REPOSITORY" --launch aif-fix --host codex-cli --prepare \
  --workspace worktree --package-profile default "${NAMING_ARGS[@]}" \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/fix-task.json" \
  --preflight-answer 'short_checks=""' --preflight-answer 'gate_warnings="ignore"' \
  --runtime-answer fix_plan_execution=true --json > "$SCRATCH/prepare-fix.json"
cat "$SCRATCH/prepare-fix.json"
REVIEW_DIGEST=sha256:REPLACE_WITH_REVIEWED_FIX_DIGEST
"$PRIFLY_BIN" --project "$AUTHORITY" project start \
  --repository "$REPOSITORY" --launch aif-fix --host codex-cli \
  --workspace worktree --package-profile default "${NAMING_ARGS[@]}" \
  --input task="$WORKFLOW_SOURCE/examples/task-description-limit/fix-task.json" \
  --preflight-answer 'short_checks=""' --preflight-answer 'gate_warnings="ignore"' \
  --runtime-answer fix_plan_execution=true --expected-launch-digest "$REVIEW_DIGEST" \
  --json > "$SCRATCH/start-fix.json"
cat "$SCRATCH/start-fix.json"
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
  --host codex-cli --prepare --json > "$SCRATCH/continue.json"
cat "$SCRATCH/continue.json"
CONTINUE_DIGEST=sha256:REPLACE_WITH_REVIEWED_CONTINUE_DIGEST
"$PRIFLY_BIN" --project "$AUTHORITY" project continue \
  --repository "$REPOSITORY" --launch "$FLOW" --source-run "$SOURCE_RUN" \
  --host codex-cli --expected-launch-digest "$CONTINUE_DIGEST" --json
```

Изменение owner value требует нового review. Несовместимая сборка может отказать до создания Run.
Для продолжения прежнего контракта нужны исходные package source, owner value и project consumers.
Возврат одного числа не мигрирует Run из 2.0.0 в 3.0.0. Naming snapshot продолжения берётся из исходного Run.
Старый Run сохраняет исходный task и definitions. После отмены writer сначала разрешите его эффекты штатным способом.

## Opt-in project consumer

Самостоятельный запуск выше не добавляет project worker.
Проектный step, который получает task через объявленную extension point, должен использовать:

```yaml
inputs:
  task: {schema_ref: "{{schema_task}}"}
```

Старая внешняя ссылка `aif:schema/task@1.1.0` имеет другую идентичность даже при совпадении предела 12 000.
Прямой public Call `aif-ui-ux.review-for-change` версии 2.0.0 требует именно frozen task1.1.0.
Он несовместим с owned task пакета 3.0.0. Для classic/profiled 3.0.0 используйте project-copy W6, если нужна такая приёмка.
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

[Приёмка A1–A10 и полный CI](../../docs/changes/configure-task-description-limit/acceptance.md) фиксируют проверенные границы.
