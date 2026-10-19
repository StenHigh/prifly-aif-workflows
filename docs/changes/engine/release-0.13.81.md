# Pri-Fly0.13.81 — E3 consumer qualification

2026-10-19: latest stable — [v0.13.81](https://github.com/StenHigh/prifly/releases/tag/v0.13.81),
source `94b7eb2ccad4828b9e9db363ce2236f6427b4e5f`.
[Issue13 CLOSED](https://github.com/StenHigh/prifly/issues/13),
[Core handoff](https://github.com/StenHigh/prifly/issues/13#issuecomment-6270875976).

Official Linux AMD64 asset скачан в отдельный `/tmp` каталог. SHA256 архива
`095da449e9f01cc7f756a8af5045465a49dfd9ac6e3a602833699368e7feb26b`
совпал с release manifest; SHA256 распакованного binary
`b2e02b36b2e062aacb4acf2b5cd3a35c0c8aee19379b77c6ff4d5714a22e6f50`.
Установленный CLI/сервер не обновлялись.

## Что изменилось для пакетов

- После отмены writer и inspected owner resolution same-launch reviewed
  recovery поддерживает execute writer и последующий quality. Cancellation
  facts исходного Run сохраняются, resolution не становится успешным output.
- До resolution сохраняется `recover_source_unsettled`. Occupied producer
  PLAN сохраняет `workspace_tree_output_exists`; только явное решение владельца
  освобождает capture path. Следующий source — текущий владелец claim.
- Сохраняются прежние `recovery-plan/1`, `recovery/2` и authoring YAML. Изменять
  workflow/extend/bindings или версии shipping packages для E3 не требуется.
  Core обновил authoring guide/runner guidance; project runner update в этой
  задаче не выполнялся, чтобы не менять пользовательские установки.
- В релиз также включён Light frontend. Released `monitor --help` подтверждает
  `--ui light`, `--full-monitor-url`, `--base-path`, `--light-projection`.
  Consumer projection/browser/domain acceptance — отдельный E6 follow-up,
  issue11 пока OPEN. В этой задаче monitor/services/domains не менялись.

## Принятая consumer-квалификация

Старые writer probes на source081931f проверяли **отказ**0.13.80. Теперь
`tests/probes/feature_check.py` проверяет положительный контракт0.13.81:

| Case | Наблюдение | Результат |
|---|---|---|
| implement-cancel | unknown writer до resolve отказывает; после not_applied prepare read-only, writer+quality повторены, source immutable | succeeded,2 Runs,1 workspace claim |
| plan-cancel | после applied prepare read-only; partial PLAN даёт named guard, bytes сохраняются; explicit fixture owner move и recovery от нового владельца claim | succeeded,3 Runs,1 workspace claim |
| cancel-resume | read-only cancellation, полный quality replay | succeeded,2 Runs,1 workspace claim |
| blocked-resume | обычный partial после unavailable quality | succeeded,1 workspace claim |
| upgrade-refusal | изменённый accepted prefix сохраняет recover_prefix_changed; explicit reviewed replay от configure | succeeded,1 workspace claim |

Для обоих writer prepares проверены source state/version, Run inventory,
claim list, candidate/index/HEAD и owner/plan bytes. После нового исполнения
исходный Run также не изменился. PLAN перемещал только fixture owner своего
временного проекта; файл сохранялся отдельно до конца проверки.

Это private HOME/temp repository/authority, synthetic synchronous actors и
реальные CLI/programs/Git. Все5 fixtures очистились, active claims не оставлены;
временный HOME удалён, свои monitor processes завершены. Live models, другие
host runtimes, приватные environments и integration/provider writers не
квалифицируются этой матрицей.

## Ворота и поставка

Verify126 components /83 steps /8 packages PASS; compatibility5 launches /
4 builds /4 trusted и core-state/41 PASS. Versions3/folders7/derive PASS.
Все8 shipping package trees совпадают с v1.53.0, включая classic/profiled.

[Машиночитаемые результаты](release-0.13.81-results.json) содержат binary/source
hashes, точную адаптацию probe, исходные observations и gate outputs.
Адаптация опубликована в `63788337e9c1d375f73424b4d71c47bdc7339e4c`.
[CI39284492475](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/39284492475)
пока **queued**: все3 jobs ожидают runner, проверки ещё не стартовали.
GitHub сообщает о [сбое Actions](https://stspg.io/nrv2k8s68bwn).
[Снимок состояния CI](release-0.13.81-ci-results.json) закрепляет commit и время
проверки. Локальная квалификация PASS; финальная CI-приёмка E3 остаётся открытой.
После зелёного полного прогона нужно сохранить artifact `feature-recovery-results`,
подтвердить released binary/version и обновить этот статус.
Прежний CI39250210672 на0.13.80 сохраняется как исторический результат.
Новый package tag/catalog release не требуется.

Для воспроизведения используйте current positive probes на0.13.81+ и
[полную инструкцию small-feature](../../../examples/small-feature/README.md#продолжение-после-отмены-пишущего-шага).
Исходный отказ0.13.80 остаётся в [историческом evidence](E3-writer-cancellation-0.13.80-results.json).
