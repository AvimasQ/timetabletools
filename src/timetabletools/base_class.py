"""Базовые классы и исключения модуля."""

import keyword


class TimetableError(Exception):
    """Базовый класс исключений модуля."""


class ValidationTypeError(TimetableError, TypeError):
    """Неверный тип значения."""


class ValidationError(TimetableError, ValueError):
    """Неверное значение."""


class NotFoundError(TimetableError, KeyError):
    """Объект не найден."""


class BaseClass:
    """Базовый класс: произвольные атрибуты в словаре misc."""

    _misc: dict[str, object]

    @staticmethod
    def _validate_attr_name(name: str) -> None:
        """Проверить, что имя атрибута — корректный идентификатор."""
        if not isinstance(name, str):
            raise ValidationTypeError("Имя атрибута должно быть строкой")
        if not name.isidentifier() or keyword.iskeyword(name):
            raise ValidationError(
                f"{name!r} не является корректным именем атрибута")

    def __init__(self) -> None:
        """Создать объект с пустым набором произвольных атрибутов."""
        self._misc = {}

    def __getattr__(self, name: str) -> object:
        """Прочитать произвольный атрибут из misc."""
        misc = self.__dict__.get("_misc")
        if misc is not None and name in misc:
            return misc[name]
        raise AttributeError(
            f"У объекта {type(self).__name__!r} нет атрибута {name!r}")

    def __setattr__(self, name: str, value: object) -> None:
        """Обновить существующий misc-атрибут; новые так не добавляются."""
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        misc = self.__dict__.get("_misc")
        if misc is not None and name in misc:
            misc[name] = value
            return
        if isinstance(getattr(type(self), name, None), property):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(
            f"Нельзя добавить атрибут {name!r} напрямую; "
            f"используйте add_attr()")

    @property
    def misc(self) -> list[str]:
        """Имена произвольных атрибутов."""
        return list(self._misc.keys())

    def add_attr(self, name: str, value: object) -> None:
        """Добавить произвольный атрибут (кроме базовых имён)."""
        BaseClass._validate_attr_name(name)
        if name.startswith("_") or hasattr(type(self), name):
            raise ValidationError(
                f"Атрибут {name!r} является базовым "
                f"и не может быть добавлен")
        self._misc[name] = value


class NamedClass(BaseClass):
    """Именованный класс: добавляет поле name."""

    _name: str

    @staticmethod
    def _validate_name(name: str) -> None:
        """Проверить, что имя — строка."""
        if not isinstance(name, str):
            raise ValidationTypeError("Имя должно быть строкой")

    def __init__(self, name: str) -> None:
        """Создать именованный объект."""
        super().__init__()
        NamedClass._validate_name(name)
        self._name = name

    @property
    def name(self) -> str:
        """Имя объекта."""
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """Изменить имя с проверкой типа."""
        NamedClass._validate_name(name)
        self._name = name
