## Разработка

1. Устанавливаем **uv**: 
   - `pip install uv`
2. Устанавливаем **.venv**:
    - `uv sync`
3. Поднимаем локальную бд: 
   - `docker-compose up` (не забудьте запустить приложение **Docker**)
4. Актуализируем бд: 
   - `uv run manage.py migrate`
5. Запускаем: 
   - `uv run manage.py runserver`

> В корне проекта должен быть `.env`!

**! Проверить линтеры:** `pre-commit run --all-files`

(если не работает, то сначала: `pre-commit install`)