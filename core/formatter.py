from telethon.tl.types import Message


def format_dialog(contact_name: str, messages: list[Message]) -> str:
    """Форматирует список сообщений одного диалога в текстовый блок."""
    lines = [f"=== Диалог с {contact_name} ==="]

    for msg in messages:
        if not msg.date:
            continue

        time_str = msg.date.strftime("%H:%M %d.%m.%Y")
        sender = "Я" if msg.out else contact_name
        text = _get_text(msg)
        lines.append(f"{time_str} | От: {sender} | Сообщение: {text}")

    lines.append("")  # пустая строка-разделитель между диалогами
    return "\n".join(lines)


def _get_text(msg: Message) -> str:
    if msg.text:
        return msg.text.replace("\n", " ")
    if msg.media:
        return "[медиа]"
    return "[пустое сообщение]"
