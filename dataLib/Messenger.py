class Messenger:
    min_level: int = 0
    _level_names = ["debug", "info", "warning", "error", "CRITICAL"]

    @staticmethod
    def __print(level: int, message: str) -> None:
        if level > Messenger.min_level:
            print(f"{Messenger._level_names[level % len(Messenger._level_names)]}: {message}")

    @staticmethod
    def debug(message: str) -> None:
        Messenger.__print(0, message)

    @staticmethod
    def info(message: str) -> None:
        Messenger.__print(1, message)

    @staticmethod
    def warning(message: str) -> None:
        Messenger.__print(2, message)

    @staticmethod
    def error(message: str) -> None:
        Messenger.__print(3, message)

    @staticmethod
    def critical(message: str) -> None:
        Messenger.__print(4, message)


