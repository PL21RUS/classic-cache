from abc import ABC, abstractmethod
from inspect import isclass, ismethod
from typing import Callable, Hashable


class FuncKeyCreator(ABC):
    """
    Общий класс хэширования функции и ее аргументов
    """

    MODULE_SEP = '->'
    ARGS_SEP = ':'

    @abstractmethod
    def hash_arguments(self, *args, **kwargs) -> Hashable | None:
        """
        Метод представления `args` и `kwargs` функции в хэш (число/строка)
        :param args: позиционные аргументы
        :param kwargs: именованные аргументы
        :return: хэш-представление
        """
        ...

    def __call__(self, func: Callable, *args, **kwargs) -> str:
        """
        Преобразование функции и ее аргументов в ключ доступа элемента кэша.

        Аргументы функции **должны** обладать возможностью отдавать
        своё хэш-представление!
        """

        hashed_arguments = self.hash_arguments(*args, **kwargs)

        function_name = func.__qualname__

        # TODO: отлавливаем ли статические методы в кейсах наследования классов?
        if ismethod(func):
            # экземпляр класса или class method
            origin = (
                func.__self__.__class__
                if not isclass(func.__self__) else func.__self__
            )
            function_name = origin.__qualname__

        func_key = f'{func.__module__}{self.MODULE_SEP}{function_name}'
        return (
            f'{func_key}{self.ARGS_SEP}{hashed_arguments}'
            if hashed_arguments else func_key
        )
