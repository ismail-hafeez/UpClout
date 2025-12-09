from PIL import Image
import os
import streamlit as st
import requests

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000/chat"

# Load Owly Image
image_path = os.path.join(os.path.dirname(__file__), "Owly.png")
try:
    owly_image = Image.open(image_path)
    st.set_page_config(page_title="UpClout Chatbot", page_icon=owly_image)
except Exception as e:
    st.warning(f"Could not load Owly.png: {e}")
    st.set_page_config(page_title="UpClout Chatbot", page_icon="🤖")

# Header with Image
col1, col2 = st.columns([1, 8])
with col1:
    if 'owly_image' in locals():
        st.image(owly_image, width=60)
    else:
        st.write("🤖")
with col2:
    st.title("Ask Owly")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# --- UI: Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- UI: Chat Input ---
if prompt := st.chat_input("Ask about influencers, brands, or trends..."):
    # 1. Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Call Backend
    payload = {
        "message": prompt,
        "history": st.session_state.messages[:-1],  
        "thread_id": st.session_state.thread_id
    }

    with st.chat_message("assistant"):
        try:
            st.spinner("...")
            # Stream the response
            with requests.post(BACKEND_URL, json=payload, stream=True) as response:
                if response.status_code == 200:
                    # Retrieve thread_id from headers
                    thread_id = response.headers.get("X-Thread-ID")
                    if thread_id:
                        st.session_state.thread_id = thread_id

                    # Stream content to UI
                    response_text = st.write_stream(response.iter_content(chunk_size=None, decode_unicode=True))
                    
                    # Append full response to history for next turn
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Connection Error: {e}")
