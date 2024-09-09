from dataclasses import field
from typing import Any, Mapping, Hashable, Type

try:
    from redis import Redis
    from redis.client import Pipeline as RedisPipeline
    redis_installed = True
except ImportError:
    Redis = RedisPipeline = Type
    redis_installed = False

from classic.components import component

from ..cache import Cache, CachedValueType
from ..key_generators import Blake2b


@component
class RedisCache(Cache):
    """
    Redis-реализация кэширования (TTL without history)
    """
    connection: Redis
    key_function = field(default_factory=Blake2b)

    def __post_init__(self):
        if not redis_installed:
            raise ImportError(
                'RedisCache requires "redis" package to be installed'
            )

    def _save_value(
        self,
        connection: Redis | RedisPipeline,
        key: Hashable,
        value: CachedValueType,
        ttl: int | None = None,
    ) -> None:
        """
        Сохранение элемента `value` в кэше с ассоциацией по ключу доступа `key`
        с временем жизни `ttl` (`None` - элемент не покидает кэш)
        :param connection: прямое соединение с Redis / pipeline'ом
        :param key:  ключ доступа
        :param value: элемент для сохранения
        :param ttl: время "жизни" элемента
        """
        encoded_key = self._serialize(key)
        encoded_value = self._serialize(value)

        if ttl:
            # set TTL operation (will be deleted after x seconds)
            connection.setex(encoded_key, ttl, encoded_value)
        else:
            # write as is without TTL
            connection.set(encoded_key, encoded_value)

    def set(
        self,
        key: Hashable,
        cached_value: CachedValueType,
        ttl: int | None = None,
    ) -> None:
        self._save_value(self.connection, key, cached_value, ttl)

    def set_many(
        self,
        elements: Mapping[Hashable, CachedValueType],
        ttl: int | None = None,
    ) -> None:
        # Используем механизм pipeline для ускорения процесса записи
        # https://redis.io/docs/manual/pipelining/

        pipe = self.connection.pipeline()

        for key, value in elements.items():
            self._save_value(pipe, key, value, ttl)

        pipe.execute()

    def get(self, key: Hashable, cast_to: Type) -> CachedValueType | None:
        encoded_key = self._serialize(key)
        _value = self.connection.get(encoded_key)

        if not _value:
            return None
        else:
            return self._deserialize(_value, cast_to)

    def get_many(self, keys: dict[Hashable, Type]) -> Mapping[Hashable, Any]:
        encoded_keys = [self._serialize(key) for key in keys]
        decoded_values = self.connection.mget(encoded_keys)

        # Воспользуемся zip() для облегчения процесса итерации, т.к.
        # значения возвращаются в том же порядке, как были поданы ключи.
        # Дополнительно фильтруем ключ-значение, если оно исчезло
        # из Redis'а по какой-то причине
        return {
            key: self._deserialize(decoded_value, cast_to)
            for (key, cast_to), decoded_value in zip(
                keys.items(), decoded_values
            )
        }

    def invalidate(self, key: Hashable) -> None:
        encoded_key = self._serialize(key)

        # Можем вызывать as is, т.к. несуществующие ключи будут проигнорированы
        self.connection.delete(encoded_key)

    def invalidate_all(self) -> None:
        # Делаем асинхронное удаление данных
        # на стороне Redis без блокировки нашего потока
        self.connection.flushdb(asynchronous=True)
