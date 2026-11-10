# Приёмка candidate task limit на Core0.13.90

Статус: локальная финальная native matrix PASS; exact-source CI ещё не завершён.
Дата: 2026-11-10. Публикация repository release не выполнена.

Official Linux binary проверен по обеим подписям manifest и SHA-256.
Binary digest: `db8a158149088e6f9bfb9df3ebe5fc97e1b57942a620c78b65841f5c996bd984`.
Source Core: `5e7f81cf5e6b53b72b86a937584e18f699f90ff9`.
[Provenance и baseline/candidate gates](../engine/release-0.13.90-results.json).

## Пакетный контракт

Classic/profiled/fix3.0.0 объявляют один параметр с default12 000.
Owned task1.2.0 использует whole-scalar placeholder в description.maxLength.
Project consumers используют точный local alias `schema_task`.
Frozen contracts1.2.0/1.0.0 и остальные пять shipping packages сохраняют bytes.

```text
параметр -> единая схема task -> root / plan / nested workflows / project consumers
                                             |
                                     repair и reviewed continue
                                             |
                                   сохранённый исходный Run
```

## Матрица A1–A10

| Критерий | Native-проверка |
|---|---|
| A1 | `update`: v1.57.0 → candidate, затем новый source commit. Owner config32 000, extend и project sentinel сохраняются; длинный task стартует. |
| A2 | `boundaries`: default12 000 принимает12 000;12 001 получает schema_invalid в prepare/start. |
| A3 | Owner32 000 принимает16 557 и32 000;32 001 отклоняется до Run. |
| A4 |0, -1,1.5, строка, boolean, null, unsafe integer, object и array получают project_compile_parameter_invalid. |
| A5 | Кириллица/emoji; диагностика содержит /description, effective limit и actual length. |
| A6 | Смена32 000 →40 000 меняет review digest; старый digest получает project_start_stale_launch без нового Run. |
| A7 | Все task refs в compiled closure совпадают. Classic/profiled проходят plan, opt-in reader, verify/review repair и succeeded для fast/full/ultra. Fix проходит настоящий regression/repair/check. |
| A8 | `shared-authority`: два проекта с32 000/40 000 используют одну authority и разные exact refs; прежний Run не меняется. |
| A9 | Для partial Run с16 557 сужение до12 000 отклоняет continue prepare. Возврат32 000 позволяет reviewed continue с принятым prefix. |
| A10 | Package README, release guide, draft catalog и ready examples описывают один released синтаксис, отдельный opt-in и ограничения continue. |

Финальная матрица прошла16 cases /31 Runs /42 чтения полного task.
Она удалила19 собственных temporary roots и monitor registrations; active claims0.

Driver: [shipping_task_limit.py](../../../tests/probes/shipping_task_limit.py).
Финальные результаты: [shipping-0.13.90-results.json](shipping-0.13.90-results.json).
Он проверяет все package profiles и три host adapters при compilation.
Его actors работают синтетически; Git, CLI, claims, artifacts и регрессионные команды настоящие.
Каждый fixture удаляет собственные Runs/claims, temporary root и monitor registration.

```sh
python3 -B tests/probes/shipping_task_limit.py \
  --binary /absolute/path/to/released/prifly-v0.13.90 \
  --jobs 3 --output /tmp/aif-task-limit-results.json
```

## Общие проверки

Unit:122 PASS. Versions4, folders7 и derive `--check` PASS.
Contracts generator и W6 generator воспроизводятся через `--check`.
Verify8 packages/132 components/88 steps PASS.
Compatibility5 launches/4 builds/6 trusted PASS; seal core-state/41.
W6:18 native compiles на трёх hosts и8 отказов PASS;
[результаты](w6-0.13.90-results.json).
Готовые inputs из examples проверены отдельно для всех трёх пакетов:
prepare/start и экспорт полного сохранённого task PASS;
[результаты](examples-0.13.90-results.json).
Это ещё3 Run и3 очищенных authority; вместе с матрицей34 Run и22 authority.

Живые модели, приватная инфраструктура и размер фактического контекста модели не квалифицируются.
Новые пределы не меняют contracts независимых public UI/UX imports.
Exact-source CI и итоговый source commit записываются после завершения полной матрицы.
