# Project test environment lifecycle for product review

Этот standalone contract решает документационную часть [issue #2](https://github.com/StenHigh/prifly-aif-workflows/issues/2)
без изменения эталонных classic/profiled и движка. Применяется к
[UI/UX package](../aif-ui-ux/README.md) и будущим проектным extensions.
Реальную совместимость private backend, dependency fingerprints и browser
adapter обязан подтвердить потребляющий проект; fixture её не доказывает.

Перед prepare проект закрепляет:

- Один owner для invocation, profile, exact setup/cleanup adapter instructions.
- Browser adapter, test origin/source identity, viewport/scenarios и identity
  с разрешёнными test operations. Credentials в immutable inputs не включаются.
  Read-only readers меняют только ephemeral browser state; реальные записи
  через test API/DB требуют собственного declared external effect, даже если
  среда disposable. Поле allowed_operations не расширяет effects шага.
- Общий совместимый profile для browser QA → PHP gate → final tests либо
  отдельный явно разрешённый transition. W2 использует первый режим: один
  profile от setup до release, read-only reviewers его не меняют.
- Отдельные directories для ephemeral dependencies/build/cache/data/evidence.
  Candidate/worktree/claim не являются расходуемой средой и не удаляются.
- Shared resource для сериализации Attempts и lease для всей жизни среды,
  либо уникальные browser contexts, sessions и ports каждого job.

## Последовательность с одним profile

Declared setup executor `ensure` проверяет владельца и source candidate,
поднимает общий compatible profile вне candidate и возвращает typed receipt
с owner/session/profile/origin/configuration digest/candidate digest.
Browser QA, PHP gate и tests пользуются тем же profile; readers не запускают
setup/install/release. Если общий profile недоступен, required gate получает
blocked с причиной. Наличие работающего URL другого дерева не является pass.

Release executor сначала сохраняет нужное evidence и сверяет owner **и exact
session**, затем освобождает только эти ресурсы. Не трогает Git worktree,
claim, чужой сервер или чужие изменения. Uncertain outcome записывается как
reconcile_required. Effects include external_write и declared exact operations;
разрешение execution не распространяется на посторонние операции.

## Если profiles несовместимы

| Ответ runner | Значение | Следующий шаг |
|---|---|---|
| `release_required` | Достоверно существует принадлежащая invocation среда A; ensure B требует её нормального release | Если transition заранее разрешён, отдельный executor сохраняет evidence, проверяет ownership, выполняет scoped release A и ensure B. Иначе owner_required/blocked с требуемой операцией |
| `reconcile_required` | Итог предыдущей операции неизвестен либо interruption оставил промежуточное состояние | Сначала адресно обнаружить фактическое состояние/ownership. Завершить или признать выполненной конкретную операцию, затем продолжать; не повторять release/ensure вслепую |
| Ownership mismatch / busy | Ресурс относится к другой session/job | Не освобождать его; ждать lease/resource или запросить решение владельца |
| Tool/server unavailable | Проверка сейчас не может исполняться | Required → blocked; optional → declared warnings policy; не менять applicability |

Transition A → B является самостоятельным declared effect с разрешёнными
release/ensure операциями и bounded target. Его нельзя добавить внутрь read-only
gate или выполнить под W2 ensure permission, который разрешает только ensure.
Если нужен такой маршрут, проект авторит multi-stage graph; W2 не подменяет
его неявным пересозданием среды. Example fixture разрешает transition только
при explicit flag и совпадающем owner; это тест adapter, не штатный worker.

## Cancellation и recovery

Cleanup tail не гарантируется при cancellation, host crash или unusable
receipt. Run operator сохраняет delivery/effect receipts и обнаруживает только
свою среду по owner/session. Если setup оборвался до receipt, использует заранее
заданный owner и проектный journal. Сначала reconciliation, затем scoped cleanup
или подтверждённое reuse; чужой job или Git claim не является cleanup target.

Reviewed continue W2 повторяет capture/setup/UI/UX/evaluate/release/finalize
после завершения reconciliation. Прежние browser observations нельзя объявлять
fresh только потому, что candidate SHA не менялся: исполнить сценарии заново
и создать fresh report, с фактическими URL/session/observations. Receipt и
source binding — declarations адаптера, не engine deployment attestation.

## Executable fixture и границы

[OwnedEnvironment](../tests/probes/product_environment.py) создаёт loopback
HTTP server над конкретным claimed tree, port 0 выделяет свободный порт,
состояние/lease лежат вне candidate. Atomic create lease не даёт другому job
занять shared stand. Release сверяет owner/session; interruption после stop
оставляет lease для reconciliation. Это локальный fixture с known process
ownership; production runner должен проверять реальные процессы/containers.

[Unit/lifecycle cases](../tests/test_product_review.py) проверяют общий profile,
A→PHP→tests с заранее разрешённым адресным переходом, отказ без permission,
unique jobs/shared lease, чужую ownership и interrupted release. [Runtime
probe](../tests/probes/product_check.py) проверяет shared resource contention,
cancellation и explicit operator cleanup на released 0.13.76. Реальный Chromium
проходит UI/UX на одном общем profile. Настоящий PHP stack и private consumer
lifecycle остаются project qualification; issue #2 автоматически не закрывается.
