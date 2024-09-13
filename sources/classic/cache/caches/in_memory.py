import time
from dataclasses import field

from typing import Mapping, Type

from classic.components import component

from ..cache import Cache, Key, Value, Result
from ..key_generators import PureHash


@component
class InMemoryCache(Cache):
    key_function = field(default_factory=PureHash)
    cache: dict[Key, tuple[int | None, bytes]] = field(default_factory=dict)

    def set(
        self,
        key: Key,
        value: Value,
        ttl: int | None = None,
    ) -> None:
        self.cache[key] =(
            time.monotonic() + ttl if ttl else None, self._serialize(value)
        )

    def set_many(
        self,
        elements: Mapping[Key, Value],
        ttl: int | None = None
    ) -> None:
        for key, value in elements.items():
            self.set(key, value, ttl=ttl)

    def exists(self, key: Key) -> bool:
        try:
            expiry, _ = self.cache[key]
        except KeyError:
            return False

        return expiry is None or time.monotonic() < expiry

    def get(self, key: Key, cast_to: Type[Value]) -> Result:
        try:
            expiry, cached_value = self.cache[key]
        except KeyError:
            return None, False

        if expiry is not None and time.monotonic() >= expiry:
            return None, False

        return self._deserialize(cached_value, cast_to), True

    def get_many(self, keys: dict[Key, Type[Value]]) -> Mapping[Key, Result]:
        return {key: self.get(key, cast_to) for key, cast_to in keys.items()}

    def invalidate(self, key: Key) -> None:
        self.cache.pop(key, None)

    def invalidate_all(self) -> None:
        self.cache.clear()
