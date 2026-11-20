# Модуль `timetabletools`

Универсальная библиотека для описания и обработки расписаний: события
с интервалами времени, организаторы и коллекция событий с поиском
пересечений. Модуль не привязан к конкретной предметной области — подходит
для расписаний занятий, встреч, конференций, бронирований и т.п.

Модуль не зависит от форматов хранения: сохранение и загрузка реализуются
вызывающим кодом. В репозитории есть демонстрационное приложение
`timetable_app` — один из примеров такого кода (расписание занятий,
JSON/XML).

## Импорт

```python
from timetabletools import (
    BaseClass, NamedClass,
    Host, Event, HostList, Timetable,
    TimetableError, ValidationTypeError, ValidationError, NotFoundError,
    NULL_ID,
)
```

Диаграмма классов: [`class-diagram-module.drawio.png`](class-diagram-module.drawio.png)
(исходник — [`class-diagram-module.drawio`](class-diagram-module.drawio),
раскладка ELK).

## Иерархия

```
BaseClass
├── NamedClass
│   ├── Host
│   └── Event
└── Timetable

TimetableError(Exception)
├── ValidationTypeError(TimetableError, TypeError)
├── ValidationError(TimetableError, ValueError)
└── NotFoundError(TimetableError, KeyError)
```

## Произвольные атрибуты: `BaseClass`

Любой объект `Host`, `Event` и `Timetable` может хранить дополнительные
атрибуты в словаре `misc`.

- `obj.misc` — список имён добавленных атрибутов.
- `obj.add_attr(name, value)` — добавить атрибут.
- `obj.name_attr` — прочитать атрибут как обычное поле.
- `obj.name_attr = value` — изменить **существующий** атрибут.

Правила:

- имя должно быть корректным идентификатором Python и не быть ключевым
  словом (`ValidationError`/`ValidationTypeError`);
- имя не может начинаться с `_` и не может совпадать с базовым атрибутом
  класса (`ValidationError`);
- добавить **новый** атрибут через `obj.new = ...` нельзя — будет
  `AttributeError`; для этого есть только `add_attr`.

```python
host = Host("Иванов Иван Иванович")
host.add_attr("email", "ivanov@example.com")
print(host.email)          # ivanov@example.com
print(host.misc)           # ['email']
host.email = "i.ivanov@example.com"   # изменение существующего атрибута
```

## `NamedClass`

Добавляет поле `name` (строка) со свойством и сеттером. Все проверки имени
выполняются при создании и при изменении.

## `Host` — организатор

```python
Host(name: str, *, id: int = NULL_ID)
```

- `id` — целое число; по умолчанию `NULL_ID = -1` («ещё не в коллекции»).
- `name` — имя (getter/setter).
- `bool(host)` — `True`, если ID назначен (не `NULL_ID`).
- `host == other` — сравнение по имени и `misc`.
- `repr(host)` — удобное представление для отладки.

## `Event` — событие

```python
Event(name, event_start: datetime, event_end: datetime,
      *, host_id: int | None = None)
```

- `event_start`, `event_end` — `datetime`; сеттеры проверяют порядок
  (`ValidationError`, если начало позже конца).
- `host_id` — ID организатора или `None`; проверяется тип
  (`ValidationTypeError`).
- `event == other` — сравнение по всем полям, включая `host_id` и `misc`.
- `bool(event)` — всегда `True`.

Связь с организатором хранится **по ID**, а не объектом:

```python
event = Event("Совещание", start, end, host_id=0)
host = timetable.get_host(event.host_id)
```

## `HostList` — коллекция организаторов

```python
hosts = HostList()
host_id = hosts.add_host("Петров П.П.")   # выдаётся первый свободный ID
hosts.get_host(host_id)
hosts.remove_host(host_id)
```

- `add_host(name)` — создать `Host` и вернуть его ID.
- `next_id` — первый незанятый ID (после удаления освободившийся ID
  используется повторно).
- `get_host(id)` / `remove_host(id)` — `NotFoundError`, если ID нет.
- Поддерживаются `len(hosts)`, итерация, `id in hosts`, `host in hosts`,
  `hosts[id]`, `repr`.

## `Timetable` — расписание

```python
timetable = Timetable()
```

Работа с событиями:

- `add_event(event)` — добавить событие; полностью идентичное событие уже
  добавить нельзя (`ValidationError`).
- `remove_event(event)` — удалить событие (`NotFoundError`, если его нет).
- `sort()` — отсортировать по времени начала.
- `events_on(day: date)` — события, начинающиеся в указанный день.
- `events_between(start: datetime, end: datetime)` — события, начало которых
  попадает в диапазон.
- `find_overlaps()` — список пар пересекающихся событий. Соприкосновение
  (одно заканчивается ровно тогда, когда начинается другое) пересечением
  не считается.

Работа с организаторами:

- `add_host(name)` / `get_host(id)` / `remove_host(id)` — делегируют
  `HostList`.
- `remove_host` запрещает удаление, если организатор используется в событиях
  (`ValidationError`).
- `hostlist` — коллекция организаторов расписания.

Также поддерживаются `len(timetable)`, итерация, `event in timetable`,
`timetable[index]` (включая срезы), `repr`, а также `misc`/`add_attr`.

Пример:

```python
import datetime as dt
from timetabletools import Event, Timetable

timetable = Timetable()
host_id = timetable.add_host("Иванов Иван Иванович")
timetable.get_host(host_id).add_attr("email", "ivanov@example.com")

timetable.add_event(Event(
    "Планёрка",
    dt.datetime(2026, 11, 9, 10, 0),
    dt.datetime(2026, 11, 9, 11, 0),
    host_id=host_id,
))
timetable.sort()
print(len(timetable), timetable.events_on(dt.date(2026, 11, 9)))
print(timetable.find_overlaps())
```

## Исключения

| Класс | Наследует | Когда возникает |
|---|---|---|
| `TimetableError` | `Exception` | базовый класс всех ошибок модуля |
| `ValidationTypeError` | `TimetableError`, `TypeError` | неверный тип значения |
| `ValidationError` | `TimetableError`, `ValueError` | неверное значение (порядок дат, дубликат, базовое имя атрибута) |
| `NotFoundError` | `TimetableError`, `KeyError` | объект не найден по ID |

Благодаря наследованию от встроенных исключений код продолжает работать
с обычными `except TypeError/ValueError/KeyError`.

## Примечания

- ID организаторов всегда образуют непрерывный диапазон `0..n-1` и
  переиспользуются после удаления.
- `misc` не сериализуется модулем: формат хранения — ответственность
  вызывающего кода.
- `Event.host_id` — ссылка по ID; проверка существования организатора
  выполняется в `Timetable` при удалении.
- `timetable_app` — отдельный пример использования модуля, а не его часть.
