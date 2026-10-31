# Приёмка issue #7

Статус: локальная приёмка и все три jobs полного CI PASS.
Владелец согласовал completed/rejected без обязательного gate 2026-10-31.

## Проверяемый контракт

Матрица: classic/profiled × fail/no_work при первой проверке, после fix и внутри fix.
Всего 12 cases; первые четыре также повторяют rejected через continue.
Ожидается 28 Runs, включая продолжения до security.

Каждый исходный stop: completed/rejected, пустые root outputs, без последующих gates/commit.
Каждый continue: frontier verify/execute, принятый префикс и план сохранены.
Tree/HEAD, staged index, untracked owner work и claim должны сохраниться.
Prepare должен оставлять источник, claims и Run inventory прежними.
Cleanup должен освободить claims и удалить регистрацию временной authority.

## Локальные результаты

- [Native matrix](native-results.json): 12 cases / 28 Runs PASS, classic/profiled без других установленных пакетов.
- Оба verdicts до fix, после fix и внутри fix: completed/rejected, пустые root outputs.
- Все continue начинают verify; plan/tree/HEAD/index/untracked owner work и claim сохранены.
- Prepare не меняет источник, дерево, claims и список Runs; повторный rejected также проверен.
- [Negative baseline](negative-baseline.json): v1.54.0 даёт failed/unhandled_child_outcome; новая проверка выявляет дефект.
- [Основные ворота](local-gates.json): versions4/folders7/derive, unit113, verify126/83/8 и compatibility5/4/4/core-state41 PASS.
- [Local install/update](install-update-results.json): обе версии, три hosts, ready example preview/start, cancel/continue и сохранённые owner files PASS.
- W6 project bundle --check PASS; остальные шесть shipping packages имеют прежние bytes.
- [Неизменённые маршруты](unchanged-routes.json): 6 pairs PASS против v1.53.0, включая blocked и успешный fix.

Binary SHA-256: `3b073126921bca3e9d78b7649b51bd20527fd70cf4de44e0d440b5428b7712e5`.
Все проверки используют official released Pri-Fly0.13.82.

## CI

[PR #11](https://github.com/StenHigh/prifly-aif-workflows/pull/11),
source `a9f94fe37df371e13a6a7a3872b56e02399e5e3f`.
[CI41219942108](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/41219942108):
verify, parallel-ui-ux и call-review-uiux завершились SUCCESS.
Artifacts classic-readability-results и classic-verify-outcomes подтверждают6 равных pairs
и12 cases/28 Runs на official0.13.82 с тем же binary SHA-256.
Оба downloaded JSON точно совпали с локальными reports; cleanup PASS.
[Итоговая приёмка](ci-results.json) закрепляет source, jobs и SHA-256 artifacts.
После qualified source добавлены только документы приёмки; shipping, tests и CI workflow bytes прежние.

## Команды

`BINARY` — абсолютный путь к official released Pri-Fly. Локальная dev-сборка не подходит.

```sh
python3 -B tests/probes/verify_outcomes.py --binary "$BINARY" --jobs 3 --report /tmp/verify-outcomes.json
python3 -B tests/test_versions.py
python3 -B tests/test_folders.py
python3 -B tools/derive_profiled.py --check
python3 -B tests/verify.py --binary "$BINARY"
python3 -B tests/compatibility.py --binary "$BINARY"
python3 -B tests/probes/readability_compare.py --binary "$BINARY" \
  --baseline /absolute/path/to/v1.53.0 --candidate "$PWD" \
  --cases owner-only exhausted disabled clean repaired blocked \
  --output /tmp/readability-unchanged.json
```

Для negative baseline используйте verify_outcomes.py с `--source` старого выпуска,
`--package aif-classic --case fail`: новый контракт обязан отказать на прежнем failed.

Готовый example task и reviewed questionnaire/start используются внутри native матрицы.
Opt-in W6 остаётся отдельным recipe; этот change не добавляет import/repair маршруты.

## Границы

Новый контракт continue проверяется для Runs исправленного пакета.
Миграция старых failed Runs не заявляется. Live model acceptance не заявляется.
PR#11 MERGED. Annotated tag/GitHub Release v1.56.0 опубликованы на source1985ae1.
Каталог79f01ce закрепляет classic/profiled на этот tag/commit; остальные шесть pins v1.55.0 прежние.
[Published install/update](published-results.json): default catalog add и GitHub v1.55→v1.56
обоих пакетов, exact bytes tag, три hosts, owner files и local edit refusal PASS.
На публичных bytes выполнены6 Runs: rejected/repeated rejected/continue до security;
same claim, plan/tree/index/untracked work сохранены, cleanup PASS.
