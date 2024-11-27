import json
from typing import Dict
import tkinter as tk
import logging

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

class ThemeManager:
    def __init__(self, theme_file: str = "themes.json"):
        """
        Initialize the ThemeManager with a path to the theme file.

        :param theme_file: Path to the themes JSON file (default: "themes.json")
        """
        self.theme_file = theme_file
        self.themes = self.load_themes()
        self.current_theme = "dark"  # Default theme is now dark
        self.default_theme_used = False  # Flag to indicate if default theme was used

    def load_themes(self) -> Dict[str, Dict[str, str]]:
        """
        Load themes from a JSON file.

        If the file is not found or contains invalid JSON, it returns a default dark theme.

        :return: Dictionary of themes where keys are theme names and values are dictionaries of color settings.
        """
        try:
            with open(self.theme_file, 'r') as file:
                themes = json.load(file)
                
                # Check if 'dark' theme exists in the loaded themes
                if "dark" not in themes:
                    logging.warning(f"'dark' theme not found in {self.theme_file}. Using default dark theme.")
                    self.default_theme_used = True
                    themes["dark"] = {
                        "background": "#1E1E1E",
                        "text": "#FFFFFF",
                        "highContrastForeground": "#FFFFFF"
                    }
                return themes
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Themes file not found or corrupted: {e}. Using default dark theme.")
            self.default_theme_used = True
            return {
                "dark": {
                    "background": "#1E1E1E",
                    "text": "#FFFFFF",
                    "highContrastForeground": "#FFFFFF"
                }
            }

    def get_themes(self) -> Dict[str, Dict[str, str]]:
        return self.themes

    def add_theme(self, theme_name: str, theme_data: Dict[str, str]):
        """
        Add a new theme or update an existing one with validation.

        :param theme_name: Name of the theme to add or update
        :param theme_data: Dictionary with theme color settings
        """
        required_keys = ["background", "text"]  # Example keys
        if all(key in theme_data for key in required_keys):
            self.themes[theme_name] = theme_data
            self.save_themes()
            self.default_theme_used = False  # Reset flag when a theme is added
        else:
            logging.error(f"Attempt to add an invalid theme '{theme_name}'. Missing required keys.")

    def apply_theme(self, theme_name: str) -> Dict[str, Dict[str, str]]:
        if theme_name in self.themes:
            self.current_theme = theme_name
            return self.themes[theme_name]
        logging.warning(f"Requested theme '{theme_name}' not found. Using default dark theme.")
        return self.themes.get("dark", {})  # Fallback to dark theme if theme not found

    def remove_theme(self, theme_name: str):
        """
        Remove a theme by its name.

        :param theme_name: Name of the theme to remove
        """
        if theme_name in self.themes:
            del self.themes[theme_name]
        self.save_themes()

    def save_themes(self):
        """
        Save the current themes to the JSON file.
        """
        try:
            with open(self.theme_file, 'w') as file:
                json.dump(self.themes, file, indent=4)
        except IOError as e:
            logging.error(f"Error saving themes: {e}")

    def get_current_theme(self) -> Dict[str, Dict[str, str]]:
        """
        Get the currently applied theme.

        :return: The currently active theme dictionary.
        """
        return self.themes.get(self.current_theme, self.themes.get("dark", {}))  # Fallback to dark theme if current_theme is not found

    def was_default_theme_used(self) -> bool:
        """
        Check if the default theme was used due to file issues.

        :return: True if default theme was used, False otherwise.
        """
        return self.default_theme_used