# Система «Производственный анализ»

Django-приложение для оперативного учёта и анализа выполнения производственных планов.

## Разработка

1. Устанавливаем **uv**: 
   - `pip install uv`
2. Устанавливаем **.venv**:
    - `uv sync`
3. Поднимаем локальную бд: 
   - `docker-compose up` (не забудьте запустить приложение **Docker**)
4. Актуализируем бд: 
   - `uv run manage.py migrate`
5. Добавляем тестовые данные (флаг --clear для очистки предыдущих данных): 
   - `uv run manage.py setup_demo_data`
6. Запускаем: 
   - `uv run manage.py runserver`

> В корне проекта должен быть `.env`!

**! Проверить линтеры:** `pre-commit run --all-files`

(если не работает, то сначала: `pre-commit install`)

## Использование
Откройте в браузере: http://localhost:8000/

Тестовые учётные записи:
- Оператор: 100001 / PIN: 1234
- Мастер: 300001 / PIN: 1234
- Начальник: 200001 / PIN: 1234
- Администратор: 100000 / PIN: 0000


## Структура проекта

```
production-analysis/
├── shift_report/           # Основное приложение
│   ├── models/            # Модели данных
│   ├── views/             # Представления
│   ├── templates/         # Шаблоны
│   ├── urls/              # URL-маршруты
│   ├── services/          # Бизнес-логика
│   ├── forms/             # Формы
│   └── management/        # Команды управления
├── docs/                   # Документация
├── static/                 # Статические файлы
└── manage.py
```

## URL-маршруты

### Общие

| URL | Описание |
|-----|----------|
| `/` | Главная страница |
| `/login/` | Вход в систему |
| `/logout/` | Выход |
| `/profile/` | Профиль пользователя |
| `/change-pin/` | Смена PIN-кода |

### Оператор

| URL | Описание |
|-----|----------|
| `/operator/` | Дашборд оператора |
| `/operator/blank/<id>/` | Просмотр бланка |
| `/operator/record/<id>/input/` | Ввод данных |

### Мастер

| URL | Описание |
|-----|----------|
| `/master/` | Панель мониторинга |
| `/master/workplace/<id>/` | История РМ |
| `/master/blank/<id>/` | Мониторинг бланка |
| `/master/deviation/<id>/measure/` | Добавление меры |

### Бланки

| URL | Описание |
|-----|----------|
| `/blanks/` | Список бланков |
| `/blanks/create/` | Создание бланка |
| `/blanks/bulk-create/` | Массовое создание |
| `/blanks/templates/` | Шаблоны бланков |

### Аналитика

| URL | Описание |
|-----|----------|
| `/analytics/` | Дашборд аналитики |
| `/analytics/deviations/` | Анализ отклонений |
| `/analytics/comparison/` | Сравнительный анализ |
| `/analytics/reports/` | Отчёты |

### Администрирование

| URL | Описание |
|-----|----------|
| `/system/` | Панель администратора |
| `/system/import/` | Импорт данных |
| `/system/export/` | Экспорт данных |
| `/system/directory/<type>/` | Просмотр справочника |
| `/admin/` | Django Admin |

## Модели данных

### Справочники

- `Workshop` — Цеха
- `Sector` — Участки
- `Workplace` — Рабочие места
- `Product` — Продукция
- `Shift` — Смены
- `DeviationGroup` — Группы причин
- `DeviationReason` — Причины отклонений
- `Employee` — Сотрудники

### Документы

- `PABlank` — Бланк производственного анализа
- `PARecord` — Почасовая запись
- `DeviationEntry` — Запись об отклонении
- `TakenMeasure` — Принятая мера
- `PATemplate` — Шаблон бланка


## Импорт начальных данных

### Порядок импорта

1. Цеха (`workshops`)
2. Участки (`sectors`)
3. Рабочие места (`workplaces`)
4. Смены (`shifts`)
5. Продукция (`products`)
6. Группы причин (`deviation_groups`)
7. Причины отклонений (`deviation_reasons`)
8. Сотрудники (`employees`)

### Пример CSV для сотрудников

```csv
personnel_number,first_name,last_name,middle_name,role,workshop_code,sector_code,workplace_code,pin,is_active
100001,Иван,Иванов,Иванович,operator,WS001,SEC001,WP001,1234,true
100002,Пётр,Петров,Петрович,master,WS001,SEC001,,1234,true
```