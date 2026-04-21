from tkinter import messagebox

def show_info(title: str, message: str):
    messagebox.showinfo(title, message)

def show_error(title: str, message: str):
    messagebox.showerror(title, message)

def ask_yes_no(title: str, message: str) -> bool:
    return messagebox.askyesno(title, message)
