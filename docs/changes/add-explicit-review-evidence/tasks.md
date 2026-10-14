# Tasks W1

Реализация выполнена локально; evidence и ограничения — в [acceptance.md](acceptance.md).
Выпуск пакета/тега и каталог в эту сессию не входят.

- [x] Сверить текущие gate/challenge/session schemas и определить минимальный
  report и consumers без скрытого изменения shared contract (A1, A7, A9).
- [x] Описать check catalog, обязательность, методы, пропуски и candidate basis
  с воспроизводимой командой проверки (A1–A5).
- [x] Выбрать evaluator и existing bindings; явно определить, какие проверки
  машинные, какие основаны на отчёте host (A2, A5).
- [x] Реализовать schema, bridge и evaluator fixtures (A1–A7).
- [x] Прогнать RED/GREEN: missing/duplicate check, static вместо browser,
  unavailable required, optional skip, stale dirty/index/untracked/modes,
  intervening edits и resume до finish на released binary. У W1 нет собственного
  repair; повтор quality после такой записи относится к W3 caller (A1–A6, A8).
- [x] Проверить прежние пакеты, derive_profiled при необходимости и
  version/compile/compatibility gates; снять фактический continue boundary (A9).
- [x] Провести живую host-приёмку; указать honoured/unavailable отдельно,
  сохранить реальные versions, команды и наблюдения (A7, A8).
- [x] Записать acceptance matrix A1–A9, ограничения и migration notes.
- [ ] Выпустить отдельный package/repository release и обновить каталог после
  release-поручения. Новая папка подготовлена с initial version 1.0.0;
  тег и центральный каталог пока не опубликованы.
