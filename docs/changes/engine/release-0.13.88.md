# Сверка после закрытия Pri-Fly #14

Дата проверки: 2026-11-09. Latest stable — [Pri-Fly0.13.88](https://github.com/StenHigh/prifly/releases/tag/v0.13.88).
Локальный main обновлён fast-forward до88bdc92. Изменений shipping packages здесь нет.

## Состояние задачи

[Core #14](https://github.com/StenHigh/prifly/issues/14) закрыт и поставлен в0.13.85.
Он поддерживает объявленные точки внутри child call/repeat и явные typed consumers.
Проектный measurement передаёт новый carrier следующему reader после repair.
Это opt-in composition/5 и folder/3; прежний опубликованный/4 сохранён.

[Consumer #9](https://github.com/StenHigh/prifly-aif-workflows/issues/9#issuecomment-6584207674)
тоже закрыт. Реализация опубликована в [workflows1.57.0](../../releases/v1.57.0.md).
Classic/profiled/fix/UIUX2.0.0 используют /5, feature1.4.0 переносит optional report refs.
Повторять эту реализацию не требуется. Полная историческая приёмка закреплена на Core0.13.86.

## Прочитанные выпуски

| Core | Изменение для consumer |
|---|---|
| 0.13.83 | Первые package-declared nested points/4 и typed consumers |
| 0.13.85 | Composition/5, public point exports/folder3, отдельные compiled variants; принято в workflows1.57.0 |
| 0.13.86 | Исправлен stale launch при composition5 и worktree_naming; выбран минимумом workflows1.57.0 |
| 0.13.87 | Versioned runner operations handbook; изменений workflow bytes не требует |
| 0.13.88 | Project profile5, отдельные naming inputs, --naming-input и сохранённый naming snapshot |

В списке стабильных выпусков нет0.13.84. Заметки87 краткие;
дополнительно прочитан [дифф86→87](https://github.com/StenHigh/prifly/compare/v0.13.86...v0.13.87).
Naming inputs88 остаются opt-in проектной настройкой. Приёмка этой новой настройки
не выводится из compile/compatibility. Новая пакетная реализация для неё не назначена.

## Проверки на official88

Использован ранее проверенный published Linux AMD64 binary из release assets.
Фактический SHA-256 совпал с опубликованным:
43bb756b7c44fe4c858496678d67b9eac48fb420bc99920f7a59a9209f7a3e85.
Пользовательский установленный CLI не менялся.

```sh
python3 -B tests/verify.py --binary /absolute/path/to/released/prifly
python3 -B tests/compatibility.py --binary /absolute/path/to/released/prifly
```

Путь binary — placeholder. Команды выполняются из корня репозитория.
Verify: восемь packages,132 components,88 Steps PASS.
Compatibility: пять launches, четыре distinct builds, шесть trusted packages,
profiled seal core-state/41 PASS. Оба tests удалили свои monitor registrations.
[Machine-readable результаты](release-0.13.88-results.json) фиксируют источник и границы.

## Отдельное наблюдение CI

Свежий [docs CI42571423001](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/42571423001)
прошёл compile/compatibility, но полный workflow завершился failure.
Fix probe получил project_workflow_commit_mismatch при установке из временного каталога:
catalog закреплял ee76702, а temporary source main разрешился в be9e92f.
Другие jobs также имели отказы установки Core. Их причины здесь не квалифицируются.

Этот CI не является новой полной приёмкой Core88.
Проверки report transport и исторические доказательства закрытия#9/#14 не переписаны.
Исправление test-install pins остаётся отдельной задачей.
