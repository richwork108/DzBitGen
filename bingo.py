import tkinter as tk

def copy_text():
    selected_text = text_widget.selection_get()
    root.clipboard_clear()
    root.clipboard_append(selected_text)

# Read the content of the text file
with open('Win.txt', 'r') as file:
    text_content = file.read()

# Create the Tkinter window
root = tk.Tk()
root.title("Selectable Text")

# Create a Text widget to display the content
text_widget = tk.Text(root)
text_widget.pack()
text_widget.insert(tk.END, text_content)

# Add a Button to allow copying the selected text
copy_button = tk.Button(root, text="Copy Selected Text", command=copy_text)
copy_button.pack()

# Run the Tkinter main loop
root.mainloop()
