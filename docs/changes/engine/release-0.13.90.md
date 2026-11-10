# Pri-Fly 0.13.90: проектные compile parameters

Проверка: 2026-11-10. [Core #22](https://github.com/StenHigh/prifly/issues/22) закрыт как completed.
Решение опубликовано в [stable v0.13.90](https://github.com/StenHigh/prifly/releases/tag/v0.13.90).
Source: `5e7f81cf5e6b53b72b86a937584e18f699f90ff9`.

Обе подписи release manifest и SHA-256 Linux amd64 архива проверены.
Binary SHA-256: `db8a158149088e6f9bfb9df3ebe5fc97e1b57942a620c78b65841f5c996bd984`.
Использован отдельный официальный binary; установленная dev-сборка не использовалась.

До изменения пакетов verify прошёл для 8 пакетов, 132 компонентов и 88 шагов.
Compatibility прошёл для 5 launches, 4 builds и 6 trusted packages; seal остаётся core-state/41.
После внедрения параметра эти ворота прошли повторно с теми же количествами.
Четыре monitor registrations от этих прогонов удалены.
Точная provenance и обе пары результатов: [release JSON](release-0.13.90-results.json).

## Изменения для пакетов

Новая capability `project_compile_parameters` использует два sidecar `/1`.
Пакет объявляет integer, диапазон, default и точные schema bindings в `compile-parameters.yaml`.
Проект сохраняет значения в `project/compile-values.yaml`.
Compiler применяет их до task validation в compile, prepare и start.
Поддерживаются Project profile `/3`–`/5`; прежние markers и Run wire contracts сохраняются.

```text
package declaration + owner values
  -> проверка типа и binding
  -> effective owned schema
  -> compile / prepare / reviewed start
  -> immutable definitions/task в новом Run
```

Для issue #3 механизм внедрён в candidate classic/profiled/fix3.0.0.
Task переходит с внешней frozen schema1.1.0 на owned schema1.2.0.
Default12 000 сохранён; project consumers используют `schema_task`.
Frozen contracts, независимые UI/UX и feature schemas сохраняют прежние bytes.
Полная пакетная приёмка, update и continue записываются в [change](../configure-task-description-limit/proposal.md).
