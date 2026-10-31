# Решение

## Контракт

`verify-once.stopped` и `verify-batch.unstarted` сохраняют outcome no_work.
Они не могут обещать gate: fail/no_work шага допускают его отсутствие.
Корень добавляет `stages.verify.on.no_work: abandoned`.
Abandoned уже завершает Run как completed/rejected и не публикует выходы.

Это также закрывает no_work от вложенного fix. Прежний gate доступен в истории,
но не становится root output для незавершённой проверки.
Partial по-прежнему требует gate. Blocked, owner-only, лимит и выключенный verify сохраняют маршруты.

## Продолжение

1. `continue --prepare` выбирает корневую стадию verify и действие execute.
2. Новый Run переносит принятые warmup/plan/improve/implement.
3. Он получает ту же claim, текущий HEAD, staged index и untracked work.
4. Он выполняет verify целиком с новым счётом раундов.
5. Повторный fail/no_work снова даёт rejected; успешная проверка допускает security.

```text
Принятый префикс ───────────────┐
Сохранённое дерево и план ──────┼─> новый Run: verify -> security -> review -> commit
Reviewed continue ─────────────┘                 └─ fail/no_work -> rejected
```

Artifact implementation из принятого префикса может называть прежний head.
Действующие инструкции verify требуют читать фактическое дерево, а не откатывать его к этому head.
Схемы и эти инструкции не меняются.

## Версии и границы

Classic root/package: 1.48.0 -> 1.49.0. Profiled: 1.49.0 -> 1.50.0 через derive.
Остальные компоненты этих пакетов сохраняют bytes; README обновляются вручную.
Остальные шесть shipping packages не меняются.

На released0.13.82 старые failed/unhandled_child_outcome Runs отклоняют continue
с recover_frontier_unsupported. Изменение on у verify может также вызвать
recover_frontier_changed для остановленных Runs прежней версии.
Новый пакет не меняет старые sealed Runs и не обещает их миграцию.
Повтор implement и удаление прежнего дерева не выполняются автоматически.

Native tests используют реальные CLI/Git/Runs и синтетические ответы.
Они не квалифицируют работу живых моделей или внешнюю инфраструктуру.
