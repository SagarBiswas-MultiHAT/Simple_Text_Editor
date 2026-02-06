import tkinter as tk
from tkinter import filedialog, messagebox


# Function to open a file
def open_file():
    filepath = filedialog.askopenfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
    )
    if filepath:
        with open(filepath) as file:
            editor.delete(1.0, tk.END)
            editor.insert(tk.END, file.read())
        status_bar.config(text=f"Opened: {filepath}")


# Function to save the current file
def save_file():
    global current_file
    if current_file:
        with open(current_file) as file:
            file.write(editor.get("1.0", "end-1c"))
        status_bar.config(text=f"Saved: {current_file}")
    else:
        save_file_as()


# Function to save the current file as a new file
def save_file_as():
    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
    )
    if filepath:
        with open(filepath) as file:
            file.write(editor.get("1.0", "end-1c"))
        status_bar.config(text=f"Saved: {filepath}")
        global current_file
        current_file = filepath


# Function to create a new file
def new_file():
    global current_file
    if messagebox.askyesno("New File", "Do you want to save the current file?"):
        save_file()
    editor.delete(1.0, tk.END)
    current_file = None
    status_bar.config(text="New File")


# Function to show the About dialog
def about():
    messagebox.showinfo("About", "Simple Text Editor\nCreated by Your Name")


# Function to exit the editor
def exit_editor():
    if messagebox.askyesno("Exit", "Do you really want to exit?"):
        root.destroy()


# Function to handle keyboard shortcuts
def bind_shortcuts():
    root.bind("<Control-s>", lambda event: save_file())


# Initialize the main application window
root = tk.Tk()
root.title("Simple Text Editor")

# Create the menu bar
menu_bar = tk.Menu(root)

# Create the File menu and add commands
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="New", command=new_file)
file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_command(label="Save As", command=save_file_as)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=exit_editor)
menu_bar.add_cascade(label="File", menu=file_menu)

# Create the Help menu and add commands
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=about)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Configure the menu bar
root.config(menu=menu_bar)

# Create the text editor widget
editor = tk.Text(root, wrap="word")
editor.pack(expand="yes", fill="both")

# Create the status bar
status_bar = tk.Label(root, text="New File", anchor="w")
status_bar.pack(side="bottom", fill="x")

# Initialize the current file variable
current_file = None

# Bind keyboard shortcuts
bind_shortcuts()

# Start the main event loop
root.mainloop()
