# W6 — план qualification

Статус: **consumer qualification не выполнялась**. Prerequisite A1 подтверждён:
released0.13.79, verify/compatibility/contracts и E5 corpus51 PASS
([evidence](../engine/release-0.13.79.md)). Ниже будущая consumer matrix, а не PASS
A2–A10. Историческая неподдерживающая база0.13.77 остаётся step-only extend.

| Группа | Обязательные наблюдения | Критерии |
| --- | --- | --- |
| Native contract | Released E5: exact call refs,1/3 inputs, downstream outputs; missing/ambiguous/wrong-kind refs, late producer/type mismatch/incomplete outcomes refused. | A1, A3, A5 |
| Consumers | Review-only, sequential UI/UX-only и combined: authored minimal graph + project extend над установленным classic; source bytes canonical прежние. | A2, A9 |
| Ownership | Один parent Run/claim и actual working candidate, включая dirty/index/untracked; original report refs/digests доступны. | A3, A4 |
| Decisions | Успех проходит; defect, required unavailable, owner blocker, missing/stale report и cleanup failure не достигают commit. Warnings policy explicit. | A5, A6 |
| Browser | Реальные scenarios и Chromium observations, точные owner/session, cleanup перед продолжением. Приватный consumer не подменяется fixture. | A6, A10 |
| Recovery | Cancel/timeout/child error, settlement, operator reconciliation, fresh whole-child replay, intervening edit; unknown effects не retry вслепую. | A6, A7 |
| Compatibility | Изменения callee/route/config между prepare/start и после accepted child; exact digest refusal/replay point; legacy step extensions прежние. | A7, A9 |
| Limits | Depth/steps/transitions/resource/storage/effect/trust limits; refusal без silent override, внешние actors не считаются остановленными по Native state. | A8 |
| Host matrix | Compile/runtime на поддерживаемых hosts с synthetic receipts отдельно; scoped actual consumer на заявленном host и отдельная отметка browser/model/session evidence. | A10 |

Сохранять supporting release/binary SHA256, exact implementation SHA, команды,
результаты, original artifact identities, source-boundary hashes и final CI URL.
Только после фактического выполнения отметить соответствующие W6-A пункты PASS.
Classic fixture не квалифицирован до проверки placement/freshness и budgets
именно с неизменным upstream root. Отдельный успешный consumer это не заменяет.
