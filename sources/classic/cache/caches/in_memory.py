import time
from typing import Any, Mapping, Hashable, Type

from classic.components import component

from ..cache import Cache, CachedValueType
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
        key: Hashable,
        cached_value: CachedValueType,
        ttl: int | None = None,
    ) -> None:
        self.cache[key] = (
            time.monotonic() + ttl if ttl else None, cached_value
        )

    def set(
        self,
        key: Hashable,
        cached_value: CachedValueType,
        ttl: int | None = None,
    ) -> None:
        self._save_value(key, cached_value, ttl)

    def set_many(
        self,
        elements: Mapping[Hashable, CachedValueType],
        ttl: int | None = None,
    ) -> None:
        for key, value in elements.items():
            self._save_value(key, value, ttl)

    def get(self, key: Hashable, cast_to: Type) -> CachedValueType | None:
        if key in self.cache:
            expiry, value = self.cache[key]
            if expiry is None or time.monotonic() < expiry:
                return value
            else:
                del self.cache[key]
        return None

    def get_many(self, keys: dict[Hashable, Type]) -> Mapping[Hashable, Any]:
        return {key: self.get(key, cast_to) for key, cast_to in keys.items()}

    def invalidate(self, key: Hashable) -> None:
        self.cache.pop(key, None)

    def invalidate_all(self) -> None:
        self.cache.clear()
