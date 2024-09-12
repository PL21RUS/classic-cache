from typing import Any, Callable, Hashable

from orjson import dumps

from ..key_generator import FuncKeyCreator


class OrJson(FuncKeyCreator):
    """
    Персистентное хэширование функции и аргументов при помощи orjson
    """

    def __init__(
        self,
        options: int | None = None,
        default: Callable[[Any], Any] | None = None
    ):
        """
        Инициализация опций orjson (см. https://github.com/ijl/orjson)
        :param options: опции поведения сериализатора с помощью флагов
        :param default: callable для серилазации нестандартных типов данных
        """
        self.options = options
        self.default = default

    def hash_arguments(self, *args, **kwargs) -> Hashable | None:
        if not (args or kwargs):
            return None

        kwargs = sorted(kwargs.items())
        arguments = (*args, *kwargs)

        return dumps(arguments, self.default, self.options)
