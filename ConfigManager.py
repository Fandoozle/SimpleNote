import json

class ConfigManager:
    def __init__(self, config_file="config.json"):
        """
        Initialize ConfigManager with a default or specified config file.

        :param config_file: Path to the configuration file (default: "config.json")
        """
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """
        Load configuration from the JSON file or return default values if the file doesn't exist or is corrupted.

        :return: A dictionary containing configuration parameters
        """
        try:
            with open(self.config_file, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Warning: Config file '{self.config_file}' not found or corrupted. Using default settings.")
            return {
                "autosave_delay": 60000,  # 1 minute in milliseconds
                "window_width": 800,
                "window_height": 600,
                "window_x": 100,
                "window_y": 100
            }

    def get(self, key, default=None):
        """
        Retrieve a configuration value.

        :param key: The key for the configuration setting to retrieve
        :param default: The default value to return if the key isn't found
        :return: The value of the key or the default value if key does not exist
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """
        Set a configuration value and save it to the JSON file.

        :param key: The key for the configuration setting
        :param value: The value to set for the key
        """
        self.config[key] = value
        self.save_config()

    def save_config(self):
        """
        Save the current configuration to the JSON file.
        """
        try:
            with open(self.config_file, 'w') as file:
                json.dump(self.config, file, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def __getitem__(self, key):
        """
        Allows accessing config values like a dictionary.

        :param key: The key for the configuration setting to retrieve
        :return: The value of the key
        """
        return self.config[key]

    def __setitem__(self, key, value):
        """
        Allows setting config values like a dictionary.

        :param key: The key for the configuration setting
        :param value: The value to set for the key
        """
        self.set(key, value)