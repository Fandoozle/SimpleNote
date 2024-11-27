# KeybindingsManager.py

from typing import Callable, Dict, Any
import tkinter as tk

def bind_keyboard_shortcuts(editor: Any):
    """
    Bind keyboard shortcuts to various methods for the editor.

    :param editor: An instance of TextEditor where shortcuts will be bound
    """
    keybindings = {
        "<Control-b>": lambda: editor.toggle_bold(),
        "<Control-i>": lambda: editor.toggle_italic(),
        "<Control-u>": lambda: editor.toggle_underline(),
        "<Control-f>": lambda: editor.open_find_replace_dialog(),
        "<Control-s>": lambda: editor.save(),
        "<Control-z>": lambda: editor.custom_undo(),
        "<Control-y>": lambda: editor.custom_redo(),
        "<Control-l>": lambda: editor.toggle_line_numbers()
    }

    for key, method in keybindings.items():
        print(f"Binding {key} to method")  # Debug print
        editor.text.bind(key, lambda e, m=method: _safe_call(m))

def bind_events_for_text_widget(text_widget: tk.Text, on_scroll: Callable, delayed_update_line_numbers: Callable, 
                                on_enter_pressed: Callable, on_backspace: Callable):
    """
    Bind events to the text widget for scrolling, line number updates, and auto-indentation.

    :param text_widget: The Text widget to bind events to.
    :param on_scroll: Function to handle scroll events.
    :param delayed_update_line_numbers: Function to handle line number updates.
    :param on_enter_pressed: Function for handling enter key press for auto-indentation.
    :param on_backspace: Function for handling backspace key for auto-indentation.
    """
    text_widget.bind('<MouseWheel>', on_scroll)
    text_widget.bind('<Any-KeyPress>', delayed_update_line_numbers)
    text_widget.bind('<<Modify>>', delayed_update_line_numbers)
    text_widget.bind('<Return>', on_enter_pressed)
    text_widget.bind('<BackSpace>', on_backspace)

def _safe_call(method: Callable) -> None:
    """
    Safely call a method, catching and displaying any errors.

    :param method: The method to call
    """
    try:
        method()
    except AttributeError as e:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Error", f"Method not found: {e}")
    except Exception as e:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Error", f"An error occurred: {e}")