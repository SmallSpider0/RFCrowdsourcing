# 添加当前路径至解释器，确保单元测试时可正常import其它文件
import os
import sys
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 基于顶层包的import
from utils.config import Config

# 系统库
import logging
import os
import multiprocessing
from collections import deque
from logging.handlers import RotatingFileHandler

logging.getLogger('SmallSpider').setLevel(logging.ERROR)
lock = multiprocessing.Lock()

LOG_QUEUE = deque(maxlen=200)
LOG_INDEX = 0


class Logger:
    logger = None
    __instance = {}
    __config = None

    __loglevels = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "error": logging.ERROR
    }

    def __init__(self, module):
        self.logger = logging.getLogger(module)
        self.__config = Config()
        logtype = self.__config.get_config('app').get('logtype') or "console"
        loglevel = self.__config.get_config('app').get('loglevel') or "info"
        self.logger.setLevel(level=self.__loglevels.get(loglevel))
        if logtype == "server":
            # TODO：待实现
            pass
            # logserver = self.__config.get_config('app').get('logserver', '').split(':')
            # if logserver:
            #     logip = logserver[0]
            #     if len(logserver) > 1:
            #         logport = int(logserver[1] or '514')
            #     else:
            #         logport = 514
            #     log_server_handler = logging.handlers.SysLogHandler((logip, logport),
            #                                                         logging.handlers.SysLogHandler.LOG_USER)
            #     log_server_handler.setFormatter(logging.Formatter('%(filename)s: %(message)s'))
            #     self.logger.addHandler(log_server_handler)
        elif logtype == "file":
            # 记录日志到文件
            logpath = self.__config.get_config('app').get('logpath') or ""
            if logpath:
                if not os.path.exists(logpath):
                    os.makedirs(logpath)
                log_file_handler = RotatingFileHandler(filename=os.path.join(logpath, module + ".txt"),
                                                       maxBytes=5 * 1024 * 1024,
                                                       backupCount=3,
                                                       encoding='utf-8')
                log_file_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s: %(message)s'))
                self.logger.addHandler(log_file_handler)
        # 记录日志到终端
        log_console_handler = logging.StreamHandler()
        log_console_handler.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s: %(message)s'))
        self.logger.addHandler(log_console_handler)

    @staticmethod
    def get_instance(module):
        if not module:
            module = "main"
        if Logger.__instance.get(module):
            return Logger.__instance.get(module)
        with lock:
            Logger.__instance[module] = Logger(module)
        return Logger.__instance.get(module)


def debug(text, module=None):
    return Logger.get_instance(module).logger.debug(text)


def info(text, module=None):
    return Logger.get_instance(module).logger.info(text)


def error(text, module=None):
    return Logger.get_instance(module).logger.error(text)


def warn(text, module=None):
    return Logger.get_instance(module).logger.warning(text)


def console(text):
    print(text)


if __name__ == "__main__":
    debug(f"【Main】test {123}")
    info(f"【Main】test {123}")
    error(f"【Main】test {123}")