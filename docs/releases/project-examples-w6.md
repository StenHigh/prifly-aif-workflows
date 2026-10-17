# W6 — поставка проектных примеров без нового package tag

Новые [recipes](../../examples/review-uiux-extensions/README.md) поставляются
из checkout этого репозитория. Это дополнение к v1.53.0: каталог и bytes всех
восьми пакетов сохраняются, canonical classic/profiled также прежние.
Самостоятельные W1/W2 остаются в каталоге в версиях1.0.0.

Минимум для native call extension — Pri-Fly0.13.78. Проверенная база текущего
изменения — официальный stable0.13.80. Profile/4 naming из этого выпуска
необязателен: installer сохраняет /4, а /2 переводит только в /3.

До публикации изменений примеров на main:

```sh
python3 -B tests/test_versions.py
python3 -B tests/test_folders.py
python3 -B tools/derive_profiled.py --check
python3 -B tools/build_review_uiux_bundle.py --check
python3 -B tests/test_call_review.py
python3 -B tests/verify.py --binary /absolute/path/to/released/prifly
python3 -B tests/compatibility.py --binary /absolute/path/to/released/prifly
python3 -B tests/call_review_contract.py --binary /absolute/path/to/released/prifly --report /tmp/w6-contract.json
python3 -B tests/probes/call_review_check.py --binary /absolute/path/to/released/prifly \
  --matrix --jobs 3 --browser-library /absolute/path/to/playwright --report /tmp/w6-native.json
```

Для installer/builder нужен PyYAML из requirements примера. Для browser fixture
используйте зафиксированный lockfile и Chromium:

```sh
npm ci --ignore-scripts --no-audit --no-fund --prefix tests/fixtures/product
tests/fixtures/product/node_modules/.bin/playwright install --with-deps chromium
```

Те же проверки добавлены в отдельный CI job `call-review-uiux`, рядом со всеми
прежними jobs. LLM-сессии в CI не запускаются: actual host qualification
проводится отдельно и не подменяется synthetic matrix. Команда scoped combined
classic с реальными reader-сессиями (нужны локально проверенные upstream skills):

```sh
python3 -B tests/probes/call_review_check.py --binary /absolute/path/to/released/prifly \
  --mode combined --consumer classic --live-skills /absolute/path/to/pinned-aif-skills \
  --browser-library /absolute/path/to/playwright --artifacts /tmp/w6-live \
  --report /tmp/w6-live.json
```

Skills directory содержит `aif-review.md` и `severity.md` AI Factory2.19.0;
caller обязан проверить их source/hashes. Квалифицируется только выбранный
изолированный consumer и host; private project environment остаётся отдельной
приёмкой. [Фактические результаты и ограничения](../changes/add-review-uiux-call-extensions/acceptance.md).

Снимите source fingerprints, проверьте CI implementation commit и сохраните
original reports/receipts перед очисткой временного стенда. Перед будущим
package release повторите latest-stable сверку по AGENTS.md; этот change не
даёт основания обновлять версии прежних пакетов или выпускать новый tag.
