# Pri-Fly workflows for AI Factory

Два Project workflow folder для [Pri-Fly](https://gitlab.com/stenhigh/prifly),
которые ведут разработку по практике [AI Factory](https://github.com/StenHigh):

| Папка | Назначение |
|---|---|
| [`aif-classic/`](aif-classic/) | Канонический последовательный путь автора AI Factory: `warmup → plan → improve → implement → verify → security → review → commit`. Improve передаёт исправленный native plan в следующий круг; блокирующий verify/security/review возвращает typed gate с `suggested_next: /aif-fix` и ничего не чинит сам. |
| [`aif-fanout/`](aif-fanout/) | Отдельная доработка существующего плана двумя независимыми ракурсами review → выбор разработчика → применение принятого. Это веер задач, не выбор модели. |

Этот репозиторий — workflow repository для каталога
[`StenHigh/prifly-workflows`](https://github.com/StenHigh/prifly-workflows).
Pri-Fly сам не поставляет product workflows: он остаётся движком, а сценарии
AI Factory развиваются здесь.

## Установка в проект

С Pri-Fly новее `v0.5.0` (команды `project workflows` появились после него):

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
  `.claude/skills`); host не угадывается по папкам.
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
python3 -B tests/test_folders.py                          # статический контракт папок
python3 -B tests/verify.py --binary "$HOME/.local/bin/prifly"   # compile обоих package настоящим Pri-Fly
```

`tests/verify.py` создаёт временный Git-репозиторий, ставит обе папки, пишет
stub skills и проверяет questionnaire, sealed decision catalog, profiles
Fast/Full/Ultra, `exclude`/`settings`, порядок classic route, read-only gates,
parallel fan-out и оба host roots. Сеть, AI Factory runtime и LLM не нужны.
GitHub Actions выполняет то же самое после установки Pri-Fly официальным
installer.

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
