from datetime import datetime
from typing import Optional
from telethon import TelegramClient
from telethon.tl.types import User, Message


async def get_private_dialogs(client: TelegramClient) -> list[dict]:
    """Возвращает список личных чатов (не боты, не группы)."""
    dialogs = []
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, User) and not entity.bot:
            name = _get_name(entity)
            dialogs.append({"name": name, "entity": entity, "dialog": dialog})
    return dialogs


async def fetch_messages(
    client: TelegramClient,
    entity,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    on_progress=None,
) -> list[Message]:
    """Загружает сообщения из чата с учётом временного диапазона."""
    messages = []
    count = 0

    # print(f"[DEBUG] fetch_messages: date_from={date_from}, date_to={date_to}")
    # print(f"[DEBUG] offset_date (date_from) передан в iter_messages: {date_from}")

    async for msg in client.iter_messages(
        entity,
        offset_date=date_from,  # при reverse=True — нижняя граница (начало выборки)
        reverse=True,
    ):
        msg_dt = msg.date.replace(tzinfo=None)
        # print(f"[DEBUG] msg id={msg.id} date={msg_dt} | date_to check: {date_to and msg_dt > date_to}")

        if date_to and msg_dt > date_to:
            break
        messages.append(msg)
        count += 1
        if on_progress:
            on_progress(count)

    # print(f"[DEBUG] fetch_messages завершён: собрано {len(messages)} сообщений")
    return messages


def _get_name(user: User) -> str:
    parts = [user.first_name or "", user.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    return name or f"id{user.id}"
