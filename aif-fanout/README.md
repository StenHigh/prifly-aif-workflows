# AI Factory fan-out workflow

Этот optional package дорабатывает существующий plan одним parallel pass:
независимые ракурсы `coverage` и `risk` → выбор разработчика → применение
принятых предложений. Он намеренно отделён от `aif-classic`.

Названия ветвей — ракурсы review, не имена моделей. Текущий assisted-session
adapter закрепляет instruction contexts, но **не** выбирает provider, model или
reasoning level. Этот package не является model routing: для этого нужен
будущий model-profile protocol.
