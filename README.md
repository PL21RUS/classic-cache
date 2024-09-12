# Classic Cache

Classic Cache - предоставляет функциональность кеширования. Она поддерживает 
кэширование как в памяти, так и на  основе Redis, и позволяет легко 
переключаться между ними. Является частью проекта "Classic".

## Установка

Для установки Classic-Cache вы можете использовать pip:

```bash
pip install classic-cache
```

## Использование

Вот несколько примеров использования Classic-Cache.

### Кэширование в памяти

```python
from classic.cache import cached, InMemoryCache
from classic.components import component

@component
class SomeClass:

    @cached(ttl=60)
    def some_method(self, arg1: int, arg2: int) -> int:
        return arg1 + arg2

some_instance = SomeClass(cache=InMemoryCache())
```

В этом примере результаты `some_method` будут кэшироваться в течение 60 секунд. 
Кэш хранится в памяти.

### Кэширование в Redis

```python
from classic.cache import cached, RedisCache
from classic.components import component
from redis import Redis

@component
class SomeClass:

    @cached(ttl=60)
    def some_method(self, arg1: int, arg2: int) -> int:
        return arg1 + arg2

some_instance = SomeClass(cache=RedisCache(connection=Redis()))
```

В этом примере результаты `some_method` будут кэшироваться в течение 60 секунд. 
Кэш хранится в Redis.

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

## Вклад в проект

Вклады приветствуются! Пожалуйста, не стесняйтесь отправлять запрос на слияние.

## Лицензия

Classic-Cache лицензирована по лицензии MIT.
