# CONTEXT_STATE

Рабочее состояние репозитория пакетов AI Factory для следующей сессии.
Нормативная правда — в самих YAML и в `aif-classic/decisions/INVENTORY.md`;
этот файл только ориентирует. История до 2026-09-25 (заходы пилота, выпуски
движка 0.10–0.13.54, переход на AI Factory 2.19.0, WorkflowRevision v4) —
в git: `git show d388b92:CONTEXT_STATE.md` (2330 строк, оглавление — `mdq tree`).

## Состояние на 2026-10-13

- **Живая приёмка трёх bridge v1.51.2 (2026-10-13) — PASS:**
  Latest stable проверен: Pri-Fly v0.13.76, новых выпусков нет.
  Пользователь подтвердил остальные пункты финальной приёмки; в этой сессии
  проверяли только естественный verdict при required dependency unavailable.
  3 изолированных Run, 15 уникальных accepted fresh Codex CLI reader sessions,
  настоящие AI Factory 2.19.0 skills/scripts/references. Checks/security/review
  сами выбрали pass + blocked, blocking=false; root partial с exact исходным
  gate, без repair/commit. После восстановления original dependency bytes
  reviewed continue → новые checks/security/review → local commit/succeeded.
  Один claim 1→2, source/base/owner work сохранены; все стенды/claims/monitor
  очищены. Full security audit реально исполнился во всех 5 security Attempts.
  Controller не редактировал ни verdict/gate, ни summary; expected verdict
  и asserts оставались вне host prompt. Первоначальный resumed review draft
  checks-фикстуры был отвергнут model_profile_reason_missing; сохранён отдельно,
  стенд очищен. Уточнён только neutral report schema context (dedicated reason),
  checks case повторён fresh hosts и прошёл. Это оформление report, не новый
  дефект routing/пакета. Warmup/fix/commit — deterministic setup, live evidence
  относится к readers; другая модель не заявлена. Пакеты не изменены, bump нет.
  Воспроизводимый manual probe tests/probes/live_readers.py, отчёт и JSON:
  tests/probes/results/aif-fix-bridge-1.0.2-live.md. Не включён в CI: расходует
  настоящий configured Codex host usage. Issue #4 закрыт completed; приёмка:
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6150208132.

- **Уточнение bridge к v1.51.2 / aif-fix 1.0.2 (2026-10-13):**
  выверены против выпущенного Pri-Fly `v0.13.76`; новых stable нет.
  Живой повторный пилот v1.51.1 подтвердил blocked pass во всех трёх readers,
  пустой short_checks report и chained resume:
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6133548812.
  Уточнены только check/security/review bridges: verdict — пригодность отчёта,
  gate.status — доступность/результат проверки. Установленная required missing
  dependency: usable pass + blocked gate; verdict blocked — невозможность
  пригодной оценки с обязательным diagnostic gate. Usable needs_revision
  маршрутизируется так же. 3 contexts/3 steps/2 quality workflows/root/package
  версии 1.0.2; graph/effects/schemas/warmup/build и classic/profiled/fanout
  byte-for-byte не менялись. Static10, derive, verify (59 components/34 steps),
  compatibility, 28 runtime cases и 4 classic probes — PASS; ещё 3 blocked
  needs_revision/resume cases — PASS. Собственная проверка real add/update из
  local Git origin: partial blocked quality 1.0.1→1.0.2 prepare accepted,
  frontier quality/reuse warmup+build, fresh gates/commit succeeded. Partial
  на deliberately withheld commit после accepted quality: recover_prefix_changed
  at quality, reviewed --from-stage quality → succeeded. В обоих один claim 1→2,
  base/owner work сохранены, source/tree при prepare не меняются. Exploratory
  cancel delivered writable commit: resolve not_applied settles failed with
  active cancel, prepare recover_source_unsettled; это source guard, не bug
  пакета. Стенды/claims/monitor очищены. Evidence:
  tests/probes/results/aif-fix-bridge-1.0.2.md и JSON рядом.
  Собственные tests — synthetic host + released CLI/Git/capture, нового LLM
  пилота/модельной независимости не заявляем. 1.0.0→1.0.1 full warmup replay
  остаётся непроверенным. Выпущен signed v1.51.2, source commit
  `0e93c36672e23ac404463f815cb89c7c3ffe31fe`:
  https://github.com/StenHigh/prifly-aif-workflows/releases/tag/v1.51.2.
  Центральный каталог `e11069d467d67567ad224089556aa955461579b5` меняет только
  aif-fix exact pin; остальные 3 записи остались на v1.51.1. После публикации
  standard catalog search/add, exact origin и 4 полных synthetic Runs — PASS:
  direct, fix-plan, repair-review и blocked-review/resume → succeeded; cleanup
  claims/monitor завершён. tests/probes/results/aif-fix-published-v1.51.2.json.
  CI main green: https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38318122211.
  CI tag green: https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38318683722.
  Issue #4 остаётся открытым на остальные границы живой приёмки.

- **Pilot fixes опубликованы v1.51.1 (2026-10-13):** aif-fix 1.0.1,
  подписанный commit `2be86bf1683951f71c1606f3fb3930ac16af23db` и annotated tag,
  https://github.com/StenHigh/prifly-aif-workflows/releases/tag/v1.51.1.
  Центральный каталог commit `564adde734b4fa1a0573ab7ec3e813d00eb81230`:
  4 entries exact pinned на этот tag/source commit. Published catalog install
  и полный synthetic smoke Run — PASS/succeeded, claims/стенд очищены;
  tests/probes/results/aif-fix-published-v1.51.1.json.
  Разбор и исправления опубликованы в issue #4:
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6132816375.
  CI tag: https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38309753196.
  До update завершить остановленные v1.51.0 на старом installed contract либо
  отдельно рассмотреть explicit replay по engine prepare; recover_prefix_changed
  at warmup проверен, полного cross-version replay не было. Issue открыт.

