from typing import Hashable

from ..key_generator import FuncKeyCreator


class PureHash(FuncKeyCreator):
    """
    Наивная, но быстрая реализация с использованием Python'овского `hash`
    (потенциально могут быть коллизии из-за малой мощности словаря).

    **Обеспечивает персистентность только в рамках одного процесса!**
    """

    def hash_arguments(self, *args, **kwargs) -> int | str | None:

        # В боевых условиях надо вызывать с -OO для вырезания assert'ов
        assert all(isinstance(arg, Hashable) for arg in args)
        assert all(isinstance(value, Hashable) for value in kwargs.values())

        kwargs = tuple(sorted(kwargs.items()))

        if args and kwargs:
            tuple_creation = args + kwargs
        elif args:
            tuple_creation = args
        else:
            tuple_creation = kwargs

        return hash(tuple_creation) if args or kwargs else None
