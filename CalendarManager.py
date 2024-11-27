# CalendarManager.py

import tkinter as tk
from tkinter import Toplevel, Button
from tkcalendar import Calendar

def open_calendar(master, text_widget, current_theme):
    """
    Open a calendar dialog if it doesn't exist or has been closed.
    
    :param master: The main Tkinter window.
    :param text_widget: The Text widget where the date will be inserted.
    :param current_theme: Dictionary containing current theme colors.
    :return: The calendar window as Toplevel, or None if already open.
    """
    calendar_window = create_calendar_window(master, current_theme)
    setup_calendar_widget(calendar_window, current_theme)
    add_select_button(calendar_window, text_widget, current_theme)
    return calendar_window

def create_calendar_window(master, current_theme):
    """
    Create and configure the calendar window, centered on the main application.
    
    :param master: The main Tkinter window.
    :param current_theme: Dictionary containing current theme colors.
    :return: The Toplevel window for the calendar
    """
    window = Toplevel(master)
    window.title("Calendar")
    window.geometry("300x300")

    # Calculate the center position relative to the main window
    main_window_x = master.winfo_x()
    main_window_y = master.winfo_y()
    main_window_width = master.winfo_width()
    main_window_height = master.winfo_height()

    # Calendar window dimensions
    calendar_width = 300
    calendar_height = 300

    # Calculate center coordinates
    center_x = main_window_x + (main_window_width // 2) - (calendar_width // 2)
    center_y = main_window_y + (main_window_height // 2) - (calendar_height // 2)

    # Set the geometry of the calendar window to center it
    window.geometry(f"{calendar_width}x{calendar_height}+{center_x}+{center_y}")

    configure_widget(window, bg=current_theme["background"])
    window.protocol("WM_DELETE_WINDOW", lambda: close_calendar(window))
    return window

def setup_calendar_widget(calendar_window, current_theme):
    """
    Initialize and configure the Calendar widget.
    
    :param calendar_window: The Toplevel window for the calendar.
    :param current_theme: Dictionary containing current theme colors.
    """
    cal = Calendar(calendar_window, 
                selectmode='day', 
                year=2024, month=11, day=18, 
                background=current_theme["background"], 
                foreground=current_theme["text"])
    cal.pack(expand=True, fill="both")
    calendar_window.cal = cal

def add_select_button(calendar_window, text_widget, current_theme):
    """
    Create and add the 'Select' button to the calendar window.
    
    :param calendar_window: The Toplevel window for the calendar.
    :param text_widget: The Text widget where the date will be inserted.
    :param current_theme: Dictionary containing current theme colors.
    """
    cal = calendar_window.cal
    cal.bind("<<CalendarSelected>>", lambda event: select_date(cal, text_widget, calendar_window))
    confirm_btn = Button(calendar_window, 
                        text="Select", 
                        command=lambda: select_date(cal, text_widget, calendar_window))
    configure_widget(confirm_btn, 
                    bg=current_theme.get("button_background", current_theme["background"]), 
                    fg=current_theme.get("button_foreground", current_theme["text"]))
    confirm_btn.pack(pady=5)

def select_date(cal, text_widget, calendar_window):
    """
    Process the date selection from the calendar.
    
    :param cal: The Calendar widget.
    :param text_widget: The Text widget where the date will be inserted.
    :param calendar_window: The Toplevel window for the calendar.
    """
    try:
        selected_date = cal.selection_get()
        text_widget.insert(tk.INSERT, str(selected_date))
        close_calendar(calendar_window)
    except AttributeError:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Error", "No date selected.")

def close_calendar(calendar_window):
    """
    Handle the closing of the calendar window.
    
    :param calendar_window: The Toplevel window for the calendar.
    """
    if calendar_window:
        calendar_window.destroy()

def configure_widget(widget, bg=None, fg=None):
    """
    Configure widget background and foreground colors.
    
    :param widget: The widget to be configured.
    :param bg: Background color.
    :param fg: Foreground color.
    """
    if bg:
        widget.configure(bg=bg)
    if fg:
        widget.configure(fg=fg)