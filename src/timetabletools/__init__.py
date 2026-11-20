"""Универсальный модуль классов данных расписаний."""

from .base_class import (BaseClass, NamedClass, NotFoundError,
                         TimetableError, ValidationError,
                         ValidationTypeError)
from .event import Event
from .host import NULL_ID, Host
from .hostlist import HostList
from .timetable import Timetable

__all__ = [
    "BaseClass",
    "NamedClass",
    "Host",
    "Event",
    "HostList",
    "Timetable",
    "TimetableError",
    "ValidationTypeError",
    "ValidationError",
    "NotFoundError",
    "NULL_ID",
]
