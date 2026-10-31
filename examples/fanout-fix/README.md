# Самостоятельные fanout и fix

Требуется Pri-Fly0.13.82 и AI Factory2.19.0 skills выбранного host.
Команды используют codex-cli и Git-проект с начальным commit.
`SOURCE` — абсолютный путь к checkout этого репозитория.
`WORKFLOW_REF` — проверяемая ветка `codex/issue-6-remaining-readability`; после выпуска используйте `v1.55.0`.
Выпуск v1.55.0 пока не опубликован. Входы сохраняются вне рабочего дерева.

```text
fanout: plan → coverage + risk → join → выбор → применение → новый plan
fix: task → warmup → fix-task → [fix-plan → решение → fix-from-plan]
                              → checks → security → review → commit
                                           ↑         ↓
                                           └─ repair ┘
```

## Подготовка

```sh
SOURCE=/absolute/path/to/aif-workflows
WORKFLOW_REF=codex/issue-6-remaining-readability
cp "$SOURCE/examples/fanout-fix/plan.json" /tmp/fanout-plan.json
cp "$SOURCE/examples/fanout-fix/task.json" /tmp/fix-task.json
prifly project init --repository . --host codex-cli
prifly project workflows add StenHigh/prifly-aif-workflows --path aif-fanout --ref "$WORKFLOW_REF" --repository .
prifly project workflows add StenHigh/prifly-aif-workflows --path aif-fix --ref "$WORKFLOW_REF" --repository .
```

Для существующего проекта пропустите init. Установите только нужный пакет.
Адаптируйте task/plan под проект. Сохраните файлы пакетов в Git перед start.

## Fanout: preview и start

```sh
prifly project questionnaire --repository . --launch aif-fanout --host codex-cli --input plan=/tmp/fanout-plan.json --workspace worktree --prepare
prifly project start --repository . --launch aif-fanout --host codex-cli --input plan=/tmp/fanout-plan.json --workspace worktree --expected-launch-digest REVIEW_DIGEST
```

`REVIEW_DIGEST` — точное поле review_digest просмотренной сводки.
Runner исполняет tasks. Два ракурса не обещают разные модели.
Fanout не объявляет resumable. Команда continue для него не поддерживается.
Graph возвращает JSON plan; он не импортирует native PLAN из classic.

## Fix: preview и start

```sh
prifly project questionnaire --repository . --launch aif-fix --host codex-cli --input task=/tmp/fix-task.json --workspace worktree --package-profile default --preflight-answer short_checks='"python3 -m unittest discover -s tests"' --preflight-answer gate_warnings='"ignore"' --prepare
prifly project start --repository . --launch aif-fix --host codex-cli --input task=/tmp/fix-task.json --workspace worktree --package-profile default --preflight-answer short_checks='"python3 -m unittest discover -s tests"' --preflight-answer gate_warnings='"ignore"' --expected-launch-digest REVIEW_DIGEST
```

Замените short_checks командой проекта в обоих вызовах.
Если появится fix_plan_execution, владелец отдельно решает, исполнять ли план.
Профиль custom использует tracked `.ai-factory/fix-plans/FIX_PLAN.md`.
Профиль default использует native untracked `.ai-factory/FIX_PLAN.md`.

## Fix: поддерживаемый continue

После partial/rejected или settled cancellation с принятым prefix:

```sh
prifly project continue --repository . --launch aif-fix --source-run SOURCE_RUN --host codex-cli --prepare
prifly project continue --repository . --launch aif-fix --source-run SOURCE_RUN --host codex-cli --expected-launch-digest CONTINUE_DIGEST
```

`SOURCE_RUN` — исходный Run. `CONTINUE_DIGEST` — digest просмотренной сводки.
Не переопределяйте workspace, input или решения исходного Run.
После отмены writer осмотрите эффекты и выполните требуемое owner resolution.
Resume root quality повторяет checks/security/review. Root build повторяет fix route.
Существующий custom FIX_PLAN требует отдельного review при конфликте пути.

## Opt-in и обновление

Установка fanout не добавляет его в classic/fix. Проектное подключение требует собственного reviewed графа.
Generic fix extensions могут использовать root build→quality или commit→done; bound inputs отсутствуют.
Для review/UI/UX используйте отдельный [W6 recipe](../review-uiux-extensions/README.md).

```sh
prifly project workflows update aif-fanout --ref "$WORKFLOW_REF" --repository .
prifly project workflows update aif-fix --ref "$WORKFLOW_REF" --repository .
```

Update сохраняет extend.yaml и project/. Завершите старые Runs перед сменой author versions.
Отказ recover_prefix_changed требует reviewed replay; автоматический перенос prefix не обещается.
