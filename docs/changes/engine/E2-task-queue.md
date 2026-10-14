## Проблема и ожидаемое поведение

Несколько host-сессий могут вести разные Runs, но ручной Markdown backlog не
даёт устойчивого атомарного захвата задачи и связи с последующими start/continue.
Нужна локальная project queue: выбрать следующую задачу, безопасно закрепить
владельца и связать её с Runs без потери/повтора работы после сбоя.

**E2 / приоритет P3**, после подтверждения регулярной работы с несколькими
задачами. База: released Pri-Fly **0.13.76**. Это отдельная capability, не часть
E1 board и не замена runtime Run. Task identity существует до первого запуска;
несколько Runs одной задачи сохраняют свои самостоятельные outcomes/evidence.

Пример: два host одновременно берут next. Каждому достаётся разная задача.
Первый host теряет связь после start; повтор восстанавливает связь с уже
созданным Run, а не стартует ту же задачу ещё раз.

## Объём

- Локальные записи задач с устойчивой identity, исходным запросом, revision,
  очередностью, provenance и явным состоянием обработки. Точную схему/команды
  определить в core change; предлагаются операции add/list/claim-next/release.
- Атомарный захват с owner identity и защитой от конфликтующей/повторной
  команды. Priority ordering имеет определённое разрешение равенства.
- Run associations записываются устойчиво вместе с admission либо через
  согласованный recoverable intent, чтобы crash не создавал orphan/double start.
- Generated runner берёт claimed task, сохраняет original request и проводит
  existing exact launch selection → questionnaire → typed validation → prepare
  → reviewed start. Claim/next сам по себе не разрешает исполнение.
- Continue связывается с той же задачей по recorded identity. Task status не
  переинтерпретирует cancelled/partial Run как потерянную задачу или успешную.
- Изменение task revision после prepare инвалидирует prepared execution;
  правка очереди не меняет sealed input уже начавшегося Run.

## Границы

Provider-neutral local queue: core не получает отдельные ветки GitHub/GitLab/
Jira и не меняет статусы внешних задач. Import/source adapters и write-back —
отдельные операции. No automatic issue close, push, MR или merge.

Нет автоматического бесконечного draining, scheduler, фонового host spawning
или разрешения всех executable effects одной командой next. В первой версии
запуск очередной задачи требует existing reviewed start.

Task claim не равен Git/workspace claim. Нет timeout, который слепо возвращает
задачу в ready, когда исход допущенной работы неизвестен. Release/recovery
учитывает активные Runs, pending/uncertain obligations и незавершённые decisions.
Credentials и приватные payload не должны попадать в публичные fixtures.

## Критерии приёмки

- [ ] **E2-A1:** Два одновременных claim-next в одной project queue атомарно
  получают разные tasks; conflicting owner/revision отказывает без partial mutation.
- [ ] **E2-A2:** Повтор того же command identity возвращает прежний результат;
  другой payload с той же identity конфликтует, не создавая новый claim/Run.
- [ ] **E2-A3:** Crash до/после claim, admission и записи association восстанавливает
  известные факты. Уже созданный Run находится; неизвестный dispatch требует
  reconcile, не blind retry или автоматического requeue.
- [ ] **E2-A4:** Claim/next не запускает programs и не выбирает launch молча.
  Reviewed prepare/start с existing digest и executable authorization сохраняется;
  свободный original task text и typed input выбранного launch не теряются.
- [ ] **E2-A5:** Task revision меняется между prepare/start — отказ до dispatch;
  правка task после старта не меняет закреплённые inputs/evidence прежнего Run.
- [ ] **E2-A6:** Partial/cancelled → continue → continue связано с одной task
  identity и разными Runs; ни один accepted результат не переписывается.
- [ ] **E2-A7:** Нельзя освобождать/reclaim task поверх живой или uncertain работы
  по истечению таймера. Явные безопасные release/reconcile пути протестированы.
- [ ] **E2-A8:** Задана точная семантика готовности/завершения задачи: успешный
  локальный Run не выдаётся за внешнюю публикацию/приёмку. Неуспешный Run
  остаётся доступен из истории независимо от дальнейшего состояния queue.
- [ ] **E2-A9:** Legacy проекты/Runs работают без queue и не мигрируют автоматически;
  queue изолирована по project/authority, copy/clone/bootstrap имеет описанное поведение.
- [ ] **E2-A10:** CLI concurrency/crash/recovery fixtures проходят на released
  binary; отдельно живой runner на поддерживаемых hosts подтверждает выбор,
  prepare, ожидание ответа и отсутствие дублирующего start.

## Зависимости и оформление change

Не зависит от E1: первая версия может быть CLI + runner, E1 впоследствии читает
те же associations. Отдельное представление Runs: [E1 / #4](https://github.com/StenHigh/prifly/issues/4).
W1–W5 не зависят от queue. Опирается на existing durable
commands, admission/recovery и provider-neutral task intake; перед реализацией
проверить, какие primitives уже доступны, а новые contracts описать явно.

Оформить отдельный core change с proposal/design/tasks и нормативными deltas для
task queue, CLI/runner и state/read schemas по фактическому объёму. Сначала
описать recovery/crash windows и квалификацию; затем реализовывать next UX.
