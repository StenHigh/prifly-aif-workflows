# Независимые UI/UX в aif-feature

В неопубликованном `aif-feature@1.2.3` можно явно выбрать `parallel-ui-ux`.
Нужны released Pri-Fly **0.13.77**, Python 3, Codex CLI с доступной авторизацией,
AI Factory skills (квалификация на 2.19.0) и проверенный browser adapter проекта.
По умолчанию feature остаётся sequential. Core и классические workflows не меняются.

Порядок: `checks → security → code review → {UI || UX} → cleanup → aggregate
→ repair либо guard/commit`. Оба reader получают один candidate и отдельные
sealed requests/browser grants. Они не редактируют код и не управляют окружением.
После repair весь quality round повторяется с новым snapshot и окружением.

## Настройка проекта

В project `extend.yaml` выбрать:

```yaml
profile: frontend
settings:
  feature:
    review_mode: parallel-ui-ux
  quality:
    limit: 3
exclude: []
extensions: []
```

Для `parallel-ui-ux` квалифицированы **1–3 полных quality-круга**. `limit: 4–8`
отвергается до writers по запечатанной configuration Run; значение не уменьшается
молча. Последовательный и backend parallel сохраняют прежний диапазон1–8.
Восьмираундовый frontend Run на released binary получил
`storage_budget_exhausted`; публичного CLI override этого бюджета нет.
Ограничение не увеличивает SQLite budget и не отменяет native storage guards.
Pure begin каждого круга повторяет проверку по typed limit, включая continuation
и внутренние вызовы; устаревшего host admission для обхода недостаточно.

Task содержит обычную frontend product configuration с UI/UX criteria и scenarios.
В ней `environment.shared_resource` должен быть `null`; поддерживается только
изолированный owned HTTP loopback origin с явным портом. Native quality resources
должны допускать обе Attempts: `limit: 1` не подходит даже для одного Run.

В существующей project configuration задать input `browser_adapter` (default
`null`) следующим JSON descriptor. Настройки и пути заменить на проектные:

```json
{
  "protocol": "aif-feature-browser/1",
  "root": "/absolute/reviewed/browser-adapter",
  "entrypoint": "adapter.py",
  "files": {"adapter.py": "sha256:<64 lowercase hex digits>"},
  "settings": {}
}
```

`root` — абсолютный каталог проверенного bundle. Все файлы исполнения bundle
должны быть перечислены с SHA256, включая entrypoint; максимум32 файла,
descriptor до64KiB. Пути относительные, без выхода из bundle и symlinks.
Source drift останавливает допуск. Внешние browser dependencies и их установка
тоже требуют проверки проекта: descriptor сам их не устанавливает и не аттестует.
Configuration input запечатывается в Run обычным механизмом Pri-Fly; в локальном
fixture descriptor передаётся как JSON в `settings.feature.browser_adapter`.

После `run drive` существующий runner явно вызывает:

```sh
python3 -B .prifly/workflows/aif-feature/files/parallel_host.py \
  --binary /absolute/released/prifly --project /absolute/authority \
  --run run:<ID> --host codex-cli --artifacts /absolute/owned/evidence
```

Один вызов обслуживает готовый admission/environment/readers/collector/release
batch. `handled:false` возвращает обычный этап существующему runner. Writers,
checks/security/code review и Run control остаются его ответственностью.
Путь artifacts должен быть постоянным для этого Run, вне claimed Git tree;
сохранять его до завершения cleanup/reconciliation. Сессии используют текущую
авторизацию Codex CLI, отдельные thread IDs и Attempt workspaces.

## Протокол project adapter

Helper запускает только проверенный Python entrypoint через `python -I -B`,
без shell и исполнения setup/cleanup prose. На stdin JSON с `protocol`,
`operation`, `settings` и указанными ниже полями; stdout — один JSON object
с тем же `protocol`. Размер ответа до4MiB. Timeout admit30s, остальных90s.
Полный исполняемый пример: [adapter](../tests/fixtures/feature-browser/adapter.py),
[browser](../tests/fixtures/feature-browser/browser.cjs). Это тестовый пример,
не универсальный сервер для приложений.

