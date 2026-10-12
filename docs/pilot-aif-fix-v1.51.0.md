# Пилот: отдельный aif-fix в v1.51.0

Новый пакет `aif-fix:package/fix@1.0.0` не меняет classic/profiled/fanout.
Нужен выпущенный Pri-Fly **0.13.76 или новее** и AI Factory **2.19.0**:
`aif-warmup`, `aif-fix`, `aif-security-checklist`, `aif-review`, `aif-commit`
в skills root выбранного host. Проверьте версию бинаря, которым пользуется
runner, и project skill overlays; локальные заглушки из probes не подходят.

Из корня пилотного проекта:

```sh
prifly version
prifly project runners update --repository .
prifly project workflows search aif-fix
prifly project workflows add aif-fix --repository .
prifly project workflows --repository .
```

Если пакет уже установлен, используйте `project workflows update aif-fix`,
сохранив проектный extend.yaml. Прямая установка закреплённого выпуска:

```sh
prifly project workflows add StenHigh/prifly-aif-workflows --path aif-fix --ref v1.51.0 --repository .
```

После установки новый launch должен появиться в обычном списке prifly-run.
ИИ советует по brief/title/description, человек выбирает. Проверить: выбор
другого workflow после совета, точный ID без повторного выбора, отсутствие brief
и недостаточные основания для рекомендации. До выбора и reviewed prepare Run
не создаётся. Файлы generated runner вручную не править; PROJECT.md сохраняется.

В первом запуске выбрать worktree, profile default, security оставить включённым.
Вход task — `{title, description, reference?}` с наблюдаемым и ожидаемым
поведением и воспроизведением. `short_checks` задаёт дополнительные команды,
`gate_warnings` — явную политику ignore/fix/stop. Для review настроить перевод
`independent-review` в проекте, если host умеет выбор модели; всегда нужна
свежая сессия без разговора автора. Недоступность записывать честно.

| Сценарий | Что принять как результат |
|---|---|
| Ясный локальный баг | Реальная регрессия до/после; fix → checks → security → один review → local commit/finish; нет нового ordinary PLAN или challenge |
| Сложный баг | needs_planning → native fix-plan → явное разрешение исполнения → отдельный aif-fix Attempt; сохранены base, HEAD, claim, dirty/untracked работа |
| Отложенное решение | Без preanswer planner использует declared runtime decision и yield-execution, ждёт ответ; после ответа продолжается тот же Attempt |
| Отказ исполнять план | Явный false: partial с native планом; нет исполнения и фиктивного gate |
| Repair | Настоящая находка checks/security/review → отдельный repair → все включённые гейты последнего дерева |
| Blocked/cancelled/resume | Continue того же launch; accepted prefix и работа сохранены; после вмешательства дерево проверяется заново |
| Chained resume | Второй continue от текущего владельца claim; одна рабочая копия, растущие поколения, без reset/clean |
| Custom profile | Native `.ai-factory/fix-plans/FIX_PLAN.md` сохраняется staged/tracked; default файл снимает engine после capture; чужие PLAN/FIX_PLAN остаются |
| Предел/владельческий остаток | Partial с настоящей диагностикой; нет бесконечной починки или скрытого перехода в classic |

`settings.quality.repair_round_limit` в extend.yaml: default 3, диапазон 1..8.
Security отключается только явным `exclude: [security]`. Проектные TEST/MR
вставлять через documented root anchors build→quality или commit→done;
добавленным steps не передаются bound inputs. Не переносить classic anchors
или plan-specific bindings вслепую. Пилотные ветки/продуктовую работу не пушить.

Continue сначала подготовить и прочитать, затем принять его точный digest через
runner. Native plan не удалять до capture. При replay остановленного build с
tracked custom plan может потребоваться решение владельца. Если исполнение
плана было preanswered false, нельзя подменить ответ override в resume.

В отчёте пилота приложить Pri-Fly/AI Factory version, package origin/ref/commit,
host и profile, Run IDs и источники continue, фактический путь/исход,
implementation base/head, claim/generation, native manifest digests, команды и
вывод регрессии, gate findings, refusal code и path при отказе. Отдельно отметить
полученную reviewer сессию/модель и что не удалось проверить. Не включать секреты.
Issue для приёмки: [#4](https://github.com/StenHigh/prifly-aif-workflows/issues/4).

Локальная runtime матрица проверяет CLI/Git/capture с synthetic host.
[Реальный контроль](../tests/probes/results/aif-fix-0.13.76.md) подтверждает
короткий путь; полное LLM escalation/repair/resume остаётся задачей пилота.
Экономия времени/токенов не измерена; для сравнения нужны одинаковые задачи
и фактические метрики, число этапов её не доказывает.
