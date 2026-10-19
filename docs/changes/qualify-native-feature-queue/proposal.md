# Native queue → aif-feature: пакетная приёмка E1/E2

Дата:2026-10-19. Задача продолжает исходный план после W6; новых возможностей
движка и нового workflow package не требует. Реальный проектный пилот ждёт
подходящей задачи и этим стендом не заменяется.

## Объём

Через публичный CLI official latest stable Pri-Fly проверить existing
`aif-feature@1.2.3` от native queue TaskInput до финальных typed evidence,
включая reviewed continuation. Изолировать repository/authority/HOME и все
созданные процессы; не менять Core, сервер, canonical classic/profiled,
shipping package bytes, catalog или package versions.

Зависимости: E1/E2 stable0.13.77+, W1/W3 существующие evidence и feature;
W6/Light/UIUX/parallel не нужны. Проверенная база —0.13.80.

## Критерии приёмки

- Q1: add/claim сохраняют исходные bytes и digest TaskInput; до admission нет
  Run или workspace claim. TaskInput и typed input явно различаются.
- Q2: отсутствие typed input отказывает `missing_input` без создания Run;
  prepare запечатывает точную queue selection и оба input digests.
- Q3: reviewed start связывает Task с одним Run; повтор тех же add/claim/start
  с прежними command IDs не создаёт дубликатов.
- Q4: direct feature заканчивается local commit и реальными exported typed
  reports checks/security/review; command acceptance исполняется на самом деле.
- Q5: required-unavailable заканчивается partial с blocked gate, без commit;
  отмена read-only quality также допускает reviewed continuation. Без queue
  selection source отказывает `queue_source_identity_conflict`.
- Q6: continue создаёт отдельный Run той же Task и использует одну workspace
  claim. Исходный Run/TaskInput неизменны; tracked/untracked owner edits
  сохраняются, quality повторяется для свежего candidate, plan/implement нет.
  Повтор continuation command не создаёт ещё один Run.
- Q7: full monitor read API показывает финальный Run и те же evidence bytes;
  это API acceptance, не browser/Light acceptance. Run success не делает Task
  done; отдельный owner complete сохраняет всю историю associations.
- Q8: все созданные claims освобождены, свои monitor processes остановлены,
  временное дерево удалено; воспроизводимый пример, CI и evidence сохранены
  в repo вне shipping packages.

## Границы

Детерминированные assisted actors; независимость моделей и живые skills не
аттестуются. Не принимаются E2 concurrency/crash windows заново, принудительная
отмена writer, произвольная reconciliation или частные тестовые среды.
Нет auto-start из claim, auto-complete, внешнего tracker sync, push/MR/deploy.
Настоящий Light остаётся Pri-Fly#11; проектный пилот и его #2/#5 остаются открыты.
