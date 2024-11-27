"""
Modules:
ConfigManger.py
FileHandler.py
KeybindingsManager.py
ThemeManager.py
    themes.json
"""

import os
import time
import json
import sys
import tkinter as tk
import tkinterdnd2 as tkdnd
import logging

from typing import Dict, Optional, Union, Callable, Any, Literal, List

from tkinter import Menu, Text, messagebox, filedialog, simpledialog, Toplevel, Label, Entry, Button, font as tkFont
from tkinter import ttk

from tkcalendar import Calendar
from ConfigManager import ConfigManager
from KeybindingsManager import bind_keyboard_shortcuts
from CalendarManager import open_calendar, close_calendar
from StatusBar import StatusBar

def load_config(config_file: str = "config.json") -> Dict[str, Union[int, str]]:
    """
    Load configuration settings from a JSON file.

    If the file does not exist or contains invalid JSON, it returns default settings.

    :param config_file: Path to the configuration file (default: "config.json")
    :return: A dictionary with configuration settings
    """
    try:
        with open(config_file, 'r') as file:
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

class TextEditor:
    def __init__(self, master: tk.Tk):
        """
        Initialize the TextEditor with the main window.

        Sets up the basic configuration, UI elements, event bindings, and status bar scheduler.
        """
        self.master = master
        self.config_manager = ConfigManager()
        self.config: Dict[str, Union[int, str]] = self.config_manager.config
        self.master.title('Simple Note')

        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use 'clam' theme for custom styling

        # Load configuration and themes
        self.themes: Dict[str, Dict[str, str]] = self.load_themes()
        self.current_theme: Dict[str, str] = self.themes.get("dark", self.themes["light"])

        # Load light and dark themes from the themes dictionary
        self.light_theme = self.themes.get("light", {})
        self.dark_theme = self.themes.get("dark", {})

        # If light or dark themes are not defined in themes.json, use fallback themes
        if not self.light_theme:
            self.light_theme = {
                "background": "#FFFFFF",
                "text": "#000000",
                # other light theme properties...
            }
        if not self.dark_theme:
            self.dark_theme = {
                "background": "#333333",
                "text": "#FFFFFF",
                # other dark theme properties...
            }

        self.status_bar = StatusBar(master)
        self.status_bar.update_status_bar(file_path=None, word_count=0)
    
        # Autosave configuration
        self.autosave_delay: int = self.config_manager.get("autosave_delay", 60000)
        print(f"Autosave delay set to {self.autosave_delay}")
        self.master.after(self.autosave_delay, self.check_for_changes)

        # Font settings
        self.font_family: str = "Arial"
        self.font_size: int = 14
        self.font_color: str = self.current_theme.get("text", "#000000")  # Default text color

        # Create main text frame
        self.text_frame = tk.Frame(self.master, 
                                   bg=self.current_theme["background"], 
                                   highlightthickness=0, bd=0)
        self.text_frame.pack(expand=True, fill=tk.BOTH)

        self.create_text_widget()
        self.text.focus_set()  # Focus on the text widget for immediate input

        self.set_theme(self.current_theme)  # Call set_theme after all attributes are initialized

        self.find_replace_open = False  # Flag to check if find/replace dialog is open

        # key bindings
        self.bind_keyboard_shortcuts = lambda: bind_keyboard_shortcuts(self)
        self.bind_keyboard_shortcuts()  # Bind the shortcuts here

        self.create_menu()

        # File management attributes
        self.file_path: Optional[str] = None
        self.last_saved_time: float = time.time()
        self.last_content: str = ""

        # Line number updating
        self.update_line_number_delay: int = 100
        self.update_line_number_scheduled: bool = False

        # Calendar window management
        self.calendar_window = None  # Make sure this is initialized here

        # Enable drag and drop for files
        self.master.drop_target_register(tkdnd.DND_FILES)
        self.master.dnd_bind('<<Drop>>', self.drop)

        # Undo/Redo buffer configuration
        self.max_undo_stack_size = 50  # You can adjust this to limit the number of undo actions
        self.undo_stack = []
        self.redo_stack = []

        self.master.update_idletasks()
        self.set_window_size()

        self.set_theme(self.current_theme)  # Call set_theme after all attributes are initialized


        #logging
        self.setup_logging()

    def setup_logging(self) -> None:
        """Configure logging to write errors to a file."""
        # Set up basic configuration for logging errors
        logging.basicConfig(filename='simple_note.log', level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    

    def open_file_directly(self, file_path: str):
            """
            Open and read the contents of a file into the text widget.

            Also updates file-related attributes after reading the file. Logs errors for debugging.

            :param file_path: Path to the file to open
            """
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.text.delete('1.0', 'end')
                self.text.insert('1.0', content)
                
                self.file_path = file_path
                self.last_content = content
                self.last_saved_time = time.time()
                self.status_bar.update_status_bar(file_path, len(self.text.get('1.0', 'end-1c').split()))
                
            except PermissionError as e:
                messagebox.showerror("Error", "Permission denied. You do not have the rights to read this file.")
                logging.error(f"Permission denied. You do not have the rights to read this file: {e}")
            except FileNotFoundError as e:
                messagebox.showerror("Error", "File not found. Please check the file path.")
                logging.error(f"File not found. Please check the file path: {e}")
            except IOError as e:
                messagebox.showerror("Error", f"An error occurred while reading the file: {e}")
                logging.error(f"An error occurred while reading the file: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                logging.error(f"An unexpected error occurred: {e}")

    def drop(self, event):
        """
        Handle file drag and drop event.

        Checks if the dropped item is a file and opens it if so.
        """
        file_path = event.data.replace('{', '').replace('}', '')
        if os.path.isfile(file_path):
            self.open_file_directly(file_path)
        else:
            messagebox.showerror("Error", "The dropped item is not a file.")

    def _handle_undo_redo(self, stack_to_pop: List[str], stack_to_push: List[str]) -> None:
        """Handle the logic for undo or redo actions."""
        if stack_to_pop:
             # Save current state before applying undo/redo
            current_state = self.text.get("1.0", tk.END)
            stack_to_push.append(current_state)
            new_state = stack_to_pop.pop()
            # Replace current text with the state from the undo/redo stack
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", new_state)
            self.text.edit_modified(False)  # Mark as unmodified

    def custom_undo(self) -> None:
        if self.undo_stack:
            self._handle_undo_redo(self.undo_stack, self.redo_stack)
        else:
            messagebox.showinfo("Undo", "No further undo actions available.")

    def custom_redo(self) -> None:
        if self.redo_stack:
            self._handle_undo_redo(self.redo_stack, self.undo_stack)
        else:
            messagebox.showinfo("Redo", "No further redo actions available.")

    def save_undo_state(self) -> None:
        """Save current text state in the undo stack."""
        current_state = self.text.get("1.0", tk.END)
        if not self.undo_stack or current_state != self.undo_stack[-1]:
            self.undo_stack.append(current_state)
            if len(self.undo_stack) > self.max_undo_stack_size:
                self.undo_stack.pop(0)  # Remove the oldest if buffer exceeds max size
            self.redo_stack.clear()  # Clear redo stack when new action is performed

    def clear_undo_redo(self) -> None:
        """Clear both undo and redo stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        messagebox.showinfo("Undo/Redo", "Undo/Redo history has been cleared.")


    """
    Calendar Functions
    """

    def insert_date_from_calendar(self):
        """
        Open the calendar and insert the selected date into the text editor.
        Ensures `self.calendar_window` is correctly managed.
        """
        if self.calendar_window is None or not self.calendar_window.winfo_exists():
            self.calendar_window = open_calendar(self.master, self.text, self.current_theme)
        else:
            # If calendar is already open, bring it to the front
            self.calendar_window.lift()

        # Bind the select button to insert the date
        if hasattr(self, 'calendar_window') and self.calendar_window.winfo_exists():
            if hasattr(self.calendar_window, 'cal'):
                self.calendar_window.cal.bind("<<CalendarSelected>>", lambda event: self._insert_selected_date())

    def load_themes(self) -> Dict[str, Dict[str, str]]:
        """
        Attempt to load color themes from a JSON configuration file.

        If the file is not found or contains invalid JSON, a default light theme is returned.
        
        :return: Dictionary of themes where keys are theme names and values are dictionaries of color settings.
        """
        theme_file = "themes.json"
        try:
            # Try to open and read the themes file
            with open(theme_file, 'r') as file:
                # Parse JSON content into a dictionary
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file is missing or invalid, inform the user and use default theme
            messagebox.showerror("Error", "Themes file not found or corrupted. Using light theme.")
            
            # Return a default light theme
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
                    "menu_disabled_foreground": "#A3A37A7A7AA3",
                    "highContrastBackground": "#000000",
                    "highContrastForeground": "#FFFFFF"
                }
            }

    def set_system_theme(self):
            """
            Set the theme based on the operating system.

            This method applies:
            - Light theme for Windows ('nt' OS),
            - Dark theme for other operating systems.

            Note: This assumes that `self.light_theme` and `self.dark_theme` are already defined in __init__.
            """
            # Check if the current OS is Windows
            if os.name == 'nt':  # 'nt' is the string returned by os.name for Windows
                self.set_theme(self.light_theme)  # Apply light theme for Windows
            else:
                self.set_theme(self.dark_theme)  # Apply dark theme for other systems (e.g., macOS, Linux)

    def set_window_size(self) -> None:
        """
        Configure the initial size and position of the main window to center it on the screen,
        ensuring space for the scrollbar with a minimum size.
        """
        # Get screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Get window dimensions from config or use defaults
        width = self.config_manager.get("window_width", 800)
        height = self.config_manager.get("window_height", 600)

        # Calculate center position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Set the geometry with minimum size to ensure scrollbar visibility
        self.master.minsize(width + 20, height)  # Add 20 pixels for scrollbar
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def toggle_line_numbers(self) -> None:
        """
        Toggle the visibility of line numbers in the text editor.

        If line numbers are currently visible, they are hidden. If hidden, they are displayed.
        """
        if self.line_number_bar.winfo_ismapped():  # Check if it's mapped to the screen
            # If visible, remove it from the layout
            self.line_number_bar.pack_forget()
        else:
            # If not visible, add it to the left side of the text widget
            self.line_number_bar.pack(side=tk.LEFT, fill=tk.Y, before=self.text)
            self.update_line_numbers()  # Call this to update line numbers when shown

    def create_text_widget(self) -> None:
        """
        Create and configure the main text widget and associated elements like the line number bar.

        This method sets up:
        - The font for text display
        - Line number bar
        - Main text area with scroll capabilities
        - Text styling tags
        - Event bindings for scrolling, updating line numbers, and auto-indentation
        - Adds padding to the text widget to prevent text from touching the edges
        """
        # Define the font to be used in the text widgets
        font = tkFont.Font(family=self.font_family, size=self.font_size)

        # Set up the line number bar, but hide it by default
        self.line_number_bar = Text(self.text_frame, 
                                    width=7, padx=4, 
                                    takefocus=0, border=0,
                                    background=self.current_theme["background"],
                                    state='disabled', wrap='none', 
                                    highlightthickness=0, font=font)
        # Hide the line number bar initially
        self.line_number_bar.pack_forget()  # Changed from pack() to pack_forget()

        # Create the main text widget for editing
        self.text = Text(self.text_frame, 
                        background=self.current_theme["background"], 
                        font=font, fg=self.font_color, 
                        undo=True, wrap='none', 
                        highlightthickness=0, bd=0,
                        padx=10, pady=10)  # Add padding here
        self.text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Bind mouse wheel events for scrolling on both text and line number widgets
        self.text.bind('<MouseWheel>', self.on_scroll)
        self.line_number_bar.bind('<MouseWheel>', self.on_scroll)

        # Configure text styling tags
        # Bold
        bold_font = font.copy()
        bold_font.configure(weight="bold", size=self.font_size)
        self.text.tag_configure("bold", font=bold_font)
        
        # Italic
        italic_font = font.copy()
        italic_font.configure(slant="italic", size=self.font_size)
        self.text.tag_configure("italic", font=italic_font)
        
        # Underline
        underline_font = font.copy()
        underline_font.configure(underline=True, size=self.font_size)
        self.text.tag_configure("underline", font=underline_font)

        # Normal (default) font configuration
        self.text.tag_configure("normal", font=font)

        # Bind events for updating line numbers
        # This will trigger on any key press or text modification
        self.text.bind('<Any-KeyPress>', self.delayed_update_line_numbers)
        self.text.bind('<<Modify>>', self.delayed_update_line_numbers)

        # Bind key events for auto-indentation
        self.text.bind('<Return>', self.on_enter_pressed)
        #self.text.bind('<Tab>', self.on_tab_pressed)
        self.text.bind('<BackSpace>', self.on_backspace)

        # Configure indentation tag for visual representation of code indentation
        self.text.tag_config('indent', tabs=('0.5c',))

        self.style.configure("Vertical.TScrollbar", 
                            background=self.current_theme.get("scrollbar_background", "#D3D3D3"),
                            troughcolor=self.current_theme.get("scrollbar_trough", "#FFFFFF"),
                            bordercolor=self.current_theme.get("scrollbar_border", "#A9A9A9"),
                            arrowcolor=self.current_theme.get("scrollbar_arrow", "#000000"))

        # Create the scrollbar with the custom style
        self.scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", style="Vertical.TScrollbar", command=self.text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=True)
        self.text.config(yscrollcommand=self.scrollbar.set)

    def on_enter_pressed(self, event: tk.Event) -> Literal['break']:
        """
        Handle the Enter key press event for auto-indentation.

        This method calculates the indentation level of the current line 
        and inserts a new line with the same level of indentation.

        :param event: The Tkinter event object for the key press.
        :return: 'break' to prevent further event processing.
        """
        self.save_undo_state()
        # Get the content of the current line
        current_line: str = self.text.get('insert linestart', 'insert lineend')
        # Calculate the number of spaces from the start of the line
        indent_level: int = len(current_line) - len(current_line.lstrip())

        # Insert a new line with the calculated indentation
        self.text.insert('insert', '\n' + ' ' * indent_level)
        return 'break'  # Prevent further event propagation
    """
    def on_tab_pressed(self, event: tk.Event) -> Literal['break']:
        if event.keysym == 'i' and event.state & 0x4:
            return None  # Do nothing if it's Control + I
        self.save_undo_state()
        self.text.insert('insert', '    ')  # Insert four spaces for a tab
        return 'break'
    """

    def on_backspace(self, event: tk.Event) -> Optional[Literal['break']]:
        """
        Handle the Backspace key press event for de-indentation.

        This method removes indentation when the cursor is at the start of a line.
        It handles both space-based indentation (4 spaces) and tab-based indentation.

        :param event: The Tkinter event object for the key press.
        :return: 'break' to prevent further event processing if indentation was removed, None otherwise.
        """
        self.save_undo_state()

        # Get cursor position
        cursor_pos = self.text.index('insert')
        
        # Get the start and end indices of the current line
        line_start = self.text.index('insert linestart')
        line_end = self.text.index('insert lineend')
        
        # Retrieve the current line's text
        line_text = self.text.get(line_start, line_end)

        # If the cursor is at the start of the line
        if cursor_pos == line_start:
            # Check for space-based indentation
            if line_text.startswith('    '):
                # Remove 4 spaces
                self.text.delete(cursor_pos, cursor_pos + '4c')
            # Check for tab-based indentation
            elif line_text.startswith('\t'):
                # Remove one tab
                self.text.delete(cursor_pos, cursor_pos + '1c')
            return 'break'  # Prevent further event propagation
        
        # If cursor not at line start, let default backspace behavior occur
        return None
        
    def on_scroll(self, *args: Any) -> None:
        """
        Synchronize the scrolling between the main text widget and the line number bar.

        This function handles both mouse wheel scrolling and programmatic scrolling events.

        :param args: The event arguments, which can either be a Tkinter event or scroll command args.
        """
        # Check if the scroll event is from a mouse wheel
        if isinstance(args[0], tk.Event):
            # Calculate scroll units based on mouse wheel delta
            scroll_units = int(-1 * (args[0].delta / 120))  # -1 for reverse scrolling on Windows
            # Scroll the text widget
            self.text.yview('scroll', scroll_units, 'units')
        else:
            # If not a mouse event, use the passed scroll command
            self.text.yview(*args)  # type: ignore[arg-type]

        # Synchronize the line number bar with the text widget's scroll position
        self.line_number_bar.yview_moveto(self.text.yview()[0])

    def delayed_update_line_numbers(self, event=None) -> None:
        """
        Schedule an update for line numbers with a delay to prevent excessive updates.

        This method ensures that line numbers are only updated after a brief period of inactivity,
        reducing CPU usage during active typing.

        :param event: Optional event object, typically from a key press or text modification.
        """
        # Only schedule an update if one isn't already scheduled
        if not self.update_line_number_scheduled:
            self.update_line_number_scheduled = True
            # Use `self.master.after` to delay the update
            self.master.after(self.update_line_number_delay, self.update_line_numbers)

    def update_line_numbers(self):
        """
        Refresh the line numbers in the line number bar to reflect changes in the text area.

        This method:
        - Clears the existing line numbers,
        - Counts the new number of lines,
        - Inserts fresh line numbers,
        - Updates the indentation visualization,
        - Resynchronizes the scroll position of the line number bar with the text area.
        """
        # Enable editing on the line number bar
        self.line_number_bar.config(state='normal')
        
        # Clear all existing line numbers
        self.line_number_bar.delete('1.0', tk.END)
        
        # Get the entire content of the text widget, stripping any trailing newlines
        content = self.text.get("1.0", tk.END).strip()
        
        # Count lines, ensuring at least one line even if the content is empty
        line_count = content.count('\n') + 1 if content else 1
        
        # Insert new line numbers
        for i in range(1, line_count + 1):
            self.line_number_bar.insert(tk.END, f"{i}\n")
        
        # Disable editing on the line number bar to prevent user input
        self.line_number_bar.config(state='disabled')
        
        # Reset the scheduling flag
        self.update_line_number_scheduled = False
        
        # Synchronize the scroll position
        self.line_number_bar.yview_moveto(self.text.yview()[0])

        # Update indentation visualization
        self.update_indentation()

    def create_menu(self):
        """
        Create and configure the main menu bar with various submenus for file, edit, format, and view operations.

        This method sets up:
        - File operations (Open, Save, Close)
        - Edit operations (Undo, Redo, Find and Replace)
        - Text formatting (Font Size, Font, Color, Bold, Italic, Underline)
        - Customization options
        - View toggles and additional utilities like the calendar
        """
        # Initialize the main menu bar
        menu_bar = Menu(self.master)

        # File menu
        file_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        # Note: Changed 'fg' to 'foreground' for consistency with Tkinter's API
        file_menu.add_command(label='Open', command=self.open_file)
        file_menu.add_command(label='Save', command=lambda: self.save_and_update_status())
        file_menu.add_command(label='Close', command=self.close_file)
        # Customize menu
        file_menu.add_command(label="Customize Theme", command=self.open_customize_dialog)
        file_menu.add_command(label="About", command=self.open_about_dialog)
        menu_bar.add_cascade(label='File', menu=file_menu)

        # Edit menu
        edit_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        edit_menu.add_command(label="Undo | Ctrl+Z", command=self.custom_undo)
        edit_menu.add_command(label="Redo | Ctrl+Y", command=self.custom_redo)
        edit_menu.add_command(label="Find and Replace", command=self.open_find_replace_dialog)
        edit_menu.add_command(label="Clear Undo/Redo", command=self.clear_undo_redo)  # Add this
        menu_bar.add_cascade(label='Edit', menu=edit_menu)

        # Format menu
        format_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        format_menu.add_command(label='Font Size', command=self.change_font_size)
        format_menu.add_command(label='Change Font', command=self.change_font)
        format_menu.add_command(label='Font Color', command=self.change_font_color)
        format_menu.add_command(label='Bold | Ctrl+b', command=self.toggle_bold)  # Corrected keyboard shortcut in label
        format_menu.add_command(label='Italic | Ctrl+i', command=self.toggle_italic)  # Corrected keyboard shortcut in label
        format_menu.add_command(label='Underline | Ctrl+u', command=self.toggle_underline)  # Corrected keyboard shortcut in label
        menu_bar.add_cascade(label='Format', menu=format_menu)

        # View menu - Line Numbers
        view_menu_line_numbers = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        view_menu_line_numbers.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers)
        menu_bar.add_cascade(label='View', menu=view_menu_line_numbers)

        # Calendar menu
        calendar_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        calendar_menu.add_command(label="Open Calendar", command=lambda: open_calendar(self.master, self.text, self.current_theme))
        #calendar_menu.add_command(label="Select Date", command=self.open_calendar)  # New button to just open the calendar
        menu_bar.add_cascade(label='Calendar', menu=calendar_menu)

        # Bind the close window event to the close_file method
        self.master.protocol("WM_DELETE_WINDOW", self.close_file)
        
        # Set the menu bar to the main window
        self.master.config(menu=menu_bar)

    def open_customize_dialog(self):
        """
        Open a dialog window for selecting and applying different themes.

        This method creates:
        - A top-level window for theme selection,
        - Buttons for each available theme,
        - A close button to dismiss the dialog.
        """
        # Create a new top-level window for theme selection
        dialog = Toplevel(self.master)
        dialog.title("Select Theme")
        
        main_window_x = self.master.winfo_x()
        main_window_y = self.master.winfo_y()
        main_window_width = self.master.winfo_width()
        main_window_height = self.master.winfo_height()

        dialog_width = 300  # Width of the dialog, adjust as necessary
        dialog_height = 100  # Height of the dialog, adjust as necessary

        # Center dialog relative to main window
        center_x = main_window_x + (main_window_width // 2) - (dialog_width // 2)
        center_y = main_window_y + (main_window_height // 2) - (dialog_height // 2)

        dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")

        # Apply the current theme background color to the window
        dialog.configure(bg=self.current_theme["background"])

        # Loop through all available themes
        for theme_name, theme in self.themes.items():
            # Create a button for each theme, with the theme name as its label
            # The button's command will set the theme when clicked
            button = Button(dialog, 
                            text=theme_name.capitalize(), 
                            command=lambda t=theme: self.set_theme(t))
            button.pack(pady=5)  # Add padding between buttons for visual separation

    def open_about_dialog(self):
        """
        Open a dialog window for program information.
        """
        # Create a new top-level window for theme selection
        dialog = Toplevel(self.master)
        dialog.title("About Simple Note")
        
        main_window_x = self.master.winfo_x()
        main_window_y = self.master.winfo_y()
        main_window_width = self.master.winfo_width()
        main_window_height = self.master.winfo_height()

        dialog_width = 300  # Width of the dialog, adjust as necessary
        dialog_height = 200  # Height of the dialog, adjust as necessary

        # Center dialog relative to main window
        center_x = main_window_x + (main_window_width // 2) - (dialog_width // 2)
        center_y = main_window_y + (main_window_height // 2) - (dialog_height // 2)

        dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")

        # Apply the current theme background color to the window
        dialog.configure(bg=self.current_theme["background"])

        # Create and configure the label with program information
        about_text = f"""
        **Simple Note**
        Version: 1.0
        Python Version: {sys.version.split()[0]}
        
        This is a simple text editor with features for:
        - Text editing and formatting
        - File operations (Open, Save)
        - Custom themes
        - Drag and Drop file support
        - Calendar integration
        """
        
        about_label = Label(dialog, text=about_text, 
                            justify=tk.LEFT, bg=self.current_theme["background"], 
                            fg=self.current_theme["text"], wraplength=280)
        about_label.pack(pady=5, padx=10)

    def apply_theme(self, theme: Dict[str, str]) -> None:
            """
            Apply a theme to the entire application, affecting the color scheme of all UI components.
            """
            # Store the new theme for future reference
            self.current_theme = theme

            # Apply theme to main window components
            self.master.configure(bg=theme["background"])  # Main window
            self.text_frame.configure(bg=theme["background"])  # Text editor frame

            # Update text widgets
            self.text.configure(bg=theme["background"], fg=theme["text"])
            self.line_number_bar.configure(bg=theme["background"], fg=theme.get("line_numbers", theme["text"]))
            self.status_bar.configure(bg=theme["background"], fg=theme.get("status_text", theme["text"]))

            # Update scrollbar style
            self.style.configure("Vertical.TScrollbar", 
                                background=theme.get("scrollbar_background", "#D3D3D3"),
                                troughcolor=theme.get("scrollbar_trough", "#FFFFFF"),
                                bordercolor=theme.get("scrollbar_border", "#A9A9A9"),
                                arrowcolor=theme.get("scrollbar_arrow", "#000000"))

            # Update menu bar colors
            menu_bar = self.master.cget('menu')  # This should return the Menu object
            if isinstance(menu_bar, Menu):  # Check if it's actually a Menu object
                menu_bar.configure(
                    background=theme.get("menu_background", theme["background"]),
                    foreground=theme.get("menu_foreground", theme["text"]),
                    activebackground=theme.get("menu_active_background", theme["background"]),
                    activeforeground=theme.get("menu_active_foreground", theme["text"]),
                    disabledforeground=theme.get("menu_disabled_foreground", "#A3A3A3")
                )
                for menu in menu_bar.winfo_children():
                    if isinstance(menu, Menu):
                        menu.configure(
                            background=theme.get("menu_background", theme["background"]),
                            foreground=theme.get("menu_foreground", theme["text"]),
                            activebackground=theme.get("menu_active_background", theme["background"]),
                            activeforeground=theme.get("menu_active_foreground", theme["text"]),
                            disabledforeground=theme.get("menu_disabled_foreground", "#A3A3A3")
                        )
            else:
                print("Menu bar not found or not a Menu object")

            # Update calendar window if it's currently open
            if hasattr(self, 'calendar_window') and self.calendar_window:
                if self.calendar_window.winfo_exists():
                    self.calendar_window.configure(bg=theme["background"])
                    if hasattr(self, 'cal'):
                        self.cal.config(background=theme["background"], foreground=theme["text"])

            # Update dialogs and windows if open
            if hasattr(self, 'find_replace_open') and self.find_replace_open:
                for child in self.master.winfo_children():
                    if isinstance(child, Toplevel) and child.title() == "Find and Replace":
                        self._update_dialog_theme(child, theme)
                        break

            # Set the font color based on the theme
            self.font_color = theme.get("text", self.font_color)
            self.text.configure(fg=self.font_color)

            # Refresh text styling tags to reflect the new theme
            self.update_font()

            # Configure indentation visualization
            self.text.tag_configure('indent', tabs=('0.5c',), background=theme.get('indent_guide', theme['background']))
            self.text.tag_configure('dedent', background=theme.get('indent_guide', theme['background']))

    def set_theme(self, theme: Dict[str, str]) -> None:
        """
        Apply a new theme to the application. This method is identical to apply_theme 
        for consistency in terminology but can be used for dynamic theme changes.
        """
        self.apply_theme(theme)

    def _update_dialog_theme(self, dialog: Toplevel, theme: Dict[str, str]) -> None:
        """
        Recursively update the theme of a dialog and all its children widgets.

        :param dialog: The top-level dialog window to update.
        :param theme: The theme dictionary to apply.
        """
        dialog.configure(bg=theme["background"])
        for widget in dialog.winfo_children():
            if isinstance(widget, (Label, Entry, Button)):
                widget.configure(bg=theme["background"], fg=theme["text"])
            elif isinstance(widget, Text):
                widget.configure(bg=theme["background"], fg=theme["text"])

    def set_system_theme(self):
        """
        Set the theme based on the operating system.

        This method applies:
        - Light theme for Windows ('nt' OS),
        - Dark theme for other operating systems.

        Note: This assumes that `self.light_theme` and `self.dark_theme` are already defined.
        """
        # Check if the current OS is Windows
        if os.name == 'nt':  # 'nt' is the string returned by os.name for Windows
            self.set_theme(self.light_theme)  # Apply light theme for Windows
        else:
            self.set_theme(self.dark_theme)  # Apply dark theme for other systems (e.g., macOS, Linux)

    def open_find_replace_dialog(self) -> None:
        """
        Open a modal dialog for finding and replacing text within the editor.

        This method:
        - Checks if the dialog is already open to avoid multiple instances,
        - Creates a new top-level window for find/replace operations,
        - Centers the dialog on the screen,
        - Applies the current theme,
        - Sets up UI elements for finding and replacing text,
        - Binds window close events and keyboard shortcuts.
        """
        # Prevent opening multiple find/replace windows
        if getattr(self, 'find_replace_open', False):
            return

        # Flag to indicate that find/replace dialog is open
        self.find_replace_open = True

        # Create the find/replace dialog window
        find_replace_window = Toplevel(self.master)
        find_replace_window.title("Find and Replace")
        # Set the background color according to the current theme
        find_replace_window.configure(bg=self.current_theme["background"])

        # Calculate dialog position to center it on screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        dialog_width, dialog_height = 400, 200
        x = (screen_width // 2) - (dialog_width // 2)
        y = (screen_height // 2) - (dialog_height // 2)
        find_replace_window.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Make this dialog modal
        find_replace_window.grab_set()
        # Focus on this window to ensure user interaction starts here
        find_replace_window.focus_force()

        # Find text label and entry
        find_label = Label(find_replace_window, text="Find:", bg=self.current_theme["background"], fg=self.current_theme["text"])
        find_label.pack(pady=5)
        find_entry = Entry(find_replace_window)
        find_entry.pack(pady=5)
        find_entry.focus_set()  # Set focus here for immediate typing

        # Replace with label and entry
        replace_label = Label(find_replace_window, text="Replace with:", bg=self.current_theme["background"], fg=self.current_theme["text"])
        replace_label.pack(pady=5)
        replace_entry = Entry(find_replace_window)
        replace_entry.pack(pady=5)

        # Replace button
        replace_button = Button(find_replace_window, 
                                text="Replace", 
                                command=lambda: self.replace_text(find_entry.get(), replace_entry.get()),
                                bg=self.current_theme["button_background"], 
                                fg=self.current_theme["button_foreground"])
        replace_button.pack(pady=5)

        # Close button
        close_button = Button(find_replace_window, 
                            text="Close", 
                            command=lambda: self.close_find_replace_dialog(find_replace_window),
                            bg=self.current_theme["button_background"], 
                            fg=self.current_theme["button_foreground"])
        close_button.pack(pady=5)

        # Bind ESC key to close the dialog
        find_replace_window.bind("<Escape>", lambda event: self.close_find_replace_dialog(find_replace_window))
        # Bind the window close event (X button) to our close method
        find_replace_window.protocol("WM_DELETE_WINDOW", lambda: self.close_find_replace_dialog(find_replace_window))

    def close_find_replace_dialog(self, dialog):
        """
        Close the find/replace dialog window.

        This method:
        - Destroys the dialog window,
        - Updates the open state flag to indicate the dialog is closed.
        """
        dialog.destroy()  # Remove the dialog from the screen
        self.find_replace_open = False  # Mark the dialog as closed

    def replace_text(self, search_text: str, replace_text: str) -> None:
        """
        Replace all occurrences of `search_text` with `replace_text` in the text widget.

        This method:
        - Searches for the `search_text` from the beginning of the text.
        - Replaces each occurrence with `replace_text`.
        - Continues until no more matches are found.

        :param search_text: The text to find in the editor.
        :param replace_text: The text to replace with.
        """
        self.save_undo_state()

        if not search_text:
            messagebox.showinfo("Info", "Please enter a search term.")
            return

        start_pos = '1.0'  # Starting position for search
        while True:
            # Search for the text from the current position to the end
            start_pos = self.text.search(search_text, start_pos, stopindex=tk.END)
            if not start_pos:  # If no match was found, break out of the loop
                break
            
            # Calculate the end position of the found text
            end_pos = f"{start_pos}+{len(search_text)}c"
            
            # Delete the found text
            self.text.delete(start_pos, end_pos)
            # Insert the replacement text at the same position
            self.text.insert(start_pos, replace_text)
            
            # Update the start position for the next search to continue from where we left off
            start_pos = f"{start_pos}+{len(replace_text)}c"

    def toggle_bold(self):
        """
        Toggle the bold text style for the selected or current insertion point.
        """
        self.toggle_style("bold")

    def toggle_italic(self):
        """
        Toggle the italic text style for the selected or current insertion point.
        """
        print("toggle_italic called")
        self.toggle_style("italic")
        return "break"  # Prevent further event propagation

    def toggle_underline(self):
        """
        Toggle the underline text style for the selected or current insertion point.
        """
        self.toggle_style("underline")

    def refocus_text(self) -> None:
        """Ensure focus is on the text widget after configuration changes."""
        self.text.focus_set()
        # Call this when necessary, e.g., after theme change or window resize
        self.master.bind("<Configure>", lambda e: self.refocus_text())

    def toggle_style(self, style: str):
        """
        Toggle a text style (like bold, italic, or underline) or combination for the selected or current text.

        :param style: The style to toggle ("bold", "italic", or "underline").
        """
        print(f"toggle_style called with {style}")  # Debug print
        self.save_undo_state()
        
        try:
            start, end = self.text.index(tk.SEL_FIRST), self.text.index(tk.SEL_LAST)
        except tk.TclError:
            # If there's no selection, just use the insertion point
            insert = self.text.index(tk.INSERT)
            start = end = insert

        current_tags = self.text.tag_names(start)
        print(f"Current tags at start: {self.text.tag_names(start)}")  # Debug print before toggling
        if style in current_tags:
            self.text.tag_remove(style, start, end)
            print(f"Tag {style} removed at range: {start} to {end}")  # Debug print
        else:
            self.text.tag_add(style, start, end)
            print(f"Tag {style} added at range: {start} to {end}")  # Debug print
        print(f"Current tags after operation: {self.text.tag_names(start)}")  # Debug print after toggling

        # Update the font for the range to ensure correct rendering of combined styles
        self.update_font_for_range(start, end)
        self.text.update_idletasks()  # Force an update of the widget

    def update_font_for_range(self, start: str, end: str) -> None:
        """
        Update the font for a given range in the text widget to reflect current tags.

        This method ensures that the "combined" tag is both added when styles are present 
        and removed when no longer needed.

        :param start: Starting index of the range.
        :param end: Ending index of the range.
        """
        print(f"Updating font for range {start} to {end}")  # Debug print
        base_font = tkFont.Font(family=self.font_family, size=self.font_size)
        try:
            for index in self.text.tag_ranges("sel"):
                font = base_font.copy()
                tags = self.text.tag_names(index)
                has_style = False

                if "bold" in tags:
                    font.configure(weight="bold")
                    has_style = True
                if "italic" in tags:
                    font.configure(slant="italic")
                    has_style = True
                if "underline" in tags:
                    font.configure(underline=True)
                    has_style = True
                if has_style:
                    self.text.tag_configure("combined", font=font)
                    self.text.tag_add("combined", index, self.text.index(f"{index}+1c"))
                else:
                    # Remove the "combined" tag if no style is applied
                    self.text.tag_remove("combined", index, self.text.index(f"{index}+1c"))
        except Exception as e:
            print(f"Error updating font for range: {e}")

    def change_font_size(self):
        """
        Allow the user to change the font size of the text in the editor.

        This method opens a dialog for size input and updates the font if a valid size is entered.
        """
        new_size = simpledialog.askinteger("Font Size", "Enter new font size:", minvalue=1, maxvalue=72)
        if new_size:
            self.font_size = new_size
            self.update_font()

    def change_font(self):
        """
        Allow the user to change the font family of the text in the editor.

        This method presents a dialog to choose from available font families and updates the font if a valid choice is made.
        """
        fonts = tkFont.families()  # Get list of available font families
        font_choice = simpledialog.askstring("Font", "Choose a font:", initialvalue=self.font_family)
        if font_choice in fonts:
            self.font_family = font_choice
            self.update_font()

    def change_font_color(self):
        """
        Allow the user to change the font color in the editor.

        This method prompts for a hex color code and applies it if the input is valid.
        """
        color = simpledialog.askstring("Font Color", "Enter color in hex (e.g., #FF0000 for red):")
        if color and color.startswith("#"):
            self.font_color = color
            self.text.configure(fg=self.font_color)

    def update_font(self):
        """Update the font settings for the text widget and style tags."""
        font = tkFont.Font(family=self.font_family, size=self.font_size)
        self.text.configure(font=font)
        # Update each style tag with the new base font
        for tag in ["bold", "italic", "underline", "combined"]:
            tag_font = font.copy()
            if tag == "bold":
                tag_font.configure(weight="bold")
            elif tag == "italic":
                tag_font.configure(slant="italic")
            elif tag == "underline":
                tag_font.configure(underline=True)
            # 'combined' tag uses base font; specifics handled elsewhere
            self.text.tag_configure(tag, font=tag_font)
        
        # Update each tag configuration with the new font
        for tag in ["bold", "italic", "underline"]:
            tag_font = font.copy()
            if tag == "bold":
                tag_font.configure(weight="bold")
            elif tag == "italic":
                tag_font.configure(slant="italic")
            elif tag == "underline":
                tag_font.configure(underline=True)
            self.text.tag_configure(tag, font=tag_font)

    def update_indentation(self) -> None:
        """
        Visualize indentation in the text widget by adding or removing 'indent' tags.

        This method iterates through each line to:
        - Calculate the indentation level,
        - Apply the 'indent' tag for spaces at the beginning of lines with indentation,
        - Remove the 'indent' tag from lines with no or only whitespace indentation.

        :return: None
        """
        # Count total lines in the text widget
        total_lines = self.text.count('1.0', tk.END, 'lines')[0] + 1  # +1 because count starts at 1
        
        for line_num in range(1, total_lines):
            # Get the start and end index for the current line
            line_start = f'{line_num}.0'
            line_end = f'{line_num}.end'
            
            # Retrieve the text of the current line
            line_text = self.text.get(line_start, line_end)
            
            # Calculate the indentation level by subtracting the length of the line with leading spaces removed
            indent_level = len(line_text) - len(line_text.lstrip())
            
            # If there's an indent, add the 'indent' tag to the spaces at the beginning of the line
            if indent_level > 0:
                self.text.tag_add('indent', line_start, f'{line_num}.{indent_level}')
            else:
                # If there's no indent or it's just whitespace, remove the 'indent' tag
                self.text.tag_remove('indent', line_start)

    def set_font_color_based_on_theme(self):
        """Adjust text color based on the current theme."""
        # Set text color to improve visibility based on background
        if self.current_theme == self.dark_theme:
            self.font_color = "#FFFFFF"  # White for dark backgrounds
        else:
            self.font_color = "#000000"  # Black for light backgrounds
        
        # Apply the new font color
        self.text.configure(fg=self.font_color)

    def open_file(self):
        """
        Open a file, read its contents, and display them in the text editor.

        This method:
        - Opens a file dialog to select a file,
        - Reads the file content,
        - Clears the current text widget and inserts the new content,
        - Updates file-related instance variables and the status bar.

        :raises PermissionError: If the file cannot be opened due to permission issues.
        :raises FileNotFoundError: If the file does not exist.
        :raises IOError: For other I/O related errors.
        """
        try:
            # Prompt user to select a file
            file_path = filedialog.askopenfilename(defaultextension=".txt", 
                                                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if not file_path:  # If no file was selected
                return

            # Open and read the file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Clear existing text and insert new content
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', content)
            
            # Update file tracking information
            self.file_path = file_path
            self.last_content = content
            self.last_saved_time = time.time()
            self.status_bar.update_status_bar()()
        
        except PermissionError:
            messagebox.showerror("Error", "Permission denied. You do not have the rights to read this file.")
        except FileNotFoundError:
            messagebox.showerror("Error", "File not found. Please check the file path.")
        except IOError as e:
            messagebox.showerror("Error", f"An error occurred while reading the file: {e}")   

    def save_and_update_status(self, event=None):
        """
        Save the current file and then update the status bar.

        :param event: Optional Tkinter event, typically bound to a key or menu action.
        """
        self.save()
        self.status_bar.update_status_bar(self.file_path, len(self.text.get('1.0', 'end-1c').split()))

    def save(self, event=None):
        """
        Save the content of the text editor to a file.

        This method:
        - If no file path exists, prompts for one,
        - Writes the current content to the file,
        - Updates the application's state after saving.

        :param event: Optional Tkinter event, typically bound to a key or menu action.
        """
        try:
            if not self.file_path:
                # If no file path is set, prompt the user to choose one
                self.file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
                if not self.file_path:  # If no file path was chosen
                    return

            # Write the current content to the file
            with open(self.file_path, 'w', encoding='utf-8') as file:
                content = self.text.get('1.0', 'end-1c')
                file.write(content)
            
            # Update last save information
            self.last_saved_time = time.time()
            self.last_content = content
            self.status_bar.update_status_bar(self.file_path, len(self.text.get('1.0', 'end-1c').split()))
            messagebox.showinfo("Saved", f"File saved at {self.file_path}")

            # Update autosave delay in config if changed
            self.config_manager.set("autosave_delay", self.autosave_delay)

        except PermissionError as e:
            messagebox.showerror("Error", "Permission denied. You do not have the rights to write to this file.")
            logging.error(f"PermissionError while saving: {e}")
        except FileNotFoundError as e:
            messagebox.showerror("Error", "The file path specified does not exist.")
            logging.error(f"The file path specified does not exist.: {e}")
        except OSError as e:
            # This includes IOError but also other OS-related errors
            if e.errno == 36:  # ENAMETOOLONG
                messagebox.showerror("Error", "The file name is too long.")
            elif e.errno == 28:  # ENOSPC
                messagebox.showerror("Error", "No space left on device.")
            else:
                messagebox.showerror("Error", f"An OS error occurred while saving the file: {e.strerror}")
        except UnicodeEncodeError:
            messagebox.showerror("Error", "Encoding error while saving. Please check for invalid characters.")
        except Exception as e:
            # Catch any other unexpected exceptions
            messagebox.showerror("Error", f"An unexpected error occurred while saving the file: {str(e)}")

    def check_for_changes(self) -> None:
        """
        Periodically check for unsaved changes in the text editor and save if necessary.
        """
        print("Checking for changes")
        current_content: str = self.text.get('1.0', tk.END)
        if current_content != self.last_content:
            print("Changes detected, saving")
            self.save()
            self.last_content = current_content
        
        # Schedule next check
        print(f"Scheduling next check in {self.autosave_delay} ms")
        self.master.after(self.autosave_delay, self.check_for_changes)

    def close_file(self) -> None:
        """
        Close the application, prompting to save if there are unsaved changes.
        """
        if self.text.edit_modified():
            choice = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save before quitting?")
            if choice is None:
                return  # User cancelled, do not close
            elif choice:
                self.save()
        
        # Ask for confirmation to exit, regardless of saved state
        if self.text.edit_modified() or messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.master.destroy()

if __name__ == "__main__":
    # Create the main window using TkinterDnD for drag and drop functionality
    root = tkdnd.Tk()
    
    # Instantiate the TextEditor class with the root window
    app = TextEditor(root)
    
    # Start the Tkinter event loop, which will display the window and wait for user interactions
    root.mainloop()
