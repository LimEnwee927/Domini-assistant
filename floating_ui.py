import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt

from speech import listen
from text_generator import generate_text_from_voice, extract_interview_info, generate_reply
from send_email import send_email
from gmail_auth import get_credentials
from gmail_reader import get_latest_email
from calendar_agent import add_event


class FloatingAI(QWidget):
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.interview_info = None
        self.agent_mode = None

        self.setWindowTitle("Mini Sky AI")
        self.setFixedSize(320, 420)

        # Floating window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Style
        self.setStyleSheet("""
        QWidget {
            background: #1e1e1e;
            color: white;
            border-radius: 12px;
        }
        QPushButton {
            background: #3a7afe;
            padding: 8px;
            border-radius: 8px;
        }
        QLineEdit, QTextEdit {
            background: #2b2b2b;
            color: white;
            border-radius: 6px;
        }
        """)

        layout = QVBoxLayout()

        self.title = QLabel("✨ DOMini Assistant")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.listen_btn = QPushButton("🎤 Speak")
        self.listen_btn.clicked.connect(self.handle_voice)

        self.read_btn = QPushButton("📩 Read Latest Email")
        self.read_btn.clicked.connect(self.handle_read_email)

        self.choice_btn = QPushButton("🗣 Choose Action")
        self.choice_btn.clicked.connect(self.handle_choice)


        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("Recipient email")

        self.output = QTextEdit()
        self.output.setPlaceholderText("Your email draft appears here...")

        self.send_btn = QPushButton("📧 Send")
        self.send_btn.clicked.connect(self.handle_send)

        layout.addWidget(self.title)
        layout.addWidget(self.listen_btn)
        layout.addWidget(self.read_btn)
        layout.addWidget(self.choice_btn)

        layout.addWidget(self.to_input)
        layout.addWidget(self.output)
        layout.addWidget(self.send_btn)

        self.setLayout(layout)

        self.old_pos = None

        # Load creds once
        self.creds = get_credentials()


    def handle_read_email(self):
        self.output.setText("Reading latest email...")

        email = get_latest_email(self.creds)
        self.current_email = email

        if not email:
            self.output.setText("No email found.")
            return

        self.agent_mode = "choice"

        self.output.setText(
            f"From: {email['sender']}\n"
            f"Subject: {email['subject']}\n\n"
            f"{email['body']}\n\n"
            "Options:\n"
            "1) Add interview to calendar\n"
            "2) Reply to recruiter\n\n"
            "Click 'Choose Action' and speak: Option one / Option two"
        )
    def handle_choice(self):
        if not self.current_email:
            self.output.setText("No email loaded yet.")
            return

        self.output.append("\nListening for choice...")
        choice = listen().lower()

        if "one" in choice:
            self.output.append("\nAdding to calendar...")

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

            self.output.append("\n📅 Event added!")
            self.output.append("\nNow speak your reply, then click 🎤 Speak.")

        elif "two" in choice:
            self.agent_mode = "reply"
            self.output.append("\n📝 Speak your reply intent, then click 🎤 Speak.")

        else:
            self.output.append("\n❌ Could not understand choice.")


    def handle_voice(self):
        self.output.append("\nListening...")
        text = listen()

        if not text:
            self.output.append("\nCould not recognize voice.")
            return

        # Agent reply mode
        if self.agent_mode == "reply" and self.current_email:
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
            return

        # Normal email drafting
        draft = generate_text_from_voice(text)
        self.output.setText(draft)


    def handle_send(self):
        to_email = self.to_input.text()
        body = self.output.toPlainText()

        if not to_email or not body:
            self.output.setText("Please enter recipient and content.")
            return

        self.output.append("\n\nSending...")

        ok = send_email(
            to_email=to_email,
            subject="Automated Email from Voice",
            body=body,
            credentials=self.creds
        )

        if ok:
            self.output.append("\n✅ Email sent successfully!")
        else:
            self.output.append("\n❌ Failed to send email.")

    # Drag window
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
