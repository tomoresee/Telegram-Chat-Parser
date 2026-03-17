import asyncio
from datetime import datetime
from typing import Optional

from core.auth import get_client, authenticate
from core.fetcher import get_private_dialogs, fetch_messages
from core.formatter import format_dialog
from core.exporter import save_to_file


def parse_date(prompt: str) -> Optional[datetime]:
    raw = input(prompt).strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%d.%m.%Y")
    except ValueError:
        print("  Неверный формат даты, игнорируется.")
        return None


async def main():
    print("=== Telegram Parser ===\n")

    client = get_client()
    async with client:
        await authenticate(client)

        print("Загружаю список чатов...")
        dialogs = await get_private_dialogs(client)

        if not dialogs:
            print("Личные чаты не найдены.")
            return

        print(f"\nНайдено личных чатов: {len(dialogs)}\n")
        for i, d in enumerate(dialogs, 1):
            print(f"  {i}. {d['name']}")

        print("\nВведите номера чатов через запятую (например: 1,3,5)")
        print("Или введите 0, чтобы выбрать все чаты.")
        choice = input("Ваш выбор: ").strip()

        if choice == "0":
            selected = dialogs
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(",")]
                selected = [dialogs[i] for i in indices if 0 <= i < len(dialogs)]
            except (ValueError, IndexError):
                print("Неверный ввод. Завершение.")
                return

        if not selected:
            print("Ни один чат не выбран. Завершение.")
            return

        print("\nУкажите временной период (или нажмите Enter, чтобы пропустить):")
        date_from = parse_date("  Начальная дата (ДД.ММ.ГГГГ): ")
        date_to_raw = parse_date("  Конечная дата  (ДД.ММ.ГГГГ): ")
        # Включаем весь конечный день: сдвигаем до 23:59:59
        date_to = date_to_raw.replace(hour=23, minute=59, second=59) if date_to_raw else None

        print(f"\nНачинаю экспорт {len(selected)} чат(ов)...\n")

        all_blocks = []
        for d in selected:
            name = d["name"]
            print(f"  Обрабатываю: {name}", end="", flush=True)

            def progress(n, _name=name):
                print(f"\r  Обрабатываю: {_name} — {n} сообщений", end="", flush=True)

            messages = await fetch_messages(
                client, d["entity"], date_from, date_to, on_progress=progress
            )
            print()  # перевод строки после счётчика

            if messages:
                block = format_dialog(name, messages)
                all_blocks.append(block)
            else:
                print(f"    (нет сообщений за указанный период)")

        if not all_blocks:
            print("\nНет данных для экспорта.")
            return

        content = "\n".join(all_blocks)
        filepath = save_to_file(content)
        print(f"\nГотово! Файл сохранён:\n  {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
