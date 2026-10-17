# W6 — consumer qualification

Реализованы project-owned recipes review/UIUX/combined и installer с reviewed
preview/apply. База — **официальный Pri-Fly0.13.80**, Linux amd64,
SHA256 `b5bc6d33206281c52afd3b17827e8cd416812d223d091f699d7883a382037a82`.
Движок, server deployment и все8 shipping packages не менялись.

## Подтверждено

| Наблюдение | Результат / граница |
| --- | --- |
| Legacy verify/compatibility | PASS:126 definitions,83 steps,8 packages;5 launches/4 builds/4 trusted. |
| Project compilation | Три режима × minimal/classic ×3 hosts:18 компиляций PASS. Это compile, не живые hosts. |
| Native placement | Review/UIUX/combined доходят до commit в обоих consumers. У classic только fixture project extend с fast/exclude improve; root/shipped files прежние. |
| Native ownership | Один Run/claim; dirty/untracked реализация проверяется до final commit. Original report refs/digests сохраняются в assessment. |
| Error decisions | Defect, unavailable, stale request, candidate edit, missing check, owner stop и cleanup failure останавливают приёмку; source bytes остаются прежними. |
| Post-commit race | Изменение файлов после seal отклоняет finish. Локальный commit может уже существовать; rollback не выполняется. |
| Owned browser | Chromium на declared desktop/mobile/flow; normal release перед commit; cancel требует operator cleanup. Synthetic fixtures не являются AI-вердиктом. |
| Scoped actual host | Combined classic succeeded:3 свежих Codex CLI-сессии, одна review и две UI/UX, один candidate/claim, среда освобождена,1 локальный commit. |
| Published source boundary | Все8 package trees совпадают с v1.53.0. Версии/catalog/tag прежние; добавление находится в examples/docs/tests/tools. |

Original live reports, native submissions/receipts, browser observations и
скриншоты — [evidence/live](evidence/live). [Сводка](evidence/live-results.json)
фиксирует session IDs и результаты; [fingerprints](evidence/live-artifacts.json)
позволяют сверить остальные исходные артефакты. Полные event streams остались
в локальном `/tmp/aif-w6-live80`; они не нужны для запуска recipe.

Live-квалификация ограничена reviewer-ами этого изолированного consumer.
Writer/classic checks/commit обслуживал synthetic controller, Git commit и
native программа выполнялись реально. Другие модели не аттестованы; App/Claude
здесь не проходили live review. Initial live request был кратким «Check declared
behavior»: reviewer честно отметил неоднозначность criteria как warning и
выполнил фактический unittest. В поставляемом примере description после этого
уточнён до полной команды и ожидаемого поведения. Это не скрытый PASS более
строгого request. Warnings допускались явной optional_policy:ignore.

## Native matrix и воспроизводимость

[CI job W6](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/39038596555)
на implementation commit `f4e40e79f39dc72bc6251ab8f97b3bd7a4134e47` —
**SUCCESS**:27 native cases,18 компиляций и8 именованных отказов.
[Полные native results](evidence/ci-w6-native.json),
[compile/refusals](evidence/ci-w6-contract.json),
[version/source ledger](evidence/qualification.json).
Все три hosts прошли synthetic runtime; actual host evidence отдельно выше.

Whole-child replay после required unavailable повторяет приёмку и видит
intervening owner edit: digest candidate меняется, base/claim сохраняются.
Accepted-prefix continue после отказа commit переносит ровно принятую приёмку;
это отдельно прошло для review/minimal и UIUX/classic. Подмена settings после
prepare отклонена как `project_start_stale_launch`, ни одного Run не создано.
[Локальный replay](evidence/replay-0.13.80.json),
[review prefix](evidence/commit-resume-0.13.80.json),
[UIUX prefix](evidence/uiux-commit-resume-0.13.80.json).

Публичный [Core E5 corpus51](evidence/core-0.13.80.json) также PASS на official80:
call cancellation/unknown effect/error/timeout с on_error и без него,
resource contention, depth/steps/transitions limits, effect policy/trust,
accepted child drift `recover_prefix_changed` и full-child replay, типизация.
Это отдельный общий native contract; direct W6 supplemental checks описаны ниже. Текст
scope в stdout старого Core script остался source-built/pending; ledger
фиксирует реально использованный released binary и hash.

[Полные README CLI команды](evidence/documentation-commands.json) проверены:
installer preview/apply, task helper и classic preflight/prepare/start до первого
handoff, без reviewer. Profile выбирается только `--package-profile`, повторять
его через preflight-answer нельзя. Worker/graph/CI fingerprints сохранены в
ledger. Code в follow-up с evidence не меняется.

**Полный CI SUCCESS** на указанном implementation SHA: verify, parallel-ui-ux
и call-review-uiux. [Итог с job/step receipts](evidence/ci-completed.json).
Документационный follow-up сохраняет implementation/graph/binding/config/test/CI
bytes по fingerprints ledger; новый package tag не выпускался.

## Границы квалификации

- Normal cleanup/release проверен. Cancel останавливает native reader, а owned
  fixture освобождает controller по exact owner/session; это **operator
  reconciliation**, а не гарантированный finally-tail графа.
