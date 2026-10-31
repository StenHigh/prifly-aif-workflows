# Самостоятельный classic и profiled

Пример использует `aif-classic@1.49.0` или `aif-profiled@1.50.0` с исправлением issue #7.
Tag `v1.56.0` опубликован; команды ниже используют выпущенные пакеты.
Требуется Pri-Fly0.13.82 для воспроизведения опубликованных проверок.
Минимальная поддерживаемая версия пакетов остаётся0.13.64.
AI Factory2.19.0 skills должны быть установлены для выбранного host.
В примере host — `codex-cli`, package profile — `fast`, workspace — `worktree`.

```text
task.json → prepare → reviewed start → warmup → plan → improve → implement
                                                           → verify → security → review → commit
                                                                 └─ partial/rejected → reviewed continue
```

## Подготовка

`/absolute/path/to/aif-workflows` замените путём к этому repository.
Запустите команды из корня целевого Git-проекта с начальным commit.
Сохраните task вне его дерева:

```sh
cp /absolute/path/to/aif-workflows/examples/classic/task.json /tmp/classic-task.json
prifly project init --repository . --host codex-cli
prifly project workflows add StenHigh/prifly-aif-workflows   --path aif-classic --ref v1.56.0 --repository .
```

В уже инициализированном проекте пропустите `project init`.
Адаптируйте task под проект. Пример `gate_checks` ниже предназначен для Python unittest.
Замените эту команду реальной командой проверок вашего проекта в обоих вызовах.
Настройки `extend.yaml` остаются проектными; пример их не перезаписывает.

## Preview и start

Сначала получите сводку запуска без создания Run:

```sh
prifly project questionnaire --repository . --launch aif-classic --prepare   --host codex-cli --input task=/tmp/classic-task.json   --workspace worktree --package-profile fast --decision-policy attended   --preflight-answer plan_tests=true   --preflight-answer gate_warnings='"ignore"'   --preflight-answer gate_checks='"python3 -m unittest discover -s tests"'   --preflight-answer plan_constraints='""'   --preflight-answer roadmap_linkage='"skip"'
```

Просмотрите сводку. Вместо `REVIEW_DIGEST` подставьте её точное поле `review_digest`:

```sh
prifly project start --repository . --launch aif-classic   --host codex-cli --input task=/tmp/classic-task.json   --workspace worktree --package-profile fast --decision-policy attended   --preflight-answer plan_tests=true   --preflight-answer gate_warnings='"ignore"'   --preflight-answer gate_checks='"python3 -m unittest discover -s tests"'   --preflight-answer plan_constraints='""'   --preflight-answer roadmap_linkage='"skip"'   --expected-launch-digest REVIEW_DIGEST
```

Runner выбранного host исполняет assisted tasks. Сам start не заменяет runner.
Политика `attended` сохраняет вопросы о scope и принятии улучшений плана.
Для `aif-profiled` установите `--path aif-profiled` и используйте launch `aif-profiled` в этих командах.
Его `extend.yaml.model_profiles` задаёт проектные переводы профилей моделей.

## Поддерживаемый continue

Для Run с принятым начальным prefix, завершившегося `partial`/`rejected`, либо отменённого read-only verify:

```sh
prifly project continue --repository . --launch aif-classic   --source-run SOURCE_RUN --host codex-cli --prepare
prifly project continue --repository . --launch aif-classic   --source-run SOURCE_RUN --host codex-cli --expected-launch-digest CONTINUE_DIGEST
```

`SOURCE_RUN` — исходный Run; `CONTINUE_DIGEST` — digest просмотренной сводки continue.
Не передавайте новые task, workspace, профиль и ответы; они берутся из исходного Run.
Отмена до принятия warmup даёт `resume_prefix_empty`; сохраните дерево перед подготовкой нового start.
После отмены writer сначала нужны осмотр эффектов и owner resolution.
Существующий capture path плана нельзя удалять автоматически ради продолжения.

Verify `fail/no_work` завершает новый Run как `completed/rejected` без gate.
То же правило действует при остановке fix внутри verify.
Continue повторяет verify целиком, сохраняя warmup/plan/improve/implement и рабочее дерево.
Счёт раундов начинается заново. Предыдущий gate остаётся в истории.
Security, review и commit ждут успешного verify либо его явного выключения в настройках проекта.

## Opt-in review/UI/UX

Самостоятельный запуск выше не добавляет сторонние readers в classic.
Для проектного подключения используйте отдельный [W6 recipe](../review-uiux-extensions/README.md).
Он описывает явные project-owned files, inputs и native call extensions.
Установка самостоятельного пакета сама по себе не создаёт import или repair route.

## Обновление

```sh
prifly project workflows update aif-classic --ref v1.56.0 --repository .
prifly project workflows update aif-profiled --ref v1.56.0 --repository .
```

Выполняйте команду только для установленного пакета. Update сохраняет `extend.yaml` и `project/`.
Незавершённые Runs лучше завершить до обновления: новые author versions меняют recovery prefix.
Сначала просмотрите `continue --prepare`; отказ `recover_prefix_changed` требует явного reviewed replay.
Новый переход у verify меняет форму стадии. Continue от старого Run может вернуть `recover_frontier_changed`.
Старые failed Runs с `unhandled_child_outcome` уже возвращают `recover_frontier_unsupported` на Pri-Fly0.13.82.
Обновление пакета не переписывает их историю и не обещает миграцию.
Не удаляйте их рабочие деревья и не запускайте implement повторно автоматически.
Сохранение работы старого Run требует отдельного осмотра владельца.
