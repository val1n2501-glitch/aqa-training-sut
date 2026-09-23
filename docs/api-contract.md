# API-контракт v1

Базовый адрес локально: `http://127.0.0.1:8000`. Формат данных — JSON, даты — ISO. Swagger: `/docs`, схема: `/openapi.json`.

## Модель

| Поле | Тип и ограничения | Создание / PUT |
|---|---|---|
| id | integer от 1 до 2⁶³−1, сервер | клиентское поле запрещено |
| title | string, trim по краям, 1–120 символов после trim | обязательно |
| description | string, 0–2000, без trim | `""` |
| status | todo / in_progress / done | todo |
| priority | low / medium / high | medium |
| due_date | YYYY-MM-DD, существующая календарная дата, или null | null |
| created_at | UTC datetime, сервер | клиентское поле запрещено |
| updated_at | UTC datetime, сервер | клиентское поле запрещено |

Прошедшие даты разрешены. Время и Unix timestamp вместо даты не разрешены. Неизвестные поля отклоняются. Строковые поля не принимают числа. `null` разрешён только у `due_date`. Регистрозависимые enum не преобразуются автоматически.

`TaskCreate` используется для POST и PUT. `TaskUpdate` — для PATCH. `TaskResponse` добавляет серверные поля. В PATCH пропущенное поле сохраняется; `due_date: null` очищает срок. Пустой PATCH `{}` отклоняется. PUT восстанавливает значения по умолчанию для всех пропущенных необязательных полей.

## Endpoints

| Метод и путь | Вход | Успех |
|---|---|---|
| GET /api/health | — | 200 `{"status":"ok","test_mode":false}` |
| GET /api/tasks | query ниже | 200 TaskList |
| POST /api/tasks | TaskCreate | 201 TaskResponse |
| GET /api/tasks/{task_id} | положительный integer | 200 TaskResponse |
| PUT /api/tasks/{task_id} | TaskCreate | 200 TaskResponse |
| PATCH /api/tasks/{task_id} | TaskUpdate | 200 TaskResponse |
| DELETE /api/tasks/{task_id} | положительный integer | 204, без тела |
| POST /api/test/reset | ResetRequest | 200, только TEST_MODE=true |

Health выполняет запрос к БД. Все CRUD-запросы к отсутствующему положительному ID дают 404. Неверный ID, например `abc`, `0` или значение больше 2⁶³−1, даёт 422. Если одновременно неверно тело запроса и отсутствует задача, валидация запроса выполняется раньше поиска и возвращает 422.

## Список

`GET /api/tasks?q=python&status=todo&priority=high&sort_by=created_at&order=desc&limit=20&offset=0`

- `q`: максимум 200 символов; подстрока в title OR description; Unicode casefold, trim по краям. Пустой/пробельный q не фильтрует. `%`, `_` и `\` не являются шаблонами SQL.
- `status`, `priority`: допустимые enum, при отсутствии фильтра нет. Фильтры и поиск сочетаются через AND.
- `sort_by`: `id` (default), `title`, `status`, `priority`, `due_date`, `created_at`, `updated_at`.
- `order`: `asc` (default) / `desc`.
- `limit`: integer 1–100, default 20.
- `offset`: integer от 0 до 2⁶³−1, default 0.
- Порядок priority: low < medium < high; status: todo < in_progress < done.
- Title сортируется с Unicode casefold. Даты без значения всегда последние. Вторичная сортировка — id ASC независимо от направления основной.
- Неизвестные query-имена игнорируются FastAPI. Пустые status/priority/sort_by/order недопустимы.

```json
{
  "items": [
    {
      "id": 7,
      "title": "Изучить HTTP",
      "description": "Методы и статус-коды",
      "status": "todo",
      "priority": "high",
      "due_date": null,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

`total` вычисляется после фильтров, до limit/offset. Offset за концом списка возвращает `items: []`, сохраняя total. По умолчанию данные идут по id ASC. Тело DELETE отсутствует: не вызывайте `.json()` на успешном удалении.

## Ошибки

422:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Некорректные входные данные",
    "details": [
      {
        "loc": ["body", "title"],
        "message": "String should have at least 1 character",
        "type": "string_too_short"
      }
    ]
  }
}
```

404:

```json
{"error":{"code":"not_found","message":"Задача не найдена","details":[]}}
```

Стабильны обёртка и имена полей, `code`, типы `loc/message/type`. Текст и type конкретной ошибки валидации определяются закреплённой версией Pydantic; при обновлении зависимостей могут измениться. Ошибка на уровне всей модели имеет `loc: ["body"]`; query — `["query", "имя"]`; путь — `["path", "task_id"]`. Некорректный JSON тоже даёт 422. `input` и внутренний `ctx` не возвращаются.

Другие HTTP-ошибки, например 405, имеют `code: "http_error"`, `message` и пустой `details`. Неожиданные серверные сбои дают обычный 500; их traceback не входит в документированный контракт ошибок.

## Примеры запросов

Примеры для macOS/Linux bash/zsh; в Windows проще использовать Swagger (в PowerShell `curl` может быть алиасом).

```bash
curl --fail-with-body http://127.0.0.1:8000/api/health
curl --fail-with-body -X POST http://127.0.0.1:8000/api/tasks -H 'Content-Type: application/json' -d '{"title":"Изучить HTTP","priority":"high"}'
curl --fail-with-body 'http://127.0.0.1:8000/api/tasks?status=todo&limit=5&offset=0'
```

Для чтения/изменения/удаления используйте **ID из ответа POST**, не предполагая, что это 1. В Swagger заполните `task_id` этим значением. PATCH с `{"status":"done"}` сохранит остальные поля; PUT с `{"title":"Другое название"}` вернёт остальные поля к defaults.

## Reset и seed

При `TEST_MODE=false` маршрут отсутствует, включая OpenAPI; вызов вернёт 404 с message `Not Found`. Никакого публичного DELETE всей коллекции нет (405).

В тестовом режиме `POST /api/test/reset` требует JSON-объект. `{}` или `{"seed":false}` очищает БД. `{"seed":true}` атомарно заменяет данные фиксированным набором:

| id | title | description | status | priority |
|---|---|---|---|---|
| 1 | Изучить HTTP | Методы и статус-коды | todo | high |
| 2 | Написать API-тест | Проверить создание задачи | in_progress | medium |
| 3 | Открыть Swagger | Изучить контракт API | done | low |

Все сроки null, timestamps `2026-01-01T00:00:00Z`. Ответ: `{"message":"Тестовые данные сброшены","count":3}` (или 0). `seed` — строго JSON boolean, неизвестные поля запрещены. Seed ID фиксированы для ручных упражнений; обычные CRUD-тесты должны читать ID из ответа. Reset не сбрасывает AUTOINCREMENT.

Пример для отдельного тестового сервера на 8001:

```bash
curl --fail-with-body -X POST http://127.0.0.1:8001/api/test/reset -H 'Content-Type: application/json' -d '{"seed":true}'
```

## Совместимость и ограничения

v1 намеренно меняет ранний учебный контракт: `done` → `status`, GET списка → объект с items/total/limit/offset, DELETE → 204, безусловное удаление коллекции → условный тестовый reset. Аутентификации, CORS для отдельного frontend-домена и блокировки конкурирующего редактирования нет. UI и API работают с одного origin. Последнее успешное обновление задачи побеждает.
