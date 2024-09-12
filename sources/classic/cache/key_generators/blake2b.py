from typing import Hashable

from hashlib import blake2b
from pickle import dumps

from ..key_generator import FuncKeyCreator


class Blake2b(FuncKeyCreator):
    """
    Реализация персистентного хэширования с использованием алгоритма **blake2b**
    (более медленная, чем `PureHash`, однако более устойчивая к коллизиям)
    """

    def hash_arguments(self, *args, **kwargs) -> Hashable | None:
        if not (args or kwargs):
            return None

        hash_instance = blake2b()
        kwargs = {key: kwargs[key] for key in sorted(kwargs.keys())}

        for arg in args:
            hash_instance.update(dumps(arg))

        for key, value in kwargs.items():
            hash_instance.update(dumps((key, value)))

        return hash_instance.hexdigest()
