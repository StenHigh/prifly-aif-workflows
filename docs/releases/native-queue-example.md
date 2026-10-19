# Поставка примера native queue → aif-feature

Дополнение к v1.53.0 вне shipping packages: runnable example, qualification probe
и CI. Версия `aif-feature@1.2.3` сохраняется; catalog и package tag не меняются.
Core, deployed monitor и canonical classic/profiled не меняются.

Проверенная база — official Pri-Fly v0.13.80, Linux AMD64,
binary SHA256 `b5bc6d33206281c52afd3b17827e8cd416812d223d091f699d7883a382037a82`.
Перед следующей публикацией повторить latest stable проверку по AGENTS.md.

```sh
python3 -B tests/test_versions.py
python3 -B tests/test_folders.py
python3 -B tools/derive_profiled.py --check
python3 -B tests/verify.py --binary /absolute/path/to/released/prifly
python3 -B tests/compatibility.py --binary /absolute/path/to/released/prifly
python3 -B tests/probes/feature_queue_check.py \
  --binary /absolute/path/to/released/prifly --report /tmp/aif-feature-queue-results.json
git diff v1.53.0 -- aif-classic aif-profiled aif-fanout aif-fix aif-feature aif-review-evidence aif-ui-ux openclaw-test-audit
```

Последняя команда должна быть пустой. После изменения qualification code
повторить затронутые cases; после документационных изменений проверить команды
и входы примеров. Synthetic actors не заменяют реальный проектный пилот.

[Готовые входы и команды](../../examples/native-queue/README.md),
[критерии приёмки](../changes/qualify-native-feature-queue/proposal.md),
[наблюдённые результаты и ограничения](../changes/qualify-native-feature-queue/acceptance.md).
Локально3 cases /5 Runs и обязательные ворота PASS; remote CI этого изменения
ещё не запускался.
