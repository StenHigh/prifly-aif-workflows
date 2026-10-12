# Исправления после живого пилота: aif-fix 1.0.1

2026-10-13. Основание — [живой отчёт #4](https://github.com/StenHigh/prifly-aif-workflows/issues/4#issuecomment-6132513896).
Выпущенный Pri-Fly 0.13.76, darwin/arm64; binary SHA-256
`5df5aceccde63c173d3f38f20426eb9dd131e6c3b0f6511a99002ad874a49f00`.
Новых stable выпусков при сверке не было.

## Разбор замечаний

| Наблюдение | Вывод и действие |
|---|---|
| Usable pass + gate.status blocked дошёл до succeeded | Дефект routing воспроизведён на 1.0.0: RED, source Run `run:11ee126583a6cc692fb5096c6cedea229b76c77a63237080f1c4d0f313a70ca4`. В 1.0.1 status blocked останавливает checks/security/review с точным gate; required unavailable dependency не превращается в success |
| short_checks="" нельзя записать как answer="" | Воспроизведён answered_questions_invalid, pointer /answered_questions/0/answer. answer — nonempty prose в report API. Session-report context у всех 9 Attempts объясняет допустимое представление; typed decision/ledger остаются пустыми. Core API не изменён |
| Внешняя QA после публикации недоступна | Разделены unrun required checks (blocked) и optional acceptance вне scope (warning по gate_warnings). Succeeded короткого workflow не доказывает внешнюю QA-приёмку |
| Разрешение плана описано basis instructions | Сам report не является runtime permission. Уточнено использование delivered fix_plan_execution/declared decision с сохранением уже предоставленного разрешения; без ledger не заявляем новый баг или новую авторизацию |
| Resume --workspace, prepare до settled cancel | Ожидаемые ограничения core; инструкция уточнена. Режим claim наследуется, перед prepare cancel доводится drive до terminal |
| persistence_unavailable и audit.sh без npm | Доступ CLI к authority и проектная среда supporting audit. Не исправляются расширением эффектов read-only gates или ручной правкой core storage |
| Standing npm advisories | По отчёту не введены изменением manifests/locks. Не превращаем работу над workflow в починку зависимостей пилота |

Пилот подтвердил реальные escalation/repair/chained resume в своей заявленной
границе. Продуктовый путь включал repair, отдельного clean direct LLM Run без
repair в нём не было. Его оставшиеся отрицательные/custom/host/model случаи
не считаются проверенными нами.

## Регрессии и ворота

[Машинный отчёт](aif-fix-pilot-fixes-0.13.76.json): **28 разных сценариев PASS**.
Предыдущая полная матрица дополнена четырьмя API/routing regressions:

- `blocked-pass-check`, `blocked-pass-security`, `blocked-pass-review`: первое
  исполнение partial с точным digest переданного blocked gate, без repair или
  commit; после восстановления зависимости resume до succeeded. Исходный fix
  не повторён, один claim переносится с generation 1→2.
- `empty-question-answer`: буквальный пустой answer отвергнут; исправленное
  описание принято в том же Attempt, а ledger short_checks по-прежнему "".
  Измерение заканчивается ready после принятого отчёта; cleanup отменяет Run,
  освобождает claim и удаляет стенд/monitor entry. Это проверка API, не LLM Run.

Новый session-report context закреплён compile-gate у всех 9 steps. Compile
всех четырёх пакетов, трёх hosts/двух fix profiles и отрицательные contracts —
PASS; compatibility, 10 static tests, derive_profiled и diff check — PASS.
Classic/profiled/fanout bytes не изменены. Runtime host синтетический,
CLI/Git/capture/materialisation настоящие; новый LLM pilot здесь не запускался.
Install отдельно перепроверен после изменения release entry на v1.51.1.

```sh
python3 -B tests/probes/fix_check.py --binary /path/to/released/prifly --report /tmp/fix-results.json
```

## Обновление остановленных Run

[Фактический prepare](aif-fix-1.0.1-upgrade-prepare.json) от partial v1.51.0
к исправленному 1.0.1: **recover_prefix_changed at warmup**. Новый reporting
context меняет effective contract; source run_version, HEAD, dirty/untracked
bytes исходного claim остаются прежними. Стенд/claim/monitor entry удалены.

Не обещаем перенос старого accepted prefix через это изменение. Закончить
старый Run на установленном v1.51.0 перед update либо отдельно рассмотреть
engine-предложение explicit replay `--from-stage warmup`. Полный cross-version
replay не исполнялся; его base/evidence нельзя объявлять сохранёнными на
основании одного prepare. Same-version resume, включая chained, зелёный.

Версии изменённых bridges, всех 9 steps, 4 workflows/package/root подняты;
новый reporting context имеет собственную identity. Issue #4 остаётся открытым
для оставшихся реальных пилотных проверок. Экономия времени/токенов не измерена.
