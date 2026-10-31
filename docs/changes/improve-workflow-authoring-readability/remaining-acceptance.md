# Приёмка остальных пакетов issue #6

Дата: 2026-10-31. База — опубликованный v1.54.0/source5d4169b.
Статус: local gates и все три CI jobs PASS. Выпуск v1.55.0 опубликован на source42e60de.
Annotated tag/GitHub Release v1.55.0 и центральный каталогe2ba0ed опубликованы.

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
[Standalone install/update](remaining-install.json): все6 packages установлены по одному без других folders.
Все18 host compiles PASS; exact candidate bytes, extend.yaml и project/owner.txt сохранены.
Update отказал при локальном изменении tracked upstream/Markdown. Fixtures/registry очищены.
[Готовые examples](remaining-example-launches.json): четыре reviewed prepare/start PASS.
Host/model/environment setup не исполнялись. Cleanup разрешил только собственные недоставленные writer Attempts как not_applied.
Claims0, registry1 и temporary root удалены.
[Compatibility](remaining-compatibility.json):5 launches/4 builds/4 trusted/core-state41 PASS.
[Parallel contracts](remaining-parallel-contract.json) и [parallel product contracts](remaining-parallel-product-contract.json): по3 hosts PASS.
[W6 contracts](remaining-w6-contract.json):18 compiles и8 честных refusals PASS.
[Source negative guard](shared-source-negative.json) отказал при LF→CRLF и source другого package.
[Final semantics/manifest](remaining-source-manifest.json):210 YAML objects равны кроме explicit versions/source representation;273 shipping files закреплены hashes.
Все134 локальные Markdown links существуют.

[Fix companion native](fanout-fix-native.json):28 cases PASS.
[Audit native](audit-native.json):18 cases PASS, включая standalone и opt-in extension.
[Review evidence native](shared-evidence-native.json):25 cases PASS, включая upgrade, refused prefix и три hosts.
[Feature upgrade](shared-feature-upgrade.json): два Runs, real Markdown change и сохранённый claim PASS.
[Fanout native](fanout-native.json): clean/selected succeed; stopped сохраняет прежний отказ.
Каждый завершённый native probe исполняет собственный cleanup; отсутствующие поля в JSON не заменяют asserts fixture.
[CI W6](remaining-ci-w6.json): source42e60de,18 compiles/8 refusals/27 native cases, all cleaned/upstream preserved PASS.
[CI parallel UI/UX](remaining-ci-parallel-uiux.json): SUCCESS; official82/hash сверены,17 reported cases cleaned.
[Полный CI](remaining-ci-results.json): все три jobs SUCCESS на source42e60de.
Итоговые artifacts подтвердили feature35/queue3/classic8 pairs с cleanup и official82/hash.
Verify также прошёл final real-browser product/feature suites.

Fanout clean и selected routes завершаются succeeded. Его прежний choose:no_work приводит к failed/unhandled_child_outcome.
Root обрабатывает только succeeded дочернего improve-pass. Probe фиксирует этот прежний отказ, без нового terminal outcome.
Fix/audit/review/UI/UX/feature используют существующие native probes с real CLI/Git и synthetic replies.
Живые модели, host independence и ускорение чтения этой проверкой не квалифицируются.

[Guide кандидата](../../releases/v1.55.0.md) содержит версии, команды и отдельные opt-in примеры.

## Публикация

[PR #10](https://github.com/StenHigh/prifly-aif-workflows/pull/10) объединён fast-forward на exact tested source42e60de.
[GitHub Release v1.55.0](https://github.com/StenHigh/prifly-aif-workflows/releases/tag/v1.55.0) и annotated tag указывают на этот commit.
[Каталогe2ba0ed](https://github.com/StenHigh/prifly-workflows/commit/e2ba0ede03094511cca930ddcdc1fb4688df4884) закрепляет все8 entries на v1.55.0/source42e60de.
README/package файлы в теге сохраняют checkpoint подготовки; этот ledger фиксирует фактическую публикацию.
Публикационные evidence и внешние examples обновляются документационным коммитом; shipping/test/tool bytes остаются прежними.

[Публичный add/update](remaining-published-install.json): все6 packages установлены через default catalog.
Реальный GitHub update v1.54.0→v1.55.0 получил exact origin42e60de и bytes файлов Git-тега.
Каждый пакет собрался на3 hosts без других workflow folders. Owner extend.yaml/project сохранились; local edit вызвал отказ.
Registry1 и temporary root очищены; реальные host/model/server operations не выполнялись.
