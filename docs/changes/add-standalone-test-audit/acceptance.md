# Локальная приёмка 2026-10-16

Подготовлен самостоятельный `openclaw-test-audit@1.0.0`. В существующие workflow
ничего не вставлено; все семь прежних package trees совпадают с HEAD.
Новых tag/catalog entries/push нет. Сверка latest stable в начале задачи:
Pri-Fly `v0.13.77`, новых stable относительно CONTEXT_STATE нет.

[qualification.json](qualification.json) сохраняет результат, binary SHA-256,
хэши authoring/executable sources и границы доказательства.

Итоговое имя по источнику skill — `openclaw-test-audit`, компоненты `openclaw:`.
После переименования повторены unit/static/version, compile и native matrix.
Исходная приёмка под прежним именем сохранена отдельно в
[qualification-before-rename.json](qualification-before-rename.json).

Пройдены:

- Folder contract: 7 tests; version contract: 3 tests; derive-profiled check.
- Новые Git/acceptance unit tests: 10 tests. Base/committed/dirty/index/untracked,
  nested paths, rename/delete, staged reversal, explicit skip, wrong/missing/
  duplicate report coverage, stale production/index/mode/deletion, session
  policy, invalid base/patterns и unmerged index.
- `tests/verify.py` на official 0.13.77: 8 packages, 126 definitions, 83 source
  steps. Новый пакет и extension example компилируются на codex-cli, codex-app,
  claude-code; binding к output, не гарантированному на pass, отказал
  `unavailable_output`. Snapshot helpers совпадают с выпущенным W1 по AST.
- `tests/compatibility.py`: 5 launches, 4 distinct builds, 4 trusted packages,
  прежний `core-state/41`. Это прежняя граница assisted handoff, без AI-host.
- Native matrix: 18 сценариев с ожидаемыми succeeded/partial, включая skip
  без reader, defect, unavailable, missing coverage, wrong request digest,
  production edit, needs_revision/blocked reader verdicts, missing session,
  partial/cancel continuation и fresh selection после нового untracked теста.
  Extension example: pass/defect/skip; обычный pass также на двух прочих хостах.
  Каждый fixture проверил неизменность исходного repository и очистил свои
  Runs/claims/registry. Тестовые изменения выполнялись только в его Run tree.
- `git diff --check`; отсутствие изменений всех семи прежних пакетов.

В ходе проверки уточнён native workspace contract: `project start` сам доводит
program-only prefix до handoff/finish; новый dirty checkout отказывает
`checkout_dirty`. Поэтому standalone инструкция не обещает аудит чужого
незакоммиченного дерева. Untracked/replay scenario создаёт новый тест в своём
уже начатом Run, старый report становится stale, continue выбирает оба пути.

Reader в native matrix синтетический. Реальные CLI/программы/Git/артефакты/
маршрутизация проверены; качество суждений LLM, другая модель и динамический
pre-fix/post-fix test proof не квалифицированы. CI дополнен двумя gates, его
нового прогона нет. В каталоге пакет ещё не опубликован.

## Выпуск

Пакет опубликован как `openclaw-test-audit@1.0.0` в v1.53.0, source c853060,
центральный catalog9a384ef. Раздел выше сохраняет исходную локальную qualification.
Предрелизные gates и реальные default-catalog install/update/native smoke
сохранены в [release ledger](../../releases/v1.53.0-results.json) и
[published results](../../releases/v1.53.0-published-results.json).
