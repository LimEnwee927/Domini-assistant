import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor, QFont, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


from speech import listen
from text_generator import generate_text_from_voice, extract_interview_info, generate_reply
from send_email import send_email
from gmail_auth import get_credentials
from gmail_reader import get_latest_email
from calendar_agent import add_event


# ---- Background thread to continuously listen ----
class VoiceListenerThread(QThread):
    recognized = pyqtSignal(str)

    def run(self):
        while True:
            text = listen()
            if text:
                self.recognized.emit(text)


class FloatingAI(QWidget):
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.interview_info = None
        self.agent_mode = None

        self.setWindowTitle("✨ DOMini Assistant")
        self.setFixedSize(380, 480)

        # Frameless and translucent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)

        # ---- Layout ----
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.title = QLabel("✨ DOMini Assistant")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title.setStyleSheet("color: white;")
        layout.addWidget(self.title)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("DOMini Assistant is listening...")
        self.output.setFont(QFont("Arial", 14))
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: rgba(43, 43, 43, 200);
                color: white;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.output)

        self.setLayout(layout)

        # ---- Position window on the right side ----
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        window_width = self.width()
        window_height = self.height()

        x = screen_width - window_width - 20  # 20 px margin from right edge
        y = (screen_height - window_height) // 2  # vertically centered
        self.move(x, y)

        # Drag support
        self.old_pos = None

        # Load Gmail creds
        self.creds = get_credentials()

        # ---- Start background voice listener ----
        self.listener_thread = VoiceListenerThread()
        self.listener_thread.recognized.connect(self.handle_voice_command)
        self.listener_thread.start()

        self.output.append("👂 Listening for commands...\nSay 'read email' to fetch the latest email.")


    # ---- Handle voice commands ----
    def handle_voice_command(self, text):
        text = text.lower()
        self.output.append(f"\n🎤 Recognized: {text}")
        self.output.moveCursor(QTextCursor.MoveOperation.End)

        if "read email" in text:
            self.read_latest_email()
        elif "option one" in text or "add to calendar" in text:
            self.handle_choice("one")
        elif "option two" in text or "reply" in text:
            self.handle_choice("two")
        elif self.agent_mode == "reply" and self.current_email:
            self.send_reply(text)
        else:
            # Normal draft mode
            draft = generate_text_from_voice(text)
            self.output.append(f"\n📝 Drafted Email:\n{draft}")

    # ---- Email reading ----
    def read_latest_email(self):
        self.output.append("\n📩 Fetching latest email...")
        try:
            email = get_latest_email(self.creds)
        except Exception as e:
            self.output.append(f"\n❌ Failed to read email: {e}")
            return

        if not email:
            self.output.append("\n❌ No email found.")
            return

        self.current_email = email
        self.agent_mode = "choice"

        self.output.append(
            f"\n📨 From: {email['sender']}\nSubject: {email['subject']}\n\n"
            f"{email['body']}\n\n"
            "Options:\n1) Add interview to calendar\n2) Reply to recruiter\n"
            "Say 'Option one' or 'Option two'"
        )

    # ---- Handle choices ----
    def handle_choice(self, choice):
        if not self.current_email:
            self.output.append("\n❌ No email loaded.")
            return

        if choice == "one":
            self.output.append("\n📅 Adding to calendar...")
            info = extract_interview_info(self.current_email["body"])
            dt = datetime.fromisoformat(f"{info['date']} {info['time']}")

            add_event(
                credentials=self.creds,
                title=info["title"],
                start_time=dt,
                duration_minutes=info.get("duration_minutes", 60),
            )

            self.interview_info = info
            self.agent_mode = "reply"
            self.output.append("\n✅ Event added! Now speak your reply.")
        elif choice == "two":
            self.agent_mode = "reply"
            self.output.append("\n📝 Speak your reply now.")
        else:
            self.output.append("\n❌ Could not understand choice.")

    # ---- Send reply ----
    def send_reply(self, text):
        reply = generate_reply(self.current_email["body"], text)
        send_email(
            to_email=self.current_email["sender"],
            subject="Re: " + self.current_email["subject"],
            body=reply,
            credentials=self.creds,
        )
        self.output.append("\n✉ Reply sent!")
        self.output.append("\n" + reply)
        self.agent_mode = None

    # ---- Drag window manually ----
    def mousePressEvent(self, event):
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FloatingAI()
    win.show()
    sys.exit(app.exec())