| Operation | Дополнительные поля запроса | Обязательный смысл ответа |
| --- | --- | --- |
| `admit` | `configuration` | `status: ready`, `capabilities` ровно `contexts: isolated`, `identities: isolated`, `environment: owned-loopback`, `cleanup: exact-owner-session`; иначе отказ до writers |
| `ensure` | `configuration`, `candidate`, `repository_workspace`, `run_id`, `attempt_id` | `status`, `reason`, `session`, `url`; при ready также `readers.ui/ux` с разными `context_id`, `identity_id` и своим `allocation` object |
| `observe` | `configuration`, `request`, `candidate`, `environment`, `browser_session`, `attempt_id`, `output_directory` | Только сценарии своего lens: `status`, `lens`, `context_id`, `identity_id`, `observations`; каждый item содержит `scenario`, `url`, `viewport`, observations, абсолютный путь `screenshot` и `screenshot_sha256` |
| `release` | `configuration`, `environment` | `release: {status, owner, session, reason}` для точного исходного owner/session |

Ensure допускает `ready/unavailable/owner_required/reconcile_required`.
Release допускает `released/not_needed/blocked/reconcile_required`.
Нельзя отвечать unavailable/not_needed после неизвестного внешнего эффекта.
Allocation привязан к Run, round, candidate, configuration, request, adapter,
owner и environment session. Другой lens не получает sibling grant. Observe
создаёт оригинальные PNG внутри своего Attempt output directory; shipped helper
сохраняет receipt с actual Attempt и native input refs. Controller проверяет
их перед отправкой любого native report и архивирует bytes с digest.

Отчёты сохраняются в исходных bytes; collector использует public artifact export.
Program gate проверяет manifest/refs/digests и прежние W1/W2 правила. Browser
наблюдения не выбирают verdict за reviewer. Fresh CLI session не доказывает другую
модель, корректность визуальной оценки или OS isolation. Проверенный адаптер —
доверенный код проекта: он обязан изолировать cookies/storage/identity и не
выполнять незаявленные внешние действия.

## Отмена и неизвестный исход

После обычного завершения обоих reviewers cleanup предшествует repair/commit.
Owner-only blocker приоритетнее дефекта другого lens. Missing/stale/invalid
evidence, недоступный браузер и неуспешный cleanup дают diagnostic stop.
Запрошенный parallel не заменяется молча на sequential или code-only review.

Native cancel сам не останавливает внешний браузер. Сначала controller должен
дождаться своих реальных actors. После terminal Run и settlement всех Attempts
оператор может освободить только своё окружение:

```sh
python3 -B .prifly/workflows/aif-feature/files/frontend_host.py cleanup \
  --binary /absolute/released/prifly --project /absolute/authority \
  --journal /absolute/owned/evidence/frontend/run-<ID>/attempt-<ID>.json
```

Команда сверяет journal с native accepted environment и исходными sealed
configuration/adapter, затем вызывает exact owner/session release. Исходный
Run она не переводит в success и reviewed continue не запускает.
Ошибка/timeout CLI до полного evidence callback оставляет `actor_phase: unknown`;
operator cleanup отказывает даже при terminal Native Run. После подтверждённого
завершения обоих actors и проверки evidence поздний отказ native submit сохраняет
`settled`. Native Attempt settlement сам по себе не подтверждает остановку browser.

Если controller был принудительно убит, actor phase неизвестна или ensure/release
прерван после внешнего эффекта, journal сохраняет intent: нужен осмотр собственных
процессов и effects, затем явная reconciliation. Автоматического retry, очистки
чужого listener и общего решения writer-cancellation E3 здесь нет.

При обновлении завершить существующие parallel Runs их прежним проверенным
helper. Новый source contract запечатывает семь Python файлов; companion другой
версии отказывает вместо исполнения по старому контракту. Перед запуском нового
режима проект отдельно проверяет новый bundle и обновляет конфигурацию.
