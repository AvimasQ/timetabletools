"""Консольная демонстрация модуля timetabletools."""

import datetime as dt
from pathlib import Path

from timetabletools import (Event, NamedClass, NotFoundError, Timetable,
                            TimetableError, ValidationError)

from .storage import load_json, load_xml, save_json, save_xml

DATA_DIR = Path(__file__).resolve().parent / "data"
JSON_PATH = DATA_DIR / "timetable.json"
XML_PATH = DATA_DIR / "timetable.xml"

MENU = """
================= РАСПИСАНИЕ ПАР =================
 1. Показать расписание
 2. Добавить пару
 3. Изменить пару
 4. Удалить пару
 5. Показать преподавателей
 6. Добавить преподавателя
 7. Удалить преподавателя
 8. Пересечения пар
 9. Пары на дату
10. Сохранить в JSON
11. Сохранить в XML
12. Загрузить из JSON
13. Загрузить из XML
 0. Выход
===================================================
"""


def ask(prompt: str) -> str:
    """Прочитать строку и убрать пробелы по краям."""
    return input(prompt).strip()


def ask_int(prompt: str) -> int:
    """Прочитать целое число или сообщить об ошибке."""
    raw = ask(prompt)
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{raw!r} — не целое число")


def ask_optional_int(prompt: str) -> int | None:
    """Прочитать целое число; пустой ввод означает None."""
    raw = ask(prompt)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{raw!r} — не целое число")


def parse_datetime(raw: str) -> dt.datetime:
    """Разобрать дату-время в формате ДД.ММ.ГГГГ ЧЧ:ММ."""
    try:
        return dt.datetime.strptime(raw, "%d.%m.%Y %H:%M")
    except ValueError:
        raise ValueError(
            f"{raw!r} не соответствует формату ДД.ММ.ГГГГ ЧЧ:ММ")


def ask_datetime(prompt: str) -> dt.datetime:
    """Запросить дату-время у пользователя."""
    return parse_datetime(ask(prompt))


def ask_date(prompt: str) -> dt.date:
    """Запросить дату в формате ДД.ММ.ГГГГ."""
    raw = ask(prompt)
    try:
        return dt.datetime.strptime(raw, "%d.%m.%Y").date()
    except ValueError:
        raise ValueError(
            f"{raw!r} не соответствует формату ДД.ММ.ГГГГ")


def format_misc(obj: NamedClass) -> str:
    """Показать произвольные атрибуты объекта в квадратных скобках."""
    parts = [f"{name}={getattr(obj, name)}" for name in obj.misc]
    return f" [{', '.join(parts)}]" if parts else ""


def format_event(timetable: Timetable, event: Event) -> str:
    """Сформировать строку для вывода события."""
    host = "—"
    if event.host_id is not None:
        try:
            host = timetable.get_host(event.host_id).name
        except NotFoundError:
            host = f"ID {event.host_id}"
    start = event.event_start.strftime("%d.%m.%Y %H:%M")
    end = event.event_end.strftime("%H:%M")
    return (f"{start}–{end} «{event.name}» "
            f"(преп.: {host}){format_misc(event)}")


def show_timetable(timetable: Timetable) -> None:
    """Показать все пары в порядке времени начала."""
    events = sorted(timetable, key=lambda item: item.event_start)
    if not events:
        print("Расписание пусто.")
        return
    for index, event in enumerate(events, start=1):
        print(f"{index:2}. {format_event(timetable, event)}")


def choose_event(timetable: Timetable) -> Event | None:
    """Показать список пар и дать выбрать одну по номеру."""
    events = sorted(timetable, key=lambda item: item.event_start)
    if not events:
        print("Расписание пусто.")
        return None
    for index, event in enumerate(events, start=1):
        print(f"{index:2}. {format_event(timetable, event)}")
    number = ask_int("Номер пары: ")
    if not 1 <= number <= len(events):
        raise ValidationError(f"Нет пары с номером {number}")
    return events[number - 1]


def add_event(timetable: Timetable) -> None:
    """Запросить данные и добавить новую пару."""
    name = ask("Название пары: ")
    start = ask_datetime("Начало (ДД.ММ.ГГГГ ЧЧ:ММ): ")
    end = ask_datetime("Конец (ДД.ММ.ГГГГ ЧЧ:ММ): ")
    host_id = ask_optional_int("ID преподавателя (Enter — нет): ")
    event = Event(name, start, end, host_id=host_id)
    room = ask("Аудитория (Enter — пропустить): ")
    if room:
        event.add_attr("room", room)
    group = ask("Группа (Enter — пропустить): ")
    if group:
        event.add_attr("group", group)
    timetable.add_event(event)
    print(f"Добавлена пара: {format_event(timetable, event)}")


