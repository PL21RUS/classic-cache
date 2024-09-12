from typing import Hashable

import msgspec

from ..key_generator import FuncKeyCreator


class MsgSpec(FuncKeyCreator):
    """
    Персистентное хэширование функции и аргументов при помощи msgspec
    """

    def hash_arguments(self, *args, **kwargs) -> Hashable | None:
        if not (args or kwargs):
            return None

        kwargs = sorted(kwargs.items())
        arguments = (*args, *kwargs)

        return msgspec.json.encode(arguments)
