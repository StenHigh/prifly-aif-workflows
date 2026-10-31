# Передача исходных отчётов: issue #9

Статус: исследование на released Pri-Fly 0.13.82. Пакетная реализация ещё не принята.
Задача: [issue #9](https://github.com/StenHigh/prifly-aif-workflows/issues/9).

Следующий reader должен получать доступный исходный отчёт без обязательного повторного измерения.
Reader — шаг, который оценивает уже полученные данные.
Применимость отчёта определяет контракт проекта, а не наличие ссылки или успешная проверка схемы.

Минимальный кандидат: необязательный список `reports` в уже передаваемом `implementation`.
Каждый элемент содержит обычный ArtifactRef: artifact_id, целочисленную revision и digest.
Отдельный обязательный этап, runner, cache или язык выбора проверок не нужны.
Исходный отчёт задаёт проект. Пакет не задаёт язык приложения или команды проверок.

Native-пример подтвердил передачу исходного report/log через существующие Core primitives.
Он также воспроизвёл ограничение project extension для вложенного repair.
Ограничение требует решения до заявления о полной приёмке issue #9.

## Объём реализации после выбора порядка measurement

1. Расширить публичный carrier и сохранить ссылки implement/fix/verify/review на всех маршрутах.
2. Передавать обновлённый carrier через clean, disabled, repair/repeat и поддерживаемый continue.
3. Разрешить достаточный применимый receipt без безусловного повторного regression check.
4. Сохранять failed/unavailable/unknown отчёты и честно обрабатывать missing/stale/corrupt refs.
5. Подключать project measurement с нужными effects до reader, включая путь после repair.
6. Обновить версии, штатный profiled derive, README, release guide, catalog и examples.
7. Проверить actual classic/profiled/fix на released Core и отдельно обозначить границы LLM-приёмки.

Все критерии исходного issue остаются обязательными.
Generic fixture не заменяет приёмку shipping workflows.
