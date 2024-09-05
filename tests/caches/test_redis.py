from dataclasses import dataclass
from datetime import datetime

import pytest
from fakeredis import FakeRedis
from freezegun import freeze_time

from classic.cache import Cache
from classic.cache.caches import RedisCache


@dataclass(frozen=True)
class FrozenDataclass:
    x: int
    y: int


# реализации кэширования (дополняем при необходимости)
@pytest.fixture(scope='function')
def redis_cache():
    return RedisCache(connection=FakeRedis())


# ссылки на экземпляров реализации кэшей (используем название фикстуры)
cache_instances = ('redis_cache', )


# параметизированный экземпляр кэша (request.param - фикстура с реализацией)
@pytest.fixture(scope='function')
def cache_instance(request) -> Cache:
    return request.getfixturevalue(request.param)


@pytest.fixture(scope='function')
def next_year():
    today = datetime.today()
    return datetime(year=today.year + 1, month=today.month, day=today.day)


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_without_ttl(cache_instance, cached_value_type):
    key = 'test'
    cache_instance.set(key, cached_value_type(10.5))
    cache_result = cache_instance.get(key, cast_to=cached_value_type)

    assert (
        cache_result and cache_result.value == 10.5 and cache_result.ttl is None
    )


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_with_ttl(cache_instance, cached_value_type):
    key, value, ttl = 'test', -0.1, 60

    cache_instance.set(key, cached_value_type(value, ttl), ttl)
    cache_result = cache_instance.get(key, cached_value_type)

    assert (
        cache_result and cache_result.value == value and cache_result.ttl == ttl
    )


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_expired(cache_instance, next_year, cached_value_type):
    key, value, ttl = 'test', 0.1, 10
    cache_instance.set(key, cached_value_type(value, ttl), ttl)

    # make sure that the cached value is expired by using 1 year gap
    with freeze_time(next_year):
        assert cache_instance.get(key, cached_value_type) is None


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_without_ttl(cache_instance, cached_value_type):
    elements = {f'test_{index}': cached_value_type for index in range(5)}
    value = 100.0
    expected = {key: type_(value) for key, type_ in elements.items()}

    cache_instance.set_many({key: element for key, element in expected.items()})

    result = cache_instance.get_many(elements)

    assert {*result.keys()} == {*expected.keys()}

    for key, element in result.items():
        expected_element = expected[key]
        assert (
            expected_element.value == element.value
            and expected_element.ttl == expected_element.ttl
        )


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_with_ttl(cache_instance, cached_value_type):
    elements = {f'test_{index}': cached_value_type for index in range(5)}
    value, ttl = 1.1, 60
    expected = {key: type_(value) for key, type_ in elements.items()}

    cache_instance.set_many(
        {key: element for key, element in expected.items()}, ttl
    )

    result = cache_instance.get_many(elements)

    assert {*result.keys()} == {*expected.keys()}

    for key, element in result.items():
        expected_element = expected[key]
        assert (
            expected_element.value == element.value
            and expected_element.ttl == expected_element.ttl
        )


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_expired(cache_instance, cached_value_type, next_year):
    elements = {f'test_{index}': cached_value_type(1.1) for index in range(5)}
    ttl = 100

    cache_instance.set_many(
        {key: element for key, element in elements.items()}, ttl
    )

    with freeze_time(next_year):
        assert not cache_instance.get_many(elements)


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_get_set_many_partial(cache_instance, cached_value_type, next_year):
    non_expired_key = 'test_0'
    value, ttl = -100.0, 50
    expired_keys = {
        f'test_{index}': cached_value_type for index in range(1, 55)
    }
    all_keys = expired_keys | {non_expired_key: cached_value_type}

    cache_instance.set(non_expired_key, cached_value_type(value))
    cache_instance.set_many(
        {key: type_(value) for key, type_ in expired_keys.items()}, ttl
    )

    with freeze_time(next_year):
        result = cache_instance.get_many(all_keys)
        assert len(result) == 1


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_invalidate(cache_instance, cached_value_type):
    key = 'test'

    cache_instance.set(key, cached_value_type(1.0))
    cache_instance.invalidate(key)

    assert cache_instance.get(key, cached_value_type) is None


@pytest.mark.parametrize('cache_instance', cache_instances, indirect=True)
def test_invalidate_all(cache_instance, cached_value_type):
    elements = {f'test_{index}': cached_value_type for index in range(5)}
    value, ttl = 1.0, 60
    expected = {key: type_(value) for key, type_ in elements.items()}

    cache_instance.set_many(expected, ttl)
    cache_instance.invalidate_all()

    assert not cache_instance.get_many(elements)


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