- **Живой отчёт пилота #4 и исправления (2026-10-13):**
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6132513896.
  Released Pri-Fly 0.13.76 по-прежнему latest stable, новых выпусков нет.
  Пилот реально подтвердил escalation pinned aif-fix, отдельный repair и
  partial→cancelled→succeeded chained resume на одном claim 1→2→3; продуктовый
  короткий путь включал repair. Прямой LLM путь без repair, custom/negative
  случаи, intervening edit и отличающаяся модель этим отчётом не подтверждены.
  Подтверждена дыра aif-fix 1.0.0: usable verdict pass + gate.status blocked
  игнорировался choice и приводил к succeeded. Регрессия RED на stable.
  В aif-fix 1.0.1 status blocked имеет приоритет в checks/security/review:
  partial с точным исходным gate, без repair/commit; после восстановления —
  same-version resume и finish, regression GREEN. Внешняя optional QA после
  публикации — warning, не blocked обязательной проверки и не полная приёмка.
  Literal answered_questions.answer="" воспроизводит answered_questions_invalid
  /answered_questions/0/answer на stable; непустое объяснение проходит, typed
  short_checks и ledger остаются "". Новый session-report context у всех 9
  Attempts документирует это и отличает report basis от runtime permission.
  Core/report API не меняли. Отказы --workspace resume override, prepare до
  settled cancel и sandbox authority access — ожидаемые условия, не bug графа.
  audit.sh без npm в PHP environment — проектная интеграция, standing npm
  advisories не исправляются под видом работы над workflow.
  Версии изменённых bridges/9 steps/4 workflows и package/root подняты;
  classic/profiled/fanout byte-for-byte не менялись. Static10, verify, compatibility
  и derive_profiled — PASS. Classic pass/blocked-resume/cancelled-resume
  probes — PASS в прежней границе до следующего handoff.
  Новые runtime cases покрывают 3 blocked usable
  reports и empty-answer отказ/объяснение; полная расширенная матрица запускается.
  Cross-version continue prepare (v1.51.0→1.0.1) — ожидаемый recover_prefix_changed
  at warmup; source run_version и claim tree неизменны. Full explicit replay
  --from-stage warmup не исполнялся, automatic prefix migration не обещается.

- **v1.51.0 опубликован для пилота (2026-10-12):** подписанный commit
  `b3ca8d2a31e9cd2e3da36b38205316f86d6be912`, подписанный annotated tag и
  https://github.com/StenHigh/prifly-aif-workflows/releases/tag/v1.51.0.
  Центральный каталог опубликован commit
  `18b873edb1dbe2b331753d94e9f33e669630e341`: четыре записи pinned на v1.51.0
  и exact package-source commit, новая запись aif-fix доступна по имени.
  Published catalog search/add + полный synthetic smoke Run — PASS/succeeded
  на released Pri-Fly 0.13.76; стенд/claim/monitor entry удалены.
  Артефакт: tests/probes/results/aif-fix-published-v1.51.0.json.
  Пилотные действия владелец передаёт сам по docs/pilot-aif-fix-v1.51.0.md;
  никаких сообщений или изменений в проекте пилота из этой сессии нет.
  Публикация отмечена в issue #4:
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6130768067.
  CI release tag: https://github.com/StenHigh/prifly-aif-workflows/actions/runs/38294848148.
  Issue #4 остаётся открытым до фактической приёмки пилотом.

- **Выпуск v1.51.0 разрешён владельцем для пилота (2026-10-12).**
  Latest stable Pri-Fly повторно проверен: 0.13.76, новых выпусков нет.
  Новый aif-fix:package/fix@1.0.0; classic/profiled/fanout остаются прежними.
  Центральный каталог получает четвертую запись aif-fix и переводит четыре
  release pins на v1.51.0/exact commit. GitHub release — notes и ссылки на
  результаты; пилотная инструкция — docs/pilot-aif-fix-v1.51.0.md.
  Перед тегом: 24-case runtime matrix одним запуском, 10 static tests,
  verify/compatibility, 4 classic probes и route probe — PASS на stable 0.13.76.
  Issue #4 остаётся открытым на фактическую приёмку пилотом.

- **Issue #4, реализация отдельного aif-fix (2026-10-12):** новый пакет
  `aif-fix:package/fix@1.0.0` подготовлен локально, 42 файла. Основной путь:
  warmup → fix-task → check-change → enabled security → один review-task →
  commit. Escalation: native fix-plan → отдельное исполнение pinned aif-fix;
  ordinary plan/improve/implement/verify/challenge не требуются. Repair —
  отдельный workspace-write Attempt, затем повтор всех включённых гейтов;
  предел 1..8 раундов (default 3), на исчерпании partial с последним gate.
  Runtime decision fix_plan_execution не automatic; true/false preanswers и
  ожидание ответа с --yield-execution/drive на том же Attempt проверены.
  Native capture работает на каждом verdict: blocked planner оставляет
  INCOMPLETE draft, default удаляет engine после capture, custom staged/tracked
  сохраняется. Чужие PLAN/FIX_PLAN не удаляются и не исполняются.
  Security bridge/step получают собственные identities: classic-инструкция
  «нет repair после security» для нового графа непригодна. Общие upstream
  pointers/schema bytes сохраняют прежние ids/version. Classic/profiled/fanout
  byte-for-byte не менялись; derive_profiled --check зелёный.
  Compile-gate включает четыре пакета/три hosts/два fix profiles и отрицательные
  bindings/handler/effects fixtures. Compatibility и 10 static tests зелёные
  на stable 0.13.76. Classic probes pass, blocked→resume, cancelled→resume
  пройдены в границах существующего probe (до следующего handoff).
  Runtime: 24 разных сценария PASS (23-case matrix + focused limit/catalog
  checks); matrix и real-host observation см.
  tests/probes/results/aif-fix-0.13.76.md.
  Реальный короткий Run с AI Factory 2.19.0 дошёл до local commit/succeeded:
  два read-only Explore и свежий reviewer без авторского разговора. Точный
  model_profile выбрать не удалось; warning, не независимый model pass.
  Полный LLM маршрут escalation/repair/resume и автоматический replay custom
  tracked plan не объявлены проверенными. Два явных plan path profiles —
  default и custom; arbitrary paths требуют нового reviewed contract.
  catalog/aif-fix.yaml — подготовленная отдельная запись, search/add проверены
  локальным Git-каталогом. Remote/tag/центральный каталог не опубликованы;
  эта запись служит основанием переноса в ../prifly-workflows с release ref/commit.
  CI дополнен fix runtime matrix. Измерений экономии токенов/времени нет.
  Отчёт добавлен в issue #4 и сверен через API:
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6129483082.

