import msgspec

from ..key_generator import FuncKeyCreator


class MsgSpec(FuncKeyCreator):
    """
    Персистентное хэширование функции и аргументов при помощи msgspec
    """

    def hash_arguments(self, *args, **kwargs) -> int | str | None:
        if not (args or kwargs):
            return None

        kwargs = sorted(kwargs.items())
        arguments = (*args, *kwargs)

        # TODO: попробовать убрать декод, если нужен только Редису,
        #  то перенести в Редис
        return msgspec.json.encode(arguments).decode('utf8')
