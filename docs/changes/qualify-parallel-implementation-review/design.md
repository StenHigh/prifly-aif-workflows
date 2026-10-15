# Design W5

Квалификация 2026-10-15: [результат, host matrix и границы](acceptance.md).
Выбран отдельный backend fixture; production feature profile блокирован native
cancellation после settled sibling, затем требует host adapter и frontend
resources. Нужный timeout replay реализован
внутренним call/on_error, возвращающим normal rejected во внешний replayable
root call. Root-only on_error не заменяет эту обёртку. Новый Core operator
не требуется; [E4](engine-followup.md) запрашивает корректное завершение existing
cancel после settlement всех параллельных read-only Attempts.

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
