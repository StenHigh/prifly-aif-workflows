<h1 align="center">Pri-Fly workflows for AI Factory</h1>

<p align="center">
  Два Project workflow folder для <a href="https://github.com/StenHigh/prifly">Pri-Fly</a>,
  которые ведут разработку по практике AI Factory: канонический путь
  <code>aif-classic</code> и веер ракурсов <code>aif-fanout</code>.
</p>

<p align="center">
  <a href="https://github.com/StenHigh/prifly-aif-workflows/actions/workflows/verify.yml"><img src="https://github.com/StenHigh/prifly-aif-workflows/actions/workflows/verify.yml/badge.svg" alt="verify"></a>
  <a href="https://github.com/StenHigh/prifly-aif-workflows/tags"><img src="https://img.shields.io/github/v/tag/StenHigh/prifly-aif-workflows?label=release&amp;color=1f6feb" alt="latest tag"></a>
  <img src="https://img.shields.io/badge/pri--fly-%E2%89%A5%200.6.0-00ADD8" alt="Pri-Fly ≥ 0.6.0">
  <img src="https://img.shields.io/badge/hosts-codex--cli%20%C2%B7%20codex--app%20%C2%B7%20claude--code-4b5563" alt="hosts">
</p>

<p align="center">
  <a href="#установка-в-проект">Установка</a> ·
  <a href="#что-нужно-целевому-проекту">Требования</a> ·
  <a href="#настройка-командой">Настройка</a> ·
  <a href="#версии">Версии</a> ·
  <a href="#проверки">Проверки</a> ·
  <a href="https://github.com/StenHigh/prifly-workflows">Каталог сценариев</a> ·
  <a href="https://github.com/StenHigh/prifly">Pri-Fly</a>
</p>

<p align="center">
  <img src="assets/readme/hero.jpg" alt="Шаги AI Factory от aif-plan до aif-commit грузятся на борт: каждый шаг — sealed package Pri-Fly" width="100%">
</p>

| Папка | Назначение |
|---|---|
| [`aif-classic/`](aif-classic/) | Канонический последовательный путь автора AI Factory: `warmup → plan → improve → implement → verify → security → review → commit`. Improve передаёт исправленный native plan в следующий круг; блокирующий verify/security/review возвращает typed gate с `suggested_next: /aif-fix` и ничего не чинит сам. Круг review открывает второй читатель в своей сессии (`review-challenge`), чьи находки review проверяет и сливает. |
| [`aif-fanout/`](aif-fanout/) | Отдельная доработка существующего плана двумя независимыми ракурсами review → выбор разработчика → применение принятого. Это веер задач, не выбор модели. |
| [`aif-profiled/`](aif-profiled/) | Тот же classic, порождённый из него `tools/derive_profiled.py`: каждый шаг объявляет профиль модели (`model_profile`), `plan` и `implement` просят отдельную сессию. Перевод профиля в модель и effort задаёт проект — дефолты в `extend.yaml`, переопределение в `.prifly/local.yaml`; движок доставляет и не выбирает. Pri-Fly ≥ 0.13.55. |

