from atproto import Client
import requests
from PIL import Image, ImageTk
import io
import time
import schedule
import tkinter as tk
from tkinter import filedialog, messagebox
import os

client = Client()

# Global variables
email = ""
password = ""
image_prompt = ""
military_time = ""
user_quote = ""
selected_day = ""
uploaded_images = []  # Changed to list for multiple images
data_saved = False


def show_instructions():
    instructions = """
How to Use BlueSky Automation (Multi-Image Version):

1. Enter your BlueSky email and password.
2. Provide an 'Image Prompt' to auto-generate an image using AI — or upload your own images.
3. Upload multiple images using "Upload Images" button (max 4 images for BlueSky).
4. Optionally, enter your custom quote to post with the images.
5. Choose the day of the week and time (HH:MM in 24-hr format) for scheduling.
6. Click "Save Data" to confirm. The automation will start after the GUI closes.
7. At the scheduled time, your images and quote will be posted to BlueSky.

- You can upload up to 4 images at once.
- If you upload images, they will be used instead of the AI prompt.
- If neither is provided, the post may fail.
"""
    messagebox.showinfo("Instructions", instructions)


def upload_images():
    global uploaded_images
    file_paths = filedialog.askopenfilenames(
        title="Select Images (Max 4)",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp")]
    )

    if file_paths:
        if len(file_paths) > 4:
            messagebox.showwarning("Too Many Images",
                                   "BlueSky supports a maximum of 4 images per post. Only the first 4 will be used.")
            uploaded_images = list(file_paths[:4])
        else:
            uploaded_images = list(file_paths)

        result_label.config(text=f"{len(uploaded_images)} image(s) uploaded successfully!")
        update_image_list_display()


def update_image_list_display():
    if uploaded_images:
        image_names = [os.path.basename(path) for path in uploaded_images]
        display_text = "Images: " + ", ".join(image_names[:2])  # Show first 2 names
        if len(uploaded_images) > 2:
            display_text += f" + {len(uploaded_images) - 2} more"
        image_list_label.config(text=display_text)
    else:
        image_list_label.config(text="No images uploaded")


def clear_images():
    global uploaded_images
    uploaded_images = []
    result_label.config(text="Images cleared!")
    update_image_list_display()


def save_data():
    global email, password, image_prompt, military_time, user_quote, selected_day, data_saved
    try:
        email = email_entry.get()
        password = password_entry.get()
        image_prompt = prompt_entry.get("1.0", tk.END).strip()
        military_time = time_entry.get()
        user_quote = quote_entry.get("1.0", tk.END).strip()
        selected_day = day_var.get()
        data_saved = True
        result_label.config(text="Data saved! Closing GUI...")
        window.update()
        window.after(1000, window.quit)
    except Exception as e:
        print(f"Error saving data: {e}")
        result_label.config(text="Error saving data!")


def generate_image(prompt, api_key):
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {api_key}"}

    print("Generating image...")

    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json={"inputs": prompt})

            if "loading" in response.text.lower():
                print("Model loading, waiting...")
                time.sleep(20)
                continue

            image = Image.open(io.BytesIO(response.content))
            image.save("generated.png")
            print("Image saved as generated.png")
            return "generated.png"

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < 2:
                time.sleep(10)

    print("Failed to generate image after 3 attempts")
    return None


def resize_image(image_path, max_size_kb=970):
    img = Image.open(image_path)
    img_format = img.format
    quality = 95

    # Create a temporary resized version
    temp_path = image_path.replace('.', '_resized.')

    while True:
        img.save(temp_path, format=img_format, quality=quality, optimize=True)

        with open(temp_path, 'rb') as f:
            current_size_kb = len(f.read()) / 1024

        if current_size_kb <= max_size_kb:
            print(f"Image resized to {current_size_kb:.2f}KB")
            return temp_path

        new_width = int(img.width * 0.9)
        new_height = int(img.height * 0.9)
        img = img.resize((new_width, new_height), Image.LANCZOS)

        quality -= 5
        if quality < 10:
            print("Unable to resize image below the required size.")
            return temp_path


