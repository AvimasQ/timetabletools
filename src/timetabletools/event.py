"""Класс Event: событие расписания."""

import datetime as dt

from .base_class import NamedClass, ValidationError, ValidationTypeError


class Event(NamedClass):
    """Событие расписания: имя, интервал, организатор (по ID) и misc."""

    _event_start: dt.datetime
    _event_end: dt.datetime
    _host_id: int | None

    @staticmethod
    def _validate_datetime(datetime: dt.datetime) -> None:
        """Проверить, что значение — datetime."""
        if not isinstance(datetime, dt.datetime):
            raise ValidationTypeError(
                "Время должно быть типа datetime.datetime")

    @staticmethod
    def _validate_time_delta(start: dt.datetime, end: dt.datetime) -> None:
        """Проверить, что начало не позже конца."""
        Event._validate_datetime(start)
        Event._validate_datetime(end)
        if start > end:
            raise ValidationError(
                "Начало события не может быть позже его завершения")

    @staticmethod
    def _validate_host_id(host_id: int | None) -> None:
        """Проверить, что ID организатора — целое число или None."""
        if host_id is not None and not isinstance(host_id, int):
            raise ValidationTypeError("host_id должен быть числом или None")

    def __init__(self, name: str, event_start: dt.datetime,
                 event_end: dt.datetime,
                 *, host_id: int | None = None) -> None:
        """Создать событие; ID организатора необязателен."""
        super().__init__(name)
        Event._validate_time_delta(event_start, event_end)
        Event._validate_host_id(host_id)
        self._event_start = event_start
        self._event_end = event_end
        self._host_id = host_id

    def __eq__(self, other: object) -> bool:
        """Сравнение по всем полям события."""
        if not isinstance(other, Event):
            return NotImplemented
        return (self._name == other._name and
                self._event_start == other._event_start and
                self._event_end == other._event_end and
                self._host_id == other._host_id and
                self._misc == other._misc)

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return (
            f"Event(name={self._name!r}, "
            f"event_start={self._event_start!r}, "
            f"event_end={self._event_end!r}, "
            f"host_id={self._host_id!r}, "
            f"misc={self._misc!r})"
        )

    def __bool__(self) -> bool:
        """Событие всегда считается непустым объектом."""
        return True

    @property
    def event_start(self) -> dt.datetime:
        """Дата и время начала."""
        return self._event_start

    @event_start.setter
    def event_start(self, event_start: dt.datetime) -> None:
        """Изменить начало с проверкой порядка."""
        Event._validate_time_delta(event_start, self._event_end)
        self._event_start = event_start

    @property
    def event_end(self) -> dt.datetime:
        """Дата и время конца."""
        return self._event_end

    @event_end.setter
    def event_end(self, event_end: dt.datetime) -> None:
        """Изменить конец с проверкой порядка."""
        Event._validate_time_delta(self._event_start, event_end)
        self._event_end = event_end

    @property
    def host_id(self) -> int | None:
        """ID организатора или None."""
        return self._host_id

    @host_id.setter
    def host_id(self, host_id: int | None) -> None:
        """Изменить ID организатора с проверкой типа."""
        Event._validate_host_id(host_id)
        self._host_id = host_id
