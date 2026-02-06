from flask import Flask, request
import subprocess
import threading

app = Flask(__name__)

# Flag to ensure voice.py is triggered only once
voice_triggered = False

@app.route('/detect', methods=['GET'])
def detect():
    global voice_triggered

    if not voice_triggered:
        print("Person detected! Triggering mini assistant...")

        # Mark as triggered so it doesn't run again
        voice_triggered = True

        # Run voice.py in a separate thread to avoid blocking Flask
        threading.Thread(target=lambda: subprocess.Popen(['python3', 'voice.py'])).start()
        return "Voice triggered", 200
    else:
        print("Person already detected, ignoring further triggers.")
        return "Already triggered", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
