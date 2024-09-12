import functools
from datetime import timedelta
from dataclasses import dataclass
from typing import Callable, Type
import inspect

from classic.components import add_extra_annotation
from classic.components.types import Decorator

from .cache import Cache


@dataclass
class BoundedWrapper:
    cache: Cache
    instance: object
    func: Callable
    return_type: Type[object]
    ttl: int | None = None

    def __call__(self, *args, **kwargs):
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        cached, found = self.cache.get(fn_key, self.return_type)
        if found:
            return cached

        result = self.func(self.instance, *args, **kwargs)

        self.cache.set(fn_key, result, self.ttl)

        return result

    def invalidate(self, *args, **kwargs):
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        self.cache.invalidate(fn_key)

    def refresh(self, *args, **kwargs):
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        result = self.func(self.instance, *args, **kwargs)
        self.cache.set(fn_key, result, self.ttl)

    def refresh_if_exists(self, *args, **kwargs):
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        found = self.cache.exists(fn_key)
        if found:
            result = self.func(*args, **kwargs)
            self.cache.set(fn_key, result, self.ttl)


@dataclass
class Wrapper:
    func: Callable
    return_type: Type[object]
    attr: str
    ttl: int | None = None

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return BoundedWrapper(
            getattr(instance, self.attr),
            instance,
            self.func,
            self.return_type,
            self.ttl,
        )


# @cached(ttl=timedelta(hours=1)) (пример использования)
def cached(ttl: int | timedelta | None = None, attr: str = 'cache') -> Decorator:
    """
    Кэширование функций component'ов
    :param ttl: время "жизни" элемента (секунды)
    :return: декоратор с возможностью извлечения из кэша значения функции
    """

    if ttl and isinstance(ttl, timedelta):
        ttl = int(ttl.total_seconds())

    def inner(func: Callable):
        return_type = inspect.signature(func).return_annotation
        assert return_type != inspect.Signature.empty, (
            'Необходимо указать аннотацию возвращаемого значения функции'
        )

        wrapper = Wrapper(func, return_type, attr, ttl)

        wrapper = functools.update_wrapper(wrapper, func)
        wrapper = add_extra_annotation(wrapper, 'cache', Cache)

        return wrapper

    return inner
