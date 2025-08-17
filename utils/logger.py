import logging


class Logger:
    def __init__(self, log_file: str = "bot.log", level: int = logging.INFO):
        self.logger = logging.getLogger("QABot")
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.hasHandlers():
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
