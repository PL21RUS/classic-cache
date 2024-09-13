try:
    from fakeredis import FakeRedis
    redis_installed = True
except ImportError:
    FakeRedis = type('FakeRedis', (), {})
    redis_installed = False

from dataclasses import dataclass
from datetime import datetime

import pytest
from freezegun import freeze_time

from classic.cache import Cache
from classic.cache.caches import RedisCache, InMemoryCache


@dataclass(frozen=True)
class FrozenDataclass:
    x: int
    y: int


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


@pytest.fixture(scope='function')
def next_year():
    today = datetime.today()
    return datetime(year=today.year + 1, month=today.month, day=today.day)


@pytest.mark.skipif(
    not redis_installed, reason='redis package is not installed'
)
def test_get_set_with_actual_version_redis(redis_cache):
    key, value, version = 'test', 1.0, 1
    redis_cache.version = version

    redis_cache.set(key, value)
    cached_value, found = redis_cache.get(key, float)

    assert found and cached_value == value


@pytest.mark.skipif(
    not redis_installed, reason='redis package is not installed'
)
def test_get_set_with_old_version_redis(redis_cache):
    key, value, version = 'test', 1.0, 1
    redis_cache.version = version

    redis_cache.set(key, value)
    redis_cache.version += 1

    cached_value, found = redis_cache.get(key, float)

    assert not found


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_without_ttl(cache_instance):
    key = 'test'
    cache_instance.set(key, 10.5)
    cache_value, found = cache_instance.get(key, float)
    assert found and cache_value == 10.5


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_none_value(cache_instance):
    key = 'test'
    cache_instance.set(key, None)
    cache_value, found = cache_instance.get(key, None)
    assert found and cache_value is None


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_with_ttl(cache_instance):
    key, value, ttl = 'test', -0.1, 60

    cache_instance.set(key, value, ttl)
    cached_value, found = cache_instance.get(key, float)

    assert found and cached_value == value


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_expired(cache_instance, next_year):
    key, value, ttl = 'test', 0.1, 10
    cache_instance.set(key, value, ttl)

    # make sure that the cached value is expired by using 1 year gap
    with freeze_time(next_year):
        __, found = cache_instance.get(key, float)
        assert not found


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_without_ttl(cache_instance):
    elements = {f'test_{index}': float for index in range(5)}
    value = 100.0
    expected = {key: (value, True) for key, cast_to in elements.items()}

    cache_instance.set_many({key: value for key in expected})

    result = cache_instance.get_many(elements)

    assert {*result.keys()} == {*expected.keys()}

    for key, (cached_value, found) in result.items():
        expected_value, expected_found = expected[key]
        assert cached_value == expected_value and found == expected_found


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_with_ttl(cache_instance):
    elements = {f'test_{index}': float for index in range(5)}
    value, ttl = 1.0, 60
    expected = {key: (value, True) for key, cast_to in elements.items()}

    cache_instance.set_many({key: value for key in expected}, ttl)

    result = cache_instance.get_many(elements)

    assert {*result.keys()} == {*expected.keys()}

    for key, (cached_value, found) in result.items():
        expected_value, expected_found = expected[key]
        assert cached_value == expected_value and found == expected_found


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_expired(cache_instance, next_year):
    elements = {f'test_{index}': float for index in range(5)}
    value, ttl = 1.1, 100

    cache_instance.set_many({key: value for key in elements}, ttl)

    with freeze_time(next_year):
        results = cache_instance.get_many(elements)
        assert all(not found for value, found in results.values())


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_partial(cache_instance, next_year):
    non_expired_key = 'test_0'
    value, ttl = -100.0, 50
    expired_keys = {f'test_{index}': float for index in range(1, 55)}
    all_keys = expired_keys | {non_expired_key: float}

    cache_instance.set(non_expired_key, value)
    cache_instance.set_many({key: value for key in expired_keys}, ttl)

    with freeze_time(next_year):
        result = [
            value for value, found in cache_instance.get_many(all_keys).values()
            if found
        ]
        assert len(result) == 1


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_invalidate(cache_instance):
    key = 'test'

    cache_instance.set(key, 1.0)
    cache_instance.invalidate(key)

    __, found = cache_instance.get(key, float)
    assert not found


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_invalidate_all(cache_instance):
    elements = {f'test_{index}': float for index in range(5)}
    value, ttl = 1.0, 60
    expected = {key: value for key in elements}

    cache_instance.set_many(expected, ttl)
    cache_instance.invalidate_all()

    results = cache_instance.get_many(elements)
    assert all(not found for __, found in results.values())


@pytest.mark.parametrize(
    'key,expected', [
        (1, bytes), ('str', bytes), (datetime(2023, 12, 31), bytes),
        (FrozenDataclass(1, 2), bytes)
    ]
)
def test_serialize(request, key, expected):
    # пример с множественными параметрами теста
    for cache in cache_instances:
        instance = request.getfixturevalue(cache)
        encoded_key = instance._serialize(key)
        assert isinstance(encoded_key, expected)
