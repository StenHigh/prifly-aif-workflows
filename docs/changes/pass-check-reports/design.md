# Контракт и подтверждённая граница

## Передача

Предпочтительный carrier — существующий `implementation` с необязательным `reports: [ArtifactRef]`.
Это один путь передачи, без второго параллельного evidence-порта.
Артефакт — сохранённые Core байты. ArtifactRef называет его revision и digest.
EvidenceRef имеет другой тип и не заменяет ordinary output binding.

Producer публикует log и report через объявленные output slots.
Он включает точную ссылку на log в report, а ссылку на report — в carrier.
Reader получает carrier обычным binding и экспортирует только объявленные ссылки через public API.
Неизвестные форматы требуют честного результата, а не обхода произвольного JSON.
Публикация артефакта не даёт разрешения provision внешней среды.

Continue может дать переиспользованному output-порту новый ArtifactRef с прежними байтами.
Исходные report/log refs внутри carrier остаются прежними.
Поэтому consumer читает эти явные refs, а не предполагает прежний identity нового output slot.

```text
log ArtifactRef -> исходный report -> implementation.reports
                                         |
                implement/fix -> verify -> review -> project consumer
                                         |
                              repair -> следующая проверка
```

Verify/review должны возвращать carrier с добавленными исходными refs.
Clean и batch должны передавать этот carrier, а не прежний входной implementation.
Disabled должен передавать вход без изменения. Fix должен сохранять доступные прежние refs.
Для `aif-fix` нужно отменить безусловное повторение regression check в check-change bridge.
Достаточный after-receipt может заменить повтор. Failed receipt нельзя считать passed.

Reader сохраняет subject/basis, methods/commands, raw exits и результаты producer.
Новый HEAD в carrier не меняет basis старого report.
Проект задаёт применимость к поведению, selection, settings и среде.
Один новый SHA не доказывает необходимость повторить все проверки.
Недостающее внешнее измерение выполняет project-owned measurement, либо reader возвращает honest blocked.

## Что воспроизведено на 0.13.82

Fixture: [tests/fixtures/report-transport](../../../tests/fixtures/report-transport/README.md).
Driver: [report_transport.py](../../../tests/probes/report_transport.py).
Он не использует прикладные команды, AI Factory skills или новые механизмы Core.

```text
Корень: produce -> project measure -> cycle(repeat) -> project consume -> done
                                         |
Дочерний round:                         read -> repair -> fixed(partial)
                                         ^                 |
                                         +-- repeat -------+
```

Корневая вставка компилируется и исполняется.
Repair вызывает следующий read, но не повторяет корневой project measure.
Вставка в существующий edge `round.repair -> fixed` получает точный отказ:

```text
project_extension_unknown_workflow: round (known: transport)
```

Публичный [extension contract 0.13.82](https://github.com/StenHigh/prifly/blob/v0.13.82/examples/authoring/extension-authoring-reference.yaml)
ограничивает вставки корнем. Native Call extension также вставляется только в корень.
Сам вызов нового workflow не добавляет вставку внутри уже существующего repeat body.

Это узкая граница текущей структуры пакетов и project extensions.
Она не означает отсутствие передачи артефактов в Core.
Пример не доказывает невозможность любой другой композиции workflow.

## Решение, которое ещё требуется

Нужен поддержанный project-owned measurement перед каждым reader, которому требуется новый отчёт.
Он должен получать текущий carrier после repair и передавать дополненный carrier следующему reader.
Один nested anchor без последующего binding этой передачи недостаточен.
Пример пока воспроизводит первую часть: недоступность nested anchor.
Доставку нового measurement output в неизменённый базовый reader ещё предстоит квалифицировать.

Корневой measurement перед verify решает только первый вход в цикл.
Перенос provision внутрь read-only verify нарушает effect boundary.
Подмена package step refs или копирование verify/check-change нарушает границу проекта из issue.
Новый runner и скрытый cache выходят за объём задачи.

Перед запросом изменения Core нужно проверить допустимую композицию существующих native calls.
Если она требует копирования базовых gates или нового режима только ради transport, она не подходит.
Если остаётся capability gap, приложить этот generic reproducer и сформулировать порядок/bindings отдельно от transport.
Владелец согласовал полный автоматический цикл и создание отдельного Core issue 2026-11-01.
[Pri-Fly #14](https://github.com/StenHigh/prifly/issues/14) содержит reproducer и критерии C1–C8.
Он требует проверить существующую композицию перед расширением Core.
Одна вставка без передачи нового carrier следующему reader не закрывает этот issue.
Core реализация выполняется в отдельной сессии. В этой порции shipping packages не меняются.
Готовый текст передачи: [handoff.md](handoff.md).