- **Ворота выверены против выпущенного Pri-Fly `v0.13.76`:** до начала
  реализации aif-fix `verify.py` и `compatibility.py` — PASS на darwin/arm64.
  Архив проверен по release asset digest
  `98eeae48df326eb5108493bd2e24fde5d96505b4fffd2afb67ca260ef92a299c`;
  binary SHA-256 `5df5aceccde63c173d3f38f20426eb9dd131e6c3b0f6511a99002ad874a49f00`.
  0.13.76 доставляет optional launch advice/native choices в generated runner;
  public schemas, графы и Run contracts не меняются. Новому пакету нужны
  понятные title/description, пользователю — `project runners update` после
  binary update. Pri-Fly #3 закрыто с отчётом; Claude pagination/dismissal
  отдельно отложены и не считаются пройденными. Обязательных поправок classic
  нет. Владелец поручил реализацию отдельного fix workflow и runtime probes.

- **Ворота выверены против выпущенного Pri-Fly `v0.13.75` (2026-10-12):**
  `tests/verify.py` и `tests/compatibility.py` с `--binary` — PASS на
  darwin/arm64, архив GitHub release проверен по опубликованному SHA-256.
  Последний CI пакетов (2026-09-30) предшествует этому выпуску, поэтому
  сверка выполнена локально. Runtime probes в этой сессии не запускались.
- **Пропущенные Pri-Fly 0.13.72–0.13.75:** release bodies перечисляют только
  подписанные assets; детали сверены по истории тегов и release evidence в
  исходниках движка. 0.13.72 — прогресс программ (fd 4, `run progress`,
  хранилище 8); 0.13.73 — opt-in `live_output` / `output_limit_bytes` у
  executor (`execution-bindings/3`, состояние 43, хранилище 9, `run output`).
  Наши assisted-шаги этого не требуют; включение — дело проектных программ.
  0.13.74 — `project recover` повторно проверяет отвергнутый output по digest
  против исправленного контракта и сразу ведёт созданный Run. 0.13.75 —
  chained recovery/resume сохраняет унаследованные accepted evidence и outputs,
  работает от текущего владельца claim; исправляет второй continue с
  `resume_prefix_empty`. Новых authoring contracts/schema fields для пакетов
  эти recovery-правки не вводят. Обязательных правок пакетов не найдено;
  ничего не внедрено и отдельного package bump не требуется.
- **Issue #4 (первоначальная редакция, короткий путь внутри classic):** прочитано и сопоставлено с
  declarations; реализации нет. До реализации уточнить перенос проверки
  конфликта с требованиями из implement в fix-task; сохранность существующего
  `.ai-factory/PLAN.md` при общем commit; независимую сессию review-task;
  повтор проверок после repair (включая security, если правка затронула его
  предмет). Plan-specific preflight ответы при auto могут оказаться не
  использованы: маршрут определяется позднее, а `when` знает только profiles
  и preflight answers. Проверка новых bindings ниже; обе ветки до finish
  живьём, repair, escalation и resume пока не проверены.
- **Issue #4, сведение веток (2026-10-12):**
  `tests/probes/route_check.py --binary <released 0.13.75>` — PASS,
  `route-probe/` — отдельный compile-only пакет, не часть classic/profiled.
  Child выбирает planned/local_fix: обязательный `implementation` на обоих
  `succeeded`, native `plan` только на planned (`required_for: []` у child и
  root). Общий tail читает implementation и optional plan. Это компилируется
  без изменения core. Пять отрицательных вариантов — ожидаемые отказы:
  обязательный plan у child и пропущенный implementation — `missing_binding`;
  обязательный plan у tail/root и прямое сведение со ссылкой на producer
  planned — `unavailable_output`. CLI-код у всех —
  `project_compile_invalid_workflow`, flow-код и путь стоят в message.
  Package list до/после равен, Run не создавался, одна запись monitor удалена.
  Это не проверка отсутствия plan при runtime, capture execution или resume.
  Замечания и результат опубликованы с разрешения владельца в комментарии
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6123197914;
  сохранённый текст сверен через API. Фикстура пока локальная, не в main.
- **Issue #4, первоисточник aif-fix (2026-10-12):** прочитаны
  `lee-to/ai-factory` tag `2.19.0` (`e144f95c89de0d0cb6c9b38dbe8c2907b00dc5ce`),
  `skills/aif-fix/SKILL.md`, docs workflow/skills/plan-files/evolve.
  Skill blob `8317c8d998f4589e4bc80234ae182558e90d61e2` одинаков на теге и
  текущем `2.x` (`ac92bebd9bfef0f326c8581b77b29f74997e797c`). Upstream
  предусматривает самостоятельный bug intake: Fix now без плана; Plan first
  создаёт отдельный FIX_PLAN и останавливается; следующий aif-fix выполняет
  его. При HANDOFF_MODE=1 — Fix now по умолчанию, без вопросов и MCP sync.
  Существующий paths.fix_plan имеет приоритет даже над описанием новой задачи:
  bridge fix-task обязан явно ограничить это текущей задачей, а не только
  передать аргументы. Default FIX_PLAN удаляется после исполнения, custom —
  сохраняется. Regression-first допускает manual/runtime reproduction и
  safe-root-cause fallback при отсутствии полезной проверки; unconditional
  stop на unreproduced в issue — более строгая политика пакета, не upstream.
  Logging и self-improvement patch обязательны в base skill, project overlays
  имеют приоритет. Fix может исследовать через 2–3 Explore sessions; отсутствие
  plan не обещает единственную сессию. Auto triage, переход в общий planned
  маршрут и обязательный downstream review/security — решения Pri-Fly-пакета.
  Документация подтверждает исходное назначение Fix now для короткой ветки;
  реализация не менялась. По последующему поручению владельца выводы и таблица
  отличий опубликованы в issue #4:
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6123338025.
  Сохранённый текст сверен через API; ссылки закреплены на commit тега 2.19.0.
- **Issue #4, новый комментарий (2026-10-12):**
  https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6123457239
  принимает направление и уточнения, но меняет исходную эскалацию: сложный баг
  получает принадлежащий задаче fix-план (`paths.fix_plan` / FIX_PLAN или явно
  объявленный эквивалент), который затем исполняет именно `aif-fix`.
  Автоматического перехода fix → обычный plan/improve/aif-implement не должно
  быть. При адаптации сохранить workspace, исходный base, сделанную работу и
  evidence. Комментарий требует воспроизводимые runtime probes на released
  engine: обе ветки до commit/finish с capture/materialisation; fix-plan
  escalation; repair с актуальным implementation и повтором checks/security;
  остановка после fix/review, blocked/cancelled и chained resume с claims/work/
  evidence и проверкой свежести. Проектные TEST/MR вне upstream, совместимость
  через generic extension fixtures. В чате пока поручено прочитать комментарий;
  реализация и runtime probes этого маршрута ещё не выполнялись.
