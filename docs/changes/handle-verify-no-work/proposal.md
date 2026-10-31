# Issue #7: штатная остановка verify без gate

Владелец согласовал `completed/rejected` для verify `fail/no_work` 2026-10-31.
Gate для этих verdicts остаётся необязательным.

1. Обработать дочерний `no_work` на корневой стадии verify.
2. Сохранить существующий rejected без выходов корня.
3. Проверить continue от verify с сохранением принятого префикса и дерева.
4. Повысить версии classic и штатного derived profiled; подготовить выпуск v1.56.0.

```text
verify или вложенный fix: fail/no_work
  -> verify-once: no_work
  -> verify-batch: no_work
  -> root: completed/rejected
  -> project continue: новый Run от verify
```

## Приёмка

Оба verdicts без gate должны завершать Run штатно, до security/review/commit.
Остановка после fix должна сохранять его HEAD и рабочие файлы.
Continue должен сохранять plan, staged/untracked owner work и одну workspace claim.
Prepare не должен менять источник, дерево, claims или список Runs.

Scope включает тот же no_work от fix внутри verify. Gate этого раунда остаётся историческим.
Review/fanout и миграция прежних failed Runs остаются вне этого изменения.
Новые требования к Core, схемам gate и обязательным выходам не вводятся.

Источники: [issue #7](https://github.com/StenHigh/prifly-aif-workflows/issues/7),
[design](design.md), [приёмка](acceptance.md).
