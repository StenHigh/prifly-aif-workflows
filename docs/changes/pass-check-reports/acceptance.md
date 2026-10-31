# Приёмка исследования

Основа: released Pri-Fly0.13.82. Проверяется generic wiring с синтетическими ответами.
Shipping classic/profiled/fix пока не изменены. Issue #9 остаётся OPEN.

Проверка запускается одной командой из корня репозитория:

```sh
python3 -B tests/probes/report_transport.py \
  --binary /absolute/path/to/released/prifly \
  --output /tmp/report-transport-results.json
```

Driver проверяет compile, реальные Runs, output slots, declared bindings и public artifact export.
Он удаляет completed producer Attempt directory перед первым reader.
Он сравнивает исходные refs и байты report/log, а не только равные JSON-значения.
Каждый case освобождает claims и удаляет monitor registration временной authority.

| Case | Проверка | Граница |
|---|---|---|
| success | Один producer, reader и project consumer получают исходный report/log | Нет прикладной suite |
| repair | Два read, один producer и один root project measurement; refs/basis прежние | Только явно unrelated metadata |
| failed | Exit1/status failed сохранены; reader blocked, root partial | Consumer на success не исполняется |
| continue | Reviewed continue переиспользует produce/measure и повторяет cycle | Новый Run; не внутренний resume Attempt |
| unknown/missing/substituted refs | Public export обязан отказать | Не сканируется authority store |
| nested extension | Существующий child edge отвергается по имени | Положительный root control исполняется |

Ожидаемые отказы export: unknown → not_found; missing revision/substituted digest → integrity_failure.
Ожидаемый отказ child insertion: project_extension_unknown_workflow, round (known: transport).
Финальные [native-results.json](native-results.json): четыре cases / пять Runs PASS.
Все двенадцать отрицательных exports получили ожидаемые коды.
Каждый case завершился без active claims и удалил одну monitor registration.
Binary SHA-256: 3b073126921bca3e9d78b7649b51bd20527fd70cf4de44e0d440b5428b7712e5.
Static versions4/folders7 и штатный profiled derive --check PASS.
Отдельный CI workflow повторяет generic reproducer на latest stable и сохраняет JSON artifact.

[CI41229072017](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/41229072017)
на source95ea2cb завершился SUCCESS. Скачанный artifact повторяет4 cases/5 Runs,
двенадцать ожидаемых export refusals и cleanup каждого case.
Core version и binary SHA-256 совпадают с local.
[CI record](ci-results.json) закрепляет source, artifact hash и результаты.
Полный [workflow verify41229071851](https://github.com/StenHigh/prifly-aif-workflows/actions/runs/41229071851)
также завершился SUCCESS на том же functional source.
Shipping8 bytes точно равны v1.56.0. PR#12 остаётся draft для исследования issue #9.

Владелец согласовал полную автоматизацию и Core-задачу 2026-11-01.
[Pri-Fly #14](https://github.com/StenHigh/prifly/issues/14) закрепляет reproducer и ожидаемый порядок/bindings.
Создание Core issue не означает поставку capability или завершение consumer issue #9.

Не заявлена приёмка disabled shipping gates, actual fix regression reuse, stale environment,
unknown report schema, внешнего provision/release, старых sealed Runs или решения живой модели.
Эти случаи входят в оставшуюся приёмку issue #9.