- **Новый вариант по предложению владельца (2026-10-12):** отдельный launch /
  пакет короткого пути вместо auto-развилки внутри classic. Предлагаемое имя
  `aif-fix`; пользователь выбирает workflow в существующем списке prifly-run.
  Classic/profiled остаются обычным development-маршрутом. Fix-path: warmup →
  fix-task → short checks → enabled security → task review → commit; сложный
  баг внутри того же fix workflow получает native fix-план и исполняется
  aif-fix. Repair возвращает к проверкам нового дерева. Root не требует обычный
  plan; fix-план — собственный артефакт bug workflow. Общие неизменные компоненты
  можно переиспользовать, commit требует bridge с безопасной уборкой только
  принадлежащих Run файлов. Рекомендация ИИ перед выбором — совет, не launch:
  текущий released runner показывает список и ждёт точный ID; правила совета
  можно сначала выразить в runner PROJECT.md. Последующее поручение о
  переработке issue выполнено ниже; реализация пока не начата.
- **Issue #4 переработано по поручению владельца (2026-10-12):**
  https://github.com/StenHigh/prifly-aif-workflows/issues/4 — новое название
  «Добавить отдельный workflow aif-fix с ручным выбором и советом ИИ перед
  запуском». Основной текст заменён целиком, прежние комментарии сохранены как
  история. Auto-selector внутри classic снят; новый пакет/launch выбирает
  человек, classic/profiled сохраняют графы. Escalation через native fix-план
  с исполнением aif-fix, repair с повтором checks/enabled security/review и
  blocked/cancelled/chained resume сохранены в критериях runtime-приёмки.
  Совет до запуска выделен в связанную задачу движка:
  https://github.com/StenHigh/prifly/issues/3 — общий generated prifly-run,
  current host session, declared launch metadata, короткое обоснование и
  ожидание ручного выбора; без hardcoded AI Factory и автоматического start.
  Обе сохранённые пары title/body сверены через API. Код workflow/runner не
  менялся; прежние compile probes не считаются реализацией нового маршрута.

- **Выпуск v1.51.0:** отдельный aif-fix 1.0.0 и четвертая запись
  каталога; classic/profiled/fanout без изменения байтов и версий. Приёмка
  полного LLM-маршрута — пилот.
- **Предыдущий выпуск:** тег `v1.50.0` — `changed_files` до 10 000 путей
  (classic 1.47.0, profiled 1.48.0). До него v1.49.0 — classic/profiled на
  `core:policy/local@4.0.0` (допускает `external_write` для проектных вставок;
  просьба движка ради шага `tests` пилота с Docker). classic 1.46.0, profiled
  1.47.0, fanout 1.4.0 (на 3.0.0, вставок в него нет). v1.48.0 — security
  читает дерево Run (`repository_workspace: read_only`). v1.47.0 — возобновление тем же workflow (`resumable`, ревизия 8). Пакеты продолжения и программа `resume` на Node удалены (владелец:
  workflow — только инструкция). До v1.51.0 каталог содержал три записи.
- **Pri-Fly 0.13.71 (2026-09-30):** ворота зелены. Программы разных Run одной
  authority идут одновременно; `extend.yaml` получил `resources` (проектные
  исключительные ресурсы, `resource_busy`) — пакету объявлять нечего, пилоту
  пригодится для Docker-стека `tests`; хранилище — версия 7.
- **Push и MR (2026-09-30, предложение пилота):** в пакет не берём —
  `merge-request` проектная вставка, push/MR проектно-специфичны, пакет только
  инструкция. Совет пилоту: push — программа `external_write` / `idempotent`,
  MR — отдельный шаг `reconcile_required` с обязательным выходом-ссылкой.
- **Pri-Fly 0.13.70 (2026-09-30):** ворота зелены (все режимы `run_check.py`,
  вставка с external_write). `basis: decision` принимает и ключи
  decision_context; поле отчёта внутри `result` — отказ с `/result/<поле>`;
  `session submit --template` пишет про answered_questions в stderr (проба
  читает stdout — не задевает). Пакет не менялся.
- **v1.50.0 (2026-09-30), находка пилота:** implement не сдавал правку на 282
  файла — `changed_files` maxItems 200 (`/changed_files … at most 200 items`),
  владелец сдал `fail` → `rejected`. Предел поднят до 10 000 (артефакт — файл,
  лимит отчёта 1 МБ его не касается; гейты судят дерево). Маршрут `blocked` для
  implement не вводили. Замер на 0.13.69: Run v1.49.0 отвергнут так же;
  после обновления `project continue` без `--from-stage` переносит warmup/plan/
  improve, implement сдаёт 282 файла, дальше verify/security/review.
- **Pri-Fly 0.13.69 (2026-09-30):** Run с ассистируемым шагом — core-state/41,
  отчёт хоста обязан нести `answered_questions` (пустой список = вопросов не
  было), иначе `answered_questions_missing`; поле — на верхнем уровне отчёта, не
  в `result`. Проба (`run_check.py`) отдаёт `[]`, когда задача несёт
  `question_report: required`. Мосты не менялись: запрета записывать ответ в них
  нет, `improve_apply` из `decision_context` хост отчитывает `basis: decision` по
  инструкции раннера. Ворота зелены на 0.13.69.
- Ранее: последний стабильный 0.13.68 (ворота и вставка с external_write
  зелены на нём, 2026-09-29; 0.13.68 — `run next` core-next/42 с
  `awaiting_host` вместо `idle`, нас не касается; старт сам выводит старые
  издания при нехватке бюджета 512). Ранее: 0.13.67 (
  0.13.67 — отказ `recover_prefix_changed` называет первую изменившуюся стадию и
  подсказывает `--from-stage`). С 0.13.66:
  программа может объявить `external_write` (контракт шага 14,
  `program_external_write`), `retry_class: idempotent` для неё допустим;
  минимальный для classic/profiled — 0.13.64. Найдено пробой: до v1.48.0
  задача security не называла дерево Run (`repository_workspace` пуст), в
  worktree хост аудитил исходную копию. `run_check.py --verdict pass` теперь
  проводит Run через security и требует дерево; на v1.47.0 краснеет.
