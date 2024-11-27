# StatusBar.py

import tkinter as tk
import time
from typing import Optional

class StatusBar:
    def __init__(self, master):
        self.status_bar = tk.Label(master, text="Ready", bd=0, relief=tk.FLAT, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status_bar(self, file_path: Optional[str] = None, word_count: int = 0):
        file_info = "Untitled" if file_path is None else file_path
        time_info = time.strftime('%I:%M:%S %p')
        self.status_bar.config(text=f"File: {file_info} - {time_info} - Words: {word_count}")

    def configure(self, **kwargs):
        self.status_bar.config(**kwargs)
        
    def update_status_bar(self, file_path: Optional[str] = None, word_count: int = 0):
        print(f"Update status bar called at: {time.time()}")
        file_info = "Untitled" if file_path is None else os.path.basename(file_path)
        time_info = time.strftime('%I:%M:%S %p')
        self.status_bar.config(text=f"File: {file_info} - {time_info} - Words: {word_count}")

    def create_status_bar(self):
        """
        Add a status bar at the bottom of the main window to display file information and time.
        """
        self.status_bar = tk.Label(self.master, text="Ready", bd=0, relief=tk.FLAT, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def manual_update_status(self):
        self.update_status_bar()