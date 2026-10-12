# aif-fix: проверка на выпущенном Pri-Fly 0.13.76

2026-10-12, darwin/arm64. Release archive SHA-256:
`98eeae48df326eb5108493bd2e24fde5d96505b4fffd2afb67ca260ef92a299c`.
Проверенный binary SHA-256:
`5df5aceccde63c173d3f38f20426eb9dd131e6c3b0f6511a99002ad874a49f00`.
Это GitHub release asset, не локальная dev-сборка.

## Runtime: 24 различных сценария — PASS

[Машинный отчет](aif-fix-0.13.76.json): перед выпуском v1.51.0 полная
матрица из 24 сценариев повторно прошла одним запуском, включая лимит repair
и установку через подготовленный Git-каталог. Host синтетический, навыки — stubs. CLI Runs, Git-коммиты,
регрессионные команды, capture/materialisation и эффекты настоящие.

| Проверка | Фактический результат |
|---|---|
| Direct, codex-cli/codex-app/claude-code | `succeeded`, local commit, final implementation; без нового ordinary/native плана или challenge |
| Catalog search/add, security exclusion, extension | Установка по имени, объявленный launch; bypass security и generic insertion выполняются |
| Escalation default/custom | Разные Attempts fix-plan/fix-from-plan; digest созданных и материализованных native bytes совпадает; base и tracked/untracked работа сохранены |
| Decision wait / plan-stop | Нет preanswer: timed yield, ожидание ответа и redelivery того же Attempt с новым envelope; явный false: partial с native планом, без фиктивного gate |
| Default/custom lifecycle | Untracked default удаляется engine после capture; custom staged/tracked остается и коммитится с актуальным progress |
| Repair check/security/review | Отдельный repair, затем check-change → enabled security → review-task текущего дерева |
| Repair limit | При лимите 1: partial с настоящим последним gate, без commit и ложного успеха |
| Blocked fix/plan/execution, owner review, cancelled check/review | Continue сохраняет работу и один исходный claim; поколения 1→2, затем finish |
| Chained resume + intervening edits | Три Run, claim 1→2→3; новое сломанное дерево замечено и исправлено; accepted warmup/build не выполняются повторно на quality resume |
| Foreign PLAN/FIX_PLAN | Файлы другой задачи сохраняются; owner stop до planner не выдает intake за gate |
| Missing output / read-only mutation | Ожидаемые `output_required_missing` / `effect_not_permitted`; исправленный отчет закрывает Attempt перед очисткой |

Resume prepare не меняет HEAD, dirty/untracked bytes и source run_version.
Итоговый implementation digest сравнивается с фактическим final HEAD/tree.
Отрицательные output/effect кейсы заканчивают измерение на `ready`, после
ожидаемого отказа и принятого исправленного отчета; cleanup отменяет Run,
освобождает claim и удаляет запись monitor. Это не отрицательный workflow success.
Каждый стенд удален; отсутствие active claims проверяется явно.

Воспроизведение всей текущей матрицы:

```sh
python3 -B tests/probes/fix_check.py --binary /path/to/released/prifly --report /tmp/aif-fix-results.json
```

## Compile, compatibility и classic

`tests/verify.py`: PASS, четыре пакета, 59 прочитанных компонентов, 34 steps.
Новый fix компилируется для трех hosts и обоих profiles. Отрицательные fixtures
подтверждают missing implementation binding, missing blocked handler и запрет
external_write. Старый route probe отдельно проверяет unavailable native plan.

`tests/compatibility.py`: PASS, пять launches, четыре разных builds/trusted
packages; граница — первый assisted handoff. Static tests: 10 PASS.
`tools/derive_profiled.py --check` и `git diff --check`: PASS.
Classic probes pass, blocked→resume, cancelled→resume: PASS в их прежней
границе — verify и следующий handoff, без заявления о полном classic finish.
Файлы aif-classic/aif-profiled/aif-fanout не изменены.

## Отдельное наблюдение настоящего host

[Trace и output digests](aif-fix-real-host-0.13.76.json). Codex выступал host
изолированного Run, читая настоящие skills AI Factory 2.19.0. Основной путь
дошел через шесть Attempts до local commit и `succeeded`. Эта проверка началась
до отделения security bridge от classic; финальный отдельный security adapter
покрыт runtime matrix, а его LLM repair-ветка здесь не наблюдалась.

Skill aif-fix запросил два Explore reader: отдельно cause и callers/history,
оба read-only. Реальная ошибка `total(2)==1`, `total(None)==-1` воспроизведена
до правки. После минимальной правки тот же `python3 -B regression.py` зеленый;
project overlay запретил logging чистой функции, learning patch сохранен.

Reviewer был новой сессией только с sealed inputs и claimed tree, без разговора
автора. Он проверил callers/history, diff и untracked patch; свежие regression,
zero/negative/float/Decimal/Fraction checks прошли без вывода. Выбор конкретной
модели `independent-review` недоступен: записан warning под gate_warnings=ignore,
а не обещание независимой модели. Отсутствующий ROADMAP тоже отмечен warning.
Security checklist просмотрен, automated audit script в mounted skill отсутствовал
и не запускался — это явно отражено в gate. Fixture commit выполнен без GPG
подписи после локального sandbox-отказа signer; глобальные настройки не менялись.
После finish стенд, claim и monitor entry удалены.

## Границы и выпуск

LLM escalation/repair/resume, manual/runtime reproduction без automation,
safe-cause fallback и interaction runner на всех hosts не проверены этим
наблюдением. Сведение контрактов и lifecycle этих веток подтверждены synthetic
runtime, а реальный интерфейс советов имеет отдельный
[отчет Pri-Fly #3](https://github.com/StenHigh/prifly/issues/3#issuecomment-6127736839).
Claude pagination/dismissal там отложены. После upgrade нужен runners update.

Поддержаны два явных fix-plan path profiles. При replay build с уже tracked
custom plan может потребоваться решение владельца; автоматический custom
restart не обещан. Arbitrary paths требуют reviewed profile, экономия токенов
и времени не измерялась.

Первый выпуск нового пакета — v1.51.0 (aif-fix 1.0.0). Центральный каталог
закрепляет release ref/commit; байты остальных пакетов остаются прежними.
Инструкция для последующей приёмки пилотом —
[docs/pilot-aif-fix-v1.51.0.md](../../../docs/pilot-aif-fix-v1.51.0.md).
Перед тегом весь текущий набор из 24 сценариев прогнан повторно; машинный отчет
содержит результат этого прогона, исходное real-host наблюдение сохранено отдельно.
