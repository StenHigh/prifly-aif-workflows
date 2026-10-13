# Пилот: отдельный aif-fix (актуально для v1.51.2)

Пакет `aif-fix:package/fix@1.0.2` не меняет classic/profiled/fanout.
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

Если пакет уже установлен, используйте `project workflows update aif-fix --ref v1.51.2`,
сохранив проектный extend.yaml. Прямая установка закреплённого выпуска:

```sh
prifly project workflows add StenHigh/prifly-aif-workflows --path aif-fix --ref v1.51.2 --repository .
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
[Первый host-контроль](../tests/probes/results/aif-fix-0.13.76.md) и
[живой пилот](https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6132513896)
отдельно подтверждают наблюдённые fix/escalation/repair/resume маршруты.
[Финальная приёмка bridge v1.51.2](../tests/probes/results/aif-fix-bridge-1.0.2-live.md)
проверяет естественные blocked reports и свежие readers после continue.
Issue #4 закрыт в описанных границах; эта инструкция остаётся для следующих
пилотов, без заявления о проверке всех специальных случаев.
Экономия времени/токенов не измерена; для сравнения нужны одинаковые задачи
и фактические метрики, число этапов её не доказывает.

## Уточнение после живого отчёта: aif-fix 1.0.1

Gate status blocked останавливает quality даже при usable pass и blocking=false.
Если внешняя QA оставлена на последующую публикацию и не входит в обязательные
проверки этого workflow, обозначить её как warning с точной границей проверки;
не смешивать это с недоступной обязательной зависимостью.

В answered_questions.answer нельзя передавать пустой текст: для short_checks=""
дать объяснение «Пустая строка: дополнительных checks не настроено», basis
decision и decision_id short_checks. Typed decision остаётся пустой строкой.
Report с basis instructions сам не фиксирует runtime fix_plan_execution.

Continue не принимает --workspace. После cancel сначала довести Run штатным
drive до terminal, затем prepare; persistence_unavailable требует доступа CLI
к authority, а не ручной правки её хранилища. Не выдавать npm audit, не запущенный
в PHP-контейнере без npm, за выполненный; подобрать применимое окружение проверки.

Переход остановленного v1.51.0 на исправленные контракты даёт
recover_prefix_changed на warmup. Закончить старый Run на его установленной
версии до update либо отдельно просмотреть предложенный engine полный replay
с --from-stage warmup. Автоматический перенос старого accepted prefix здесь
не обещан; работа/source Run при prepare не меняются. Не выполнять reset/clean.

## Уточнение bridge: aif-fix 1.0.2 / v1.51.2

Verdict — пригодность отчёта, gate.status — результат и доступность проверки.
Для установленной недоступности обязательной внешней зависимости вернуть pass
с status blocked и доказательствами: Run остановится partial без repair/commit.
Verdict blocked оставить для Attempt, который не может сформировать пригодную
оценку; обязательный диагностический gate всё равно нужен. Не заменять required
blocked на passed/warnings. Usable needs_revision маршрутизируется так же.

Изменились контракты quality, а не warmup/build. Проверенный переход partial
на blocked quality из v1.51.1 в v1.51.2: prepare принимается с frontier quality,
reuse warmup/build; после reviewed continue все quality gates исполняются заново.
Для partial на commit после принятого quality проверен отказ
recover_prefix_changed на quality; reviewed --from-stage quality повторяет все
гейты и commit до succeeded. Перед replay просмотреть prepare и точный digest.
