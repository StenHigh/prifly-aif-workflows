# Design W4

Реализован отдельный [project example](../../../examples/verified-integration/README.md)
для stable0.13.76; existing packages и core byte-unchanged. Матрица квалификации
— [acceptance.md](acceptance.md); она отделяет real Git/commands, synthetic host,
fresh CLI reader и offline provider fixtures.

## Конкретный алгоритм

Handoff содержит исходные байты W1 requests, reports, candidate commit, local
bare target/ref/commit, integrated argv checks, final code spot checks и project
risk policy. Builder принимает только явно названные files; latest Run lookup
не используется. Источник должен быть чистым, reports — соответствовать текущей
HEAD/index/bytes/modes identity. Pre-commit W3 evidence после commit требует новой
W1-проверки; перенос PASS по похожему diff запрещён.

Prepare создаёт owner-marked copy вне candidate и Attempt scratch (`/tmp`),
копирует Git objects без hardlinks, получает exact target commit и выполняет
`merge-tree --write-tree`. Exit1 — конфликт/needs_revision; operational error —
unavailable. По tree object создаётся детерминированный merge commit с обоими
parents и фиксированным timestamp, затем запускаются реальные project argv
checks. Новый W1 snapshot фиксирует HEAD/index/bytes/modes интеграции; команды
и final reader не могут изменить его и сохранить прежнюю приёмку.

Final reader получает request и integration candidate отдельными typed bindings,
assessment с reports/gates/command results и явно переданный handoff. Его отчёт
оценивается неизменённым W1 evaluator. Перед операцией freshness повторяет source,
target, integration snapshot и digest всего handoff, включая criteria/mode/policy.
Local merge сначала импортирует immutable inspected object, затем CAS update-ref
ровно NEW OLD. Intent/ack journal связывает commit, ref и handoff; lost ack читает
фактический ref, не повторяет update. Local target working checkout не изменяется.

Пути auth_money/migrations/dependencies/deploy и явные business assumptions —
project policy; owner decision привязан к обоим commits и policy digest. Без
решения outcome owner_required. Actual optional model mapping unavailable остаётся
видимым W1 warning; ignore/stop задаёт проект, другую модель не выводят из session ID.

Default assess выполняет только приёмку и owned cleanup. GitLab publication —
отдельный assisted external executor с project-owned client, точными branches
и identity. Reference client algorithm и offline fixtures закрывают generic #1
regression portion. Реальный provider/remote CAS/lease и credentials не выданы
generic package и требуют отдельной project qualification.

## Приёмка и запись разделены

Final reader получает точные criteria/reports/candidate/target inputs и
read-only integration assessment. Target Git ref сначала разрешается в commit;
refs не заменяют identity проверенного дерева. Integrated checks выполняются
в отдельной рабочей копии, поэтому baseline/merge не изменяют candidate.

Final report различает ready, needs_revision, owner_required и unavailable
как предметные данные существующего verdict/gate contract. Итоговое решение
не считается authorization на merge/push: разрешённая операция названа в
reviewed executor effects. При записи повторно проверяется target; при race
останавливаемся/reconcile, не создаём «проверенный» merge другого дерева.

## Простая вставка и сложный граф

Stable 0.13.76 уже допускает один input binding extension к доступному earlier
output. Отдельный новый guide исправляет понимание ограничений, не меняя эталонные
classic/profiled templates по решению владельца. Issue ядру не требуется. Если final assessment требует
нескольких inputs или round — authored example graph/один явно произведённый
typed bundle. Не искать artifacts по latest Run и не создавать скрытый bundle
в host conversation. Проверить template на released compiler.

## Проектные операции

Поставить generic локальную fixture с Git origin для проверки интеграции.
GitLab publication example описывает ownership Draft и reconcile-by-identity;
не требует публикации в реальный production repo для offline tests.
При real provider observation указываются точная CLI версия, permission и
границы. Их отсутствие не превращается в заявление о полной external приёмке.

Push/MR и cleanup объявляют effects и ownership. После interrupted write
сначала выяснить результат. Релиз пакетов, сторонний MR и auto-close задач
не входят в example как неявный tail. Canonical commit остаётся local.
