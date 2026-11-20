"""Чтение и запись расписания в форматах JSON и XML."""

import datetime as dt
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from timetabletools import Event, NamedClass, Timetable, TimetableError


class StorageError(TimetableError):
    """Ошибка чтения или записи файла."""



def _misc_dict(obj: NamedClass) -> dict[str, object]:
    """Произвольные атрибуты объекта в виде словаря."""
    return {name: getattr(obj, name) for name in obj.misc}


def _scalar_from_text(typ: str, text: str | None) -> object:
    """Восстановление скалярного значения из текста XML."""
    if typ == "int":
        return int(text)
    if typ == "float":
        return float(text)
    if typ == "bool":
        return text == "True"
    if typ == "NoneType":
        return None
    return text if text is not None else ""


def _write_misc(elem: ET.Element, data: dict[str, object]) -> None:
    """Запись произвольных атрибутов дочерними элементами."""
    for key, value in data.items():
        child = ET.SubElement(elem, key)
        if not isinstance(value, str):
            child.set("type", type(value).__name__)
        child.text = None if value is None else str(value)


def _read_misc(elem: ET.Element, known: set[str]) -> dict[str, object]:
    """Чтение произвольных атрибутов из дочерних элементов."""
    result: dict[str, object] = {}
    for child in elem:
        if child.tag in known:
            continue
        try:
            result[child.tag] = _scalar_from_text(
                child.get("type", "str"), child.text)
        except (TypeError, ValueError):
            raise StorageError(
                f"Неверное значение элемента <{child.tag}>") from None
    return result


def _child_text(elem: ET.Element, tag: str) -> str:
    """Текст обязательного дочернего элемента."""
    child = elem.find(tag)
    if child is None or child.text is None:
        raise StorageError(f"В XML отсутствует элемент <{tag}>")
    return child.text


