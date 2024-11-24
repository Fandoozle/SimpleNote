import json
from typing import Dict
import tkinter as tk  # Add this import

class ThemeManager:
    def __init__(self, theme_file: str = "themes.json"):
        """
        Initialize the ThemeManager with a path to the theme file.

        :param theme_file: Path to the themes JSON file (default: "themes.json")
        """
        self.theme_file = theme_file
        self.themes = self.load_themes()

    def load_themes(self) -> Dict[str, Dict[str, str]]:
        """
        Load themes from a JSON file.

        If the file is not found or contains invalid JSON, it returns a default light theme.

        :return: Dictionary of themes where keys are theme names and values are dictionaries of color settings.
        """
        try:
            with open(self.theme_file, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Themes file not found or corrupted. Using default light theme.")
            return {
                "light": {
                    "background": "#FFFFFF",
                    "text": "#000000",
                    "word_count_background": "#FFFFFF",
                    "word_count_foreground": "#000000",
                    "line_numbers": "#CCCCCC",
                    "selected_text_background": "#ADD6FF",
                    "statusbar_background": "#F0F0F0",
                    "statusbar_foreground": "#000000",
                    "cursor": "#000000",
                    "comments": "#808080",
                    "strings": "#A31515",
                    "keywords": "#0000FF",
                    "functions": "#795E26",
                    "variables": "#001080",
                    "numbers": "#098658",
                    "scrollbar_background": "#D3D3D3",
                    "scrollbar_trough": "#F0F0F0",
                    "scrollbar_border": "#A9A9A9",
                    "scrollbar_arrow": "#000000",
                    "menu_background": "#F0F0F0",
                    "menu_foreground": "#000000",
                    "menu_active_background": "#E0E0E0",
                    "menu_active_foreground": "#000000",
                    "menu_disabled_foreground": "#A3A3A3",
                    "highContrastBackground": "#000000",
                    "highContrastForeground": "#FFFFFF"
                }
            }

    def get_theme(self, theme_name: str) -> Dict[str, str]:
        """
        Retrieve a specific theme by name.

        :param theme_name: Name of the theme to retrieve
        :return: Dictionary containing the theme settings
        """
        return self.themes.get(theme_name, self.themes["light"])

    def add_theme(self, theme_name: str, theme_data: Dict[str, str]):
        """
        Add a new theme or update an existing one.

        :param theme_name: Name of the theme to add or update
        :param theme_data: Dictionary with theme color settings
        """
        self.themes[theme_name] = theme_data
        self.save_themes()

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
            print(f"Error saving themes: {e}")

    def apply_theme(self, theme: Dict[str, str], widget):
            """
            Apply theme colors to a widget.

            :param theme: Dictionary containing color settings for the theme
            :param widget: The Tkinter widget to apply the theme to
            """
            if hasattr(widget, 'config'):
                widget.config(bg=theme.get("background", "#FFFFFF"))
                
                # Only apply foreground color if the widget supports it
                if widget.winfo_class() in ["Label", "Button", "Entry", "Text", "Menu"]:
                    widget.config(fg=theme.get("text", "#000000"))
            
            # For specific widgets like Text or Menu, apply additional properties
            if isinstance(widget, (tk.Text, tk.Menu)):
                cursor = theme.get("cursor", "xterm")
                if cursor.startswith("#"):  # If it's a color code, use a default cursor instead
                    cursor = "xterm"  # or another valid cursor type like 'arrow' or 'ibeam'
                widget.config(cursor=cursor)
    