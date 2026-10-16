# Design W5

Первичная квалификация 2026-10-15: [результат, host matrix и границы](acceptance.md).
E4 устранён в released0.13.77; [повторная квалификация](release-0.13.77.md)
подтвердила terminal cancel/native release/full-round replay. Пакетная часть
2026-10-16 добавляет opt-in backend mode в aif-feature1.1.0 и reviewed adapter
исходных bytes; [итоговое устройство и приёмка](feature-composition.md).
Default sequential и classic/profiled сохраняются. [Frontend resources](frontend-qualification.md)
проверены отдельной native/browser fixture: изолированное owned окружение,
contexts/identities и порты, all-join/cleanup/cancel/replay. Capacity-one shared
stand остаётся sequential: native resource считает Attempts, а не Runs. Ни
shipping frontend adapter, ни LLM host matrix эта fixture не заменяет.
Inner call/on_error внутри quality round превращает
technical failure в обработанный исход внешнего quality/guard/commit replay unit;
root-only error handler не подменяет этот boundary. Новый Core operator не нужен.

## Сначала квалификация

До изменения shipping graph создать minimal implementation-review fixture
с existing `parallel`/all-join и read-only claimed workspace. Проверить,
как released runtime допускает и host исполняет независимые Attempts.
Успешный authored graph сам по себе не доказывает concurrent delivery.

Если необходимый путь unsupported, change фиксирует limitation и reproducible
E3, а production W3 сохраняет последовательность. Если supported только на
части hosts, reviewed profile/mode явно ограничивает применимость. Признак
honoured model_profile не является доказательством реальной concurrency.

## Round barrier

Checks выполняются в составе W3; веер независимых read-only lens получает
один candidate. Join all не прекращает сбор на первом CHANGES. Aggregator
после settle проверяет completeness/candidate, связывает findings с reader и
check, передаёт отдельному repair. Duplicate claims проверяются, не суммируются
как независимые доказательства. Optional/excluded lens не создают fake PASS.

Cancelled или uncertain obligations требуют existing settlement/recovery;
не снижать безопасность join ради быстрого finish. Политика ожидания и причины
blocked видны. Никакого writable repair параллельно с reader того же candidate.

## Измерения

Runtime fixtures дают воспроизводимые barriers/negative cases. Live evidence
показывает start/end настоящих сессий, host/tool versions, candidate и reports.
Сравнение sequential/parallel фиксирует task scope, состав checks и окружение.
Четыре agents могут сократить ожидание и увеличить токены; качество и стоимость
не выводятся из самого числа параллельных ветвей.
