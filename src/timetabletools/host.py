"""Класс Host: организатор/ведущий события."""

from .base_class import NamedClass, ValidationTypeError

NULL_ID = -1  # значение ID для объектов, ещё не добавленных в коллекцию


class Host(NamedClass):
    """Организатор/ведущий события."""

    _id: int

    @staticmethod
    def _validate_id(id: int) -> None:
        """Проверить, что ID — целое число."""
        if not isinstance(id, int):
            raise ValidationTypeError("ID должен быть числом")

    def __init__(self, name: str, *, id: int = NULL_ID) -> None:
        """Создать организатора с необязательным ID."""
        super().__init__(name)
        Host._validate_id(id)
        self._id = id

    def __eq__(self, other: object) -> bool:
        """Сравнение по имени и произвольным атрибутам."""
        if not isinstance(other, Host):
            return NotImplemented
        return self._name == other._name and self._misc == other._misc

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return (f"Host(id={self._id!r}, name={self._name!r}, "
                f"misc={self._misc!r})")

    def __bool__(self) -> bool:
        """True, если объекту уже назначен ID."""
        return self._id != NULL_ID

    @property
    def id(self) -> int:
        """ID организатора (NULL_ID, если он ещё не в коллекции)."""
        return self._id
