# Telegram Chat Parser

Инструмент для экспорта личных переписок из Telegram в текстовый файл.
Создан для анализа вопросов покупателей с помощью нейросети.

## Скриншоты

![](screenshots\01.png)
![](screenshots\02.png)
![](screenshots\03.png)
![](screenshots\04.png)

## Технологии

- **Python 3.9+** — язык разработки
- **Telethon 1.36.0** — работа с Telegram API
- **PyQt6 6.6.0+** — графический интерфейс

## Требования

- Python 3.10+
- Учётные данные Telegram API: [my.telegram.org](https://my.telegram.org)

## Установка

```bash
# Клонировать репозиторий или скачать файлы

# Установить зависимости
pip install -r requirements.txt

# Создать файл .env с API-ключами
cp .env.example .env
# Заполнить API_ID и API_HASH в .env
```

## Запуск

**Графический интерфейс (рекомендуется):**
```bash
python gui.py
```

**Командная строка:**
```bash
python main.py
```

## Использование

1. Введите номер телефона → получите код в Telegram → введите его
2. Выберите нужные чаты из списка (или «Выбрать все»)
3. Укажите временной диапазон (необязательно)
4. Нажмите «Начать экспорт»

Готовый файл сохраняется в папку `exports/` в формате `export_YYYYMMDD_HHMMSS.txt`.

## Формат экспорта

```
=== Диалог с Иван Петров ===
14:32 15.03.2024 | От: Я | Сообщение: Здравствуйте, товар еще актуален?
14:33 15.03.2024 | От: Иван | Сообщение: Да, можете забирать сегодня
```

## Структура проекта

```
telegram_parser/
├── core/
│   ├── auth.py        — Авторизация в Telegram
│   ├── fetcher.py     — Загрузка сообщений
│   ├── formatter.py   — Форматирование текста
│   └── exporter.py    — Сохранение в файл
├── main.py            — CLI-версия
├── gui.py             — Desktop GUI (PyQt6)
├── exports/           — Папка с результатами экспорта
└── .env               — API-ключи (не коммитить)
```

## Настройка .env

```env
API_ID=ваш_api_id
API_HASH=ваш_api_hash
```

Получить `API_ID` и `API_HASH` можно на [my.telegram.org](https://my.telegram.org) → API development tools.
