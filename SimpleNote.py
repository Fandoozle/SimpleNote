from typing import Dict, Optional, Union, Callable, Any
import tkinter as tk
import tkinterdnd2 as tkdnd
from tkinter import Menu, Text, messagebox, filedialog, simpledialog, Toplevel, Label, Entry, Button, font as tkFont
import os, json, time
from tkcalendar import Calendar
from typing import Optional, Literal
from tkinter import ttk
from tkinter import Tk, Text, RIGHT, Y, END, BOTH

def load_config(config_file: str = "config.json") -> Dict[str, Union[int, str]]:
    """Load configuration settings from a JSON file."""
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "autosave_delay": 60000,  # 1 minute in milliseconds
            "window_width": 800,
            "window_height": 600,
            "window_x": 100,
            "window_y": 100
        }

class TextEditor:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.config: Dict[str, Union[int, str]] = load_config()
        self.master.title('Simple Note')

        self.style = ttk.Style()
        self.style.theme_use('clam')  # or any other theme that supports custom styling

        # Load configuration and themes
        self.config: Dict[str, Union[int, str]] = load_config()
        self.themes: Dict[str, Dict[str, str]] = self.load_themes()
        self.current_theme: Dict[str, str] = self.themes.get("dark", self.themes["light"])

        # Font settings
        self.font_family: str = "Arial"
        self.font_size: int = 14
        self.font_color: str = self.current_theme.get("text", "#000000")  # Default text color

        # Create main text frame
        self.text_frame: tk.Frame = tk.Frame(self.master, 
                                             bg=self.current_theme["background"], 
                                             highlightthickness=0, bd=0)
        self.text_frame.pack(expand=True, fill=tk.BOTH)  # Expand to fill the main window

        self.create_text_widget()  # Ensure this is called before binding shortcuts
        self.text.focus_set()  # Set focus to the text widget

        self.create_status_bar()
        self.apply_theme(self.current_theme)

        self.find_replace_open: bool = False  # Flag to check if find/replace dialog is open

        self.bind_keyboard_shortcuts()  # Bind all necessary keyboard shortcuts
        self.create_menu()  # Create the menu bar

        # File management attributes
        self.file_path: Optional[str] = None  # Path of the currently opened file
        self.last_saved_time: float = time.time()  # Timestamp of last save
        self.last_content: str = ""  # Last saved content for comparison

        # Autosave configuration
        self.autosave_delay: int = self.config.get("autosave_delay", 60000)  # In milliseconds
        self.master.after(self.autosave_delay, self.check_for_changes)  # Schedule autosave

        # Line number updating
        self.update_line_number_delay: int = 100  # Delay for updating line numbers
        self.update_line_number_scheduled: bool = False

        # Bind text widget events
        self.update_status_bar()  # Initial status bar update
        self.text.bind('<Return>', self.on_enter_pressed)
        self.text.bind('<Tab>', self.on_tab_pressed)
        self.text.bind('<BackSpace>', self.on_backspace)

        # Calendar window management
        self.calendar_window: Optional[Toplevel] = None

        # Enable drag and drop for files
        self.master.drop_target_register(tkdnd.DND_FILES)
        self.master.dnd_bind('<<Drop>>', self.drop)  # Corrected method name from 'Drop' to 'drop'

        self.master.update_idletasks()
        self.set_window_size()

    def drop(self, event):
            """Handle file drag and drop event."""
            file_path = event.data.replace('{', '').replace('}', '')
            if os.path.isfile(file_path):
                self.open_file_directly(file_path)
            else:
                messagebox.showerror("Error", "The dropped item is not a file.")

    def bind_keyboard_shortcuts(self) -> None:
            """
            Set up keyboard shortcuts for the text editor.

            This method binds various key combinations to their respective editor functions.
            """
            # Bind Ctrl+B to toggle bold text
            self.text.bind("<Control-b>", lambda event: self.toggle_bold())
            # Bind Ctrl+I to toggle italic text
            self.text.bind("<Control-i>", lambda event: self.toggle_italic())
            # Bind Ctrl+U to toggle underline text
            self.text.bind("<Control-u>", lambda event: self.toggle_underline())
            # Bind Ctrl+F to open the find and replace dialog
            self.master.bind("<Control-f>", lambda event: self.open_find_replace_dialog())
            # Bind Ctrl+S to save the current file
            self.text.bind('<Control-s>', self.save)
            # Bind Ctrl+Z for undo action
            self.text.bind('<Control-z>', self.text.edit_undo)
            # Bind Ctrl+Y for redo action
            self.text.bind('<Control-y>', self.text.edit_redo)
            # Bind Ctrl+L to toggle line numbers
            self.master.bind('<Control-l>', self.toggle_line_numbers)

    def open_file_directly(self, file_path: str):
        """
        Open and read the contents of a file into the text widget.

        This method attempts to:
        1. Open the file with UTF-8 encoding.
        2. Clear the current text in the editor.
        3. Insert the file's content into the text widget.
        4. Update editor's state with the file path and last save time.

        :param file_path: The path to the file to be opened.
        :raises PermissionError: If the file cannot be opened due to permission issues.
        :raises FileNotFoundError: If the specified file does not exist.
        :raises IOError: For other I/O related errors.
        """
        try:
            # Attempt to open and read the file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Clear existing content in the text widget
            self.text.delete('1.0', 'end')
            
            # Insert the file's content at the beginning of the text widget
            self.text.insert('1.0', content)
            
            # Update the current file path
            self.file_path = file_path
            
            # Store the content for comparison in future autosave checks
            self.last_content = content
            
            # Update the last saved time
            self.last_saved_time = time.time()
            
            # Refresh the status bar to reflect the new file information
            self.update_status_bar()
            
        except PermissionError:
            # Handle permission issues when trying to read the file
            messagebox.showerror("Error", "Permission denied. You do not have the rights to read this file.")
        
        except FileNotFoundError:
            # File path provided does not exist
            messagebox.showerror("Error", "File not found. Please check the file path.")
        
        except IOError as e:
            # Catch any other I/O related exceptions
            messagebox.showerror("Error", f"An error occurred while reading the file: {e}")

    def open_calendar(self):
        """
        Open a calendar dialog if it doesn't exist or has been closed.

        This method checks if the calendar window is already open, if not:
        - Creates a new top-level window for the calendar.
        - Configures the window's appearance with the current theme.
        - Sets up the calendar widget with the current theme colors.
        - Adds a 'Select' button to confirm date selection.
        """
        if self.calendar_window is None or not self.calendar_window.winfo_exists():
            # Create a new top-level window for the calendar
            self.calendar_window = Toplevel(self.master)
            self.calendar_window.title("Calendar")
            # Set the size of the calendar window
            self.calendar_window.geometry("300x300")
            # Apply the current theme background color to the window
            self.calendar_window.configure(bg=self.current_theme["background"])
            # Bind the window close event to a method for cleanup
            self.calendar_window.protocol("WM_DELETE_WINDOW", self.on_close_calendar)

            # Initialize the Calendar widget
            self.cal = Calendar(self.calendar_window, 
                                selectmode='day', 
                                year=2024, month=11, day=18, 
                                background=self.current_theme["background"], 
                                foreground=self.current_theme["text"])
            # Pack the calendar to fill the window
            self.cal.pack(expand=True, fill="both")

            # Create a confirm button styled with the current theme
            confirm_btn = Button(self.calendar_window, 
                                text="Select", 
                                command=self.select_date,
                                bg=self.current_theme["button_background"], 
                                fg=self.current_theme["button_foreground"])
            # Place the button in the window
            confirm_btn.pack()

    def select_date(self):
        """
        Process the date selection from the calendar.

        This method retrieves the selected date, shows a message with the date, 
        and then closes the calendar window.
        """
        # Retrieve the selected date from the calendar widget
        selected_date = self.cal.selection_get()
        
        # Display the selected date in an info message box
        messagebox.showinfo("Selected Date", f"You selected: {selected_date}")
        
        # If the calendar window exists, close it
        if self.calendar_window:
            self.calendar_window.destroy()

    def on_close_calendar(self):
        """
        Handle the closing of the calendar window.

        This method ensures the calendar window is destroyed and the reference 
        is set to None to free up resources.
        """
        # Check if the calendar window exists and is an attribute of this instance
        if hasattr(self, 'calendar_window') and self.calendar_window:
            # Destroy the calendar window
            self.calendar_window.destroy()
        
        # Set the reference to None to ensure it's not used again
        self.calendar_window = None

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
                    # Here you would add other light theme properties like button colors, etc.
                }
            }

    def set_window_size(self) -> None:
        """
        Configure the initial size and position of the main window to center it on the screen,
        ensuring space for the scrollbar with a minimum size.
        """
        # Get screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Get window dimensions from config or use defaults
        width = self.config.get("window_width", 800)
        height = self.config.get("window_height", 600)

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
        # Check if the line number bar is currently visible
        if self.line_number_bar.winfo_viewable():
            # If visible, remove it from the layout
            self.line_number_bar.pack_forget()
        else:
            # If not visible, add it to the left side of the text widget
            self.line_number_bar.pack(side=tk.LEFT, fill=tk.Y)

    def create_text_widget(self) -> None:
        """
        Create and configure the main text widget and associated elements like the line number bar.

        This method sets up:
        - The font for text display
        - Line number bar
        - Main text area with scroll capabilities
        - Text styling tags
        - Event bindings for scrolling, updating line numbers, and auto-indentation
        """
        # Define the font to be used in the text widgets
        font = tkFont.Font(family=self.font_family, size=self.font_size)

        # Set up the line number bar
        # This bar displays line numbers and is disabled for user input
        self.line_number_bar = Text(self.text_frame, 
                                    width=7, padx=4, 
                                    takefocus=0, border=0,
                                    background=self.current_theme["background"],
                                    state='disabled', wrap='none', 
                                    highlightthickness=0, font=font)
        self.line_number_bar.pack(side=tk.LEFT, fill=tk.Y)
        # Configure the text color of the line numbers
        self.line_number_bar.config(fg=self.current_theme["text"])

        # Create the main text widget for editing
        self.text = Text(self.text_frame, 
                        background=self.current_theme["background"], 
                        font=font, fg=self.font_color, 
                        undo=True, wrap='none', 
                        highlightthickness=0, bd=0)
        self.text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Bind mouse wheel events for scrolling on both text and line number widgets
        self.text.bind('<MouseWheel>', self.on_scroll)
        self.line_number_bar.bind('<MouseWheel>', self.on_scroll)

        # Configure text styling tags
        # Bold
        bold_font = font.copy()
        bold_font.configure(weight="bold")
        self.text.tag_configure("bold", font=bold_font)
        
        # Italic
        italic_font = font.copy()
        italic_font.configure(slant="italic")
        self.text.tag_configure("italic", font=italic_font)
        
        # Underline
        underline_font = font.copy()
        underline_font.configure(underline=True)
        self.text.tag_configure("underline", font=underline_font)

        # Normal (default) font configuration
        self.text.tag_configure("normal", font=font)

        # Bind events for updating line numbers
        # This will trigger on any key press or text modification
        self.text.bind('<Any-KeyPress>', self.delayed_update_line_numbers)
        self.text.bind('<<Modify>>', self.delayed_update_line_numbers)

        # Bind key events for auto-indentation
        self.text.bind('<Return>', self.on_enter_pressed)
        self.text.bind('<Tab>', self.on_tab_pressed)
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
        # Get the content of the current line
        current_line: str = self.text.get('insert linestart', 'insert lineend')
        # Calculate the number of spaces from the start of the line
        indent_level: int = len(current_line) - len(current_line.lstrip())

        # Insert a new line with the calculated indentation
        self.text.insert('insert', '\n' + ' ' * indent_level)
        return 'break'  # Prevent further event propagation

    def on_tab_pressed(self, event: tk.Event) -> Literal['break']:
        """
        Handle the Tab key press event for indentation.

        This method inserts four spaces instead of a tab character for consistency.

        :param event: The Tkinter event object for the key press.
        :return: 'break' to prevent further event processing.
        """
        self.text.insert('insert', '    ')  # Insert four spaces for a tab
        return 'break'  # Prevent further event propagation

    def on_backspace(self, event: tk.Event) -> Optional[Literal['break']]:
        """
        Handle the Backspace key press event for de-indentation.

        This method removes indentation when the cursor is at the start of a line.
        It handles both space-based indentation (4 spaces) and tab-based indentation.

        :param event: The Tkinter event object for the key press.
        :return: 'break' to prevent further event processing if indentation was removed, None otherwise.
        """
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
        menu_bar.add_cascade(label='File', menu=file_menu)


        # Edit menu
        edit_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        edit_menu.add_command(label="Undo | Ctrl+Z", command=self.text.edit_undo)
        edit_menu.add_command(label="Redo | Ctrl+Y", command=self.text.edit_redo)
        edit_menu.add_command(label="Find and Replace", command=self.open_find_replace_dialog)
        menu_bar.add_cascade(label='Edit', menu=edit_menu)

        # Format menu
        format_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        format_menu.add_command(label='Font Size', command=self.change_font_size)
        format_menu.add_command(label='Change Font', command=self.change_font)
        format_menu.add_command(label='Font Color', command=self.change_font_color)
        format_menu.add_command(label='Bold | Ctrl+B', command=self.toggle_bold)  # Corrected keyboard shortcut in label
        format_menu.add_command(label='Italic | Ctrl+I', command=self.toggle_italic)  # Corrected keyboard shortcut in label
        format_menu.add_command(label='Underline | Ctrl+U', command=self.toggle_underline)  # Corrected keyboard shortcut in label
        menu_bar.add_cascade(label='Format', menu=format_menu)

        # Customize menu
        #customize_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        #customize_menu.add_command(label="Customize Theme", command=self.open_customize_dialog)
        #menu_bar.add_cascade(label='Customize', menu=customize_menu)

        # View menu - Line Numbers
        view_menu_line_numbers = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        view_menu_line_numbers.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers)
        menu_bar.add_cascade(label='View', menu=view_menu_line_numbers)

        # Calendar menu (Note: You had two 'view_menu' with the same name which is problematic)
        calendar_menu = Menu(menu_bar, tearoff=0, background=self.current_theme["menu_background"], foreground="#FFFFFF")
        calendar_menu.add_command(label="Open Calendar", command=self.open_calendar)
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
        
        # Loop through all available themes
        for theme_name, theme in self.themes.items():
            # Create a button for each theme, with the theme name as its label
            # The button's command will set the theme when clicked
            button = Button(dialog, 
                            text=theme_name.capitalize(), 
                            command=lambda t=theme: self.set_theme(t))
            button.pack(pady=5)  # Add padding between buttons for visual separation

        # Add a 'Close' button to dismiss the dialog
        close_button = Button(dialog, 
                            text="Close", 
                            command=dialog.destroy)  # Destroy the dialog window when clicked
        close_button.pack(pady=5)  # Add padding around the close button

    def set_theme(self, theme: Dict[str, str]) -> None:
        """
        Apply a new theme across the application, affecting the color scheme of all UI components.

        This method updates:
        - The main window and text frame backgrounds,
        - Colors of the text widget, line number bar, and status bar,
        - The calendar window if open,
        - Menu bar and potentially other menu items,
        - Confirm button in the calendar window.

        :param theme: A dictionary with keys for different UI elements and their corresponding color values.
        """
        # Store the new theme for future reference
        self.current_theme = theme

        # Apply theme to main window components
        self.master.configure(bg=theme["background"])  # Main window
        self.text_frame.configure(bg=theme["background"])  # Text editor frame

        # Update the text widget
        self.text.configure(bg=theme["background"], fg=theme["text"])  # Text color and background

        # Update line number bar, using specific color if available, otherwise default to text color
        self.line_number_bar.configure(bg=theme["background"], fg=theme.get("line_numbers", theme["text"]))

        # Change status bar colors
        self.status_bar.configure(bg=theme["background"], fg=theme.get("status_text", theme["text"]))

        # Update calendar window if it's currently open
        if self.calendar_window and self.calendar_window.winfo_exists():
            # Change the background of the calendar window
            self.calendar_window.configure(bg=theme["background"])
            # If the calendar object exists, update its colors
            if hasattr(self, 'cal'):
                self.cal.config(background=theme["background"], foreground=theme["text"])

        # Update menu bar colors
        if hasattr(self, 'menu'):
        # Update menu bar and menus
            for menu in self.master.winfo_children():
                if isinstance(menu, Menu):
                    menu.configure(
                        background=theme.get("menu_background", theme["background"]),
                        foreground=theme.get("menu_foreground", theme["text"]),
                        activebackground=theme.get("menu_active_background", theme["background"]),
                        activeforeground=theme.get("menu_active_foreground", theme["text"]),
                        disabledforeground=theme.get("menu_disabled_foreground", "#A3A3A3")
                    )
            
            # Update the main menu bar
            menu_bar = self.master.cget('menu')
            if menu_bar:
                menu_bar.configure(
                    background=theme.get("menu_background", theme["background"]),
                    foreground=theme.get("menu_foreground", theme["text"]),
                    activebackground=theme.get("menu_active_background", theme["background"]),
                    activeforeground=theme.get("menu_active_foreground", theme["text"]),
                    disabledforeground=theme.get("menu_disabled_foreground", "#A3A3A3")
                )

            # Update dialogs and windows (like find/replace)
        def update_dialog_theme(dialog: Toplevel):
            """
            Recursively update the theme of a dialog and all its children widgets.

            :param dialog: The top-level dialog window to update.
            """
            # Set the background color of the dialog itself
            dialog.configure(bg=theme["background"])
            
            # Iterate through all children of the dialog
            for widget in dialog.winfo_children():
                # Apply theme to basic widgets like Labels, Entries, and Buttons
                if isinstance(widget, (Label, Entry, Button)):
                    widget.configure(bg=theme["background"], fg=theme["text"])
                # For Text widgets, change both background and foreground color
                elif isinstance(widget, Text):
                    widget.configure(bg=theme["background"], fg=theme["text"])

        # Check if the find/replace dialog is open before attempting to update
        if hasattr(self, 'find_replace_open') and self.find_replace_open:
            # Search for the Find and Replace window among child windows of the main window
            for child in self.master.winfo_children():
                if isinstance(child, Toplevel) and child.title() == "Find and Replace":
                    update_dialog_theme(child)
                    break  # Exit the loop after updating the find/replace dialog

        # Update the font color for the main text area
        self.font_color = theme.get("text", self.font_color)  # Use theme text color if specified, otherwise keep current
        self.text.configure(fg=self.font_color)

        # Refresh text styling tags to reflect the new theme
        # Note: Ensure `update_font` method also updates all relevant tags with new theme settings
        self.update_font()

        self.style.configure("Vertical.TScrollbar", 
                            background=theme.get("scrollbar_background", "#D3D3D3"),
                            troughcolor=theme.get("scrollbar_trough", "#FFFFFF"),
                            bordercolor=theme.get("scrollbar_border", "#A9A9A9"),
                            arrowcolor=theme.get("scrollbar_arrow", "#000000"))

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
        self.toggle_style("italic")

    def toggle_underline(self):
        """
        Toggle the underline text style for the selected or current insertion point.
        """
        self.toggle_style("underline")

    def toggle_style(self, style):
        """
        Toggle a text style (like bold, italic, or underline) for the selected or current text.

        :param style: The style to toggle ("bold", "italic", or "underline").
        """
        try:
            # Attempt to get the selection range
            start, end = self.text.index(tk.SEL_FIRST), self.text.index(tk.SEL_LAST)
        except tk.TclError:
            # If no text is selected, apply style at the insertion point
            start = end = self.text.index(tk.INSERT)

        # Get current tags at the start position
        current_tags = self.text.tag_names(start)
        
        if style in current_tags:
            # If the style is already applied, remove it
            self.text.tag_remove(style, start, end)
            # Ensure any applied style is reset to normal
            self.text.tag_add("normal", start, end)
        else:
            # Remove all current styles from the selection
            for tag in current_tags:
                self.text.tag_remove(tag, start, end)
            # Apply the new style
            self.text.tag_add(style, start, end)

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
        """
        Update the font settings for the text widget and all its style tags.

        This method:
        - Creates a new font with the current font family and size,
        - Applies this font to the text widget,
        - Reconfigures style tags to reflect the new font settings.
        """
        # Create a new font object with the current family and size
        font = tkFont.Font(family=self.font_family, size=self.font_size)
        
        # Set the base font for the text widget
        self.text.configure(font=font)
        
        # Update each tag configuration with the new font
        for tag in ["bold", "italic", "underline", "normal"]:
            self.text.tag_configure(tag, font=font.copy(
                weight="bold" if tag == "bold" else "normal",
                slant="italic" if tag == "italic" else "roman",
                underline=True if tag == "underline" else False
            ))

    def update_indentation(self) -> None:
        """
        Visualize indentation in the text widget by adding or removing 'indent' tags.

        This method:
        - Iterates over each line in the text widget,
        - Calculates the indentation level,
        - Applies or removes the 'indent' tag based on the presence of indentation.
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

    def apply_theme(self, theme):
        """
        Apply a theme to the entire application by updating the background and foreground colors.

        This method:
        - Changes the background color of the main window, text frame, status bar, and line number bar.
        - Updates the foreground color for text and status bar.
        - Configures indentation visualization tags.
        """
        # Update background color for main components
        self.master.configure(bg=theme["background"])  # Main window
        self.text_frame.configure(bg=theme["background"])  # Text frame
        self.text.configure(bg=theme["background"], fg=theme.get("text", "#000000"))  # Text widget
        self.status_bar.configure(bg=theme["background"], fg=theme.get("text", "#000000"))  # Status bar
        self.line_number_bar.configure(bg=theme["background"], fg=theme.get("line_numbers", "#CCCCCC"))  # Line number bar

        # Set the font color based on the theme, falls back to current color if not specified
        self.font_color = theme.get("text", self.font_color)
        self.text.configure(fg=self.font_color)  # Apply the font color to the text widget

        # Configure indentation visualization
        # The 'indent' tag is used to visually represent indentation
        self.text.tag_configure('indent', 
                                tabs=('0.5c',), 
                                background=theme.get('indent_guide', self.current_theme['background']))
        
        # The 'dedent' tag can be used for negative indentation, but here it's just setting the background
        self.text.tag_configure('dedent', 
                                background=theme.get('indent_guide', self.current_theme['background']))

    def set_font_color_based_on_theme(self):
        """
        Adjust the text color based on whether the current theme is dark or light.

        This method changes the text color to:
        - White (#FFFFFF) for dark themes
        - Black (#000000) for light themes
        """
        if self.current_theme == self.dark_theme:
            self.font_color = "#FFFFFF"  # White for better visibility on dark backgrounds
        else:
            self.font_color = "#000000"  # Black for light backgrounds
        
        # Apply the new font color to the text widget
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
            self.update_status_bar()
        
        except PermissionError:
            messagebox.showerror("Error", "Permission denied. You do not have the rights to read this file.")
        except FileNotFoundError:
            messagebox.showerror("Error", "File not found. Please check the file path.")
        except IOError as e:
            messagebox.showerror("Error", f"An error occurred while reading the file: {e}")   

    def create_status_bar(self):
        """
        Add a status bar at the bottom of the main window to display file information and time.
        """
        self.status_bar = tk.Label(self.master, text="Ready", bd=0, relief=tk.FLAT, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status_bar(self):
        """
        Refresh the status bar with current file name, time, and word count.

        This method is called periodically to update the status bar information.
        """
        # Determine the file name to display
        if hasattr(self, 'file_path') and self.file_path:
            file_info = os.path.basename(self.file_path)
        else:
            file_info = "Untitled"
        
        # Update the label text with current information
        self.status_bar.config(text=f"File: {file_info} - {time.strftime('%I:%M:%S %p')} - Words: {len(self.text.get('1.0', 'end-1c').split())}")
        
        # Schedule next update in 1 second
        self.master.after(1000, self.update_status_bar)

    def save_and_update_status(self, event=None):
        """
        Save the current file and then update the status bar.

        :param event: Optional Tkinter event, typically bound to a key or menu action.
        """
        self.save()
        self.update_status_bar()

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
            self.update_status_bar()
            messagebox.showinfo("Saved", f"File saved at {self.file_path}")

        except PermissionError:
            messagebox.showerror("Error", "Permission denied. You do not have the rights to write to this file.")
        except IOError as e:
            messagebox.showerror("Error", f"An error occurred while saving the file: {e}")

    def check_for_changes(self) -> None:
        """
        Periodically check for unsaved changes in the text editor and save if necessary.
        """
        current_content: str = self.text.get('1.0', tk.END)
        if current_content != self.last_content:
            self.save()
            self.last_content = current_content
        
        # Schedule next check
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