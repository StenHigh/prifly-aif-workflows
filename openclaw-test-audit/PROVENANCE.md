# Происхождение

Checklist адаптирован из MIT-licensed [OpenClaw test-audit](https://github.com/openclaw/openclaw/blob/70bfdc2b58e42f02af5bdc4d345875a9e6ad3928/.agents/skills/test-audit/SKILL.md),
commit `70bfdc2b58e42f02af5bdc4d345875a9e6ad3928`. Точные пути и SHA-256
прочитанных исходников записаны в [upstream.json](upstream.json), лицензия —
в [LICENSE.openclaw](LICENSE.openclaw). Это встроенная адаптация, не ссылка на
меняющийся `main` во время исполнения. Установка OpenClaw skill на хост не нужна.

Сохранены критерии независимого контракта, реальной регрессии, дублирования,
границ проверки и production seams, а также правила сохранения полезных
статических, протокольных, release и других независимых проверок.

Область сужена до тестовых путей текущей задачи. Массовое удаление тестов,
редактирование production, OpenClaw pnpm/Vitest команды, внешние testbox hosts,
autoreview и их PR/merge-процедуры не перенесены. Запуск тестов и baseline proof
остаются проектными проверками. Read-only reviewer сообщает, что наблюдал,
а что заключил по коду. Он не переключает дерево Run для проверки старой версии.

`files/candidate.py` использует неизменённые функции `git`, `snapshot`, `digest`
и `encoded` из нашего `aif-review-evidence/files/evidence.py` выпуска v1.52.0
(алгоритм `git-candidate/1`). Изменены только заголовок модуля и набор содержимого:
review-specific evaluator и CLI в эту копию не входят. Исходный пакет не менялся.
Выбор тестов, формат аудита и evaluator реализованы здесь отдельно.
