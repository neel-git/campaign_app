import os
import yaml
from typing import Any, Dict
from pathlib import Path


class ConfigurationLoader:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.environment = os.getenv("DJANGO_ENV", "development")
        self._config = None

    def _load_yaml(self, filepath: str) -> Dict[str, Any]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        with open(filepath, "r") as file:
            config = yaml.safe_load(file)
            return self._process_environment_variables(config)

    def _process_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(config, dict):
            return {
                key: self._process_environment_variables(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [self._process_environment_variables(item) for item in config]
        elif (
            isinstance(config, str) and config.startswith("${") and config.endswith("}")
        ):
            env_var = config[2:-1]
            return os.getenv(env_var, "")
        return config

    def load_config(self) -> Dict[str, Any]:
        if self._config is None:
            # Load base configuration
            base_config = self._load_yaml(
                os.path.join(self.base_dir, "config", "base.yml")
            )

            env_config = self._load_yaml(
                os.path.join(
                    self.base_dir, "config", "environments", f"{self.environment}.yml"
                )
            )

            self._config = self._deep_merge(base_config, env_config)

        return self._config

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = base.copy()

        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value

        return merged

    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self.load_config()
            for part in key.split("."):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
