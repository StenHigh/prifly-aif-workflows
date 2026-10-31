# Приёмка остальных пакетов issue #6

Дата: 2026-10-31. База — опубликованный v1.54.0/source5d4169b.
Статус: source-кандидат подготовлен; local native проверки и exact-source CI выполняются.
Выпуск v1.55.0 и центральный каталог не опубликованы.

## Разделение изменений

1. Fanout/fix: сложные bindings, joins, conditions, native captures и 11 Markdown instructions fix.
2. Test audit: две Markdown instructions; существующий graph уже раскрыт.
3. Review/UI/UX/feature: 21 Markdown instruction и сложные quality/parallel mappings.

```text
база v1.54.0 → YAML/Markdown → точные pre-bump пары → версии и зависимости
                                                   ↓
                                  standalone install → native/CI → выпуск
```

Classic/profiled сохраняют все bytes v1.54.0. Изменения не исправляют issue #7.
Короткие scalar ports, host-skill pointers, схемы и Python contexts сохраняют прежнюю форму.
Их bindings целиком видны рядом с ключами; executable code не переносится в Markdown.

## Равенство до повышения версий

[Fanout/fix](fanout-fix-pre-bump.json): девять пар на трёх hosts и обоих fix profiles.
[Test audit](audit-pre-bump.json): три пары на трёх hosts.
[Review/UI/UX/feature](shared-pre-bump.json): 12 пар, включая оба feature profiles.
Все24 пары совпали по package identity, build_key, component refs и SHA-256 всех sealed bytes.
Нормализация identity/versions не применялась. YAML objects с разрешённым source равны.
Все34 extracted инструкции совпали с прежними decoded UTF-8 bytes, включая завершающий LF при его наличии.
Pre-bump файлы фиксируют длину и SHA-256 каждой инструкции.
После bump compiled identity намеренно меняется; равенство старых build keys больше не требуется.

## Самостоятельность и проектные копии

Shared guards сравнивают metadata и raw Markdown bytes между W1/W2/W3.
Допускается только различие собственного package-local prefix в source.
Guard требует существующий source внутри своей package folder.
Переименованные disposable parallel fixtures копируют Markdown и меняют только собственный prefix.
W6 builder разрешает source в inline text проектной копии и фиксирует hash Markdown в manifest1.0.1.
Generated W6 component files сохраняют exact bytes и версии1.0.0.
Upgrade probes меняют реальный Markdown и context version; obsolete inline string replacement удалён.
Install/update probes редактируют реальный Markdown и проверяют project_workflow_modified.

## Ворота

Official released Pri-Fly0.13.82, binary SHA-256:
`3b073126921bca3e9d78b7649b51bd20527fd70cf4de44e0d440b5428b7712e5`.
Versions4, folders7, десять существующих unit/guard suites и W6 builder --check PASS.
Verify126 components/83 steps/8 packages PASS после extraction/bump.
Native и install/overlay результаты дополняются после завершения; незавершённый CI не считается PASS.

Fanout clean и selected routes завершаются succeeded. Его прежний choose:no_work приводит к failed/unhandled_child_outcome.
Root обрабатывает только succeeded дочернего improve-pass. Probe фиксирует этот прежний отказ, без нового terminal outcome.
Fix/audit/review/UI/UX/feature используют существующие native probes с real CLI/Git и synthetic replies.
Живые модели, host independence и ускорение чтения этой проверкой не квалифицируются.

[Guide кандидата](../../releases/v1.55.0.md) содержит версии, команды и отдельные opt-in примеры.
