import configparser

_CONFIG_PATH = 'config/conf.ini'


class Config:
    @staticmethod
    def get_option(option):
        config = configparser.ConfigParser()
        config.read(_CONFIG_PATH)
        return config['DEFAULT'][option]
