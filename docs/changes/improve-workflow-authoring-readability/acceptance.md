# Приёмка читаемости workflow: issue #6

Дата: 2026-10-31. Первая порция: classic и штатный derived profiled.
Статус: локальная первая порция PASS; exact-commit CI и release/catalog ещё впереди.

## Входы и эквивалентность до bump

Исходный HEAD `7260962d02285607d50a01389e5b6fd85dbfb1e2` совпал с GitHub main после fetch/pull --ff-only.
После v1.53.0 classic/profiled не менялись; patch не откатывает последующие изменения.
Pinned handoff принадлежит Pri-Fly `d010dd3ed4a4e6fb2af05a3ba7455fe256ab408d`.
Patch SHA-256 сверён: `d91952033fd67f59098d9eb0ae6b9bcba05f1afa148cc9ccadc91a229df48cf2`.
Семь файлов совпали с pinned handoff manifest после `git apply --check` и apply.

Четыре YAML-объекта совпали до version bump.
Decoded UTF-8 bytes bridge совпали, включая завершающий LF:9938 bytes,
SHA-256 `8772b0ef8121540cceb00cd912ba005ef434ed7fe467fde6e88913262a1fd24c`.
[Результат проверки](pre-bump-equivalence.json).

Двенадцать пар сборок совпали по полной identity и SHA-256 всех sealed components.
Матрица: codex-cli/codex-app × canonical/local extend × fast/full/ultra.
Host skills и local extend взяты из локального Core checkout только для чтения.
Probes не исполняют команды из local extend и не вызывают модели.
[Результаты пар сборок](pre-bump-builds.json).

[Парные маршруты](pre-bump-routes.json): owner-only, exhausted, disabled, clean, repaired, fail, no_work, blocked.
Все восемь пар до bump совпали.
В repaired новая implementation дошла до повторного verify, security и следующего review reader.
`fail/no_work` сохранили прежний `unhandled_child_outcome`; отдельный [issue #7](https://github.com/StenHigh/prifly-aif-workflows/issues/7) требует решения владельца.

## Runtime и ворота

Official released Pri-Fly0.13.82, Linux AMD64, source d010dd3.
Archive SHA-256 `8c6da4649246540b5923ebf0dbfcece662cc3fbfe48d0171a1f4c5247ef7c3c3` совпал с release manifest.
Binary SHA-256 `3b073126921bca3e9d78b7649b51bd20527fd70cf4de44e0d440b5428b7712e5`.
Runtime82 исправляет concurrent package install и Git worktree registry lock; authoring/API прежние.
Baseline verify126/83/8 и compatibility5/4/4/core-state41 PASS; cleanup по1 monitor entry.
[Verify](baseline-verify.json), [compatibility](baseline-compatibility.json).

После bump version4/folder7/derive, verify126/83/8 и compatibility5/4/4/core-state41 PASS.
[Финальный verify](final-verify.json), [финальная compatibility](final-compatibility.json).
Continue с verify после blocked и отмены PASS: [blocked](blocked-continue.json), [cancelled](cancelled-continue.json).
[Финальные восемь пар маршрутов](final-routes.json) после bump совпали; каждый fixture очистил claims и свою monitor entry.

[Install/update smoke](install-update-results.json): baseline→candidate, classic1.48.0 и profiled1.49.0,
сборки на трёх hosts, examples prepare/start и cancellation→continue с verify PASS.
Шесть Runs, synthetic warmup/plan/implement и resumed verify handoff; модели не вызываются.
Update сохранил extend.yaml byte-for-byte и project/owner.txt.
Локальная правка Markdown дала project_workflow_modified.
Cleanup: active claims0, registry entry1 удалена, temporary directory удалена.
Отмена до принятия warmup честно даёт resume_prefix_empty; этот путь не заявляется как continue.
[Version guard](source-version-negative.json) отказал при изменении Markdown LF→CRLF без bump context и принял новый context version.
Новый compile gate проверяет standalone profiled при отсутствии установленного classic.
[Отрицательная проба](profiled-source-negative.json) отказала при намеренной ссылке profiled на отсутствующий classic; output не создан.
CI переиспользует adopted native route probe; новый DSL, formatter и generator не добавляются.

## Документация и границы

[Release guide](../../releases/v1.54.0.md), [готовый task и команды](../../../examples/classic/README.md),
[inventory восьми пакетов](inventory.md). Старые evidence сохраняют прежние результаты.
Новая версия автора намеренно меняет compiled identity; прежние build keys нужны только до bump.
Синтетические replies проверяют wiring и effects, а не живые host/model integrations.
Владелец принял форму по review; скорость чтения не измерялась.
