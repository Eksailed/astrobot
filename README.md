# 🌌 AstroBot — Персональный AI-Астролог + Mini App

Персонализированный астрологический сервис с искусственным интеллектом для Telegram: точные расчеты по швейцарским эфемеридам (`pyswisseph`), ежедневные транзитные гороскопы, расклады Таро и умный чат с «астрологом» на базе **Qwen 2.5 72B** (через OpenRouter).

---

## 🚀 Стек технологий

* **Telegram Bot:** Python 3.11, `aiogram 3.x`, FSM-сценарии.
* **Астрологическое ядро:** `pyswisseph` (Swiss Ephemeris), `geopy`, `timezonefinder` (автоопределение часового пояса и точный перевод времени рождения в UTC).
* **ИИ:** OpenRouter API (`qwen/qwen-2.5-72b-instruct`) с динамической инъекцией натального паспорта и транзитов.
* **База данных и кэш:** PostgreSQL (SQLAlchemy 2.0 async + `asyncpg`), Redis (суточные лимиты и сессии).
* **Платежи:** Telegram Stars (`XTR`), подписка PRO (299 ₽ / 150 Stars).
* **Mini App:** React 18, Vite, TailwindCSS, `@telegram-apps/sdk-react`.
* **API:** FastAPI (валидация `initData` по HMAC-SHA256).

---

## 📂 Структура проекта

```text
astro_bot/
├── bot/
│   ├── handlers/          # Хэндлеры команд (/start, /horoscope, /tarot, /pro, /delete)
│   ├── keyboards/         # Клавиатуры и кнопки Mini App
│   ├── middlewares/       # Проброс сессии БД в хэндлеры
│   ├── states/            # FSM-состояния (ввод даты, времени, города)
│   └── main.py            # Точка входа Telegram-бота
├── services/
│   ├── astrology/         # Эфемериды, геокодинг, расчет домов и аспектов
│   ├── ai/                # Клиент OpenRouter (Qwen2.5) и системный промпт
│   ├── tarot/             # 78 карт Таро, расклады и толкования
│   └── limits.py          # Суточные лимиты (1 вопрос ИИ, 1 таро для Free)
├── db/
│   ├── models/            # Модели: User, NatalChart, Subscription, ChatMessage
│   ├── repositories/      # CRUD-репозитории
│   └── session.py         # Async SQLAlchemy engine
├── api/                   # FastAPI бэкенд для Telegram Mini App
│   ├── auth.py            # Валидация Telegram WebApp initData
│   └── main.py            # REST эндпоинты
├── webapp/                # React Mini App (интерактивная карта и Таро)
├── docker-compose.yml     # Postgres + Redis + Bot + API
├── Dockerfile
└── requirements.txt
```

---

## ⚙️ Быстрый старт

### 1. Настройка переменных окружения
Скопируйте `.env.example` в `.env` и укажите ваши ключи:
```bash
cp .env.example .env
```
Заполните обязательные параметры:
* `BOT_TOKEN`: токен от [@BotFather](https://t.me/BotFather)
* `OPENROUTER_API_KEY`: ключ от [OpenRouter.ai](https://openrouter.ai/)
* `WEBAPP_URL`: ссылка на развернутый Mini App (например, через Vercel / Cloudflare Pages)

### 2. Запуск через Docker Compose (Рекомендуемый способ)
```bash
docker compose up --build -d
```
Это автоматически поднимет:
- PostgreSQL 15 на порту `5432`
- Redis 7 на порту `6379`
- Telegram-бота `astro_bot`
- FastAPI бэкенд `astro_api` на порту `8000`

### 3. Запуск Mini App локально (для разработки)
```bash
cd webapp
npm install
npm run dev
```

---

## 🔒 Безопасность и GDPR
* Реализована команда `/delete` — по первому запросу пользователя полностью стираются все персональные данные, расчеты натальной карты и история переписки с ИИ.
* Встроен обязательный дисклеймер 18+ при первом запуске бота.
