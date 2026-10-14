# UI/UX review on an owned test environment

Отдельный пакет `aif-product:package/ui-ux@1.0.0`, подготовленный для W3.
Требует выпущенный Pri-Fly **0.13.76**, Python 3 stdlib для programs и host
skills `aif-review/SKILL.md`, `aif-review/references/SEVERITY.md`.
Пакет пока не выпущен в каталоге. Classic/profiled/fix/fanout не меняются.

```text
configure → quality {
  capture → environment → UI → UX → evaluate → release → finalize
} → succeeded | partial
```

UI проверяет существующую дизайн-систему, desktop/mobile, hierarchy, spacing,
typography, overflow и contrast. UX исполняет заданные flows и применимые
loading/empty/error, keyboard/focus, labels/alt и copy. Проект выбирает
сценарии, браузер и test identity; универсального oracle качества здесь нет.
Отдельные readers и отчёты не доказывают отдельные сессии или другие модели.
Read-only readers могут менять ephemeral browser state; submit_test в этом
пакете относится к локальному состоянию test страницы. Сценарий, пишущий в
backend/API/database, требует отдельного declared effect исполнителя/графа;
одного allowed_operations в configuration для такой записи недостаточно.

## Установка и просмотр запуска

Для локального пилота скопировать эту папку целиком в
`.prifly/workflows/aif-ui-ux/` и добавить к existing project profile:

```yaml
packages:
  aif-ui-ux:
    source: .prifly/workflows/aif-ui-ux
launches:
  aif-ui-ux:
    title: UI and UX review
    description: Owned test environment and sequential product acceptance.
    kind: workflow
    workflow: .prifly/workflows/aif-ui-ux/workflow.yaml
```

`configuration` — один JSON input по [schema](schemas/configuration.yaml).
[Fixture configuration](examples/configuration.json) иллюстрирует поля;
нулевой `base_commit` заменить реальным полным SHA-1 commit, instructions
setup/cleanup — точным проектным контрактом. Пример не запускает настоящий
проектный сервер сам. Не помещать secrets в sealed input/evidence.

Перед запуском просмотреть выбранные checks, requiredness, policy, scenarios
и среду; preview валидирует их и печатает digest точных байтов input:

```sh
python3 -B .prifly/workflows/aif-ui-ux/files/preview.py \
  --configuration /absolute/path/configuration.json
prifly project local set --repository . --allow-executable python=/absolute/path/python3
prifly project questionnaire --repository . --launch aif-ui-ux \
  --host codex-app --workspace worktree \
  --input configuration=/absolute/path/configuration.json --allow-execution --prepare
```

В native prepare проверить input digest, sealed programs и external permissions,
затем `project start` с теми же параметрами и полученным
`--expected-launch-digest`. Native summary связывает input по digest; отдельный
preview показывает его предметные поля, новый UI в Pri-Fly для этого не нужен.
Compile/prepare не исполняют setup. `--allow-execution` разрешает только
объявленные programs; permission на произвольный shell из него не следует.

## Состав и evidence

`ui`/`ux` внутри configuration — запросы W1: одинаковые base, round, optional
policy и session policy, отдельные check IDs. Method всех checks — browser.
`enabled: false` явно исключает check, с записью `excluded` и причиной.
`surface: backend` + непустой `scope_reason` задаёт `applicable: false` и
`not_applicable`. Для frontend checks applicable; отсутствие browser/server
не позволяет менять это поле. Полностью исключённый/backend scope не готовит
среду, но оба readers возвращают явные записи о пропусках.

Каждый applicable enabled check получает один или несколько scenarios:
`id`, `lens`, `check_id`, относительный page path, viewport, actions и
expectations. Описание проецированного W1 request связывает check с этим
catalog, scope и environment contract. Ограничение W1 description — 4000
символов на check: большие catalogs разбивать на несколько checks.

Reports используют неизменённый [W1 schema](schemas/report.yaml), точный
request artifact digest и captured candidate. В browser evidence поле
`observation` — JSON **строка** с ровно четырьмя ключами:

```json
{"scenario":"mobile","viewport":{"width":375,"height":800},"url":"http://127.0.0.1:12345/index.html","observations":"Actual rendered page observations and finding"}
```

`locator` равен этому URL, `tool` называет реальный tool, `exit_code: null`.
Каждый выполненный check покрывает все свои scenarios, с точными ID, viewport
и origin из ready environment receipt. Diff/DOM/code чтение не заменяет
browser method; UI reader должен также осмотреть отрисованную страницу.
Failed result содержит конкретный finding. Скриншоты и прочее evidence хранить
в task output workspace либо в owned внешнем хранилище, вне candidate.

Evaluator повторяет snapshot HEAD/index/tracked/nonignored-untracked bytes,
удалений и modes. Проверяет W1 coverage и criteria digest, sealed projection,
ownership/profile/configuration/candidate receipt, scenarios и URL. Finalize
повторяет snapshot после cleanup и проверяет точный release owner/session.
Это проверка непротиворечивости declarations; она не аттестует содержимое
браузера, prose, deployment source или модельную независимость.

## Среда и результаты

Полный контракт — [standalone environment guide](../docs/product-review-environment.md).
`environment` и `release` — assisted project adapter steps с
`external_write`, `retry_class: reconcile_required`, явными ensure/release
permissions и read-only repository. Они исполняют только закреплённые
проектные setup/cleanup instructions. Shipped package не содержит Docker/npm
или provider credentials. Install/build/cache располагаются вне candidate.

`environment` возвращает ready, unavailable, not_needed, owner_required либо
reconcile_required. Ready требует фактический session, origin и подтверждённый
source candidate. Required missing browser/server → partial/blocked;
optional unavailable → warnings по ignore/stop. Полезный diagnostic report
подаётся с session verdict pass; product failed → partial/failed, без repair.
Unavailable/declined model отдельно остаётся warning по той же policy.

Root exports `gate`, `ui_report`, `ux_report`, `environment`, `release` для
succeeded/partial. Если setup/reader/release вообще не смог произвести usable
receipt/report, результат rejected; уже созданную среду reconciles оператор
по sealed owner до следующего действия. У cancelled Run cleanup tail не
выполняется автоматически. Вызов reviewed `project continue` повторяет весь
quality: новая capture, среда, оба readers и cleanup; base/claim/work сохраняются.
Сначала завершить точную reconciliation предыдущей среды. Никаких reset/stash,
пересоздания candidate или скрытого repair при continue нет.

Для shared стенда в **проектном** extend.yaml объявить, например:

```yaml
resources:
  browser-stand:
    limit: 1
    stages: [quality]
extensions: []
```

`configuration.environment.shared_resource` должен называть этот ресурс.
Pri-Fly сериализует Attempts, в том числе внутри quality call. Между Attempts
среду защищает owned lease проектного runner; resource не является lease на
всё время жизни стенда. Второй job не присваивает чужую среду после завершения
setup Attempt. По умолчанию shared_resource null: отдельные session/ports.

## Qualification

[Матрица W2](../docs/changes/add-ui-ux-review-components/acceptance.md) разделяет
synthetic runtime, actual Chromium fixture и current Codex-app observation.
Тестовый notes adapter выполняет только свой catalog; его deterministic
assertions не считаются LLM visual review. Живое наблюдение current Codex-app использовало shared session. Дополнительно
Codex CLI0.162.1 прошёл четыре required separate fresh sessions, с actual
browser/screenshot inspection, неизменёнными reports и retained workspace-write
sandbox/auto-review отдельных command escalations. Другая модель и live Claude
не квалифицированы; при required separate session отсутствие даёт blocked.
