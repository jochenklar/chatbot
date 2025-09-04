from types import SimpleNamespace

import yaml


class Settings(SimpleNamespace):

    @classmethod
    def init_settings(cls):
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        return cls((key.upper(), values) for key, values in config.items())


settings = Settings.init_settings()
