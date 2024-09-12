try:
    from fakeredis import FakeRedis
    redis_installed = True
except ImportError:
    FakeRedis = type('FakeRedis', (), {})
    redis_installed = False

import pytest

from classic.cache import cached, Cache
from classic.components import component

from classic.cache.caches import RedisCache, InMemoryCache


@component
class SomeClass:

    @cached(ttl=60)
    def some_method(self, arg1: int, arg2: int) -> int:
        return arg1 + arg2


# реализации кэширования (дополняем при необходимости)
@pytest.fixture(scope='function')
@pytest.mark.skipif(
    not redis_installed, reason='redis package is not installed'
)
def redis_cache():
    return RedisCache(connection=FakeRedis())


@pytest.fixture(scope='function')
def in_memory_cache():
    return InMemoryCache()


# ссылки на экземпляров реализации кэшей (используем название фикстуры)
cache_instances = ['in_memory_cache']
if redis_installed:
    cache_instances.append('redis_cache')


# параметизированный экземпляр кэша (request.param - фикстура с реализацией)
@pytest.fixture(scope='function')
def cache_instance(request) -> Cache:
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_invalidate(cache_instance):
    some_instance = SomeClass(cache=cache_instance)
    some_instance.some_method(1, 2)

    fn_key = cache_instance.key_function(SomeClass.some_method, 1, 2)
    __, found = cache_instance.get(fn_key, int)
    assert found

    some_instance.some_method.invalidate(1, 2)
    __, found = cache_instance.get(fn_key, int)
    assert not found


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_refresh(cache_instance):
    some_instance = SomeClass(cache=cache_instance)
    some_instance.some_method.refresh(1, 2)

    fn_key = cache_instance.key_function(SomeClass.some_method, 1, 2)
    __, found = cache_instance.get(fn_key, int)
    assert found
