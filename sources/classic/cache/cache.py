from abc import ABC, abstractmethod
from typing import Mapping, Any, Hashable, TypeVar, Type

import msgspec

from .key_generator import FuncKeyCreator

Key = TypeVar('Key', bound=Hashable)
Value = TypeVar('Value', bound=object)
Result = tuple[Value, bool]


class Cache(ABC):
    """
    Базовый интерфейс кэширования элементов (ключ-значение + поддержка TTL)
    """

    key_function: FuncKeyCreator
    """
    Реализация хэширования функции и ее аргументов
    """

    def _serialize(self, element: Any) -> bytes:
        """
        Сериализует элемент в байты для сохранения в кэше.
        :param element: Элемент для сериализации.
        :return: Сериализованный элемент в виде байтов.
        """
        return msgspec.json.encode(element)

    def _deserialize(self, element: bytes | None, cast_to: Any) -> Any:
        """
        Десериализует элемент из байтов.
        :param element: Элемент для десериализации в виде байтов.
        :param cast_to: Тип, к которому следует привести
        десериализованный элемент.
        :return: Десериализованный элемент.
        """
        return msgspec.json.decode(element, type=cast_to)

    @abstractmethod
    def set(
        self,
        key: Key,
        value: Value,
        ttl: int | None = None,
    ) -> None:
        """
        Сохраняет элемент в кэше.
        :param key: Ключ, по которому будет доступен элемент.
        :param value: Значение элемента.
        :param ttl: Время жизни элемента в кэше в секундах.
         Если None, элемент будет храниться в кэше бессрочно.
        """
        ...

    @abstractmethod
    def set_many(
        self,
        elements: Mapping[Key, Value],
        ttl: int | None = None
    ) -> None:
        """
        Сохраняет несколько элементов в кэше.
        :param elements: Словарь, где ключ - это ключ для доступа к элементу,
         а значение - это сам элемент.
        :param ttl: Время жизни элементов в кэше в секундах. Если None,
         элементы будут храниться в кэше бессрочно.
        """

    @abstractmethod
    def exists(self, key: Key) -> bool:
        """
        Проверяет, существует ли элемент в кэше.
        :param key: Ключ, по которому осуществляется доступ к элементу.
        :return: True, если элемент существует и его время жизни не истекло,
         иначе False.
        """
        ...

    @abstractmethod
    def get(self, key: Key, cast_to: Type[Value]) -> Result:
        """
        Получает элемент из кэша.
        :param key: Ключ, по которому осуществляется доступ к элементу.
        :param cast_to: Тип, к которому следует привести полученный элемент.
        :return: Значение элемента и флаг, указывающий, был ли элемент найден в
         кэше.
        """
        ...

    @abstractmethod
    def get_many(self, keys: dict[Key, Type[Value]]) -> Mapping[Key, Result]:
        """
        Получает несколько элементов из кэша.
        :param keys: Словарь, где ключ - это ключ для доступа к элементу,
         а значение - это тип, к которому следует привести полученный элемент.
        :return: Словарь, где ключ - это ключ для доступа к элементу,
         а значение - это кортеж, состоящий из значения элемента и флага,
         указывающего, был ли элемент найден в кэше.
        """

    @abstractmethod
    def invalidate(self, key: Key) -> None:
        """
        Удаляет элемент из кэша.
        :param key: Ключ, по которому осуществляется доступ к элементу.
        """
        ...

    @abstractmethod
    def invalidate_all(self) -> None:
        """
        Удаляет все элементы из кэша.
        """
        ...
