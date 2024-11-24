from typing import Dict, Union
import json
import os

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the ConfigManager with a path to the config file.

        :param config_file: Path to the configuration file (default: "config.json")
        """
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Union[int, str]]:
        """
        Load configuration settings from a JSON file.

        If the file does not exist or contains invalid JSON, it returns default settings.

        :return: A dictionary with configuration settings
        """
        try:
            with open(self.config_file, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Log the error for debugging
            print(f"Error loading config: {e}")
            # Return default configuration if file is missing or corrupted
            return {
                "autosave_delay": 60000,  # 1 minute in milliseconds
                "window_width": 800,
                "window_height": 600,
                "window_x": 100,
                "window_y": 100
            }

    def save_config(self, new_config: Dict[str, Union[int, str]]):
        """
        Save the configuration to the JSON file.

        :param new_config: Dictionary of configuration settings to save
        """
        try:
            with open(self.config_file, 'w') as file:
                json.dump(new_config, file, indent=4)
            self.config = new_config  # Update in-memory config
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Union[int, str] = None) -> Union[int, str, None]:
        """
        Retrieve a value from the configuration.

        :param key: The key to look up in the config dictionary
        :param default: The default value to return if the key does not exist
        :return: The value associated with the key or the default value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Union[int, str]):
        """
        Set a value in the configuration and save it to file.

        :param key: The key for the new or updated configuration setting
        :param value: The value to set for the given key
        """
        self.config[key] = value
        self.save_config(self.config)