- **Смена политики и старые Run (замер 0.13.65):** Run, начатый на v1.48.0,
  после обновления до v1.49.0 возобновляется отказом `recover_prefix_changed:
  effective contract changed at stage improve` (с 0.13.67 дописано `; resume
  with --from-stage improve to run it and everything after it again`); с
  `--from-stage improve` —
  стартует, improve и implement заново. Причина названа верно (движку сообщено).
- **Внешняя запись проектной вставки (замер 0.13.66):** шаг-программа
  `prifly-step/1` с `effects: {class: external_write, retry_class: idempotent}` и
  `external_write: {system, operations, target}`, вставленный между review и
  commit, на v1.49.0 собирается (контракт 14) и стартует; на v1.48.0 старт —
  `…pinned policy 3.0.0 admits none, workspace_write; the workflow that admits
  it pins core:policy/local@4.0.0 or later`. Отдельного теста нет: откат
  политики ловит `verify.py`. Ворота зелены на нём: пять + `run_check.py` pass, blocked, `--resume`
  (blocked→verify), `--resume --verdict cancelled`; все в CI.
- **Задание пилоту** (`SMSPlace/PRIFLY-MERGE-REQUEST-STEP-PROMPT.md`, ведёт
  движок, передаёт владелец): выполнено пилотом на v1.47.0 + 0.13.62; догоняющее
  — v1.48.0 + 0.13.64 (`workflows update`, больше ничего). Возобновление:
  `project continue --launch aif-classic --source-run RUN --host HOST`
  (`--prepare`, затем `--expected-launch-digest`).

### Возобновление (v1.47.0)

- На корне classic: `resumable: {from_outcomes: [partial, rejected],
  from_cancelled: true}`. `project continue --launch aif-classic --source-run
  RUN`: точка — стадия, приведшая к finish (у отменённого — отменённая), префикс
  переносится (warmup, plan, improve, implement), дерево передаётся, verify —
  первая выданная задача. `fork.reason: resume_stopped_run`,
  `recovery.reused`.
- Свежесть реализации — инструкцией: мосты verify/security/review судят дерево
  и HEAD, изменённое — `git diff <base_commit>` + неотслеживаемые.
- На 0.13.61 возобновление требовало `workspace:` у launch и повторных ответов
  анкеты; 0.13.62 берёт режим дерева и ответы из исходного Run. `--host`
  передаётся всегда (без него `project_compile_host_required`); `--workspace`/
  `--input` при возобновлении — `resume_input_override`.
- Механизм `continuation` (0.13.58) остаётся у движка для продолжения ДРУГИМ
  workflow; у нас не используется. Прежняя версия с хвостами — тег v1.46.0.

### `blocked`: как устроено (v1.45.0)

- verify, security, review на `core:schema/step-result@2.0.0`,
  `gate.required_for: [pass, needs_revision, blocked]` → шаг поднимается до
  StepDefinition v10 (только assisted-шаг `prifly-step/2` может обещать выход на
  ребре `blocked`; программному — отдельное изменение движка, никто не просил).
- Корень, `verify-once`, `review-once` — WorkflowRevision v6; прочие графы и
  fanout — v4. Узлы без гейта: `impossible_verdicts: [blocked]` (их контракт
  результата 1.0.0 сам отвергает `blocked`).
- `blocked` не зацикливается: круг на ту же стадию ограничен только бюджетом Run
  и кончился бы `budget_exhausted`. В once → finish `rejected` с gate → batch
  `standing` (partial) → корень `fix-after-*`; security → `security-blocked`.
  Повтор — `prifly project continue`.
- Мосты различают подтверждённое падение, неполную acceptance evidence и
  недоступную зависимость; третье — `blocked`, `gate.status: blocked`.
- Вставки из `extend.yaml` в корень v6 обязаны ответить за `blocked`; правка и
  обновление — один коммит (на v1.44.0 та же строка отвергается). README,
  «Обновление до v1.45.0» — замер обоих отказов.
- Движок довёл `blocked` за семь выпусков (0.13.49–0.13.55); шесть дефектов
  нашли мы по опубликованному бинарю: ревизия 6 не объявлена, `required_for`
  без `blocked` (дважды), `project compile` опускал шаг в базовый контракт,
  выдача Attempt, приём отчёта; седьмой (`run explain` не называл ребро у
  `call`-стадии) движок нашёл, доведя наш стенд до конца. Урок: проверка, кончающаяся на первом handoff,
  не видит рантайм — отсюда пятые ворота.

## План

0. ~~Продолжение внутри того же workflow~~ — сделано в v1.47.0 на 0.13.61.
   Обходы 0.13.61 сняты на 0.13.62 (проба без них зелёная).
1. ~~Ждём выпуск движка с приёмом `blocked`~~ — закрыто 0.13.55 (2026-09-25):
   проба в обе стороны в CI, каталог на v1.45.0.
2. ~~Пилот переходит на v1.47.0~~ — выполнено; догоняющее обновление до v1.48.0 + Pri-Fly 0.13.64. Прежняя формулировка:
   `workflows update aif-classic`, `impossible_verdicts: [blocked]` во вставки
   `tests` и `merge-request`. Разбирать отказы — по дословному тексту.
3. **Живая проверка `blocked` исполнителем** (настоящий хост, база выключена):
   gate `status: blocked`, `run explain` называет ребро, затем `project
   continue`. Только по слову владельца; можно совместить с п. 5.
4. **Разбор первого захода пилота на v1.45.0:** не путает ли гейт `blocked` с
   падением, доходит ли причина до владельца.
5. **Долг движку: `local-context/3` на профилях `full` и `ultra`** (обещано
   2026-09-17, `fast` закрыт). Манифест рабочей копии должен нести объявленные
   `workspace_trees` целиком; наш пакет — единственная сборка, где три вида
   захвата переключаются профилем. Живые заходы — по слову владельца.

## Что здесь лежит

- `aif-classic/` — канонический маршрут AI Factory: разогрев, планирование,
  доработка плана, реализация, verify, security, review, фиксация, починка.
- `aif-fanout/` — необязательная параллельная доработка плана.
- `aif-profiled/` — classic, порождённый `tools/derive_profiled.py`: каждый шаг
  несёт `model_profile`, plan/implement просят отдельную сессию. Руками не
  правится — только перегенерацией; `test_folders.py` это держит.
