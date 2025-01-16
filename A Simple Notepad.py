import tkinter as tk # Import the tkinter module for creating GUI applications
from tkinter import filedialog, messagebox # Import filedialog for file dialogs and messagebox for message dialogs

# Function to open a file
def open_file():
    # Open a file dialog to select a text file, allowing only text files or all files
    filepath = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    # If a file is selected (filepath is not empty)
    if filepath:
        # Open the file in read mode
        with open(filepath, 'r') as file:
            # Clear the current content in the text editor
            editor.delete(1.0, tk.END)
            # Insert the file content into the text editor
            editor.insert(tk.END, file.read())

# Function to save the content to a file
def save_file():
    # Open a file dialog to choose where to save the file, with options for text files or all files
    filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    # If a file path is chosen (filepath is not empty)
    if filepath:
        with open(filepath, 'w') as file:
            # Retrieve all the text from the text editor, starting from the very first character (position "1.0")
            # --> 1.0" means the first character of the first line (1 is the line number, 0 is the character index within that line).
            # up to just before the last automatically added newline (position 'end-1c'),
            # and then write this text to the file.
            file.write(editor.get("1.0",'end-1c'))

# Function to display the "About" information
def about():
        # Show a message box with information about the editor
    messagebox.showinfo("About", "Simple Text Editor\nCreated by SAGAR BISWAS")

# Function to confirm exit and close the editor
def exit_editor():
    # Ask the user if they really want to exit
    if messagebox.askyesno("Exit", "Do you really want to exit?"):
        root.destroy()  # Close the main application window

# Create the main application window
root = tk.Tk()
root.title("Simple Text Editor") # Set the title of the window

# Create a menu bar
menu_bar = tk.Menu(root)

# Create a "File" menu
file_menu = tk.Menu(menu_bar, tearoff=0) # Create a "File" menu that cannot be torn off into a separate window (tear-off feature disabled)
file_menu.add_command(label="Open", command=open_file) # Add "Open" option to the menu
file_menu.add_command(label="Save", command=save_file) # Add "Save" option to the menu
file_menu.add_separator() # Add a separator line
file_menu.add_command(label="Exit", command=exit_editor)  # Add "Exit" option to the menu

# Add the "File" menu to the menu bar
menu_bar.add_cascade(label="File", menu=file_menu)

# Create a "Help" menu
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=about) # Add "About" option to the menu

# Add the "Help" menu to the menu bar
menu_bar.add_cascade(label="Help", menu=help_menu)

# Set the menu bar as the menu for the main window
root.config(menu=menu_bar)

# Create a text editor widget
editor = tk.Text(root, wrap="word")  # "wrap='word'" ensures lines are wrapped at word boundaries,  so the sentence remains readable without any horizontal scrolling.
editor.pack(expand="yes", fill="both") # Makeing the 'editor' widget expand to fill both the horizontal and vertical space of its container.

# Start the application's main loop (wait for user interaction)
root.mainloop()
