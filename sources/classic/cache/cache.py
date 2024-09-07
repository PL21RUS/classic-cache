import time
from abc import ABC, abstractmethod
from typing import Mapping, Any, Hashable, TypeVar, Type, Generic

import msgspec

from .key_generator import FuncKeyCreator

CachedValueType = TypeVar('CachedValueType')


class CachedValue(Generic[CachedValueType], msgspec.Struct):
    """
    Хранимое значение в кэше с дополнительной метаинформацией
    """
    value: CachedValueType
    """Значение элемента из кэша"""

    ttl: int | None = None
    """Время "жизни" элемента в кэше (секунды), None - "живет" бесконечно"""

    created: float = msgspec.field(default_factory=time.monotonic)
    """Время создания элемента"""


class Cache(ABC):
    """
    Базовый интерфейс кэширования элементов (ключ-значение + поддержка TTL)
    """

    key_function: FuncKeyCreator
    """
    Реализация хэширования функции и ее аргументов
    """

    def _serialize(self, element: Any) -> bytes:
        return msgspec.json.encode(element)

    def _deserialize(self, element: bytes | None, cast_to: Any) -> Any:
        if element is None:
            return None
        return msgspec.json.decode(element, type=cast_to)

    @abstractmethod
    def set(
        self,
        key: Hashable,
        cached_value: CachedValueType,
        ttl: int | None = None,
    ) -> None:
        """
        Сохранение элемента `element` в кэше
        :param key: ключ доступа к элементу
        :param cached_value: значение элемента упакованное в структуру
         `CachedValue`
        :param ttl: время "жизни"
            (как долго элемент может находиться в кэше)
        """
        ...

    @abstractmethod
    def set_many(
        self,
        elements: Mapping[Hashable, CachedValueType],
        ttl: int | None = None
    ) -> None:
        """
        Сохранение множества элементов `elements` в кэше
        :param elements: ключи доступа и значения элементов
        упакованное в структуру `CachedValue`
        :param ttl: время "жизни"
            (как долго элемент может находиться в кэше)
        """

    @abstractmethod
    def get(self, key: Hashable, cast_to: Type) -> CachedValueType | None:
        """
        Получение сохраненного элемента из кэша
        :param key: ключ доступа к элементу
        :param cast_to: тип элемента
        :return: Элемент, если он существует и не просрочен, иначе `None`
        """
        ...

    @abstractmethod
    def get_many(self, keys: dict[Hashable, Type]) -> Mapping[Hashable, Any]:
        """
        Получение множества сохраненных элементов из кэша
        :param keys: маппинг ключ доступа к элементу на тип элемента
        :return: Словарь ключей и элементов,
            которые существуют в кэше и не являются просроченными
        """

    @abstractmethod
    def invalidate(self, key: Hashable) -> None:
        """
        Удаление элемента из кэша
        :param key: ключ доступа к элементу
        """
        ...

    @abstractmethod
    def invalidate_all(self) -> None:
        """
        Удаление всех элементов из кэша
        """
        ...
