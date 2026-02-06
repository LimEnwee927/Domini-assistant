import streamlit as st
from speech import listen
from text_generator import generate_text_from_voice
from send_email import send_email
from gmail_auth import get_credentials


st.set_page_config(page_title="Voice to Email", layout="centered")
st.title("🎤 Voice-to-Email Draft Generator")


# ---- Session State ----
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

if "draft" not in st.session_state:
    st.session_state.draft = ""


# ---- Load Gmail credentials once ----
@st.cache_resource
def load_creds():
    return get_credentials()

creds = load_creds()


# ---- UI ----
st.write("Click and speak. Your voice becomes an email draft.")


if st.button("🎤 Speak"):
    with st.spinner("Listening..."):
        voice_text = listen()

    if voice_text:
        st.session_state.voice_text = voice_text
        st.session_state.draft = generate_text_from_voice(voice_text)
    else:
        st.warning("Could not recognize your voice.")


# ---- Show recognized text ----
if st.session_state.voice_text:
    st.subheader("You said:")
    st.write(st.session_state.voice_text)


# ---- Show draft ----
if st.session_state.draft:
    st.subheader("Generated Email Draft")

    st.session_state.draft = st.text_area(
        "Edit before sending:",
        st.session_state.draft,
        height=220
    )


# ---- Send button ----
if st.session_state.draft and st.button("📧 Send Email"):
    recipient_email = "cse022005@gmail.com"
    subject = "Automated Email from Voice"

    with st.spinner("Sending email..."):
        result = send_email(
            to_email=recipient_email,
            subject=subject,
            body=st.session_state.draft,
            credentials=creds
        )

    if result:
        st.success("✅ Email sent successfully!")
    else:
        st.error("❌ Failed to send email.")
