"""Класс HostList: коллекция организаторов."""

from .base_class import NotFoundError
from .host import Host


class HostList:
    """Коллекция организаторов с автоматической выдачей свободного ID."""

    _hosts: dict[int, Host]

    def __init__(self) -> None:
        """Создать пустую коллекцию."""
        self._hosts = {}

    def add_host(self, name: str) -> int:
        """Добавить организатора и вернуть его ID."""
        newid = self.next_id
        newhost = Host(name=name, id=newid)
        self._hosts[newid] = newhost
        return newhost.id

    @property
    def next_id(self) -> int:
        """Первый незанятый ID (учитывает удалённых организаторов)."""
        id = 0
        while id in self._hosts:
            id += 1
        return id

    def get_host(self, id: int) -> Host:
        """Получить организатора по ID."""
        if id not in self._hosts:
            raise NotFoundError(f"Хост с ID {id} не найден")
        return self._hosts[id]

    def remove_host(self, id: int) -> None:
        """Удалить организатора по ID."""
        if id not in self._hosts:
            raise NotFoundError(f"Хост с ID {id} не найден")
        del self._hosts[id]

    def __len__(self) -> int:
        """Количество организаторов в коллекции."""
        return len(self._hosts)

    def __iter__(self):
        """Итерация по организаторам."""
        return iter(self._hosts.values())

    def __contains__(self, item: object) -> bool:
        """Проверка наличия организатора по ID или по объекту."""
        if isinstance(item, int):
            return item in self._hosts
        if isinstance(item, Host):
            return item.id in self._hosts
        return False

    def __getitem__(self, id: int) -> Host:
        """Доступ к организатору по ID."""
        return self.get_host(id)

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return f"HostList({list(self._hosts.values())!r})"