def main():
    API_KEY = "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"
    images_to_post = []

    # Handle multiple uploaded images
    if uploaded_images:
        print(f"Using {len(uploaded_images)} uploaded images.")
        for i, image_path in enumerate(uploaded_images):
            resized_path = resize_image(image_path)
            with open(resized_path, 'rb') as f:
                img_data = f.read()
            images_to_post.append(img_data)
            print(f"Prepared image {i + 1}: {os.path.basename(image_path)}")

    # Generate single image if no uploads
    elif image_prompt:
        image_path = generate_image(image_prompt, API_KEY)
        if image_path:
            resized_path = resize_image(image_path)
            with open(resized_path, 'rb') as f:
                img_data = f.read()
            images_to_post.append(img_data)

    else:
        print("No image prompt or uploaded images provided.")
        return

    if not images_to_post:
        print("No images to post.")
        return

    caption = user_quote if user_quote else "No quote provided"

    try:
        # Post with multiple images
        if len(images_to_post) == 1:
            client.send_image(text=caption, image=images_to_post[0], image_alt='Image')
        else:
            # For multiple images, we need to use send_images method
            client.send_images(text=caption, images=images_to_post, image_alts=['Image'] * len(images_to_post))

        print(f"Successfully posted {len(images_to_post)} image(s) to BlueSky with quote: {caption}")

    except Exception as e:
        print(f"Error posting to BlueSky: {e}")
        # Fallback: try posting images individually
        for i, img_data in enumerate(images_to_post):
            try:
                client.send_image(text=f"{caption} (Image {i + 1}/{len(images_to_post)})", image=img_data,
                                  image_alt=f'Image {i + 1}')
                print(f"Posted image {i + 1} individually")
                time.sleep(2)  # Small delay between posts
            except Exception as individual_error:
                print(f"Failed to post image {i + 1}: {individual_error}")


# GUI
window = tk.Tk()
window.title("BlueSky Automation - Multi Image")
window.geometry("460x650")

# Try to load background image, skip if not found
try:
    bg_image = Image.open("../butterfly_background.jpg")
    bg_image = bg_image.resize((460, 650))
    bg_photo = ImageTk.PhotoImage(bg_image)
    bg_label = tk.Label(window, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except:
    window.configure(bg='lightblue')

tk.Label(window, text="Email:", bg="#ffffff").place(x=30, y=30)
email_entry = tk.Entry(window, width=25)
email_entry.place(x=120, y=30)

tk.Label(window, text="Password:", bg="#ffffff").place(x=30, y=70)
password_entry = tk.Entry(window, show="*", width=25)
password_entry.place(x=120, y=70)

tk.Label(window, text="Image Prompt:", bg="#ffffff").place(x=10, y=110)
prompt_entry = tk.Text(window, height=4, width=30)
prompt_entry.place(x=120, y=110)

# Multiple image upload section
upload_btn = tk.Button(window, text="Upload Images (Max 4)", command=upload_images, width=20)
upload_btn.place(x=120, y=180)

clear_btn = tk.Button(window, text="Clear Images", command=clear_images, width=15)
clear_btn.place(x=280, y=180)

image_list_label = tk.Label(window, text="No images uploaded", bg="#ffffff", wraplength=300)
image_list_label.place(x=120, y=210)

tk.Label(window, text="Your Quote:", bg="#ffffff").place(x=10, y=250)
quote_entry = tk.Text(window, height=3, width=30)
quote_entry.place(x=120, y=250)

tk.Label(window, text="Day:", bg="#ffffff").place(x=30, y=320)
day_var = tk.StringVar(window)
day_var.set("Everyday")
day_options = ["Everyday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_menu = tk.OptionMenu(window, day_var, *day_options)
day_menu.place(x=120, y=320)

tk.Label(window, text="Time (HH:MM):", bg="#ffffff").place(x=10, y=360)
time_entry = tk.Entry(window, width=15)
time_entry.place(x=120, y=360)

save_button = tk.Button(window, text="Save Data", command=save_data, width=12)
save_button.place(x=100, y=400)

instr_button = tk.Button(window, text="Instructions", command=show_instructions, width=12)
instr_button.place(x=220, y=400)

result_label = tk.Label(window, text="", bg="#ffffff", wraplength=300)
result_label.place(x=130, y=440)

window.mainloop()
window.destroy()

# Post-GUI logic
if data_saved:
    print("GUI closed, starting automation...")
    print(f"Email: {email}")
    print(f"Time: {military_time}")
    print(f"Quote: {user_quote[:50]}...")
    print(f"Scheduled Day: {selected_day}")
    print(f"Number of uploaded images: {len(uploaded_images)}")

    try:
        client.login(email, password)
        print("Successfully logged into BlueSky!")
    except Exception as e:
        print(f"Login failed: {e}")
        exit()

    # Schedule based on day
    if selected_day == "Everyday":
        schedule.every().day.at(military_time).do(main)
    elif selected_day == "Monday":
        schedule.every().monday.at(military_time).do(main)
    elif selected_day == "Tuesday":
        schedule.every().tuesday.at(military_time).do(main)
    elif selected_day == "Wednesday":
        schedule.every().wednesday.at(military_time).do(main)
    elif selected_day == "Thursday":
        schedule.every().thursday.at(military_time).do(main)
    elif selected_day == "Friday":
        schedule.every().friday.at(military_time).do(main)
    elif selected_day == "Saturday":
        schedule.every().saturday.at(military_time).do(main)
    elif selected_day == "Sunday":
        schedule.every().sunday.at(military_time).do(main)

    print(f"Scheduled to post on {selected_day} at {military_time}")
    print("Automation running... Press Ctrl+C to stop")

    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    print("No data was saved. Exiting...")