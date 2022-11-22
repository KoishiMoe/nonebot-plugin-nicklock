import json
import os
from typing import Dict, Optional, List

from nonebot.log import logger

CONF_PATH = os.path.join('data', 'database')
CONF_FILE = os.path.join(CONF_PATH, 'config.json')


class Config:
    config: Dict[str, Dict[str, str]] = {}
    __groups: Optional[List[str]] = None

    def __init__(self, config: dict):
        self.config = config

    @staticmethod
    def load() -> Optional['Config']:
        os.makedirs(CONF_PATH, exist_ok=True)
        if not os.path.exists(CONF_FILE):
            return Config({})
        with open(CONF_FILE, 'r', encoding='utf-8') as f:
            try:
                self = Config(json.load(f))
                return self
            except json.JSONDecodeError:
                logger.error('NickLock: 配置文件解析失败')
                return None

    def save(self) -> bool:
        self.__groups = None
        with open(CONF_FILE, 'w', encoding='utf-8') as f:
            try:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
                return True
            except Exception as e:
                logger.error(f'NickLock: 配置文件保存失败: {e}')
                return False

    def get(self, group: str, default=None) -> Dict[str, str]:
        if default is None:
            default = {}
        result = self.config.get(group)
        if result is None:
            self.config[group] = default
            result = self.config[group]
        return result        

    @property
    def groups(self) -> List[str]:
        if self.__groups is None:
            self.__groups = list(self.config.keys())
        return self.__groups

    def __del__(self):
        if self.config:
            self.save()


config = Config.load()