def edit_event(timetable: Timetable) -> None:
    """Изменить поля выбранной пары; пустой ввод оставляет поле как есть."""
    event = choose_event(timetable)
    if event is None:
        return
    name = ask("Новое название (Enter — оставить): ")
    start_raw = ask("Новое начало (Enter — оставить): ")
    end_raw = ask("Новый конец (Enter — оставить): ")
    host_raw = ask("Новый ID преподавателя (Enter — оставить): ")
    start = parse_datetime(start_raw) if start_raw else None
    end = parse_datetime(end_raw) if end_raw else None
    if start is not None and end is not None and start > end:
        raise ValidationError("Начало пары не может быть позже конца")
    if name:
        event.name = name
    if start is not None and end is not None:
        if start <= event.event_end:
            event.event_start = start
            event.event_end = end
        else:
            event.event_end = end
            event.event_start = start
    elif start is not None:
        event.event_start = start
    elif end is not None:
        event.event_end = end
    if host_raw:
        event.host_id = int(host_raw)
    print("Пара обновлена.")


def delete_event(timetable: Timetable) -> None:
    """Удалить выбранную пару."""
    event = choose_event(timetable)
    if event is None:
        return
    timetable.remove_event(event)
    print("Пара удалена.")


def show_hosts(timetable: Timetable) -> None:
    """Показать всех преподавателей с их ID."""
    hosts = timetable.hostlist
    if len(hosts) == 0:
        print("Преподавателей нет.")
        return
    for host in hosts:
        print(f"[{host.id}] {host.name}{format_misc(host)}")


def add_host(timetable: Timetable) -> None:
    """Добавить преподавателя."""
    host_id = timetable.add_host(ask("ФИО преподавателя: "))
    print(f"Преподаватель добавлен, ID = {host_id}.")


def delete_host(timetable: Timetable) -> None:
    """Удалить преподавателя по ID."""
    host_id = ask_int("ID преподавателя: ")
    timetable.remove_host(host_id)
    print("Преподаватель удалён.")


def show_overlaps(timetable: Timetable) -> None:
    """Показать пары, которые пересекаются по времени."""
    overlaps = timetable.find_overlaps()
    if not overlaps:
        print("Пересечений нет.")
        return
    for first, second in overlaps:
        print(f"Пересечение: «{first.name}» и «{second.name}»")


def events_on_date(timetable: Timetable) -> None:
    """Показать пары на выбранную дату."""
    day = ask_date("Дата (ДД.ММ.ГГГГ): ")
    events = timetable.events_on(day)
    if not events:
        print("В этот день пар нет.")
        return
    for event in events:
        print(format_event(timetable, event))


def _save_json(timetable: Timetable) -> None:
    """Сохранить расписание в JSON-файл."""
    save_json(timetable, JSON_PATH)
    print(f"Сохранено в JSON: {JSON_PATH}")


def _save_xml(timetable: Timetable) -> None:
    """Сохранить расписание в XML-файл."""
    save_xml(timetable, XML_PATH)
    print(f"Сохранено в XML: {XML_PATH}")


def _load_json() -> Timetable:
    """Загрузить расписание из JSON-файла."""
    timetable = load_json(JSON_PATH)
    print_loaded(timetable)
    return timetable


def _load_xml() -> Timetable:
    """Загрузить расписание из XML-файла."""
    timetable = load_xml(XML_PATH)
    print_loaded(timetable)
    return timetable


def print_loaded(timetable: Timetable) -> None:
    """Показать, сколько объектов загружено."""
    print(f"Загружено: пар — {len(timetable)}, "
          f"преподавателей — {len(timetable.hostlist)}.")


ACTIONS = {
    "1": show_timetable,
    "2": add_event,
    "3": edit_event,
    "4": delete_event,
    "5": show_hosts,
    "6": add_host,
    "7": delete_host,
    "8": show_overlaps,
    "9": events_on_date,
    "10": _save_json,
    "11": _save_xml,
}


def main() -> None:
    """Запустить цикл консольного меню."""
    timetable = Timetable()
    print("Демонстрация модуля timetabletools.")
    while True:
        print(MENU)
        try:
            command = ask("Выбор: ")
        except EOFError:
            print("\nЗавершение работы.")
            return
        if command == "0":
            print("До свидания.")
            return
        try:
            if command == "12":
                timetable = _load_json()
            elif command == "13":
                timetable = _load_xml()
            else:
                action = ACTIONS.get(command)
                if action is None:
                    print("Неизвестная команда.")
                else:
                    action(timetable)
        except EOFError:
            print("\nЗавершение работы.")
            return
        except TimetableError as error:
            print(f"Ошибка: {error}")
        except ValueError as error:
            print(f"Некорректные данные: {error}")
        except OSError as error:
            print(f"Ошибка ввода-вывода: {error}")


if __name__ == "__main__":
    main()
