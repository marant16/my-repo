def main():
    import tkinter as tk
    from tkinter import Label, messagebox
    from PIL import Image, ImageTk, ImageGrab
    import pyperclip
    import os
    import requests
    import hashlib
    import threading
    import time
    import base64
    import io

    # Define the encode_image_pil function used in get_payload
    def encode_image_pil(image: Image.Image) -> str:
        """
        Encodes a PIL Image to a base64 string. Converts RGBA images to RGB.
        
        Args:
            image (PIL.Image.Image): The image to encode.
        
        Returns:
            str: The base64-encoded string of the image.
        """
        # Convert image to RGB if it's in RGBA or another mode that JPEG doesn't support
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            image = image.convert("RGB")
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        return base64_image

    def get_payload(prompt: str, image: Image.Image) -> dict:
        """
        Generates a JSON payload for the OpenAI API with a prompt and a base64-encoded image.
        
        Args:
            prompt (str): The prompt to send along with the image.
            image (PIL.Image.Image): The image to encode and include in the payload.
        
        Returns:
            dict: The JSON payload for the API request.
        """
        # Encode the image to base64
        base64_image = encode_image_pil(image)
        # Create the JSON payload
        payload = {
            "model": "gpt-4o-mini",  # Replace with the correct model name if different
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                # "detail": "low"  # Optional parameter
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000, 
            "temperature": 0.2
        }
        return payload

    def get_headers() -> dict:
        """
        Returns the headers required for the OpenAI API request.
        
        Returns:
            dict: The headers dictionary with Content-Type and Authorization.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        return headers

    def send_image_to_openai(imagen: Image.Image, prompt: str, max_retries: int = 3, retry_delay: float = 2.0) -> str:
        """
        Sends an image and a prompt to the OpenAI API and returns the text response.

        Args:
            imagen (PIL.Image.Image): The image to send.
            prompt (str): The prompt to send along with the image.
            max_retries (int): The maximum number of retry attempts in case of failure.
            retry_delay (float): The delay between retries in seconds.

        Returns:
            str: The text response from the OpenAI model, or an error message if unsuccessful.
        """
        payload_processing = get_payload(prompt, imagen)
        headers = get_headers()

        for attempt in range(max_retries):
            try:
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload_processing)
                response.raise_for_status()  # Ensure we raise an error for bad responses

                # Attempt to access the desired data
                response_json = response.json()

                if 'choices' in response_json and response_json['choices']:
                    # Assuming the response structure matches the provided example
                    return response_json['choices'][0]['message']['content']
                else:
                    raise KeyError("Key 'choices' not found in response")

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}. Attempt {attempt + 1} of {max_retries}")
            except KeyError as e:
                print(f"Key error: {e}. Attempt {attempt + 1} of {max_retries}")
            
            # Wait before retrying
            time.sleep(retry_delay)

        return "Error: Failed to retrieve a valid response from the OpenAI API after multiple attempts."

    # Function to compute hash of an image for change detection
    def get_image_hash(image):
        if image is None:
            return None
        md5 = hashlib.md5()
        with io.BytesIO() as buffer:
            image.save(buffer, format='PNG')
            md5.update(buffer.getvalue())
        return md5.hexdigest()

    # Function to bring window to front
    def bring_to_front():
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.after_idle(root.attributes, '-topmost', False)

    # Function to capture the image from clipboard
    def capture_clipboard_image():
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            return image
        return None

    # Function to resize image while maintaining aspect ratio
    def resize_image(image, max_size=(250, 250)):
        img = image.copy()
        img.thumbnail(max_size, Image.LANCZOS)
        return img

    # Function to view the image preview
    def view_image():
        if current_image:
            img_tk = ImageTk.PhotoImage(current_image)
            img_preview_label.config(image=img_tk)
            img_preview_label.image = img_tk
            preview_window.deiconify()
            preview_window.lift()
        else:
            messagebox.showinfo("No Image", "No image to display.")

    # Function to process the image with OpenAI GPT-4o-mini
    def process_image():
        global current_image
        if current_image:
            # Run the processing in a separate thread to keep the GUI responsive
            threading.Thread(target=process_image_thread, args=(current_image,), daemon=True).start()
        else:
            messagebox.showinfo("No Image", "No image to process.")

    def process_image_thread(image: Image.Image):
        try:
            # Disable the process button to prevent multiple clicks
            process_button.config(state=tk.DISABLED)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Processing image with OpenAI GPT-4o-mini... Please wait.")

            # Define the prompt
            prompt = "You are an OCR tool. Extract and transcribe all text from the provided image."

            # Send image to OpenAI
            text = send_image_to_openai(image, prompt)

            # Display the extracted text in the text box
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, text)

            # Copy the recognized text to the clipboard
            pyperclip.copy(text)

        except Exception as e:
            messagebox.showerror("OpenAI API Error", f"An error occurred during OCR processing:\n{e}")
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Error processing image.")
        finally:
            # Re-enable the process button
            process_button.config(state=tk.NORMAL)

    # Function to monitor clipboard for new images
    def monitor_clipboard():
        global last_image_hash, current_image
        while True:
            image = capture_clipboard_image()
            image_hash = get_image_hash(image)

            if image and image_hash != last_image_hash:
                last_image_hash = image_hash
                current_image = image.copy()  # Store a copy of the current image

                # Update the preview in the main window without resizing
                img_display = resize_image(current_image.copy(), max_size=(250, 250))
                img_tk = ImageTk.PhotoImage(img_display)
                img_label.config(image=img_tk)
                img_label.image = img_tk

                # Bring the window to front
                bring_to_front()

            time.sleep(1)  # Check every second

    # Initialize GUI
    root = tk.Tk()
    root.title("OpenAI GPT-4o-mini OCR Clipboard Tool")
    root.geometry("350x450")
    root.resizable(False, False)

    # Create GUI components
    img_label = Label(root)
    img_label.pack(pady=10)

    # Frame for buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    view_button = tk.Button(button_frame, text="View Preview", command=view_image)
    view_button.pack(side=tk.LEFT, padx=5)

    process_button = tk.Button(button_frame, text="Process Image", command=process_image)
    process_button.pack(side=tk.LEFT, padx=5)

    # Text box to display OCR result
    result_text = tk.Text(root, height=15, wrap=tk.WORD)
    result_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    # Preview window (initially hidden)
    preview_window = tk.Toplevel(root)
    preview_window.title("Image Preview")
    preview_window.geometry("400x400")
    preview_window.resizable(False, False)
    preview_window.withdraw()  # Hide initially

    img_preview_label = Label(preview_window)
    img_preview_label.pack(pady=10, padx=10)

    # Variables to track clipboard changes
    last_image_hash = None
    current_image = None

    # Start clipboard monitoring in a separate thread
    clipboard_thread = threading.Thread(target=monitor_clipboard, daemon=True)
    clipboard_thread.start()

    # Run the GUI loop
    root.mainloop()


if __name__ == "__main__":
    main()