- `tests/` — пятеро ворот, те же, что гоняет `.github/workflows/verify.yml`:
  - `test_versions.py` — версии сдвинулись вместе с байтами (нужна полная
    история, в CI стоит `fetch-depth: 0`);
  - `test_folders.py` — статический контракт папок и закреплённые хэши навыков;
  - `verify.py --binary <prifly>` — компиляция обоих пакетов настоящим
    бинарником; пинит количество компонентов, а анкету и каталог решений
    спрашивает по `id`, не по индексу. Ничего не импортирует и не запускает —
    в конце стоит `before == after` по `package list`;
  - `compatibility.py --binary <prifly>` — одна authority ведёт Classic по
    Fast → Full → Ultra → default → Fast со своим `extend.yaml` и разными
    байтами host skills; каждый вариант импортируется и запускается; плюс один
    старт `aif-profiled` — версия состояния запечатанного Run (≥ 35) и перевод
    профиля в первой задаче;
  - `probes/run_check.py --check` (pass, blocked, `--resume`, cancelled→resume) — живые ворота (с 2026-09-25):
    настоящий Run, хостом выступает сам скрипт, проходит verify и получает
    следующий Attempt. Первые четыре кончаются на первом handoff и не увидели,
    что 0.13.53 не выдаёт verify задачу у v1.45.0.

## Правила устройства, которые стоили по прогону пилота каждое

- Автономный прогон отвечает на объявленное решение сам только если оно
  `automatic`, `sensitivity: ordinary` и несёт `recommendation`. **Не покупать
  этим ночь.** С Pri-Fly 0.9.0 владелец запечатывает ответ при запуске:
  `project start --runtime-answer ID='<JSON выбранного choice>'`; мост
  применяет его раньше автополитики и пишет источником `actor`.
  `improve_apply` носил пониженную метку ровно два релиза (1.8.0–1.9.0) и
  возвращён к `automatic: false` / `scope-changing`; перевёрнутый тест в
  `verify.py` теперь стережёт отсутствие этих трёх свойств.
- Мост не перечисляет ключи `decision_context` поимённо: перечень устаревает и
  молча теряет ответ владельца. Инструкция — читать всю карту.
- Закрепление навыка не тянет его `references/**`: каждый файл объявляется
  своим контекстом, иначе отказ на компиляции (это лучше, чем исполнитель,
  застрявший посреди прогона).
- Шаг, который отчитывается и заканчивается, спросить не может: `aif-fix`
  берёт `HANDOFF_MODE=1` при любой политике; планирование и реализация — только
  когда `decision_sheet.decision_policy` = `autonomous`, и умолчания режима
  никогда не перебивают объявленный ответ.
- `gate_warnings: fix` безопасен только там, где предупреждения гейта
  ограничены вносимым изменением; постоянный общепроектный WARN уводит прогон
  за пределы задачи.
- Выходной слот со `schema_ref` компилируется в `format: json` сам, и байты
  проверяются при приёме. Объявлять формат руками не нужно; отчёт, который
  говорит, что байты не проверяются, проверять компиляцией.
- Версия компонента — его личность для потребителя. Один релиз отдал разные
  байты под той же версией (`aif-fix-bridge@1.0.0` в v1.6.0 и в v1.7.0),
  поймал это пилот, а не мы; сторож поставлен в v1.9.0.
- Каждый шаг, который запускает закреплённый навык, нуждается в собственном
  мосте. У `security` его не было десять релизов: `instructions_ref` указывал
  прямо на навык, и шаг не знал ни про `gate_warnings`, ни про то, кто выбирает
  следующую стадию, ни про запрет писать — при том что навык несёт `Write` и
  `Edit`, а шаг объявляет `effects: {class: none}`. Движок отверг бы байты, но
  исполнитель узнал бы об этом, уже потратив сессию. Мост добавлен в 1.11.0.
- Мост описывает то, что делает граф, а не то, что звучит согласованно. У
  `security` `gate_warnings: fix` и `stop` делают одно и то же: шага починки
  после него нет, и блокирующий результат завершает прогон как `partial`.
  Скопировать туда формулировку verify/review значило бы пообещать починку,
  которой не будет.
- Правило добавляется туда, где его можно нарушить. Абзац про отдельные
  ревьюерские сессии ушёл в `aif-review-bridge` (у навыка есть `Task`/`Agent`)
  и намеренно не ушёл в `aif-verify-bridge`, где таких инструментов нет.
- Проверка, записанная в план, должна быть исполнена на том дереве, для
  которого пишется, с чтением вывода и кода возврата. Три захода подряд
  следующий шаг чинил не суждения предыдущего, а исполнимость его команд:
  шесть дефектов из семи в четвёртом заходе — команды, ни разу не запущенные.
  Правило в мосте планирования с 1.12.0.
- Хэши апстрим-навыков в `INVENTORY.md` — запись происхождения, а не сторож.
  Навыков в репозитории нет, CI компилирует по заглушкам, сверить их нечем;
  тест в `test_folders.py` держит только то, что запись не потеряли, и говорит
  об этом прямо. Сверяя такой хэш вручную, называть дерево, **и называть его
  себе, а не в публичной записи**: 2026-09-06 я снял хэши не в том чекауте и
  объявил расхождение, которого не было. Из чужого проекта сюда попадают только
  обезличенные факты — имена веток, каталогов и коммитов чужого репозитория
  остаются в переписке.
- **Каждый шаговый узел объявляет обработчик на каждый вердикт, который его шаг
  может вернуть.** Принятый вердикт без обработчика движок считает
  `unhandled_verdict` и роняет прогон целиком: у пилота гейт вернул
  `needs_revision`, потому что при блокирующих находках `pass` показался
  нечестным, и шесть пройденных шагов пропали. Ловушка стояла ещё на разогреве,
  планировании, реализации и фиксации. С 1.15.0 второй обработчик есть везде, а
  `verify.py` проверяет это на каждом узле всех трёх графов.
- Вердикт гейта — `pass` всегда; блокирование едет полем `blocking` артефакта,
  которое читает следующий узел. Исполнитель графа не видит и выбирает вердикт
  из общего перечня `StepResult`, так что защита от ошибки — только текст моста.
  Поэтому же артефакт `gate` обязателен и для `needs_revision`: гейту, который
  не смог заключить, всё равно есть что сказать, и обработчику есть что связать.
