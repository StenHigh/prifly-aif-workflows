# Native queue → aif-feature: результаты приёмки

2026-10-19, official stable Pri-Fly **v0.13.80**, Linux AMD64. Новых stable
после выверенной базы80 нет. Binary SHA256
`b5bc6d33206281c52afd3b17827e8cd416812d223d091f699d7883a382037a82`.

**Локальная квалификация Q1–Q8: PASS.** Три сценария, пять настоящих native
Runs. Детерминированные assisted actors, реальные CLI/programs/Git и full
monitor HTTP; живые AI Factory actors/модели и браузер здесь не квалифицируются.

| Сценарий | Первый Run | Продолжение | Итог |
|---|---|---|---|
| backend | succeeded | Не требуется | Review evidence и local commit, одна Task/один Run |
| blocked-resume | partial; required checks unavailable, gate blocked | Новый Run, тот же workspace claim; полный quality replay | succeeded, одна Task/два связанных Runs |
| cancel-resume | cancelled на read-only checks до первого отчёта | Новый Run, тот же workspace claim; полный quality replay | succeeded, одна Task/два связанных Runs |

Во всех сценариях:

- add/claim не создают Run/workspace claim; prepare без typed input даёт
  `missing_input`, оригинальный TaskInput сохраняется byte-for-byte;
- prepare связывает точную queue selection и input digests; повтор прежних
  add/claim/start и, где применимо, continue не создаёт дубликатов;
- попытка complete при живом Run даёт `queue_task_busy`; continue без queue
  identity даёт `queue_source_identity_conflict`, не создавая новый Run;
- в continuation сохраняются tracked/untracked owner edits и bytes реализации,
  plan/implement/repair не повторяются; checks/security/review получают свежий
  candidate. Исторический source Run и исходный TaskInput неизменны;
- реальный `python3 -B -m unittest test_greeting` проходит; exported evidence
  содержит все три reports и общий candidate. Synthetic session=shared,
  model unavailable остаются записаны честно: итоговый gate **warnings**;
- отдельный full monitor индексирует все fixture Runs; точные bytes финального
  evidence через HTTP совпадают с sealed ref и CLI export, без truncation;
- после Run success Task ещё claimed. Только явный owner complete переводит
  её в done, сохраняя историю; повтор complete возвращает duplicate receipt;
- все workspace claims освобождены, отдельный monitor завершён, private HOME
  и временное дерево удалены. Чужие monitor/серверные процессы не менялись.

Первый отменённый checks ещё не дал отчёта: свежесть в этом случае сравнивается
с фактическим candidate перед owner edits, а не с несуществующим report digest.

## Ворота и источник

Versions3, folders7, derive check и feature unit8 PASS. Verify126 components /
83 steps /8 packages PASS; compatibility5 launches /4 builds /4 trusted PASS,
core-state/41. Все8 shipping package trees совпадают с v1.53.0, включая
canonical classic/profiled; Core/server/catalog/package versions не менялись.

[results.json](results.json) содержит fingerprints probe и inputs, исходные
typed outputs, точные monitor evidence bytes/refs, срезы Task/Run associations,
именованные отказы и gates. Полный command ledger сохранён локально по пути и
SHA256 из results.json; воспроизводится [probe](../../../tests/probes/feature_queue_check.py).
Полный ledger не дублируется в git: он повторяет большие Run/intent views.

Regression step и upload JSON добавлены в existing CI. **Full exact-SHA CI
[39250210672](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/39250210672)
SUCCESS** для source `679e2a1a9da2a15fdff6e23c8f13d60a0610f9ec`, committed/pushed
в main: verify, parallel-ui-ux и call-review-uiux. Во всех jobs установлен
official0.13.80; скачанный artifact native-feature-queue-results подтверждает
3 cases /5 Runs PASS и cleanup PASS. Итоговые gates warnings сохраняют честные
границы synthetic actors. [CI evidence](ci-results.json) хранит GitHub metadata,
artifact identity/digests, source fingerprints и исходные typed reports/monitor bytes.

Docs/evidence follow-up [skip ci] не меняет tested code/CI/inputs или package
trees; проверено byte comparison с CI commit. Новый tag/catalog release не
требуется: это examples/docs/tests вне packages, все8 shipping trees прежние.

Проектный пилот, private environment/baseline adapters (#2/#5), реальные хосты,
E3 writer cancellation и browser/Light acceptance остаются отдельными задачами.
Этот результат принимает пакетный CLI-маршрут E1/E2; не переопределяет полную
Core concurrency/crash/live-host квалификацию очереди.
