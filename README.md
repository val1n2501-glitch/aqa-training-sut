# AQA Training SUT

Учебный Task Manager для практики Python AQA. SUT (System Under Test) — приложение, на котором ученик самостоятельно разрабатывает API- и UI-автоматизацию.

Приложение позволяет создавать и редактировать задачи, менять статус и приоритет, назначать срок, искать, фильтровать и удалять записи. Данные хранятся в SQLite и сохраняются после перезапуска. Backend — FastAPI и SQLAlchemy, frontend — HTML, CSS и JavaScript.

## Место в курсе

| Компонент | Роль |
|---|---|
| Course Site | Уроки, задания и прогресс |
| ChatGPT Project | Персональный наставник |
| SUT | Приложение под тестирование |
| Student repository | Собственная автоматизация ученика |

Для работы ученика есть отдельный [student template](https://github.com/val1n2501-glitch/aqa-automation-student-template). Этапы обучения описаны в [roadmap](docs/student-roadmap.md). Этот репозиторий содержит приложение и небольшие проверки его запуска.

## Быстрый запуск

Нужны Git, Python 3.13 и [uv](https://docs.astral.sh/uv/getting-started/installation/). Команды ниже предназначены для macOS/Linux (bash/zsh).

```bash
git clone https://github.com/val1n2501-glitch/aqa-training-sut.git
cd aqa-training-sut
uv sync --locked
uv run --locked python -m app
```

После запуска откройте [интерфейс](http://127.0.0.1:8000/), [Swagger](http://127.0.0.1:8000/docs) или [health](http://127.0.0.1:8000/api/health). Остановка — Ctrl+C. База по умолчанию создаётся в `data/tasks.db`.

Версия стенда — **1.0.0**, стабильный тег — `v1.0.0`. Пока PR в `main` не слит, ветка по умолчанию — `release/v1`; обычный clone получает рабочий стенд.

Для воспроизводимой работы выбирайте версию из [Releases](https://github.com/val1n2501-glitch/aqa-training-sut/releases), переключайтесь на соответствующий тег и снова выполняйте `uv sync --locked`. Версию стенда записывайте в README своего проекта автоматизации.

На Windows используйте PowerShell: команды `git`, `uv sync --locked` и
`uv run --locked python -m app` те же. uv автоматически создаёт `.venv`.
Если нужна явная активация: macOS/Linux — `source .venv/bin/activate`,
PowerShell — команда ниже.

```powershell
.\.venv\Scripts\Activate.ps1
```

## Конфигурация

[.env.example](.env.example) — справочник переменных. Приложение не загружает `.env` автоматически: переменные нужно передать через окружение процесса.

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `APP_HOST` | `127.0.0.1` | Адрес сервера |
| `APP_PORT` | `8000` | Порт сервера |
| `DATABASE_URL` | SQLite-файл `data/tasks.db` в проекте | Хранилище задач |
| `TEST_MODE` | `false` | Доступ к служебному reset |
| `BASE_URL` | Задаётся для UI smoke | Адрес уже запущенного стенда |

В обычном режиме reset отсутствует, в том числе в OpenAPI. `TEST_MODE=true` используйте только для отдельной учебной БД: reset удаляет все задачи в выбранной базе. Формат reset и seed описан в [API-контракте](docs/api-contract.md).

## Минимальные проверки

В репозитории шесть проверок жизнеспособности: health, главная страница, Swagger, один POST → GET, недоступность reset в обычном режиме и открытие страницы с формой в браузере. Они не заменяют собственный набор тестов ученика.

Пять API-проверок работают через TestClient с временной SQLite:

```bash
uv run --locked pytest -m api
```

Для UI smoke установите Chromium:

```bash
uv run --locked playwright install chromium
```

В первом терминале запустите обычный сервер с отдельной БД:

```bash
TEST_MODE=false DATABASE_URL=sqlite:///./data/ui-smoke.db APP_PORT=8001 uv run --locked python -m app
```

Во втором терминале, из той же папки проекта:

```bash
BASE_URL=http://127.0.0.1:8001 uv run --locked pytest -m ui
```

В PowerShell для первого терминала задайте `$env:TEST_MODE="false"`,
`$env:DATABASE_URL="sqlite:///./data/ui-smoke.db"`, `$env:APP_PORT="8001"`,
затем выполните `uv run --locked python -m app`. Во втором терминале:
`$env:BASE_URL="http://127.0.0.1:8001"` и `uv run --locked pytest -m ui`.
На Linux системные зависимости браузера устанавливаются командой
`uv run --locked playwright install --with-deps chromium`.

После проверки остановите сервер через Ctrl+C. Проверки стиля:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
```

GitHub Actions устанавливает зависимости, запускает Ruff, API smoke и один UI smoke против обычного сервера с `TEST_MODE=false`.

## Docker

Нужен запущенный Docker. Соберите образ и запустите приложение с отдельным volume для данных:

```bash
docker build -t aqa-training-sut:1.0.0 .
docker volume create aqa-training-data
docker run --name aqa-training-sut -p 127.0.0.1:8000:8000 -v aqa-training-data:/data aqa-training-sut:1.0.0
```

Откройте интерфейс на порту 8000. Именованный volume сохраняет задачи при пересоздании контейнера. Для остановки из другого терминала:

```bash
docker stop aqa-training-sut
```

Для повторного запуска существующего контейнера: `docker start -a aqa-training-sut`. Значение `TEST_MODE` в образе по умолчанию — `false`.

## Структура

```text
app/             # приложение, SQLite, API и frontend
tests/           # минимальные технические smoke-проверки
docs/            # контракт и ориентиры самостоятельной работы
.github/         # CI стенда
Dockerfile
pyproject.toml
uv.lock
```

[API-контракт](docs/api-contract.md) описывает поведение приложения. [Направления тестирования](docs/test-cases.md) помогают сформировать собственный план, а [bug lab](docs/bug-lab.md) объясняет идею будущей отдельной лаборатории.

## Ограничения

Это локальный учебный стенд без аутентификации и разграничения доступа. Не размещайте в нём реальные персональные или конфиденциальные данные. Миграции схемы БД и координация независимых параллельных тестовых сессий не реализованы. Для отдельных запусков используйте отдельные базы.

## Условия использования

Авторские права на стенд сохраняются. Разрешены личное обучение, некоммерческое обучение и использование стенда в учебном портфолио с указанием источника. Включение в платные курсы требует письменного разрешения правообладателя; выдавать стенд за собственную разработку нельзя. Полные условия — в [LICENSE](LICENSE). Собственную автоматизацию размещайте в отдельном student repository и явно отделяйте её авторство от авторства стенда.