- Часовой предел работы шага — умолчание для того, кто не объявил своего, а не
  закон движка. Объявленный `active_timeout_ms` его заменяет. Владелец не хочет
  ограничений по времени вовсе (его сессии доходили до восьми часов), поэтому с
  1.14.0 каждый шаг объявляет тридцать суток. Число не оценка работы: оно
  существует, чтобы час не действовал, и держится далеко от предела
  представления, где миллисекунды в наносекундах подходят к переполнению int64.
  Следствие принято осознанно: зависший шаг сам не умрёт, его снимает
  `run cancel`.
- Мост называет цену вердикта, а не только его имя. У проверки `pass` с
  поднятым `blocking` **запускает** круг починки, а `needs_revision` его
  пропускает: осторожный на вид вердикт выключает ремедиацию. У починки
  `needs_revision` завершает весь прогон — ни безопасности, ни обзора, ни
  фиксации, ни вставленных проектом шагов. Ни то, ни другое из формы шага не
  выводится, пилот дописывал это в брифинг руками каждый заход; в мостах с
  1.16.0.
- Раздел приёмки, перечисляющий собственный диф, протухает от собственного
  коммита. У пилота план объявлял семь файлов, а после коммита починки их стало
  девять. Планированию сказано писать такой раздел выводимым из дерева, с
  командой вывода; починке — перевыводить числа после своего коммита и
  говорить об этом в сводке. Форма ответа найдена пилотом и сильнее исходной
  формулировки: **пин берётся по закрытому диапазону или неподвижному
  множеству** — два фиксированных хэша, явный список путей, — но не по
  `base..HEAD`. Их пин 851 файл / 581 коммит между двумя хэшами пережил
  собственный коммит и остался буквально верным.
- Цикл должен уметь остановиться, когда следующий круг ничего не изменит.
  `blocking` не различал «остались чинибельные блокеры» и «остались только
  владельческие»: у пилота три блокера были неисполнимы **по построению**
  (гейт, невозможный на их ветке; норма, называющая несуществующий валидатор;
  решение владельца), и цикл выгорел до лимита, потратив два круга и сорок
  минут. Хуже потери времени — доложенная причина: `exhausted` говорит «круги
  кончились», тогда как остаток не был нашим. С 1.17.0 `gate-result` несёт
  `blocking_owner_only`, циклы проверки и обзора ветвятся на нём в исход
  `owner-decides`. Поле смещено в сторону продолжения: один чинибельный блокер
  делает его ложью, а ошибка в безопасную сторону останавливает цикл и
  показывает находки человеку.
  **Механизм закрывает не тот случай, который его породил.** Пилот пересчитал
  свой шестой заход по определению поля: во всех трёх кругах оно было бы
  ложью — рядом с тремя владельческими блокерами каждый круг находилась одна
  чинибельная мелочь, и каждый раз новая, порождённая предыдущим кругом. То
  есть у них не «остался только владельческий остаток», а «владельческий
  остаток соседствует с непрерывно порождающимся чинибельным», и лимит
  по-прежнему связывает. Возможный поток находок был следствием
  самореферентного артефакта и может иссякнуть от правила про закрытый
  диапазон; возможно, полезнее мерить не остаток, а возраст блокера («висит с
  круга N»). Оба варианта — догадки, мерить седьмым заходом, а не рассуждением.
- `.ai-factory/PLAN.md` — рабочее состояние прогона, а не история проекта:
  шаг фиксации его удаляет, коммитить ради записи не нужно. Ответ был только в
  мосте фиксации и оттого выводился по-разному; с 1.16.0 сказан также в
  проверке и починке.
  Подтверждено с обратной стороны на седьмом заходе пилота: план от шестого
  захода остался в дереве, и седьмой не смог начать планирование — шаг объявлен
  создающим этот файл, а байты, которых он не создавал, движок не перезаписывает
  (`workspace_tree_output_exists`). То есть эфемерность не пожелание, а условие
  следующего прогона: план, переживший свой заход, блокирует следующий.
- Пример, который лежит закомментированным, компилятор не видит: он протухает,
  пока двигается контракт, и никто не замечает. Перевод на v4 обновил фикстуру
  в `compatibility.py` и не тронул шаблон вставки в поставляемом `extend.yaml`,
  то есть единственный пример, который люди копируют, стал ровно той формой,
  которую компилятор отвергает. Нашёл пилот, раскомментировав его. Починено в
  1.19.0, и `test_folders.py` теперь читает эту строку и требует в ней все
  четыре вердикта.
- **Версии компонентов на каждом релизе двигать не нужно, и это не помогло бы.**
  Под профилем `prifly-project-profile/3` версия скомпилированного компонента
  выводится из ключа сборки **всего пакета** плюс вида и авторской ссылки
  (`cmd/prifly/project_build.go:73`), а ключ сборки покрывает пакет целиком.
  Поэтому комментарий в `extend.yaml` переименовывает все компоненты, включая
  схемы без единой ссылки: между `v1.18.0` и `v1.19.0` так «дрейфануло» 25 из
  59, и это нормальная работа формулы, а не расхождение. Авторская версия в
  запечатанном виде под `/3` вообще не хранится — она живёт в
  `build-provenance.json` как `author_ref`, а `package inspect` показывает
  build-key.
  Отсюда же понятно, что `test_versions.py` на исходниках — правильный уровень
  проверки, а сводить компоненты по авторской версии нельзя: под `/3` она даёт
  ложное срабатывание на каждом релизе.
  Под профилем `/2` всё иначе, и это состояние живых проектов: компоненты
  запечатываются под **авторскими** версиями, поэтому authority с прошлым
  прогоном упирается в `definition_drift` при любом обновлении пакета, а
  `package remove`/`revoke` не помогают — инвентарь держится отдельно. Чистая
  authority спасает не сменой профиля (профиль берётся из репозитория задачи и
  остаётся `/2`), а тем, что инвентарь пуст; обход одноразовый, второе
  обновление в той же authority упрётся снова. Измерено пилотом 2026-09-07.
- Проверка, чей ключ выведен из того же, что она проверяет, всегда зелёная. Я
  построил сторож, сводивший компоненты по build-key, и он не мог упасть в
  принципе: build-key меняется вместе с байтами. Поймано отрицательной
  проверкой — строка в мосте без смены версии, сторож зелёный, — сторож удалён,
  вывод из него отозван у пилота. Строить сторож без проверки на падение
  нельзя.
