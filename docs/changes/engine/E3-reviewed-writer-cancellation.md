## Результат перепроверки E3

На **latest stable Pri-Fly v0.13.80** (проверено 2026-10-19) после отмены assisted writer и явного owner `run resolve` подготовка продолжения всё ещё отказывает `recover_source_unsettled`. Неопределённая obligation уже разрешена; повторная проверка показывает `failed`, `outcome:null`, `cancel_requested:true` и отсутствие uncertain Attempts.

Нужен поддержанный **reviewed recovery** после проверки и разрешения эффектов отменённого writer. Сохранение запрета до разрешения эффектов обязательно. Граница наблюдалась на0.13.76/77 и подтверждена на0.13.80; отдельное issue E3 ранее не публиковалось.

## Среда и закреплённый consumer

- Официальный [Linux AMD64 release asset v0.13.80](https://github.com/StenHigh/prifly/releases/download/v0.13.80/prifly-linux-amd64.tar.gz), не dev-сборка.
- SHA256 распакованного binary: `b5bc6d33206281c52afd3b17827e8cd416812d223d091f699d7883a382037a82`.
- Consumer: [StenHigh/prifly-aif-workflows@081931fb395d09311a49cb5037f0531db18c9c09](https://github.com/StenHigh/prifly-aif-workflows/tree/081931fb395d09311a49cb5037f0531db18c9c09), `aif-feature@1.2.3`.
- Root декларирует `resumable.from_outcomes: [partial, rejected]`, `from_cancelled: true`. Plan/implement — `workspace_write`, `retry_class: never`.
- Проверка: synthetic synchronous actors, реальные CLI/Git; свежие временные repository/authority/worktree, private HOME. Реальные модели, внешний provider и частная среда не участвуют. Core, server и canonical classic/profiled не менялись.

## Воспроизведение

Нужны Linux, Python3, Git, gh и скачанный official binary. В свежем checkout consumer:

```sh
gh repo clone StenHigh/prifly-aif-workflows e3-consumer
cd e3-consumer
git checkout 081931fb395d09311a49cb5037f0531db18c9c09

# Абсолютный путь к распакованному official v0.13.80:
e3_binary=/absolute/path/to/released/prifly
sha256sum "$e3_binary"
"$e3_binary" --json version

python3 -B tests/probes/feature_check.py --binary "$e3_binary" --case plan-cancel --report /tmp/e3-plan.json
python3 -B tests/probes/feature_check.py --binary "$e3_binary" --case implement-cancel --report /tmp/e3-implement.json
python3 -B tests/probes/feature_check.py --binary "$e3_binary" --case cancel-resume --report /tmp/e3-read-only-control.json
```

[Публичный fixture](https://github.com/StenHigh/prifly-aif-workflows/blob/081931fb395d09311a49cb5037f0531db18c9c09/tests/probes/feature_check.py) сам подготавливает typed task/launch и обслуживает Attempts. Writer probes ожидают именно существующую границу: **exit0 означает воспроизведение отказа, а не успешное writer resume**. После реализации нового контракта эти negative assertions нужно заменить/расширить. Fixture освобождает созданные claims, registry entries и temp dirs.

Native последовательность внутри writer fixture:

1. Reviewed prepare/start `aif-feature`; дойти до выданного plan либо implement Attempt.
2. Для plan оставить известные partial bytes `.ai-factory/PLAN.md`; для implement отменить до actor write, сохранив engine-materialized plan.
3. `run cancel RUN --reason ...`; `run drive RUN` отказывает `recovery_required`.
4. Дождаться возврата synchronous fixture actor, осмотреть свои bytes/effects; `run resolve RUN --attempt ATTEMPT --outcome applied|not_applied --reason ...`.
5. `run drive RUN`, затем прочитать `run status RUN`: uncertain Attempts отсутствуют, writer имеет resolved diagnostic, Run failed/cancel_requested.
6. `project continue --repository REPO --launch aif-feature --source-run RUN --host codex-cli --allow-execution --prepare` → `recover_source_unsettled`.

`applied` здесь подтверждает наблюдённые эффекты, не завершённость плана или успешность реализации.

## Наблюдения на0.13.80

| Case | Отмена и owner resolution | Состояние после resolve | Prepare |
|---|---|---|---|
| `plan-cancel` | producer оставил partial PLAN, `applied` | uncertain → failed; `resolved_applied`, cancel_requested=true, uncertain=0 | `recover_source_unsettled` |
| `implement-cancel` | consumer до actor write, `not_applied` | uncertain → failed; `resolved_not_applied`, cancel_requested=true, uncertain=0 | `recover_source_unsettled` |
| `cancel-resume` (контроль) | read-only checks | cancelled, без unknown writer effects | prepare/start succeeds; второй Run succeeded, тот же workspace claim |

Точный Problem после обоих writer resolve:

```json
{"code":"recover_source_unsettled","message":"source Run holds a stop, active work or unresolved obligation","retryable":false,"violations":[],"safe_next_actions":["doctor","run.status"]}
```

Read-only instrumentation дополнительно сравнила source Run version/state, inventory Run IDs, candidate/index/HEAD digest, owner bytes и partial PLAN до/после prepare: изменений нет, новый Run не создан. Resolve также сохранил workspace bytes. Все3 fixtures очищены, active claims не оставлены. Контроль дошёл до полного quality replay и local commit; model/session independence не аттестуется.

## Контракт recovery и критерии приёмки

- [ ] Пока writer effects не разрешены, precise refusal сохраняется; неизвестные внешние эффекты не допускают blind retry или requeue.
- [ ] После inspected owner resolution есть явно поддержанный reviewed маршрут подготовки recovery с original base, claim и decisions. Source и рабочие bytes не меняются при prepare.
- [ ] Для implement/not_applied без actor write можно после review повторить writer и затронутую quality, сохраняя existing work и один workspace claim.
- [ ] Для producer/applied с occupied unsealed PLAN остаётся named refusal и точное owner action. Partial plan не принимается как успешный output; bytes не удаляются/перезаписываются автоматически. После явного разрешения этого отдельного конфликта есть документированный recovery route.
- [ ] Решение не очищает cancel flag обходом runtime API и не синтезирует успешный writer result. Восстановление учитывает вложенные invocations и native output materialisation, а не только root flag.
- [ ] Новая реализация повторяет все затронутые quality checks; старый PASS не переносится на изменённый candidate. Prefix mismatch сохраняет именованный отказ.
- [ ] Нативные tests покрывают producer/consumer, applied/not_applied, unresolved effects, repeated cancel, chained recovery и регрессии partial/read-only cancellation.
- [ ] Published contract/CLI/runner docs объясняют разрешённый маршрут и его отказы. Другой workflow/host не подменяет unsupported writer resume.

В released [recovery.go](https://github.com/StenHigh/prifly/blob/v0.13.80/internal/runtime/recovery.go#L329) `source.CancelRequested` участвует в отказе до выбора recovery frontier; [recovery_frontier.go](https://github.com/StenHigh/prifly/blob/v0.13.80/internal/runtime/recovery_frontier.go#L88) также учитывает invocation cancellation. Это указатели на наблюдаемую границу, не готовое предложение убрать safeguards.

E3 не закрывается исправлением parallel read-only cancellation #6 или успешной queue/read-only qualification. Пакетное обычное развитие, graceful partial и read-only continue продолжают работать; canonical classic менять для решения этого issue не требуется.
