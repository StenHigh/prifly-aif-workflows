# W1 — локальная приёмка

Публикация: [v1.52.0](../../releases/v1.52.0.md), 2026-10-16; exact source/catalog и published smoke —
[release evidence](../../releases/v1.52.0-results.json). Ниже сохранена
историческая приёмка initial checkpoint с её исходной версией и ограничениями.

Дата: 2026-10-14. Статус: **implemented locally / accepted within limits / unreleased**.
Реализация: [aif-review-evidence](../../../aif-review-evidence/README.md), initial 1.0.0.
Classic/profiled/fix/fanout не изменены; изменение движка не требовалось.

## Реализованный контракт

- Отдельные request, candidate, report и gate schemas; four steps / two graphs.
- Configure закрепляет validated request; quality содержит capture → assisted
  read-only review → deterministic program evaluation. Программы на Python stdlib
  доставляются declared execution bindings с pinned supporting file.
- Состав checks определяется input request. Report содержит его artifact digest:
  прежние code/IDs не позволяют принять старый отчёт после изменения criteria.
- Candidate учитывает base/HEAD, logical index, tracked и nonignored untracked
  bytes/modes, missing paths и symlink targets. Два snapshot reads должны совпасть.
- Оценщик вычисляет текущий candidate самостоятельно. Structured diagnostic,
  defect и warning не смешиваются с verdict пригодности session report.
- Continue повторяет целиком quality; host declarations о fresh session и model
  choice различены, неизвестное не объявляется независимым pass.

## Released binary и проверки

Платформа проверки: Linux/amd64, Pri-Fly **0.13.76** из GitHub Release.
Archive SHA-256: `b44d98b37093d99415a82c4020bb8dd2452f0ec98dbf2078a0cd1d1f0e2fb720`.
Binary SHA-256: `03ac382112a12001ea9e2a86e5a20db2d5e24ec79ce5339f6257c473d0f3322d`.
Archive сверён с опубликованным release manifest; local dev binary не использован.

| Проверка | Результат и граница |
|---|---|
| `tests/test_review_evidence.py` | 14 PASS: coverage/policy, valid-but-different candidate, changed criteria, real Git bytes/index/modes/deletions/symlinks |
| Negative canary | Удаление candidate comparison и request-digest comparison в временных mutants вызывает FAIL соответствующего теста; исходный worker не менялся |
| `test_versions.py`, `test_folders.py`, `derive_profiled.py --check` | 3 + 7 PASS, derivation unchanged |
| `verify.py --binary RELEASED` | PASS; five packages, 65 compiled steps/workflows and 38 source steps; W1 compiled on three hosts, bad binding/handler/workspace fixtures refused |
| `compatibility.py --binary RELEASED` | PASS; existing authority/profile compatibility, boundary до handoff |
| Four `run_check.py` modes | PASS: classic pass, blocked, blocked→continue, cancelled→continue |
| `fix_check.py` | 28 PASS, current unchanged bug package |
| `evidence_check.py` | [25 completed synthetic-host cases](runtime-results.json), real program evaluator/Git/released CLI; three host bindings |
| Current Codex-app host | [Live observations](live-observations.json): actual arithmetic command; optional browser unavailable → succeeded/warnings; required unavailable → partial, despite usable session pass |

CI workflow запускает новые unit и runtime проверки. Это локальная приёмка:
новый remote CI run, release tag и central catalog publication не выполнялись.

## Критерии

| ID | Подтверждение |
|---|---|
| A1 | Missing/duplicate/unknown IDs блокируют; policy-bound excluded/not_applicable имеют reason и not_run. Changed criteria with same IDs/code invalidates old report. |
| A2 | Browser check с code evidence, пустое evidence/observation и passing command с nonzero exit не принимаются. Реальный browser pass не заявляется. |
| A3 | Required unavailable: synthetic и actual host дают partial с diagnostic, без repair/commit. Executed failed check даёт failed/blocking. |
| A4 | Optional-ignore/optional-stop проверены; unrun evidence не переименовывается в executed. Live optional browser остаётся явным warning. |
| A5 | Dirty/index/untracked/delete/mode/HEAD и symlink target cases; evaluator проверяет valid candidate digest и current tree, не только JSON-схему. External symlink contents и ignored caches вне basis. |
| A6 | Owner edit между reader/evaluate останавливает acceptance; blocked/cancelled/chained resume снимают новый snapshot, сохраняя base, claim и work. Repair caller должен вызывать quality заново; собственного repair здесь нет. |
| A7 | Shared/unavailable session не удовлетворяет require_separate_session. Separate declaration с unavailable model не устанавливает другую модель. Live shared/unavailable указан явно. |
| A8 | Released complete runtime matrix + actual current host executed/unavailable observations; остальная host/model qualification не подменена synthetic PASS. |
| A9 | Stopped quality contract update сохраняет configure и reruns quality. Configure retry-contract change даёт named prefix refusal без изменения source Run version/outputs и owner work; explicit first-stage replay даёт отдельный named refusal. |

## Измеренные ограничения

- На 0.13.76 после изменения effective configure contract: `recover_prefix_changed`.
  `--from-stage configure` затем даёт `resume_prefix_empty`: раньше первого
  root-stage ничего не принято. Автоматический cross-contract first-stage replay
  и перенос candidate в новый start не реализованы; работа сохраняется.
- Snapshot не является atomic filesystem snapshot/hard sandbox. Symlinks не
  читаются за пределами дерева; ignored dependencies и внешняя среда оцениваются
  отдельно. Submodules/unmerged index, unsupported kinds и >10000 paths отказаны.
- Content observations, separate session и model choice — declarations host.
  Оценщик не доказывает правдивость structurally valid fabricated prose или
  факт browser execution. Live используется текущая общая Codex-сессия;
  независимый reader/model, live Claude/Codex CLI и реальный browser не проверены.
- Данные состояния assessment имеют смысл для measured candidate на момент
  оценки. Последующая правка требует новой quality-проверки у W2/W3 consumer.
- Skills root и SEVERITY pinned при compile. Live источник — AI Factory 2.19.0;
  synthetic suite использует skills stubs, а не сравнение качества LLM.
- Сравнительная экономия времени/токенов не измерена. Новый catalog/tag не выпущен.

Собственные fixture Runs, claimed worktrees, authority stands и monitor entries
очищены. JSON evidence содержит только созданные для теста данные/наблюдения,
не данные потребляющего проекта.
