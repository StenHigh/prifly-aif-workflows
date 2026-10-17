# E6 — Настоящий Pri-Fly Light

Статус: **open / requested, не реализован и не развёрнут**.
[Pri-Fly #11](https://github.com/StenHigh/prifly/issues/11), приоритет P1.
Реализация — в репозитории Pri-Fly; в aif-workflows хранится issue/handoff.
Ниже сохранён опубликованный issue body. Production acceptance является
отдельным этапом после supporting release; новый домен пока не означает Light.

## Проблема и ожидаемый результат

Нужен **настоящий Pri-Fly Light**: отдельный простой интерфейс задач и результатов
ревью, вдохновлённый [Software Factory dashboard](https://github.com/zazencodes/zazencodes-season-3/tree/main/src/software-factory-claude-code).
На первом экране пользователь видит работу и результат приёмки, а техническую
диагностику открывает по необходимости в полном monitor.

Сейчас оба запущенных monitor0.13.79 (один со scan-root, другой без) отдают один
HTML. Отсутствие filesystem scan меняет discovery/нагрузку, но не создаёт Light UI.
Ранее выпущенные E1/#4 board и E2/#5 queue — необходимые primitives, **не готовый
отдельный продуктовый интерфейс**. Этот issue закрывает именно оставшийся UI gap;
не переоткрывает принятую runtime qualification E1/E2.

Ожидаемая production точка входа владельца:
`https://prify-light.stenhigh.net/` (точное написание). Полный monitor остаётся
на `https://prifly.stenhigh.net/`. Домены — deployment configuration, их нельзя
зашивать в Core. Внешние адреса сейчас защищены существующим reverse proxy;
новая поставка должна сохранить эту границу, без отключения authentication.

База: latest stable **0.13.79**, проверен2026-10-17. Пользователь просит отдать
реализацию Pri-Fly. Пакеты/канонический workflow в consumer repo не менять.

## Первая версия: отдельная read-only доска

- Компактные карточки с человеческим названием задачи, проектом, понятным этапом,
  причиной ожидания/остановки, текущим round и итогом. Технические IDs вторичны.
- Простая очередь задач, включая queued task **до первого Run**, и выполняемая/
  проверяемая/завершённая работа. Использовать существующие native task queue
  records и associations. Не создавать вторую очередь в board.json/Markdown.
- Task identity и recorded associations группируют связанные Runs/continuations.
  Один task не размножается визуально при continue; история и исходные outcomes
  остаются доступны. Не связанные Runs с одинаковым title не склеиваются.
  Для самостоятельного Run без queue/task association — явная fallback карточка.
- Пример представления: «Очередь → План → Реализация → Ревью → Готово», отдельная
  заметная группа «Нужно участие». Это UX-ориентир, не новая машина состояний.
  Для generic workflow фазу выводить из declared mapping/достоверной metadata,
  с fallback «В работе/этап не сопоставлен» вместо угадывания по имени/логу.
- Результаты review читаются на карточке: security/code/UI/UX **когда они включены**,
  статусы и краткие findings; по клику подробности и источники. Не требовать
  четыре reviewer для backend/generic workflow и не добавлять новые readers.
- Search/project filters, счётчики, empty/loading/error states, свежесть данных,
  desktop/mobile и keyboard. Приоритет — простой повседневный обзор.
- Ссылка из карточки в существующий полный monitor на **тот же authority/Run**,
  с настраиваемым full-monitor base URL и корректными encoded query parameters.
  Graph, traces, raw payloads, timing и storage diagnostics не доминируют в Light.

Конкретный UI sketch и read projection оформить в Core change до реализации.
Можно переиспользовать backend/components, но нужен отдельный Light entry/route
или явно выбранный mode с другим первым экраном. Смена домена, темы, page title,
режима discovery или второй listener сами по себе не выполняют эту задачу.

## Источники результатов и границы смысла

Review chips должны иметь recorded provenance: lens, candidate/round, gate/report
identity и freshness. StepResult `pass` может означать usable report при
`gate.status=blocked`; он **не является** доказательством успешного review.
Различать passed/defect/unavailable/waiting/disabled-or-not-applicable/unknown-stale
по фактическому контракту. Отсутствие отчёта не равно PASS или enabled review.

Для W1/W2/W5 consumer предусмотреть явное declared projection/mapping typed
reports/gates в UI, либо другой документированный generic contract. Не сканировать
случайные файлы, не hardcode namespaces AI Factory в runtime и не угадывать verdict
по prose. Если producer не публикует достаточные данные, показать «нет данных»,
а требуемый optional mapping описать явно. Не синтезировать model/session независимость.

После repair предыдущий PASS не действует на новом candidate. Native Run success
не означает merge/deploy: колонка «Готово» описывает именно recorded scope.
Несколько parallel ветвей и mixed review outcomes показываются без ложного
единственного активного шага. Partial/blocked/cancelled/uncertain различаются.

## Лёгкость и read API

Light переиспользует authoritative read models: bounded projection task/Run/review
summary, pagination, разумный polling/incremental updates. Главный экран не должен
качать workflow graphs, полные event traces, все artifact bodies и всю историю
на каждом обновлении. Нет обязательного filesystem scan. Большой backlog не
усекается старым общим лимитом200; UI явно показывает страницу/общее количество.

Нужные новые read-only endpoints/contracts допустимы как additive Core capability.
Если часть summary невозможна без дополнительного contract, описать его и source
provenance, не подменять факты UI-эвристикой. Inaccessible/stale source виден отдельно,
не обнуляет остальные проекты. Один source response использует согласованный cut;
между authorities показывать их собственную свежесть, без выдуманного общего cut.

## Что не входит

- Изменение существующего полного monitor, его default route/поведения или
  принудительная миграция пользователей в Light. Нужны regression tests его UI/API.
- Любые правки upstream **aif-classic/aif-profiled**, workflow defaults, skills,
  авторского repair/commit и package versions ради визуализации.
- Ненативные запускаемые из frontend `project start`, auto-continue/approve,
  auto-merge/push/MR, drag-and-drop изменения runtime states, собственный scheduler.
- Новая writable control plane или внешняя multi-user authentication система:
  v1 read-only, за существующим защищённым proxy/loopback boundary.

## Критерии приёмки

- [ ] **E6-A1 — Настоящий Light:** browser comparison на одном наборе данных
  показывает отдельную компактную доску по Light URL и прежний full monitor
  по старому URL. Отдельный entry/mode выбирается документированно; это не
  одинаковый frontend с другим названием/портом или скрытым scan-root.
- [ ] **E6-A2 — Задачи и Runs:** queued task без Run виден; start→partial→continue
  показывает одну task с recorded текущими Runs и историей. Forks, orphan Runs,
  одинаковые title и разные authorities не объединяются эвристикой.
- [ ] **E6-A3 — Этапы:** shipped feature и generic fixture отображаются по
  documented mapping/fallback. Awaiting decision/resource, failed/partial,
  cancelled/uncertain и completed различимы; название этапа не выдумывает outcome.
- [ ] **E6-A4 — Ревью:** реальные typed fixtures проверяют pass-report+blocked gate,
  defect, passed, optional skip/disabled, pending, missing и invalid/stale reports.
  Нет ложного PASS. Backend не получает фиктивные UI/UX проверки; источник
  статуса/краткие findings и raw report доступны без prose inference.
- [ ] **E6-A5 — Repair/parallel:** после candidate change старые chips помечены
  stale/историческими до fresh acceptance; разные rounds не смешиваются.
  Parallel mixed outcomes и owner blockers не становятся «всё готово».
- [ ] **E6-A6 — Navigation/UX:** поиск/project filters, счётчики, empty/error/
  loading/stale states, mobile desktop и keyboard проверены actual browser.
  Переход к exact Run в full monitor и возврат сохраняют контекст фильтра.
- [ ] **E6-A7 — Производительность:** на fixture≥1000 tasks/Runs первая страница
  и polling ограничены пагинацией; без загрузки всех graphs/events/artifacts
  и полного disk scan. Измерены response sizes/request counts/backend work и
  browser behaviour; выбранные budgets и результаты зафиксированы, а не только
  назван режим light. Нет silent truncation и неконсистентного смешения read cuts.
- [ ] **E6-A8 — Совместимость:** прежние full monitor UI/API/entrypoint, CLI queue,
  независимые Runs и старые схемы проходят regression tests. Отдельно hash/bytes
  доказательство, что classic/profiled и остальные workflow consumer packages
  не менялись; shared backend additions только additive.
- [ ] **E6-A9 — Поставка:** documented released command/config включает Light,
  отдельный path/listener и full-monitor link base. Есть полные локальные
  run/health/browser проверки, proxy prefix/asset/API routing и rollback только
  Light. Authentication существующих доменов сохраняется, new mode не открывает
  write endpoints. Сейчас ещё не существующий CLI flag не выдаётся за working.
- [ ] **E6-A10 — Production acceptance:** после released Core + отдельной server
  rollout проверки `prify-light.stenhigh.net` показывает Light, а
  `prifly.stenhigh.net` — прежний full monitor. Владелец видит реальные tasks и
  review outcomes; screenshots/browser observations и exact binary/source SHA
  сохранены. Пока этого нет, статус «реализовано/развёрнуто» не ставить.

## Зависимости и оформление

E1/#4 и E2/#5 поставляют board/read state и native queue; они уже выпущены с0.13.77.
W1/W2/W5 reports — consumer fixtures для review projection, не обязательные
product workflows Core. W6 call recipes не блокируют basic Light; отчёты
существующих графов достаточны для начальной fixture/adapter qualification.

Это самостоятельный **E6/P1 Core change** с proposal/design/tasks/spec deltas,
а не новый workflow package в aif-workflows. Прототип UI, read contract и
implementation выполняются в Pri-Fly. Rollout домена — отдельный deployment
этап после готовой проверяемой поставки. Потребитель фиксирует ссылку на issue,
ожидаемые сценарии и реальное принятие результата; domain config сейчас не
переключается на несуществующий frontend.
