"""Класс Timetable: расписание."""

import datetime as dt

from .base_class import (BaseClass, NotFoundError, ValidationError,
                         ValidationTypeError)
from .event import Event
from .host import Host
from .hostlist import HostList


class Timetable(BaseClass):
    """Расписание: события, организаторы и произвольные атрибуты."""

    _events: list[Event]
    _hostlist: HostList

    @staticmethod
    def _validate_event(event: Event) -> None:
        """Проверить, что значение — Event."""
        if not isinstance(event, Event):
            raise ValidationTypeError("Событие должно быть типа Event")

    @staticmethod
    def _validate_range(start: dt.datetime, end: dt.datetime) -> None:
        """Проверить типы границ диапазона и их порядок."""
        if (not isinstance(start, dt.datetime)
                or not isinstance(end, dt.datetime)):
            raise ValidationTypeError(
                "Границы должны быть типа datetime.datetime")
        if start > end:
            raise ValidationError(
                "Начало диапазона не может быть позже его конца")

    def __init__(self) -> None:
        """Создать пустое расписание с пустым списком организаторов."""
        super().__init__()
        self._events = []
        self._hostlist = HostList()

    def add_event(self, event: Event) -> None:
        """Добавить событие, если такого ещё нет."""
        Timetable._validate_event(event)
        if event in self._events:
            raise ValidationError("Идентичное событие уже есть в расписании")
        self._events.append(event)

    def remove_event(self, event: Event) -> None:
        """Удалить событие из расписания."""
        Timetable._validate_event(event)
        try:
            self._events.remove(event)
        except ValueError:
            raise NotFoundError("Событие не найдено в расписании") from None

    @property
    def hostlist(self) -> HostList:
        """Коллекция организаторов расписания."""
        return self._hostlist

    def add_host(self, name: str) -> int:
        """Добавить организатора и вернуть его ID."""
        return self._hostlist.add_host(name)

    def get_host(self, id: int) -> Host:
        """Получить организатора по ID."""
        return self._hostlist.get_host(id)

    def remove_host(self, id: int) -> None:
        """Удалить организатора, если он не используется в событиях."""
        if any(event.host_id == id for event in self._events):
            raise ValidationError(
                f"Хост с ID {id} используется в событиях")
        self._hostlist.remove_host(id)

    def sort(self) -> None:
        """Отсортировать события по времени начала."""
        self._events.sort(key=lambda event: event.event_start)

    def events_on(self, day: dt.date) -> list[Event]:
        """Вернуть события, начинающиеся в указанный день."""
        if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
            raise ValidationTypeError("День должен быть типа datetime.date")
        return [event for event in self._events
                if event.event_start.date() == day]

    def events_between(self, start: dt.datetime,
                       end: dt.datetime) -> list[Event]:
        """Вернуть события, начинающиеся в заданном диапазоне."""
        Timetable._validate_range(start, end)
        return [event for event in self._events
                if start <= event.event_start <= end]

    def find_overlaps(self) -> list[tuple[Event, Event]]:
        """Найти пары событий, пересекающихся по времени."""
        overlaps: list[tuple[Event, Event]] = []
        events = sorted(self._events, key=lambda event: event.event_start)
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                a, b = events[i], events[j]
                if b.event_start >= a.event_end:
                    # события отсортированы по началу: дальше пересечений нет
                    break
                if a.event_start < b.event_end and b.event_start < a.event_end:
                    overlaps.append((a, b))
        return overlaps

    def __len__(self) -> int:
        """Количество событий в расписании."""
        return len(self._events)

    def __iter__(self):
        """Итерация по событиям."""
        return iter(self._events)

    def __contains__(self, item: object) -> bool:
        """Проверка наличия события в расписании."""
        return isinstance(item, Event) and item in self._events

    def __getitem__(self, index):
        """Доступ к событию по индексу или срезу."""
        return self._events[index]

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return f"Timetable({self._events!r}, misc={self._misc!r})"
