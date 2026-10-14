# Design W4

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
