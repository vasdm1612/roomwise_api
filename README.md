# RoomWise API

RoomWise API — учебный REST-сервис на FastAPI для управления переговорными комнатами, оборудованием и бронированиями.

Дополнительная бизнес-задача проекта — endpoint `/recommendations/slots`, который подбирает подходящие свободные слоты с учетом вместимости комнаты, оборудования, занятости и предпочтительного времени пользователя.

## Что реализовано

- Реляционная SQLite-БД, которая создается автоматически при запуске приложения.
- 5 связанных таблиц: `users`, `rooms`, `equipment`, `room_equipment`, `bookings`.
- JWT-аутентификация и роли `admin` / `user`.
- CRUD для комнат, оборудования и бронирований.
- Связь комнат с оборудованием через отдельную таблицу `room_equipment`.
- Проверка конфликтов бронирований и вместимости комнаты.
- Алгоритм рекомендации свободных слотов.
- Административный отчет по загрузке комнат за выбранный период.
- Pydantic-схемы и валидация входных данных.
- Автоматические тесты через FastAPI TestClient.
- Конфигурация pytest, coverage и pylint в `pyproject.toml`.

## Стек

FastAPI, Pydantic v2, SQLite, PyJWT, pytest, pytest-cov, pylint.

## Структура проекта

```text
roomwise_api/
├── app/
│   ├── api/              # FastAPI routers
│   ├── core/             # settings, database, security, dependencies
│   ├── services/         # CRUD and business logic
│   ├── main.py           # application entry point
│   └── schemas.py        # Pydantic schemas
├── tests/                # TestClient tests
├── README.md
├── requirements.txt
├── pyproject.toml
├── pylint.txt
└── .gitignore
```

## Запуск локально

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Установка зависимостей и запуск сервера:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

После запуска доступны:

- Swagger UI: http://127.0.0.1:8000/docs
- Health-check: http://127.0.0.1:8000/health

## Авторизация

1. Зарегистрируйте пользователя через `POST /auth/register`.
2. Получите JWT-токен через `POST /auth/login`.
3. В Swagger нажмите **Authorize** и вставьте сам токен.
4. В обычных HTTP-запросах используйте заголовок `Authorization: Bearer <token>`.

Пример регистрации администратора:

```json
{
  "email": "admin@example.com",
  "full_name": "Admin User",
  "password": "strongpass123",
  "role": "admin"
}
```

## Основные endpoints

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Rooms

- `POST /rooms`
- `GET /rooms`
- `GET /rooms/{room_id}`
- `PATCH /rooms/{room_id}`
- `DELETE /rooms/{room_id}`
- `POST /rooms/{room_id}/equipment/{equipment_id}`
- `DELETE /rooms/{room_id}/equipment/{equipment_id}`

### Equipment

- `POST /equipment`
- `GET /equipment`
- `PATCH /equipment/{equipment_id}`
- `DELETE /equipment/{equipment_id}`

### Bookings

- `POST /bookings`
- `GET /bookings`
- `GET /bookings/{booking_id}`
- `PATCH /bookings/{booking_id}`
- `DELETE /bookings/{booking_id}`

### Recommendations

- `POST /recommendations/slots`

Пример тела запроса:

```json
{
  "window_start": "2026-06-03T09:00:00",
  "window_end": "2026-06-03T12:00:00",
  "duration_minutes": 60,
  "participants_count": 4,
  "required_equipment_ids": [1],
  "preferred_start": "2026-06-03T10:00:00"
}
```

### Reports

- `GET /reports/room-utilization`

## Бизнес-логика рекомендаций

Endpoint `/recommendations/slots` принимает временное окно, длительность встречи, число участников, список необходимого оборудования и предпочтительное время начала.

Алгоритм:

1. выбирает только активные комнаты;
2. отбрасывает комнаты с недостаточной вместимостью;
3. проверяет наличие обязательного оборудования;
4. анализирует существующие бронирования в заданном интервале;
5. находит свободные промежутки достаточной длины;
6. рассчитывает `score` для каждого варианта;
7. возвращает лучшие варианты в формате JSON.

## Тесты и покрытие

```bash
pytest
```

В `pyproject.toml` задан порог покрытия 70%:

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=70
```

## Pylint

```bash
pylint app > pylint.txt
```

Файл `pylint.txt` находится в репозитории и содержит результат проверки качества кода.

## Информация об авторе

Дмитрий Васимов.