def _attr_int(elem: ET.Element, name: str) -> int | None:
    """Числовое значение XML-атрибута."""
    value = elem.get(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise StorageError(
            f"Неверное значение атрибута {name!r}") from None


def _require_str(item: dict[str, object], key: str, where: str) -> str:
    """Обязательное строковое поле."""
    value = item.get(key)
    if not isinstance(value, str):
        raise StorageError(f"{where}: поле {key!r} должно быть строкой")
    return value


def _extract_misc(item: dict[str, object],
                  known: set[str]) -> dict[str, object]:
    """Неизвестные ключи словаря — это произвольные атрибуты."""
    return {key: value for key, value in item.items() if key not in known}


def _parse_datetime(value: object, key: str) -> dt.datetime:
    """Разбор даты-времени из строки."""
    if not isinstance(value, str):
        raise StorageError(f"Поле {key!r} должно быть строкой")
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        raise StorageError(
            f"Поле {key!r}: неверный формат даты-времени") from None


def _host_id(item: object) -> int:
    """Ключ сортировки хостов по ID."""
    if not isinstance(item, dict):
        raise StorageError("Элемент hosts должен быть объектом")
    value = item.get("id", 0)
    if isinstance(value, bool) or not isinstance(value, int):
        raise StorageError("ID хоста должен быть целым числом")
    return value


def _read_text(path: Path) -> str:
    """Чтение файла."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise StorageError(f"Файл не найден: {path}") from None
    except OSError as error:
        raise StorageError(
            f"Не удалось прочитать {path}: {error}") from None


def _write_text(path: Path, text: str) -> None:
    """Запись файла."""
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as error:
        raise StorageError(
            f"Не удалось записать {path}: {error}") from None


def _to_data(timetable: Timetable) -> dict[str, object]:
    """Расписание в виде вложенного словаря."""
    return {
        "meta": _misc_dict(timetable),
        "hosts": [
            {"id": host.id, "name": host.name, **_misc_dict(host)}
            for host in timetable.hostlist
        ],
        "events": [
            {"name": event.name,
             "event_start": event.event_start.isoformat(),
             "event_end": event.event_end.isoformat(),
             "host_id": event.host_id,
             **_misc_dict(event)}
            for event in timetable
        ],
    }


def _from_data(data: object) -> Timetable:
    """Восстановление расписания из вложенного словаря."""
    if not isinstance(data, dict):
        raise StorageError("Корневой элемент должен быть объектом")
    timetable = Timetable()
    meta = data.get("meta", {})
    if not isinstance(meta, dict):
        raise StorageError("Поле meta должно быть объектом")
    for key, value in meta.items():
        timetable.add_attr(key, value)
    _load_hosts(timetable, data.get("hosts", []))
    _load_events(timetable, data.get("events", []))
    return timetable


def _load_hosts(timetable: Timetable, items: object) -> None:
    """Восстановление списка преподавателей."""
    if not isinstance(items, list):
        raise StorageError("Поле hosts должно быть списком")
    for item in sorted(items, key=_host_id):
        name = _require_str(item, "name", "hosts")
        new_id = timetable.add_host(name)
        stored_id = item.get("id")
        if stored_id is not None and stored_id != new_id:
            raise StorageError("Нарушена нумерация хостов")
        host = timetable.get_host(new_id)
        for key, value in _extract_misc(item, {"id", "name"}).items():
            host.add_attr(key, value)


def _load_events(timetable: Timetable, items: object) -> None:
    """Восстановление списка пар."""
    if not isinstance(items, list):
        raise StorageError("Поле events должно быть списком")
    known = {"name", "event_start", "event_end", "host_id"}
    for item in items:
        if not isinstance(item, dict):
            raise StorageError("Элемент events должен быть объектом")
        name = _require_str(item, "name", "events")
        start = _parse_datetime(item.get("event_start"), "event_start")
        end = _parse_datetime(item.get("event_end"), "event_end")
        event = Event(name, start, end, host_id=item.get("host_id"))
        for key, value in _extract_misc(item, known).items():
            event.add_attr(key, value)
        timetable.add_event(event)



def save_json(timetable: Timetable, path: str | Path) -> None:
    """Записать расписание в файл JSON."""
    try:
        text = json.dumps(_to_data(timetable), ensure_ascii=False,
                          indent=2)
    except (TypeError, ValueError):
        raise StorageError(
            "Не удалось преобразовать данные в JSON") from None
    _write_text(Path(path), text)


def load_json(path: str | Path) -> Timetable:
    """Прочитать расписание из файла JSON."""
    try:
        data = json.loads(_read_text(Path(path)))
    except json.JSONDecodeError as error:
        raise StorageError(f"Некорректный JSON: {error}") from None
    return _from_data(data)


def save_xml(timetable: Timetable, path: str | Path) -> None:
    """Записать расписание в файл XML."""
    root = ET.Element("Timetable")
    _write_misc(ET.SubElement(root, "Meta"), _misc_dict(timetable))

    hosts_elem = ET.SubElement(root, "Hosts")
    for host in timetable.hostlist:
        elem = ET.SubElement(hosts_elem, "Host")
        elem.set("id", str(host.id))
        ET.SubElement(elem, "name").text = host.name
        _write_misc(elem, _misc_dict(host))

    events_elem = ET.SubElement(root, "Events")
    for event in timetable:
        elem = ET.SubElement(events_elem, "Event")
        ET.SubElement(elem, "name").text = event.name
        ET.SubElement(
            elem, "event_start").text = event.event_start.isoformat()
        ET.SubElement(
            elem, "event_end").text = event.event_end.isoformat()
        host_id = ET.SubElement(elem, "host_id")
        if event.host_id is None:
            host_id.set("type", "NoneType")
        else:
            host_id.set("type", "int")
            host_id.text = str(event.host_id)
        _write_misc(elem, _misc_dict(event))

    ET.indent(root, space="  ")
    _write_text(Path(path), ET.tostring(root, encoding="unicode"))


def load_xml(path: str | Path) -> Timetable:
    """Прочитать расписание из файла XML."""
    try:
        root = ET.fromstring(_read_text(Path(path)))
    except ET.ParseError as error:
        raise StorageError(f"Некорректный XML: {error}") from None
    if root.tag != "Timetable":
        raise StorageError("Ожидался элемент <Timetable>")

    timetable = Timetable()
    meta = root.find("Meta")
    if meta is not None:
        for key, value in _read_misc(meta, set()).items():
            timetable.add_attr(key, value)
    _load_hosts_xml(timetable, root.find("Hosts"))
    _load_events_xml(timetable, root.find("Events"))
    return timetable


def _load_hosts_xml(timetable: Timetable,
                    hosts: ET.Element | None) -> None:
    """Восстановление преподавателей из XML."""
    if hosts is None:
        return
    items = list(hosts.findall("Host"))
    items.sort(key=lambda elem: _attr_int(elem, "id") or 0)
    for elem in items:
        stored_id = _attr_int(elem, "id")
        new_id = timetable.add_host(_child_text(elem, "name"))
        if stored_id is not None and stored_id != new_id:
            raise StorageError("Нарушена нумерация хостов")
        host = timetable.get_host(new_id)
        for key, value in _read_misc(elem, {"name"}).items():
            host.add_attr(key, value)


def _load_events_xml(timetable: Timetable,
                     events: ET.Element | None) -> None:
    """Восстановление пар из XML."""
    if events is None:
        return
    known = {"name", "event_start", "event_end", "host_id"}
    for elem in events.findall("Event"):
        start = _parse_datetime(
            _child_text(elem, "event_start"), "event_start")
        end = _parse_datetime(
            _child_text(elem, "event_end"), "event_end")
        host_id = None
        host_id_elem = elem.find("host_id")
        if host_id_elem is not None:
            try:
                host_id = _scalar_from_text(
                    host_id_elem.get("type", "int"), host_id_elem.text)
            except (TypeError, ValueError):
                raise StorageError(
                    "Неверное значение элемента <host_id>") from None
        event = Event(_child_text(elem, "name"), start, end,
                      host_id=host_id)
        for key, value in _read_misc(elem, known).items():
            event.add_attr(key, value)
        timetable.add_event(event)
