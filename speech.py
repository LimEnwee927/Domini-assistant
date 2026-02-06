import speech_recognition as sr

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print("Recognized:", text)
        return text
    except Exception as e:
        print("Error recognizing speech:", e)
        return ""

