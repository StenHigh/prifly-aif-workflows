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
| [`aif-classic/`](aif-classic/) | Канонический последовательный путь автора AI Factory: `warmup → plan → improve → implement → verify → security → review → commit`. Improve передаёт исправленный native plan в следующий круг; блокирующий verify/security/review возвращает typed gate с `suggested_next: /aif-fix` и ничего не чинит сам. |
| [`aif-fanout/`](aif-fanout/) | Отдельная доработка существующего плана двумя независимыми ракурсами review → выбор разработчика → применение принятого. Это веер задач, не выбор модели. |

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
  `aif-plan`, `aif-improve`, `aif-implement`, `aif-verify`, `aif-security`,
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
В `aif-classic` доступны `profile: fast|full|ultra` (reviewed default),
`settings` для лимитов improve и `exclude: [improve, verify, security, review]`.

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
разными байтами host skills, каждый вариант импортирует и запускает. Каждый Run
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
