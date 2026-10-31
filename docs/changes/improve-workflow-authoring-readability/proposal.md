# Читаемые workflow: issue #6

Дата: 2026-10-31. Источник: [issue #6](https://github.com/StenHigh/prifly-aif-workflows/issues/6).

## Результат

Применить принятый patch `aif-classic`, проверить эквивалентность и выпустить пакет.
Затем перенести подход на остальные shipping packages отдельными проверяемыми порциями.
Владелец принял блочный YAML, Markdown-инструкции и README-карту по review.
Измеренного ускорения чтения не заявляем.

```text
classic patch → точная эквивалентность → версии + derived profiled → ворота → release/catalog
                                                                             ↓
остальные пакеты → inventory → отдельные изменения → эквивалентность → releases
```

## Объём

1. Проверить latest stable Pri-Fly и синхронизировать GitHub.
2. Применить закреплённый patch без потери последующих изменений.
3. Сравнить значения YAML, bytes инструкций, 12 пар сборок и восемь пар маршрутов до bump.
4. Повысить версии затронутых компонентов и зависимых workflow.
5. Получить `aif-profiled` штатным `tools/derive_profiled.py`.
6. Проверить итоговые пакеты, документацию, примеры и обновление с сохранением `extend.yaml`.
7. Выпустить проверенную порцию с точным catalog ref/commit.
8. Проверить остальные shipping packages по inventory и выпустить последующие порции.

Не менять ID, schemas, policies, ports, routes, limits и тексты инструкций ради оформления.
Не добавлять DSL, formatter или генератор. Короткие понятные файлы оставлять без механических изменений.
Дефект `verify fail/no_work` оформить отдельно; terminal outcome требует решения владельца.

## Приёмка

- Четыре YAML-объекта patch эквивалентны до bump.
- Decoded bridge: 9938 bytes, SHA-256 `8772b0ef8121540cceb00cd912ba005ef434ed7fe467fde6e88913262a1fd24c`.
- 12 пар: codex-cli/codex-app × canonical/local settings × fast/full/ultra.
- Восемь пар: owner-only, exhausted, disabled, clean, repaired, fail, no_work, blocked.
- Repaired implementation доходит до следующего verify и последующих quality stages.
- Итоговые версии, derived package, локальные ворота и exact-commit CI согласованы.
- README, release guide, catalog, examples и CONTEXT_STATE отражают результат.
- Inventory покрывает восемь shipping packages с изменением либо причиной сохранения.
- Published update сохраняет проектный `extend.yaml`.

Native probes используют synthetic replies и реальные CLI/Runs. Живые host/model integrations этим не принимаются.
