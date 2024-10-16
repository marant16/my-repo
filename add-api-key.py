
def main():
    import tkinter as tk
    from tkinter import messagebox
    import subprocess

    def set_api_key():
        api_key = entry_key.get().strip()
        var_name = entry_name.get().strip()

        if not api_key:
            messagebox.showerror("Error", "API key field must be filled out!")
            return

        try:
            # Set environment variable using setx command
            command = f'setx {var_name} "{api_key}"'
            subprocess.run(command, shell=True, check=True)
            messagebox.showinfo("Success", f"API key saved as {var_name}!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set environment variable: {str(e)}")

    # Create the main window
    root = tk.Tk()
    root.title("API Key Setter")

    # Add label and text entry for Environment Variable Name (with default value)
    label_name = tk.Label(root, text="Environment Variable Name:")
    label_name.pack(pady=5)

    entry_name = tk.Entry(root, width=50)
    entry_name.insert(0, "OPENAI_API_KEY")  # Default to OPENAI_API_KEY
    entry_name.pack(pady=5)

    # Add label and text entry for API Key
    label_key = tk.Label(root, text="API Key:")
    label_key.pack(pady=5)

    entry_key = tk.Entry(root, width=50)
    entry_key.pack(pady=5)

    # Add a button to trigger the API key setting
    button_set = tk.Button(root, text="Set API Key", command=set_api_key)
    button_set.pack(pady=20)

    # Run the GUI application
    root.geometry("400x200")
    root.mainloop()

if __name__ == "__main__":
    main()
