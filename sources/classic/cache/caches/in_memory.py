import time
from typing import Mapping, Type

from classic.components import component

from ..cache import Cache, CachedValue, Key, Value, Result
from ..key_generators import PureHash


@component
class InMemoryCache(Cache):
    """
    In-memory реализация кэширования
    """
    key_function = PureHash()

    def __init__(self):
        self.cache = {}

    def _save_value(
        self,
        key: Key,
        cached_value: CachedValue,
        ttl: int | None = None,
    ) -> None:
        self.cache[key] = (
            time.monotonic() + ttl if ttl else None, cached_value
        )

    def set(
        self,
        key: Key,
        value: Value,
        ttl: int | None = None,
    ) -> None:
        cached_value = CachedValue(value, ttl=ttl)
        self._save_value(key, cached_value, ttl)

    def set_many(
        self,
        elements: Mapping[Key, Value],
        ttl: int | None = None
    ) -> None:
        for key, value in elements.items():
            cached_value = CachedValue[Value](value, ttl=ttl)
            self._save_value(key, cached_value, ttl)

    def exists(self, key: Key) -> bool:
        if key in self.cache:
            expiry, _ = self.cache[key]
            # TODO: в каких случаях возвращать True?
            return expiry is None or time.monotonic() < expiry
        return False

    def get(self, key: Key, cast_to: Type[Value]) -> Result:
        if key in self.cache:
            expiry, value = self.cache[key]
            if expiry is None or time.monotonic() < expiry:
                return value, True
            else:
                del self.cache[key]
        return None, False

    def get_many(self, keys: dict[Key, Type[Value]]) -> Mapping[Key, Result]:
        return {key: self.get(key, cast_to) for key, cast_to in keys.items()}

    def invalidate(self, key: Key) -> None:
        self.cache.pop(key, None)

    def invalidate_all(self) -> None:
        self.cache.clear()
