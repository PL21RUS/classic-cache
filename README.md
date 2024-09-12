# Classic Cache

Classic Cache - предоставляет функциональность кеширования. Она поддерживает 
кэширование как в памяти, так и на  основе Redis, и позволяет легко 
переключаться между ними. Является частью проекта "Classic".

## Установка

Для установки Classic-Cache вы можете использовать pip:

```bash
pip install classic-cache
```

Для установки Classic-Cache с поддержкой Redis:

```bash
pip install classic-cache[redis]
```

## Использование

Вот несколько примеров использования Classic-Cache.

### Кэширование в памяти

```python
from classic.cache import cached, InMemoryCache, RedisCache
from classic.components import component

@component
class SomeClass:

    # Кэширование результата метода some_method на 60 секунд
    @cached(ttl=60)
    def some_method(self, arg1: int, arg2: int) -> int:
        return arg1 + arg2

# кеширование в памяти
some_instance = SomeClass(cache=InMemoryCache())
# кеширование в Redis
some_instance = SomeClass(cache=RedisCache(connection=Redis()))
```

### Инвалидация кэша

Вы можете вручную инвалидировать кэш для определенного метода так:

```python
some_instance = SomeClass(cache=...)
some_instance.some_method.invalidate(1, 2)
```

Это удалит кэшированный результат для `some_method` с аргументами `1` и `2`.

### Обновление кэша

Вы можете вручную обновить кэш для определенного метода так:

```python
some_instance = SomeClass(cache=...)
some_instance.some_method.refresh(1, 2)
```

Это обновит кэшированный результат для `some_method` с аргументами `1` и `2`.
