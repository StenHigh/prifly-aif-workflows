# W6 — consumer qualification

Реализованы project-owned recipes review/UIUX/combined и installer с reviewed
preview/apply. База — **официальный Pri-Fly0.13.80**, Linux amd64,
SHA256 `b5bc6d33206281c52afd3b17827e8cd416812d223d091f699d7883a382037a82`.
Движок, server deployment и все8 shipping packages не менялись.

## Подтверждено

| Наблюдение | Результат / граница |
| --- | --- |
| Legacy verify/compatibility | PASS:126 definitions,83 steps,8 packages;5 launches/4 builds/4 trusted. |
| Project compilation | Три режима × minimal/classic ×3 hosts:18 компиляций PASS. Это compile, не живые hosts. |
| Native placement | Review/UIUX/combined доходят до commit в обоих consumers. У classic только fixture project extend с fast/exclude improve; root/shipped files прежние. |
| Native ownership | Один Run/claim; dirty/untracked реализация проверяется до final commit. Original report refs/digests сохраняются в assessment. |
| Error decisions | Defect, unavailable, stale request, candidate edit, missing check, owner stop и cleanup failure останавливают приёмку; source bytes остаются прежними. |
| Post-commit race | Изменение файлов после seal отклоняет finish. Локальный commit может уже существовать; rollback не выполняется. |
| Owned browser | Chromium на declared desktop/mobile/flow; normal release перед commit; cancel требует operator cleanup. Synthetic fixtures не являются AI-вердиктом. |
| Scoped actual host | Combined classic succeeded:3 свежих Codex CLI-сессии, одна review и две UI/UX, один candidate/claim, среда освобождена,1 локальный commit. |
| Published source boundary | Все8 package trees совпадают с v1.53.0. Версии/catalog/tag прежние; добавление находится в examples/docs/tests/tools. |

Original live reports, native submissions/receipts, browser observations и
скриншоты — [evidence/live](evidence/live). [Сводка](evidence/live-results.json)
фиксирует session IDs и результаты; [fingerprints](evidence/live-artifacts.json)
позволяют сверить остальные исходные артефакты. Полные event streams остались
в локальном `/tmp/aif-w6-live80`; они не нужны для запуска recipe.

Live-квалификация ограничена reviewer-ами этого изолированного consumer.
Writer/classic checks/commit обслуживал synthetic controller, Git commit и
native программа выполнялись реально. Другие модели не аттестованы; App/Claude
здесь не проходили live review. Initial live request был кратким «Check declared
behavior»: reviewer честно отметил неоднозначность criteria как warning и
выполнил фактический unittest. В поставляемом примере description после этого
уточнён до полной команды и ожидаемого поведения. Это не скрытый PASS более
строгого request. Warnings допускались явной optional_policy:ignore.

## Завершаемые проверки

Native полная matrix, fresh replay с intervening edit, accepted-prefix
continuation и Core51 на0.13.80 выполняются; сводка и exact-SHA CI будут
зафиксированы после фактического завершения. Промежуточные результаты не
закрывают W6-A7/A8/A10 целиком.

## Границы квалификации

- Normal cleanup/release проверен. Cancel останавливает native reader, а owned
  fixture освобождает controller по exact owner/session; это **operator
  reconciliation**, а не гарантированный finally-tail графа.
- Timeout/unknown ensure/release и остановка внешнего actor требуют контракта
  среды проекта. Общая forced writer cancellation E3 не решена W6.
- Logical round остаётся sealed config round; повтор создаёт fresh artifacts,
  не скрытое изменение criteria. Partial child повторяется целиком. После
  принятого child и отказа commit native prefix может переносить receipt;
  изменённые файлы post-guard не пропускает, нужен reviewed replay приёмки.
- Installer не повышает budgets/permissions. Limits/resource/storage/trust
  отказы Core проверяются отдельно; W6 shared-resource среда не квалифицирована
  и installer её отклоняет. Бюджет custom loops/extensions проверяет проект.
- Private consumer/environment из [issue#2](https://github.com/StenHigh/prifly-aif-workflows/issues/2)
  не становится qualified результатами notes fixture. Его admission остаётся
  отдельной работой; W5 parallel grants не подключены.

[Команды и migration](../../../examples/review-uiux-extensions/README.md) ·
[Release guide](../../releases/project-examples-w6.md) · [W6-A1–A10](proposal.md).
