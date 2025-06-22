# app.py (The Definitive Version with Anti-Example Prompting)

import streamlit as st
import google.generativeai as genai
import json
from PIL import Image, ImageDraw, ImageFont
import os
import ffmpeg

# --- Configuration and Setup ---
st.set_page_config(page_title="YT Shorts Generator", page_icon="🎬", layout="centered")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configuring Gemini API. Make sure your API key is set in secrets.toml. Error: {e}")
    st.stop()

# --- Helper Function for Text Wrapping ---
def wrap_text(text, font, draw, max_width):
    lines = []
    for line in text.split('\n'):
        words = line.split(' ')
        current_line = ''
        for word in words:
            if draw.textbbox((0, 0), current_line + word, font=font)[2] <= max_width:
                current_line += word + ' '
            else:
                lines.append(current_line.strip())
                current_line = word + ' '
        lines.append(current_line.strip())
    return '\n'.join(lines)

# --- Core AI Functions ---
def generate_content(topic):
    prompt = f"""
    You are an expert in creating viral YouTube Shorts content. Based on "{topic}", generate a JSON object with:
    1.  **on_screen_text**: An intriguing two-line hook. The first line is a mysterious statement. The second MUST be a call-to-action to read the comments (e.g., *Read the comment for the full story*).
    2.  **image_prompt**: A detailed, cinematic prompt for an AI image generator.
    3.  **description**: A YouTube description with 3-5 relevant hashtags.
    4.  **tags**: A comma-separated string of 10+ relevant YouTube tags.
    Provide ONLY the JSON object.
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        st.error(f"Error generating content from AI. Details: {e}")
        if 'response' in locals() and hasattr(response, 'text'): st.code(f"AI Raw Response:\n{response.text}")
        return None

def generate_comment_story(topic, on_screen_text):
    """Generates the story using a highly specific, persona-driven prompt with anti-examples."""
    # THIS IS THE FINAL, MASTER PROMPT.
    prompt = f"""
    Context: A YouTube Short about "{topic}" was created with the on-screen text: "{on_screen_text}".

    Your Persona: You are a brilliant researcher who is an expert at explaining complex, mysterious topics. Your writing style is a mix of a cool history professor and a top conspiracy theorist. You build a compelling case, point by point. You are NOT a cheesy, hyperactive vlogger.

    Your Task: Write the pinned YouTube comment that reveals the full story.

    **CRITICAL RULES:**
    1.  **STRUCTURE IS KING:** The main body of your comment **MUST BE** a numbered list (1., 2., 3., etc.). This is the most important rule. Each point is a piece of evidence.
    2.  **AUTHORITATIVE TONE:** Start with an intriguing hook paragraph. Present your numbered points like you're revealing classified information. Use short, punchy sentences for impact where appropriate.
    3.  **NO FAKE CONVERSATIONALISM:** Do NOT use cheesy phrases like "Get this:", "The crazy part is...", or "Seriously mind-blowing." Your authority comes from the facts you present, not from trying too hard to sound cool.
    4.  **STRONG CONCLUSION:** End with a powerful paragraph that makes the reader think.

    ---
    **GOLD STANDARD EXAMPLE (THE EXACT STRUCTURE AND TONE TO FOLLOW)**
    Topic: "Mount Kailash"

    PERFECT OUTPUT:
    Mount Kailash isn't just sacred - it's bizarre. It's been called the Axis Mundi, the center of the world. But what if it's also a doorway... to something outside time itself?
    Here's what's been reported - and experienced - by those who've dared get close:
    1. Pilgrims say a full kora (circuit walk) feels like it takes just a few hours, but when they return - days have passed. No memory loss. No explanation.
    2. Ancient texts describe Mount Kailash as the meeting point of heaven and earth, where time is said to "twist like a serpent." Not metaphor. Literal.
    3. Multiple travelers have reported rapid aging of hair and nails just from camping near it. Like they were there longer than they thought.
    4. No one has ever climbed it - not even the best. Attempts have ended in retreat or sudden illness. Locals say: "It's not for humans."
    People laugh this off... until they see the footage. Until they go there. One traveler said: "You don't come back from Kailash the same. Not just spiritually... Physically."
    Still think it's just a mountain? Save this for when you're ready to question reality.
    ---
    **ANTI-EXAMPLE (WHAT NOT TO DO - THIS IS BAD)**
    Topic: "The Himalayas"

    BAD OUTPUT:
    Okay, so basically, the Himalayas aren't just *mountains*. Get this: They're *older* than we thought! The crazy part is, new research shows some Himalayan rock formations are from a time *before* the planet even had continents as we know them! We're talking *billions* of years older than previously estimated. Seriously mind-blowing.
    (Reason this is BAD: It fails the #1 rule. It has no numbered list, presents no specific evidence, and uses cheesy, fake conversational phrases.)
    ---
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating the story from AI. Details: {e}")
        return None

def create_video(image_path, on_screen_text, watermark_text, duration=10, output_path="final_video.mp4"):
    """Creates the video with a specific duration."""
    try:
        background_image = Image.open(image_path).convert("RGBA")
        width, height = background_image.size
        overlay = Image.new('RGBA', background_image.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        main_text_font_size = int(height * 0.045) 
        try: main_font = ImageFont.truetype("arialbd.ttf", main_text_font_size)
        except IOError: main_font = ImageFont.load_default()
        max_text_width = width * 0.9
        wrapped_text = wrap_text(on_screen_text, main_font, draw, max_text_width)
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=main_font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) / 2
        text_y = height * 0.1
        draw.text((text_x + 2, text_y + 2), wrapped_text, font=main_font, fill=(0, 0, 0, 180), align="center")
        draw.text((text_x, text_y), wrapped_text, font=main_font, fill="white", align="center")
        watermark_font_size = int(height * 0.025)
        try: watermark_font = ImageFont.truetype("arial.ttf", watermark_font_size)
        except IOError: watermark_font = ImageFont.load_default()
        watermark_bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
        watermark_width = watermark_bbox[2] - watermark_bbox[0]
        watermark_x = (width - watermark_width) / 2
        watermark_y = height * 0.9
        draw.text((watermark_x, watermark_y), watermark_text, font=watermark_font, fill=(255, 255, 255, 180))
        final_image = Image.alpha_composite(background_image, overlay)
        final_image_path = "temp_image.png"
        final_image.save(final_image_path)
        (ffmpeg.input(final_image_path, loop=1, t=duration).output(output_path, vcodec='libx264', pix_fmt='yuv420p', vf=f'scale={width}:{height}').run(overwrite_output=True, quiet=True))
        os.remove(final_image_path)
        return output_path
    except Exception as e:
        st.error(f"An error occurred during video creation: {e}")
        if 'final_image_path' in locals() and os.path.exists(final_image_path): os.remove(final_image_path)
        return None

# --- Streamlit UI ---
st.title("🎬 Viral Shorts Production Studio")
st.markdown("Generate a complete video package: teaser text, AI image prompt, description, tags, and the detailed comment story.")
if 'content' not in st.session_state: st.session_state.content = None
if 'comment_story' not in st.session_state: st.session_state.comment_story = None
with st.container(border=True):
    st.subheader("Step 1: Generate the Core Idea")
    topic = st.text_input("Enter a Topic (e.g., 'Tirumala Temple', 'Nikola Tesla', 'Govinda'):", "Govinda")
    if st.button("✨ Generate Ideas", type="primary"):
        st.session_state.comment_story = None
        with st.spinner("🧠 Brainstorming with Gemini..."):
            st.session_state.content = generate_content(topic)
if st.session_state.content:
    content = st.session_state.content
    with st.container(border=True):
        st.subheader("Step 2: Review Content & Generate Story")
        st.info("💡 **AI Image Prompt**")
        st.text_area("Copy this into an AI Image Generator:", value=content.get('image_prompt', ''), height=100)
        st.markdown("#### Edit Video & Post Details")
        on_screen_text = st.text_area("On-Screen Text:", value=content.get('on_screen_text', ''), height=100)
        description = st.text_area("YouTube Description:", value=content.get('description', ''), height=150)
        tags = st.text_area("YouTube Tags:", value=content.get('tags', ''), height=100)
        st.divider()
        st.markdown("#### The Pinned Comment Story")
        if st.button("✍️ Generate Comment Story"):
            with st.spinner("✍️ Uncovering the secret..."):
                st.session_state.comment_story = generate_comment_story(topic, on_screen_text)
        if st.session_state.comment_story:
            # Increased height to better fit the new, longer format
            st.text_area("Copy this for your pinned YouTube comment:", value=st.session_state.comment_story, height=400)
    with st.container(border=True):
        st.subheader("Step 3: Create Your Video")
        uploaded_image = st.file_uploader("Upload the background image you generated...", type=["jpg", "jpeg", "png"])
        watermark = st.text_input("Enter your watermark (e.g., channel name):", "Krishnaa Words")
        duration_seconds = st.slider("Select Video Duration (seconds):", min_value=5, max_value=30, value=10, step=1)
        if uploaded_image and watermark:
            if st.button("🚀 Create Video"):
                with st.spinner("🎥 Rendering your masterpiece..."):
                    video_file_path = create_video(uploaded_image, on_screen_text, watermark, duration=duration_seconds)
                    if video_file_path:
                        st.success("🎉 Video created successfully!")
                        with open(video_file_path, 'rb') as video_file:
                            video_bytes = video_file.read()
                        st.video(video_bytes)
                        st.download_button(label="📥 Download Video (MP4)", data=video_bytes, file_name="generated_short.mp4", mime="video/mp4")
                        os.remove(video_file_path)