# Design W1

## Отчёт и решение

Реализован отдельный пакет `aif-review-evidence@1.0.0`, без изменения classic/
profiled/fix/fanout. Три stdlib Python programs (`configure`, `capture`, `evaluate`)
используют existing worker protocol и `PRIFLY_REPOSITORY_WORKSPACE` на 0.13.76.
Capture/evaluate машинно снимают `git-candidate/1`; read-only assisted reader
отдаёт отдельный report. Root quality-call повторяется целиком при continue.

Отдельный report описывает работу reader; gate описывает приёмку. Точные имена
полей и refs выбираются при реализации после проверки существующих schemas.
Минимальные данные: reader/round, candidate basis, объявленные check IDs,
method, execution status, result, evidence references, пропуски и причины,
findings и происхождение отчёта. Report содержит request_digest из delivered request artifact, который evaluator
сверяет с фактическими bytes входа. Одинаковые check IDs при изменённых criteria
не допускают перенос старого report. Requiredness берётся из закреплённого состава
запуска: reader не может сделать mandatory check optional своим ответом.

Оценщик сверяет состав, status и candidate basis перед успешным завершением.
JSON-schema проверяет структуру; для межартефактных сравнений выбрать явный
workflow evaluator или declared program с existing worker protocol. Нельзя
приписать автоматическую проверку freshness компилятору только потому, что
в JSON добавлено поле digest. Program/evaluator получает явные bindings и
объявленные effects, а не неявный доступ к базе authority.

## Candidate и evidence

Перед внедрением определить воспроизводимый basis дерева и команду проверки:
base, HEAD, staged/dirty/untracked состояния, отсутствующие пути и modes.
Не использовать только `base..HEAD` или самореферентный diff. Runtime-generated
логи и reports хранятся как artifacts/вне проверяемых product paths по явной
политике. Нельзя исключать любые новые файлы из candidate по догадке.

Если byte-exact identity невозможно подтвердить данным host, это declared
limitation/blocked для требующей его приёмки. Capture, materialisation и
candidate-preservation проверяются отдельно. Read-only review не исправляет код.

## Совместимость

Новый report не расширяет общий enum `gate` значениями ui/ux без ревизии всех
потребителей. Связь отчёт → существующий gate является явной. Неподвижные shared
schemas сохраняют refs; новые/изменённые bytes требуют нового identity/version.
Existing пакеты не меняются; classic/profiled эталонные по решению владельца.
Новый package использует собственные schema refs.

Свежая сессия подтверждается host observation, другая модель — model report;
обе записи являются заявлением host, не независимой аттестацией движком.

## Измеренная граница continue на 0.13.76

Stopped quality replay сохраняет accepted configure. Изменение effective step
contract configure отказывает `recover_prefix_changed`; попытка начать с
первого root-stage configure отказывает `resume_prefix_empty`. Это сохранённое
ограничение stable, не повод добавлять фиктивный anchor или сбрасывать candidate.
Смена author version или executor arguments сама по себе не является
доказательством такого отказа. Boundary проверяется по фактическому prepare.
