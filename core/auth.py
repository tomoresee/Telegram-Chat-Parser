import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

load_dotenv()

SESSION_NAME = "telegram_session"


def get_client() -> TelegramClient:
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    if not api_id or not api_hash:
        print("Ошибка: не найдены API_ID и API_HASH.")
        print("Скопируйте .env.example в .env и заполните данные с https://my.telegram.org")
        raise SystemExit(1)

    return TelegramClient(SESSION_NAME, int(api_id), api_hash)


async def authenticate(client: TelegramClient) -> None:
    if await client.is_user_authorized():
        return

    phone = input("Введите номер телефона (в формате +79001234567): ").strip()
    await client.send_code_request(phone)

    code = input("Введите код подтверждения из Telegram: ").strip()
    try:
        await client.sign_in(phone, code)
    except SessionPasswordNeededError:
        password = input("Введите пароль двухфакторной аутентификации: ").strip()
        await client.sign_in(password=password)

    print("Аутентификация прошла успешно.\n")
