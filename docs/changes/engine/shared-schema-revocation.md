# Отказ запуска после исторического revoke общего schema supplier

Дата диагностики: 2026-11-09. Исправление рабочей authority не выполнялось.
Это отдельная причина, отличная от commit pin mismatch в CI.

## Подтверждённая цепочка

1. Старый `aif:package/classic@1.15.1` поставлял `aif:schema/feature-enabled@1.0.0`.
2. В затронутой authority старый пакет имеет status revoked.
3. Современный composition-contracts1.0.0 поставляет ту же схему с тем же полным Ref.
4. Composition-contracts1.2.0 зависит от frozen1.0.0; aif-fix2.0.0 зависит от1.2.0.
5. Start проверяет требуемые component refs против всех записанных пакетов.
6. Совпадение с revoked supplier немедленно запрещает admission, даже при другом trusted supplier.

```text
aif-fix2.0.0 -> contracts1.2.0 -> contracts1.0.0 -> feature-enabled1.0.0
                                                       ^
revoked classic1.15.1 -> тот же exact ref ---------------+
                                                       |
                                                 start refused
```

Полный schema Ref:

```json
{"id":"aif:schema/feature-enabled","version":"1.0.0","digest":"sha256:29bce348352ac8e11f65737dc77e990bc8f7687ad896e8757802ab1cd52557ee"}
```

В read-only истории отказавшего запуска проверены сам Problem, successful contract import,
revoked classic ref и одинаковый schema digest. Новый Run не был создан;
временный claim движок освободил. Приватные приложение, данные задачи и пути authority
не нужны для воспроизведения и сюда не копируются.

## Почему повторная установка не помогает

[Published Core88 gate](https://github.com/StenHigh/prifly/blob/v0.13.88/internal/runtime/package_lifecycle.go#L511)
содержит отдельный немедленный отказ для PackageRevoked.
Проверка другого resolvable supplier выполняется после этой ветки.
Комментарий в коде прямо описывает security revocation независимо от другого supplier.
Это текущая политика Core, а не случайный выбор первого пакета.

Для removed/quarantined supplier действует другой путь: допустим иной trusted supplier.
Revoke терминален. Документированный CLI не позволяет перевести revoked revision
в removed/trusted или восстановить её повторным import.
Владелец подтвердил 2026-11-09: старую версию просто убирали при обновлении.
Опасное содержимое не было причиной отзыва по сообщению владельца.
Это уточнение намерения, а не изменение старого audit record.
Старый trust reason описывает исходную установку и не является причиной последующего отзыва.

## Native reproducer

[shared_schema_revocation.py](../../../tests/probes/shared_schema_revocation.py)
создаёт временную authority и synthetic legacy package ровно с одной схемой.
Исторический classic code не используется. Пример импортирует настоящий текущий
contracts bundle и запускает finish-only workflow с этой схемой на входе.
LLM, приложение и рабочая authority не нужны.

```sh
python3 -B tests/probes/shared_schema_revocation.py \
  --binary /absolute/path/to/released/prifly \
  --output /tmp/shared-schema-revocation.json
```

Путь binary — placeholder. Рабочая директория — корень этого репозитория.
Успешное завершение driver означает воспроизведение всех трёх ожидаемых исходов,
включая отказ revoke-case; это не PASS исправленного поведения.

| История authority | Contract import | Prepare | Start |
|---|---|---|---|
| Чистая | PASS | PASS | succeeded |
| Synthetic classic удалён через remove | PASS | PASS | succeeded |
| Synthetic classic отозван через revoke | PASS | PASS | package_not_resolvable; Run не создан |

Одинаковые исходы получены на official Core0.13.86 и0.13.88.
[86 results](shared-schema-revocation-0.13.86.json),
[88 results](shared-schema-revocation-0.13.88.json).
По два finish-only Runs и три временных authority на binary.
Каждая authority удалена, её monitor registration снята; active claims отсутствуют.

Следовательно, это не новая регрессия только Core88.
Зелёные compile/compatibility и свежие install/update fixtures не проверяли этот
сценарий старой authority с историческим security revoke.
Historical evidence release1.57.0 остаётся ограниченным своим измеренным scope.

## Граница исправления

Владелец сообщил причину: обычное обновление. Записанный status reason и status changed
нужно сохранить; они доступны в exact package inspection.
Рабочее состояние authority, SQLite и старые audit records вручную не меняются.

Если revoke обозначал небезопасные components, новый supplier не должен молча
отменять запрет на их exact refs. Поддержанное исправление требует новых проверенных
ревизий затронутых контрактов либо явно согласованной политики повторного допуска.

В данном случае revoke использовали для обычного обновления. Нужен штатный путь миграции
с сохранением истории отзыва и явным решением владельца о безопасных shared schemas.
Такого пути этот driver не реализует. Простая замена условия gate на «нашёл любой
trusted supplier» изменила бы существующий security contract.

При разработке Core решения проверить весь dependency closure, а не только первую
feature-enabled schema. Старый classic может совпадать с несколькими shared refs.
Смена одного ref может лишь перенести отказ на следующую схему.

Новая authority технически не содержит старого revoke, что показывает control-case.
Это не автоматический план ремонта: новая authority не переносит прежние Runs,
claims и решения доверия и не заменяет явную миграцию существующей установки.

## Независимая ошибка CI

В [CI42571423001](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/42571423001/job/129012501635)
`fix_check.py --case install` переписывает repository/ref на temporary Git source,
но оставляет release commit из настоящего catalog/aif-fix.yaml.
Catalog закрепляет ee76702, synthetic main имеет be9e92f; Core правильно выдаёт
project_workflow_commit_mismatch. До package admission этот fixture не доходит.
Это не причина package_not_resolvable при реальном запуске.

Исправление CI должно согласовать fixture ref и pin его собственного commit,
сохранив проверку public catalog pins. Полный CI этим расследованием не исправлен.