Этот репозиторий — workflow repository для каталога
[`StenHigh/prifly-workflows`](https://github.com/StenHigh/prifly-workflows).
Pri-Fly сам не поставляет product workflows: он остаётся движком, а сценарии
AI Factory развиваются здесь.

## Установка в проект

С Pri-Fly `v0.6.0` и новее (установка из GitHub Releases):

```sh
prifly project workflows add aif-classic          # запись официального каталога
prifly project workflows add aif-fanout
# или напрямую из этого репозитория
prifly project workflows add StenHigh/prifly-aif-workflows --path aif-classic --ref v1.0.0
```

Команда копирует папку в `.prifly/workflows/aif-classic/`, объявляет package и
launch в `.prifly/project.yaml` и записывает `origin` с exact commit. Ничего не
исполняется и не становится trusted: доверие package решается при
`prifly project start`.

Для Pri-Fly `v0.5.0` и старше — вручную:

```sh
cp -R aif-classic <repo>/.prifly/workflows/aif-classic
```

```yaml
# <repo>/.prifly/project.yaml
packages:
  aif-classic:
    source: .prifly/workflows/aif-classic
launches:
  aif-classic:
    title: AI Factory classic development workflow
    description: Canonical AI Factory development workflow with bounded plan improvement.
    kind: workflow
    workflow: .prifly/workflows/aif-classic/workflow.yaml
```

Имя установленной папки должно совпадать с именем папки здесь:
`decision_catalog` в `aif-classic/workflow.yaml` ссылается на
`.prifly/workflows/aif-classic/decisions/...`.

## Что нужно целевому проекту

- Навыки AI Factory, установленные для выбранного host: `aif-warmup`,
  `aif-plan`, `aif-improve`, `aif-implement`, `aif-verify`, `aif-security-checklist`,
  `aif-review`, `aif-commit` для `aif-classic` и `aif-improve` для
  `aif-fanout`. Context YAML закрепляет bytes только из skills root того host,
  который передан compiler-у (`.codex/skills`, `.agents/skills` или
  `.claude/skills`); host не угадывается по папкам. Закрепление навыка не тянет
  за собой его собственные `references/**`, поэтому `aif-improve/references/`
  (`LIST-MODE.md`, `CHECK-MODE.md`, `EXAMPLES.md`, `VALIDATOR.md`) закреплены
  отдельными контекстами и обязаны присутствовать в skills root: иначе
  компиляция отказывает сразу, а не исполнитель упирается в отсутствующий файл
  посреди прогона.
- Runner `prifly-run`, созданный `prifly project init`. Он спрашивает
  `worktree` или `checkout`, package profile `fast|full|ultra`, declared
  preflight decisions и policy, затем вызывает `project start`.
- [`aif-classic/decisions/INVENTORY.md`](aif-classic/decisions/INVENTORY.md)
  закрепляет SHA-256 upstream skills, под которые описан decision catalog.
  Другая версия skills требует ревизии inventory.

## Настройка командой

`extend.yaml` каждой папки — единственный файл, который команда правит после
установки; `prifly project workflows update` сохраняет его byte-for-byte.

**Но `remove` его удаляет, и молча.** Измерено: `project workflows remove`
сносит папку целиком вместе с вашим `extend.yaml`, а следующий `add` кладёт
шаблон пакета. `add` поверх объявленной папки при этом отказывает
(`project_workflow_exists`) — то есть сам по себе он ничего не затирает, потеря
происходит на `remove`. Это важно для тех, кому `update` недоступен: он
отказывает `project_workflow_modified`, если вы накладываете на папку свои
файлы, и тогда единственный путь обновления — `remove` + `add`. **Сохраняйте
`extend.yaml` до `remove`**, копию делают только те, кто знает.
В `aif-classic` доступны `profile: fast|full|ultra` (reviewed default),
`settings` для лимитов improve и `exclude: [improve, verify, security, review]`.

Состав гейта (`gate_checks` в `answers.preflight` или на старте) исполняется в
рабочей копии захода — новом worktree по базовому коммиту. В ней есть только
tracked-файлы: всё из `.gitignore` (каталог с инструментами, кэши, vendor,
`node_modules`, локальные бинари) отсутствует. Проверка, которая берёт
инструмент из такого каталога, останавливается до первой проверки с
`Error 127` — измерено на `make ci-check` с компилятором из `.tools/`.
Называйте инструмент в `gate_checks` так же, как это делает ваш CI, либо
ставьте зависимости в дереве захода до проверки.

`extend.yaml` не только вычитает: `extensions` добавляет ваш собственный шаг в
маршрут, не форкая пакет, поэтому `project workflows update` продолжает
приезжать. Вставка объявляется в ребро графа — `between: {from: X, to: Y}`, —
и это сильнее, чем «после X»: нельзя молча оторвать хвост графа, потому что вы
обязаны назвать, что было дальше. `workflow` и `step` — короткие имена
компонентов, то есть имя файла без каталога, а не полный `id:` из самого файла;
подстановка `id` — естественная догадка, и она неверна. Вставляемый шаг не
имеет входов: шагу со входами нужен собственный workflow graph. Полный рабочий
пример — `examples/authoring/extension-authoring-reference.yaml` в репозитории
Pri-Fly, а с Pri-Fly новее `v0.7.0` форму отдаёт `prifly schema extension-v1`.

Подробности — в [`aif-classic/README.md`](aif-classic/README.md).

## Версии

- Tag репозитория `vX.Y.Z` — то, на что указывает каталог (`ref` + pinned
  `commit`).
- Каждое изменение папки поднимает `package.version` в её `workflow.yaml`:
  Pri-Fly считает тот же `id@version` с другими bytes конфликтом identity, а не
  обновлением. Обновление без bump ломает следующий `project start` в проекте,
  который уже seal-ил прежнюю версию.
- Совместимость с Pri-Fly: папки проверяются CI против latest stable release
  Pri-Fly; изменение YAML authoring contract Pri-Fly требует новой версии здесь.
  С `v1.38.0` нужен Pri-Fly не ниже `0.13.31`: шаги `verify` и `review` несут
  materialise-only binding плана (StepDefinition v8), и более старый движок
  отказывает на compile — `schema_invalid at /workspace_trees/0 … requires
  output_port`.
  `aif-profiled` нужен Pri-Fly не ниже `0.13.43` (`model_profile`, v9,
  `model_profiles` в `extend.yaml`).
  С `v1.45.0` все пакеты, кроме `aif-fanout`, требуют Pri-Fly не ниже `0.13.55`:
  вердикт `blocked` (WorkflowRevision v6, `core:schema/step-result@2.0.0`, шаг
  гейта на StepDefinition v10). На 0.13.50–0.13.52 шаги гейтов не собираются
  (`schema_invalid at /outputs/gate/required_for/2`), на 0.13.53–0.13.54
  собираются, но Run не проходит verify.
- `aif-profiled/` не правится руками: `python3 tools/derive_profiled.py`
  переписывает его из `aif-classic/`, `--check` говорит, разошлись ли они;
  `tests/test_folders.py` держит то же самое.
- `aif-classic-continuation/` и `aif-profiled-continuation/` тоже не правятся
  руками: `python3 tools/derive_continuation.py` пишет их из `aif-classic` и
  `aif-profiled` (`--check` — разошлись ли). Версия хвоста своя, в `TAILS` того
  же скрипта: сменились байты хвоста — поднять её там и перегенерировать.

## Обновление до v1.45.0: вставки из `extend.yaml`

**Нужен Pri-Fly не ниже 0.13.55.** На 0.13.53 и 0.13.54 пакет собирается и
стартует, но Run с включённым verify останавливается у гейта: 0.13.53 не выдаёт
ему Attempt (`schema_invalid at /output_contracts/gate/required_for/2`), 0.13.54
не принимает отчёт `blocked` (`schema_invalid at /verdict`). На 0.13.55 Run
проходит verify и с `pass`, и с `blocked` — это держат пятые ворота
(`tests/probes/run_check.py`).

С `v1.45.0` корень `aif-classic` и `aif-profiled` — на WorkflowRevision v6, и
каждая вставка из `extend.yaml` обязана ответить за `blocked`. Касается ли это
проекта:

```sh
grep -c impossible_verdicts .prifly/workflows/*/extend.yaml
```

Ноль в файле, где есть `extensions:` со вставками, — `project compile` и
`project start` после обновления откажут:

```text
missing_handler at /definition/stages/<вставка>/on/blocked: this stage does not
say where blocked leads: add on.blocked or list blocked in impossible_verdicts
```

Ответ — строка в каждой вставке, шаг которой на `step-result@1.0.0`:

```yaml
    on: {pass: done, needs_revision: abandoned, fail: abandoned, no_work: abandoned}
    impossible_verdicts: [blocked]
```

**Правка и обновление — один коммит, и раньше не получится.** На пакете до
`v1.45.0` та же строка отвергается: `this workflow is at revision 4, which answers
for pass, fail, needs_revision, no_work; "blocked" is not one of them`. Порядок:
`prifly project workflows update <пакет>` (он сохраняет ваш `extend.yaml`), затем
строка в каждую вставку, затем один коммит. Оба отказа замерены на Pri-Fly
0.13.53 против `v1.44.0` и `v1.45.0`.

Вставка, которая сама умеет отличить «зависимость недоступна» от «проверка
упала», может вместо этого вернуть `blocked`: её шаг переходит на
`core:schema/step-result@2.0.0`, а вставка ведёт `blocked` туда, где Run должен
остановиться.

## Вердикты: WorkflowRevision v4 и v6

Графы, где работает гейт (корень, `verify-once`, `review-once`), объявлены на
`WorkflowRevision v6`: набор вердиктов шага закрыт (`pass`, `fail`,
`needs_revision`, `no_work`, `blocked`). Остальные графы и `aif-fanout` — на
`v4`, где вердиктов четыре. На обеих ревизиях каждый шаговый узел обязан
сказать, куда ведёт каждый вердикт. Незамаршрутизированный вердикт не отвергается
при приёме — отчёт принимается, шаг завершается, а затем падает маршрутизация с
диагностикой `unhandled_verdict`, унося весь прогон вместе с уже сделанной
работой. Полнота — единственная защита от этого, и её проверяет компилятор.

Ревизия запрашивается явной строкой `schema_version` в `workflow.yaml`.
Выведенная ревизия по построению низшая из возможных и сама не поднимется.
**Явная ревизия — обязательство навсегда:** каждый узел, добавленный позже, тоже
обязан быть полным, иначе пакет не соберётся. Для нас это и есть цель — сторож
переезжает из теста в компилятор, — но копирующему этот образец лучше знать об
этом заранее.

`blocked` — «проверить не удалось»: зависимость, нужная проверке, недоступна, и о
работе ничего не сказано. Его возвращают только гейты verify, security и review
(`step-result@2.0.0`, `gate` обязателен и при `blocked`). Узел гейта ведёт его в
finish, несущий `gate` со `status: blocked`: не в починку, которой нечего чинить,
и не обратно на ту же стадию — при лежащей базе такой круг сжёг бы бюджет Run
и закончился `budget_exhausted`. Повтор — `prifly project continue`, когда
зависимость вернулась.

Остальные узлы объявляют `impossible_verdicts: [blocked]`. Это не обещание за
исполнителя: их шаги на `step-result@1.0.0`, и `blocked` от них отвергает сам
контракт результата, называя его. Для прочих вердиктов `impossible_verdicts` по-
прежнему не объявляется: отчёт приходит от ассистируемого хоста, и утверждать за
него, чего он не вернёт, автор графа не может.

Вставка из `extend.yaml` в корень v6 отвечает за `blocked` так же: маршрутом или
`impossible_verdicts: [blocked]`; иначе `missing_handler … on/blocked`.

Как закрыты четыре вердикта в цикле гейта, если коротко: `pass` ведёт в выбор,
`needs_revision` — в исход, докладывающий находки без круга починки, а `fail` и
`no_work` — в исход с результатом `no_work`. Последнее и есть суть развязки.
Исход `rejected` у нас декларирован как несущий результат гейта, поэтому провести
туда круг, чей шаг вообще не отработал, нельзя — привязка выхода окажется
негарантированной, и компилятор откажет (`unavailable_output`). Разделение
получилось честным: `rejected` значит «гейт отработал и блокирует», `no_work` —
«работы не было и докладывать нечего». Без этого пришлось бы выдумывать пустой
результат гейта, то есть врать в артефакте ради прохождения графа.

## Версии ссылающихся компонентов

Шаг запечатывается вместе с байтами того, на что ссылается: его `instructions_ref`
и `context_refs` входят в его собственный документ по digest. Поэтому **поднимая
версию контекста или схемы, поднимайте версию каждого шага, который их называет,
и каждого workflow, который называет такой шаг.**

Иначе версия шага перестаёт быть его идентичностью: файл шага не менялся, а
байты под его версией — другие. В проекте на профиле `prifly-project-profile/3`
это незаметно, там версия компонента выводится из содержимого. В проекте на
`/2` — а это состояние живых установок — инвентарь авторитета закреплён ровно на
авторской версии, и обновление пакета отказывает `definition_drift`, называя шаг,
которого никто не трогал.

`tests/test_versions.py` проверяет это правило и называет и ссылающийся файл, и
ссылку, чья версия ушла вперёд.

## Проверки

```sh
python3 -B tests/test_versions.py                         # версия сдвинулась вместе с байтами
python3 -B tests/test_folders.py                          # статический контракт папок
python3 -B tests/verify.py --binary "$HOME/.local/bin/prifly"   # compile обоих package настоящим Pri-Fly
python3 -B tests/compatibility.py --binary "$HOME/.local/bin/prifly"  # import и start всех profile в одной authority
```

`tests/verify.py` создаёт временный Git-репозиторий, ставит обе папки, пишет
stub skills и проверяет questionnaire, sealed decision catalog, profiles
Fast/Full/Ultra, `exclude`/`settings`, порядок classic route, read-only gates,
parallel fan-out и оба host roots. Он ничего не импортирует и не запускает.

`tests/compatibility.py` идёт дальше: в одной authority он ведёт Classic по
Fast → Full → Ultra → default → Fast с собственным `extend.yaml` владельца и
разными байтами host skills, каждый вариант импортирует и запускает; затем один
раз запускает `aif-profiled` и читает, под какой версией состояния authority
запечатал Run с объявленным профилем и переводом (`core-state/35` и новее — на
0.13.41–0.13.44 такой Run уходил под контракт без этих полей). Каждый Run
доходит до выданного assisted handoff и там останавливается: живого AI-хоста
здесь нет, и всё, что за этой границей, проверкой не заявлено. Сеть,
AI Factory runtime и LLM не нужны ни одной проверке. GitHub Actions выполняет
то же самое после установки Pri-Fly официальным installer.

## Backlog

Перенесено из delivery roadmap Pri-Fly; ведётся здесь.

- Живой pilot `aif-classic` на реальной задаче в host session: провести один
  ограниченный Run и записать только наблюдаемый результат.
- Совместимость `aif-classic` с опубликованным AI Factory package: известен
  разрыв имён skills в released package; зафиксировать поддерживаемую версию
  upstream и обновить `decisions/INVENTORY.md`.
- `aif-fanout` остаётся compile-проверяемым полигоном: реальный выбор
  provider/model/reasoning появится только после
  `assisted-model-profile-protocol` в Pri-Fly.
