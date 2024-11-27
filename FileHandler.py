import os
from tkinter import filedialog, messagebox
from typing import Optional

class FileHandler:
    def __init__(self):
        self.file_path: Optional[str] = None
        self.last_content: str = ""
        self.last_saved_time: float = 0.0

    def open_file_directly(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.file_path = file_path
            self.last_content = content
            self.last_saved_time = os.path.getmtime(file_path)
            return content
        except Exception as e:
            # Handle exceptions here or pass them back
            return None

    def save(self, event=None):
        content = self.text.get('1.0', 'end-1c')
        if self.file_handler.save_file(content):
            self.update_status_bar()

    def save_file(self, content: str) -> bool:
        """
        Save the content to a file.

        :param content: The text content to save.
        :return: True if save was successful, False otherwise.
        """
        if not self.file_path:
            self.file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                           filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if not self.file_path:
                return False
        try:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.last_content = content
            self.last_saved_time = os.path.getmtime(self.file_path)
            messagebox.showinfo("Saved", f"File saved at {self.file_path}")
            return True
        except PermissionError:
            messagebox.showerror("Error", "Permission denied. You do not have the rights to write to this file.")
        except FileNotFoundError:
            messagebox.showerror("Error", "The file path specified does not exist.")
        except OSError as e:
            if e.errno == 36:  # ENAMETOOLONG
                messagebox.showerror("Error", "The file name is too long.")
            elif e.errno == 28:  # ENOSPC
                messagebox.showerror("Error", "No space left on device.")
            else:
                messagebox.showerror("Error", f"An OS error occurred while saving the file: {e.strerror}")
        except UnicodeEncodeError:
            messagebox.showerror("Error", "Encoding error while saving. Please check for invalid characters.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while saving the file: {str(e)}")
        return False

    def is_modified(self, current_content: str) -> bool:
        """
        Check if the current content has been modified since last save.

        :param current_content: The current text content.
        :return: True if content has changed, False otherwise.
        """
        return current_content != self.last_content

    def reset_file_path(self):
        """
        Reset file path and related attributes when starting a new document.
        """
        self.file_path = None
        self.last_content = ""
        self.last_saved_time = 0.0

    def check_for_changes(self) -> None:
        print("Checking for changes")
        current_content = self.text.get('1.0', tk.END)
        if self.file_handler.is_modified(current_content):
            print("Changes detected, saving")
            self.save()
            self.file_handler.last_content = current_content
        
        # Schedule next check
        print(f"Scheduling next check in {self.autosave_delay} ms")
        self.master.after(self.autosave_delay, self.check_for_changes)

    def close_file(self) -> None:
        if self.file_handler.is_modified(self.text.get('1.0', tk.END)):
            choice = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Do you want to save before quitting?")
            if choice is None:
                return  # User cancelled, do not close
            elif choice:
                self.save()
        
        # Ask for confirmation to exit
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.master.destroy()