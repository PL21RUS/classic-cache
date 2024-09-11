import time
from abc import ABC, abstractmethod
from typing import Mapping, Any, Hashable, TypeVar, Type, Generic

import msgspec

from .key_generator import FuncKeyCreator

Key = TypeVar('Key', bound=Hashable)
Value = TypeVar('Value', bound=object)
Result = tuple[Value, bool]


# TODO: пробрасывать версию прилождения и добавить проверку с удалением
#  (если версия не бъется с текущей)
# TODO: проверить с array-like (array_like=True)
class CachedValue(Generic[Value], msgspec.Struct):
    """
    Хранимое значение в кэше с дополнительной метаинформацией
    """
    value: Value
    """Значение элемента из кэша"""

    ttl: int | None = None
    """Время "жизни" элемента в кэше (секунды), None - "живет" бесконечно"""

    created: float = msgspec.field(default_factory=time.monotonic)
    """Время создания элемента"""

    version: int | None = None
    """Версия элемента"""


class Cache(ABC):
    """
    Базовый интерфейс кэширования элементов (ключ-значение + поддержка TTL)
    """

    key_function: FuncKeyCreator
    """
    Реализация хэширования функции и ее аргументов
    """
    version: int | None = None

    def _serialize(self, element: Any) -> bytes:
        return msgspec.json.encode(element)

    def _deserialize(self, element: bytes | None, cast_to: Any) -> Any:
        if element is None:
            return None
        return msgspec.json.decode(element, type=cast_to)

    @abstractmethod
    def set(
        self,
        key: Key,
        value: Value,
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
        elements: Mapping[Key, Value],
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
    def exists(self, key: Key) -> bool:
        """
        Проверка наличия элемента в кэше
        :param key: ключ доступа к элементу
        :return: `True`, если элемент существует и не просрочен, иначе `False`
        """
        ...

    @abstractmethod
    def get(self, key: Key, cast_to: Type[Value]) -> Result:
        """
        Получение сохраненного элемента из кэша
        :param key: ключ доступа к элементу
        :param cast_to: тип элемента
        :return: Элемент, если он существует и не просрочен, иначе `None`
        """
        ...

    @abstractmethod
    def get_many(self, keys: dict[Key, Type[Value]]) -> Mapping[Key, Result]:
        """
        Получение множества сохраненных элементов из кэша
        :param keys: маппинг ключ доступа к элементу на тип элемента
        :return: Словарь ключей и элементов,
            которые существуют в кэше и не являются просроченными
        """

    @abstractmethod
    def invalidate(self, key: Key) -> None:
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