- Потолок кругов в цикле — восемь, умолчание остаётся три (`round-limit.yaml`
  `maximum: 8`, `max_iterations: 8` в четырёх пачках). Раньше стояло три, и
  проект поднять их не мог — настройка была, а хода у неё не было; это и есть
  причина правки.
  **Формулировка коммита `a1fea6e` при этом неверна, и её не следует
  повторять:** шестой заход пилота кончился `partial` не по исчерпанию кругов.
  Числа 28 → 24 → 9 падали за счёт закрываемых находок, а `blocking` держали
  три владельческие, которые `fix` закрыть не вправе (неисполнимый на их ветке
  гейт, требуемые нормой машинные строки, несуществующий валидатор). С восемью
  кругами тот заход кончился бы тем же `partial` на сорок минут позже. Поправку
  прислал пилот, пересчитав по определению `blocking_owner_only`. Выше восьми не уйти без
  торга с политикой: `core:policy/local` разрешает Run 256 экземпляров шагов и
  1024 перехода, и лимиты каждого графа обязаны покрывать вложенные пути —
  цепочка `improve-once → improve-batch → improve-series → improve-or-pass →
  classic` подогнана под этот бюджет. Проверено не компиляцией, а живым
  стартом Run с запрошенными восемью кругами.
- Поднимая версию контекста или схемы, поднимай версию каждого шага, который на
  них ссылается, и каждого workflow, который называет такой шаг: шаг запечатан
  вместе с байтами того, что он вшивает по digest. Наша собственная практика
  двигать версию моста и оставлять шаг и породила `definition_drift` у пилота —
  пять шагов «сменили байты», не имея ни одной правки в своих файлах. Правило
  сформулировал пилот, сторож стоит в `test_versions.py` и называет и файл, и
  ссылку.
- Решение владельца (2026-09-07, через пилота): **эксперименты пилота не видны
  посторонним** — ветки заходов не пушатся, MR не вливаются, и пилот пока не
  берёт продуктовых задач. Отсюда правило чтения их отчётов: находка про
  продуктовую ветку — наблюдение для владельца, а не задача следующего захода.
  Пакет этому уже соответствует и проверено, а не предположено: ни один шаг
  обоих пакетов не объявляет `external_write` — только `none` и
  `workspace_write`, — а мост фиксации прямо запрещает push и называет его
  отдельно допускаемым эффектом. То есть маршрут не может опубликовать ничего
  даже по ошибке исполнителя.
- **Мост самодостаточен: он не отсылает исполнителя наружу за правдой.** Если
  исполнителю нужно что-то знать, это написано в мосте, а не в ссылке на
  определение шага, схему или команду чтения. Проверено измерением: ни один наш
  мост не упоминает `package inspect` и не велит смотреть определение, поэтому
  движковая ловушка — `package inspect --component` без `--ref` отдаёт компонент
  чужой редакции пакета — нас не задела вовсе, а пилота задела ровно там, где он
  сам написал в брифинге «настоящий контракт в определении шага». Инструкция,
  отсылающая наружу, ломается тогда, когда наружное состояние неоднозначно.
- Граница пакета: `aif-classic` воспроизводит канонический маршрут AI Factory,
  поэтому шаг, которого нет выше по течению, сюда не берётся, каким бы полезным
  ни был. Шаг пилота `merge-request` отклонён 2026-09-04 по этой причине и
  живёт у них через `extend.yaml`.

## Порядок релиза

1. Правка → все пятеро ворот локально; последние три требуют выпущенный
   бинарник (`--binary …`; `~/.local/bin/prifly` бывает dev-сборкой — сверять
   `prifly version`).
2. Сменились байты — двигаются и версия компонента, и `package.version`, и
   версия workflow. `test_versions.py` не даст забыть.
3. Коммит → аннотированный тег `vX.Y.Z` → push ветки и тега по HTTPS с
   `-c credential.helper='!gh auth git-credential'` (SSH-ключ на этой машине —
   `dzianis-87`, а репозитории StenHigh).
4. Перевести каталог `../prifly-workflows/catalog.yaml`: все записи этого
   репозитория, `ref` и `commit`, затем push.
5. Прогнать `tests/probes/run_check.py` на выпускаемом дереве, если менялось
   то, что объявляет шаг гейта: ворота кончаются на первом handoff.
6. Сессий пилота нет: что меняется на их стороне, владелец передаёт им сам —
   дать ему текст. Движку — через `ListAgents` (сейчас `pri-fly`).

## Открыто и на заметку

- С 0.13.61 `run next` завершённого или отменённого Run включает в
  `continuations` его собственный workflow, если тот `resumable`, и предлагает
  `project.continue`.
- **Бюджет определений 512** с 0.13.68 освобождается сам: старт выводит самые
  старые trusted-издания того же пакета (не держимые незавершённым Run, не
  самое новое из прежних), `retired_editions` в ответе старта;
  `dependency_limit` — только если выводить нечего.
- `run explain` → `finish.verdict` у ребра из `call`-стадии несёт **исход**
  дочернего workflow, у `step` — вердикт шага; поле опубликовано (`core-next/36`)
  и не переименуется. Какой словарь — решает стадия `from_stage_id`.
- Обещать выход на ребре `blocked` может только assisted-шаг (`prifly-step/2`,
  контракт v10). Программный гейт с findings на `blocked` — отдельное изменение
  движка, заказывать при появлении такого гейта.
- Инструкция по обновлению со вставками есть и у движка —
  `examples/troubleshooting.md`, раздел про `missing_handler … /on/blocked`.
- Всё, что за verify, ни одними воротами не исполняется: `run_check.py` отвечает
  до verify и на `pass` останавливается на следующем гейте. Review, commit, fix и петли
  починки живьём видели только заходы пилота.
- Замеры пилота: разогрев 5–11 мин, планирование 12, доработка 12, реализация
  11–15, гейт проверки 10, повторный оборот 18 — разброс внутри шага почти
  вдвое. Довод против любого выбранного предела времени.
- Бандл `aif-improve`: без `+check` работают два файла из четырёх
  (`check-mode` и `validator` навык велит не открывать). Замечание, не дефект.
- Справка движка (`examples/authoring/workflow-authoring-reference.yaml`)
  ссылается на раздел README «Вердикты и WorkflowRevision v4», закреплённый на
  `98fd856`; раздел с v1.45.0 называется «Вердикты: WorkflowRevision v4 и v6».
