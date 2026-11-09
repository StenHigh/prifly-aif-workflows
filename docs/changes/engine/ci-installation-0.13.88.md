# Исправление установки в CI

Дата: 2026-11-09. База: main `76e7b8b` и released Pri-Fly `v0.13.88`.
Изменения затрагивают тест и два workflow GitHub Actions.
Все опубликованные пакеты, contracts и каталоги сохраняют исходные bytes.

## Причины отказа

[CI42571423001](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/42571423001)
остановился по двум независимым причинам.

1. `fix_check --case install` создавал новый локальный Git-источник, но сохранял
   поле `commit` из опубликованного каталога. Поле `ref` указывало на локальный
   `main`. Core правильно отклонял несовпадение через `project_workflow_commit_mismatch`.
2. Скачивание official installer получило HTTP504. Команда `curl` завершила
   задание после первого запроса.

## Изменения

Fixture сначала создаёт commit пакета. Второй commit публикует каталог,
который закрепляет первый commit в полях `ref` и `commit`.
Проверка сравнивает recorded origin и каждый файл установленного пакета.
Публичный каталог и проверки целостности Core сохраняются.

```text
Пакет -> commit A -> каталог(ref=commit=A) -> установка -> Run
```

Все пять установок CI используют одинаковые ограниченные retries.
`curl` повторяет временные ошибки до пяти раз после первого запроса.
Connect timeout — 20 секунд, transfer timeout — 90 секунд,
retry budget — 180 секунд. Установщик по-прежнему выполняет штатную установку.
CI сохраняет полный `aif-fix-results.json` в артефакте `fix-workflow-results`.

## Проверки

Использован отдельный official Linux AMD64 binary.
SHA-256: `43bb756b7c44fe4c858496678d67b9eac48fb420bc99920f7a59a9209f7a3e85`.
Архив совпал с release manifest. Пользовательский CLI не обновлялся.

Исходный native case воспроизвёл named refusal; исправленный case завершился
`succeeded` с одним Run. Все созданные claims и registry entries очищены.
HTTP-стенд использовал фактические curl flags из обоих workflow:
504→200 дал два запроса; 404 — один; постоянный503 — шесть и ненулевой exit.
YAML, shell, versions4, folders7 и derive_profiled прошли.
Verify прошёл для 8 пакетов, 132 компонентов и 88 шагов.
Compatibility прошёл для 5 launches, 4 builds и 6 trusted packages.
Это проверка scripted fixture, без LLM и production deployment.

Команды выполняются из checkout этой ветки. Замените путь к binary на свой
абсолютный путь к official v0.13.88.

```sh
python3 -B tests/probes/fix_check.py --binary /absolute/released/prifly --case install --report /tmp/fix-install.json
python3 -B tests/verify.py --binary /absolute/released/prifly
python3 -B tests/compatibility.py --binary /absolute/released/prifly
```

[Машиночитаемые результаты](ci-installation-0.13.88-results.json) закрепляют
source hashes, локальные observations и финальный CI.

## Итог CI

[Полный CI42648113238](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/42648113238)
завершился SUCCESS во всех шести заданиях. Проверен точный commit
`5a6fc5e0d537b790091a07275ebc14160918d7b3`.
[Report transport42648113860](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/42648113860)
также получил SUCCESS.

Скачаны 10 артефактов; все ZIP digests и привязки к commit проверены.
Они содержат 21 JSON-отчёт. Reported версия —0.13.88; recorded binary SHA-256
совпадает с указанным выше. Полный fix-набор содержит 28 cases, включая install.
Feature-набор содержит 35 cases с очисткой; очередь содержит три cases.
Обязательные ворота, параллельные reviewers, UI/UX browser и measurement-матрицы прошли.

[PR #15](https://github.com/StenHigh/prifly-aif-workflows/pull/15) влит в main.
Финальная фиксация evidence меняет только документы. Код теста, оба CI workflows,
shipping packages, contracts и каталоги остаются прежними относительно проверенного commit.
Изменение не требует релиза пакетов. Приёмка Light и Core migration issue21
остаются отдельными задачами.

## Приёмка main после слияния

PR #15 влит squash-коммитом `432327656582521f1d428189a1f663a35a94c86c`.
Его Git-дерево точно совпадает с проверенным итоговым содержимым PR.

[CI main42661120199](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/42661120199)
завершился SUCCESS во всех шести заданиях.
[Report transport main42661120682](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/42661120682)
также получил SUCCESS. Это новые push-прогоны ветки main после слияния.

Скачаны 10 артефактов с 21 JSON-отчётом; digests и merge SHA проверены.
Версия Core —0.13.88, SHA-256 бинаря совпадает с official release.
Наборы fix28, feature35 и queue3 прошли, включая исправленную установку.
[Отдельные результаты main](ci-installation-0.13.88-main-results.json) сохраняют
эти доказательства отдельно от исторической приёмки PR.

Готовность CI main подтверждена. Финальный коммит записывает только результат
проверки; все исполняемые файлы, CI workflows и опубликованные пакеты прежние.
Приёмка production Light и миграция исторического revoke остаются отдельными задачами.
