import functools
from datetime import timedelta
from typing import Callable

from classic.components import add_extra_annotation
from classic.components.types import Decorator

from .cache import Cache, CachedValue


# @cache(ttl=timedelta(hours=1)) (пример использования)

def cache(ttl: int | timedelta | None = None) -> Decorator:
    """
    Кэширование функций component'ов
    :param ttl: время "жизни" элемента (секунды)
    :return: декоратор с возможностью извлечения из кэша значения функции
    """

    if ttl and isinstance(ttl, timedelta):
        ttl = int(ttl.total_seconds())

    def inner(func: Callable):

        def wrapper(*args, **kwargs):
            class_self = args[0]
            cache_instance: Cache = getattr(class_self, '__cache__')

            # исключаем self из arg'ов
            function_key = cache_instance.key_function(
                func, *args[1:], **kwargs
            )

            cached_result = cache_instance.get(
                function_key, CachedValue[func.__annotations__['return']]
            )

            if cached_result:
                return cached_result.value
            else:
                result = func(*args, **kwargs)
                cache_instance.set(
                    function_key, CachedValue(result, ttl=ttl), ttl
                )

                return result

        wrapper = functools.update_wrapper(wrapper, func)
        wrapper = add_extra_annotation(wrapper, '__cache__', Cache)

        return wrapper

    return inner
