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
    """
    Обертка для функции, которая кэширует результаты ее выполнения.

    Атрибуты:
    cache (Cache): Экземпляр кэша, который используется для хранения результатов.
    instance (object): Экземпляр объекта, для которого вызывается функция.
    func (Callable): Функция, результаты которой кэшируются.
    return_type (Type[object]): Тип возвращаемого значения функции.
    ttl (int | None): Время жизни кэшированных результатов в секундах. Если
    None, результаты будут храниться в кэше бессрочно.
    """
    cache: Cache
    instance: object
    func: Callable
    return_type: Type[object]
    ttl: int | None = None

    def __call__(self, *args, **kwargs):
        """
        Вызывает функцию и кэширует ее результаты.
        """
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        cached, found = self.cache.get(fn_key, self.return_type)
        if found:
            return cached

        result = self.func(self.instance, *args, **kwargs)

        self.cache.set(fn_key, result, self.ttl)

        return result

    def invalidate(self, *args, **kwargs):
        """
        Инвалидирует кэшированный результат функции.
        """
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        self.cache.invalidate(fn_key)

    def refresh(self, *args, **kwargs):
        """
        Обновляет кэшированный результат функции, вызывая ее заново.
        """
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        result = self.func(self.instance, *args, **kwargs)
        self.cache.set(fn_key, result, self.ttl)

    def refresh_if_exists(self, *args, **kwargs):
        """
        Обновляет кэшированный результат функции, если он существует в кэше.
        """
        fn_key = self.cache.key_function(self.func, *args, **kwargs)
        found = self.cache.exists(fn_key)
        if found:
            result = self.func(*args, **kwargs)
            self.cache.set(fn_key, result, self.ttl)


@dataclass
class Wrapper:
    """
    Обертка для функции, которая возвращает экземпляр BoundedWrapper при вызове
    как атрибута экземпляра.

    Атрибуты:
    func (Callable): Функция, результаты которой кэшируются.
    return_type (Type[object]): Тип возвращаемого значения функции.
    attr (str): Имя атрибута, содержащего экземпляр кэша.
    ttl (int | None): Время жизни кэшированных результатов в секундах. Если
    None, результаты будут храниться в кэше бессрочно.
    """
    func: Callable
    return_type: Type[object]
    attr: str
    ttl: int | None = None

    def __get__(self, instance, owner):
        """
        Возвращает экземпляр BoundedWrapper при вызове как атрибута экземпляра.
        """
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
    Декоратор для кэширования результатов функции.

    Параметры:
    ttl (int | timedelta | None): Время жизни кэшированных результатов. Если
    передано значение типа timedelta, оно будет преобразовано в секунды. Если
    None, результаты будут храниться в кэше бессрочно.
    attr (str): Имя атрибута, содержащего экземпляр кэша.

    Возвращает:
    Decorator: Декоратор, который можно применить к функции для кэширования ее
    результатов.
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
