import os
from multiprocessing import Lock
import ruamel.yaml

# 线程锁
lock = Lock()

# 全局实例
_CONFIG = None


def singleconfig(cls):
    def _singleconfig(*args, **kwargs):
        global _CONFIG
        if not _CONFIG:
            with lock:
                _CONFIG = cls(*args, **kwargs)
        return _CONFIG

    return _singleconfig


@singleconfig
class Config(object):
    _config = {}
    _config_path = None
    _user = None

    def __init__(self):
        self._config_path = 'config/config.yaml'
        self.init_config()

    def init_config(self):
        try:
            with open(self._config_path, mode='r', encoding='utf-8') as cf:
                self._config = ruamel.yaml.YAML().load(cf)
        except Exception as err:
            print("【Config】error: %s" % str(err))
            return False

    def get_config(self, node=None):
        if not node:
            return self._config
        return self._config.get(node, {})

    def save_config(self, new_cfg):
        self._config = new_cfg
        with open(self._config_path, mode='w', encoding='utf-8') as sf:
            yaml = ruamel.yaml.YAML()
            return yaml.dump(new_cfg, sf)

    def get_config_path(self):
        return os.path.dirname(self._config_path)

    def get_temp_path(self):
        return os.path.join(self.get_config_path(), "temp")

    @staticmethod
    def get_root_path():
        return os.path.dirname(os.path.realpath(__file__))

    def get_inner_config_path(self):
        return os.path.join(self.get_root_path(), "config")

if __name__ == "__main__":
    cfg = Config()
    logtype = cfg.get_config('app').get('logtype')
    print(logtype)