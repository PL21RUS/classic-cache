import pytest
import time
import msgspec


@pytest.fixture(scope='function')
def cached_value_type():
    return msgspec.defstruct(
        'CachedValue',
        [
            ('value', float),
            ('ttl', int | None, None),
            ('created', float, msgspec.field(default_factory=time.monotonic)),
        ]
    )
