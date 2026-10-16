# Контракт и композиция

Root v8 configure валидирует config; весь quality call повторяется при
continue из partial/cancelled. Внутри quality v6 prepare вычисляет candidate
и выбранные пути. При no_work он сам выдаёт skip report/gate; assisted-шаг
не создаётся. Иначе audit читает один typed request bundle, затем evaluate
сверяет request digest, round, candidate и точный набор отчётных путей.

Candidate использует прежний `git-candidate/1` из выпущенного evidence package:
HEAD, index, tracked/nonignored untracked bytes/modes. Методы скопированы без
изменений в новый пакет, прежний evidence не правится. Selection — union
base→worktree, base→index и nonignored untracked; rename folding выключен,
поэтому удалённый путь тоже требует объяснения оставшейся проверки.

Report per path включает behavior, regression, existing_proof, concrete
evidence и findings; внутри path reviewer отвечает за каждый изменённый тест.
Машина не устанавливает истинность prose и не считает test functions. Patterns
также принадлежат проекту, это не универсальный детектор тестов. Динамическая
baseline-проверка не симулируется: недоступное доказательство явно отмечается.

Failed и blocked дают partial с разными status; passed/skipped — succeeded.
Недопустимая подготовка даёт rejected. Остановка без подтверждённого дефекта
не превращается в автоматический repair. Сессия и модель — отдельные claims
хоста; фактическая другая модель не обещается.

Пример `examples/test-audit-extension` использует собственный root graph,
где prepare→evaluate заменяется overlay на prepare→audit→evaluate. Input
вставки — один уже произведённый artifact exact request schema. Выход audit
читает evaluate. Обработаны все пять verdicts. Отдельно установленный пакет
не импортируется в чужой extend по имени; проект должен включить компоненты
в свою область и обеспечить producer/consumer, routing и budgets.

Standalone start в checkout на 0.13.77 требует чистый Git tree. Для проверки
uncommitted результатов текущего Run нужна композиция в нём; новая независимая
authority не используется для обхода ownership. В native untracked fixture
новый файл появляется в собственном Run после первого report, даёт stale,
а continue повторно выбирает и проверяет его. Исходный repository не меняется.
