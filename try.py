import streamlit as st
from speech import listen
from text_generator import generate_text_from_voice

st.title("Voice-to-Email Draft Generator")

if st.button("🎤 Speak"):
    voice_text = listen()
    if voice_text:
        st.write("You said:", voice_text)

        draft = generate_text_from_voice(voice_text)
        st.write("Generated Email Draft:")
        st.text_area("Draft", draft, height=200)
    else:
        st.write("Sorry, could not recognize your voice.")
