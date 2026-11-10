# Проверка выпуска и вывод старой сборки

Пример сопровождает [issue #17](https://github.com/StenHigh/prifly-aif-workflows/issues/17).
Он использует текущую проверку выпуска из этого checkout и официальный Pri-Fly `v0.13.90`.
Папки опубликованных пакетов не меняются.
Это самостоятельная проверка выпуска; она не подключает шаг к workflow и не запускает Run.

## Подготовка

1. Подставьте абсолютный путь checkout вместо `SOURCE`.
2. Подставьте путь официального бинаря `v0.13.90` вместо `PRIFLY_BIN`.
3. Выполните команды из корня checkout с полной историей Git и tags.

```sh
SOURCE=/absolute/path/to/aif-workflows
PRIFLY_BIN=/absolute/path/to/prifly-v0.13.90
TOOLS=/tmp/aif-compiled-version-tools
python3 -m venv "$TOOLS"
"$TOOLS/bin/python" -m pip install PyYAML==6.0.1
cd "$SOURCE"
"$PRIFLY_BIN" version
```

## Проверка собранных компонентов

```sh
"$TOOLS/bin/python" -B tests/test_compiled_versions.py
"$TOOLS/bin/python" -B tests/compiled_versions.py \
  --binary "$PRIFLY_BIN" --report /tmp/aif-compiled-versions.json
```

Проверка выбирает предыдущий стабильный tag автоматически.
Для явной базы добавьте `--baseline v1.57.0` к последней команде.
На самом release tag проверка сравнивает сборку с предшествующим выпуском.
Для обеих сторон она использует один бинарь, одинаковые stub skills и настройки владельца по умолчанию.
Матрица охватывает восемь пакетов, три hosts и все package profiles.

```text
Предыдущий tag -> compile --+
                           +-> вид + ID + версия + SHA-256 -> решение выпуска
Checkout ------> compile --+
                           +-> отдельный сценарий: инструкция / схема -> новая версия шага
```

Вид компонента, ID и итоговая версия задают его идентичность.
При разных отпечатках одной идентичности команда завершается с `compiled_definition_drift` и ненулевым кодом.
Новая итоговая версия допускает новые bytes.
Сценарий зависимостей отдельно проверяет изменение инструкции и схемы без изменения YAML шага.
Повторная сборка тех же входных данных должна сохранить версию и отпечаток.
Все authority временные; проверка удаляет собственные регистрации monitor после завершения.

Это дополнительная проверка перед выпуском.
Полный CI также проверяет компиляцию, запуск, continue и независимые сценарии пакетов.
[Приёмка](../../docs/changes/guard-compiled-component-versions/acceptance.md) указывает фактический результат и границы проверки.

## Вывод старой сборки после обновления

Сначала завершите зависимые Run и сохраните исходники для нужного continue.
Команды ниже работают с выбранной authority — каталогом состояния Pri-Fly.
Они не относятся к временным authority проверки выпуска.

```sh
AUTHORITY=/absolute/path/to/prifly-state
"$PRIFLY_BIN" --project "$AUTHORITY" run list --limit 100
"$PRIFLY_BIN" --project "$AUTHORITY" package list
```

Просмотрите состояние Run. Возьмите ID и точную старую версию сборки из `package list`.
Подставьте их в `OLD_PACKAGE_ID` и `OLD_BUILD_VERSION` перед следующей командой.
Итоговая версия сборки может отличаться от авторской версии пакета.

```sh
OLD_PACKAGE_ID='REPLACE_WITH_OLD_PACKAGE_ID'
OLD_BUILD_VERSION='REPLACE_WITH_EXACT_OLD_BUILD_VERSION'
"$PRIFLY_BIN" --project "$AUTHORITY" package remove \
  --id "$OLD_PACKAGE_ID" --version "$OLD_BUILD_VERSION" \
  --reason 'Retire the old edition after dependent Runs finish'
```

Если Run удерживает пакет, команда отказывает. Сохраните пакет до разрешения зависимости.
`package remove` выводит сборку из доверенных и освобождает её записи реестра.
`package restore` позволяет вернуть ту же сборку.
`package revoke` необратимо отзывает доверие и блокирует старые pins.
Не используйте `revoke` для штатного обновления или устранения конфликта версий.
`project workflows remove` отдельно удаляет установленную папку workflow вместе с её настройками.
Подробности сохранения настроек находятся в [README](../../README.md#настройка-командой).
