import streamlit as st
from atproto import Client
import requests, io, os
from PIL import Image

# Initialize BlueSky client
client = Client()

st.title("🌌 BlueSky Automation - Web Version")
st.markdown("Upload up to 4 images or use an AI prompt to generate one!")

# Inputs
email = st.text_input("BlueSky Email")
password = st.text_input("Password", type="password")
image_prompt = st.text_area("Image Prompt (optional)")
uploaded_files = st.file_uploader("Upload Images (Max 4)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
user_quote = st.text_area("Your Quote", "")
selected_day = st.selectbox("Day", ["Everyday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
military_time = st.text_input("Time (HH:MM)", "12:00")

# Use secrets to store your Hugging Face API key safely
API_KEY = st.secrets.get("HF_API_KEY", None)

def generate_image(prompt):
    if not API_KEY:
        st.error("Missing Hugging Face API key in secrets!")
        return None
   url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(url, headers=headers, json={"inputs": prompt})
    if response.status_code != 200:
        st.error(f"Error from API: {response.text}")
        return None
    return Image.open(io.BytesIO(response.content))

# Post button
if st.button("Post to BlueSky"):
    if not email or not password:
        st.warning("Please enter your BlueSky email and password.")
    else:
        try:
            client.login(email, password)
            st.success(f"Logged in as {email}")
        except Exception as e:
            st.error(f"Login failed: {e}")
            st.stop()

        images_to_post = []

        if uploaded_files:
            for file in uploaded_files[:4]:
                img = Image.open(file)
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                images_to_post.append(buf.getvalue())
        elif image_prompt:
            st.info("Generating AI image...")
            img = generate_image(image_prompt)
            if img:
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                images_to_post.append(buf.getvalue())

        if not images_to_post:
            st.error("No images to post! Upload or generate one first.")
        else:
            caption = user_quote or "No quote provided"
            try:
                if len(images_to_post) == 1:
                    client.send_image(text=caption, image=images_to_post[0], image_alt='Image')
                else:
                    client.send_images(text=caption, images=images_to_post, image_alts=['Image'] * len(images_to_post))
                st.success(f"Posted {len(images_to_post)} image(s) successfully!")
            except Exception as e:
                st.error(f"Failed to post: {e}")