- Timeout/unknown ensure/release и остановка внешнего actor требуют контракта
  среды проекта. Общая forced writer cancellation E3 не решена W6.
- Logical round остаётся sealed config round; повтор создаёт fresh artifacts,
  не скрытое изменение criteria. Partial child повторяется целиком. После
  принятого child и отказа commit native prefix может переносить receipt;
  изменённые файлы post-guard не пропускает, нужен reviewed replay приёмки.
- Installer не повышает budgets/permissions. Limits/resource/storage/trust
  отказы Core проверяются отдельно; W6 shared-resource среда не квалифицирована
  и installer её отклоняет. Бюджет custom loops/extensions проверяет проект.
- Private consumer/environment из [issue#2](https://github.com/StenHigh/prifly-aif-workflows/issues/2)
  не становится qualified результатами notes fixture. Его admission остаётся
  отдельной работой; W5 parallel grants не подключены.

[Команды и migration](../../../examples/review-uiux-extensions/README.md) ·
[Release guide](../../releases/project-examples-w6.md) · [W6-A1–A10](proposal.md).

## Статус критериев

A1–A5 подтверждены для описанных recipes; A6 — isolated owned fixture и
operator cleanup. A7 подтверждён для fresh/accepted-prefix replay и prepare
drift; Core timeout/changed-prefix/unknown-effect controls проверены отдельно.
Прямые W6 deadline/cancel→continue подтверждены supplementary probes ниже;
произвольные варианты внешнего reconciliation остаются проектной приёмкой. A8: root budgets не повышались, нормальный graph помещается;
Собственные W6 limits/trust/effects и finite-storage отказы также подтверждены
ниже; arbitrary custom concurrency/resources требуют своей приёмки. A9/A10 — локальные ворота/live/docs и final полный CI PASS. Эти границы не объявляются универсальной приёмкой private stacks.


## Дополнительные controlled-host проверки

Без изменений implementation bytes отдельно выполнены
[cancel→continue](evidence/cancel-continue-0.13.80.json) для review/minimal и
UIUX/classic:2 Runs,1 claim, новые reports,1 scoped commit. После UI cancel
controller сначала освобождал exact owned environment, затем готовил native
continue. [Probe source](evidence/cancel-continue-probe.py) добавляет сценарий
только в synthetic controller в памяти; recipe/engine/classic не переписывает.
Это дополнение к27 CI cases, не часть этой цифры.

Две project binding вариации до native prepare проверили timeout:
[1ms admission deadline](evidence/admission-timeout-0.13.80.json) истёк до запуска
процесса; [1500ms running process](evidence/timeout-0.13.80.json) остановил явно
заданный read-only Python sleep(3). Последний реально запущен, stop_reason
attempt_deadline_expired, group_empty:true, uncertain:false. Оба Run rejected,
без reports/commit, source classic прежний. [Probe source](evidence/timeout-probe.py)
меняет только fixture project execution binding перед sealing, не поставляемый
recipe; native diagnostic отделён от usable review gate.


## Ограничения и разрешения W6

[Собственный corpus7](evidence/permissions-0.13.80.json) на released80:
root max_child_depth/max_step_instances/max_control_transitions →limit_exceeded;
нет consent →project_execution_approval_required; чужой executable
→project_execution_not_allowed; parent policy1 не повышается child policy4
→resource_limit; destructive effect →unsupported. Все отказы до dispatch,
ни одного Run; изменялась только копия собственного minimal consumer.
[Reproduction source](evidence/permissions-probe.py).

[Storage ceiling](evidence/storage-0.13.80.json): combined classic, новая отдельная
fixture authority с finite bootstrap8MiB. Run drive остановлен
storage_budget_exhausted,10 accepted Attempts сохранены, исходный limit/control
generation прежний — recipe ничего не повышал. Controlled owner отдельно
выполнил prepare/set64MiB с exact review digest только для recovery/cleanup
стенда; принятые результаты до/после идентичны. Ни reset, ни pruning не было.
[Probe](evidence/storage-probe.py) · [initializer](evidence/storage-fixture-init.go).
Initializer использовал неизменённый released0.13.80 source API только для новой
пустой authority; **все исполняемые workflow/CLI controls — official binary80**.
Этот setup нужен для небольшого finite ceiling без изменения реального сервера,
его budgets или данных engine. Fingerprints — в qualification.json.


[Finite capacity](evidence/capacity-0.13.80.json): owner задал capacity1
только временной authority. W6 reader занимал её обычный admission slot;
второй явно запущенный controller-ом Run получил capacity_conflict и очередь,
без единого Attempt. Capacity не повышалась, затем оба controlled Runs были
cancelled/settled и очищены. Это проверка отказа/учёта slot, не обещание fairness
или завершения двух concurrent Runs. [Probe](evidence/capacity-probe.py).


Поле actual_browser в raw synthetic CI report означает выбранный browser mode
(--browser-library); unavailable/cancel могут остановиться до запуска браузера.
Фактический browser proof — выполненные ready scenarios и сохранённые live
observations/screenshots, а не одно это поле. Scope каждого исхода следует
читать вместе с scenario, reports и gate.
