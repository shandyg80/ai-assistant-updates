import os
import sys
import subprocess
import openai
import speech_recognition as sr
import pyttsx3
import requests
from flask import Flask, request, jsonify

# --------------- AUTO-UPDATE FROM GITHUB ---------------
GITHUB_RAW_URL = GITHUB_RAW_URL = "https://github.com/shandyg80/ai-assistant-updates/raw/refs/heads/main/ai_assistant.py"


def update_script():
    """Fetch the latest script from GitHub and update itself."""
    try:
        response = requests.get(GITHUB_RAW_URL)
        if response.status_code == 200:
            with open(__file__, "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✅ AI Assistant updated successfully! Restarting...")
            os.execv(sys.executable, [sys.executable] + sys.argv)  # Restart the script
        else:
            print(f"⚠️ Failed to fetch update. HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Update error: {e}")

# Auto-update before running
update_script()

# --------------- OPENAI API CONFIGURATION ---------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ ERROR: No OpenAI API key found. Set it in the environment variables.")
    sys.exit(1)

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# --------------- FLASK APP SETUP ---------------
app = Flask(__name__)

# --------------- TEXT-TO-SPEECH SETUP ---------------
engine = pyttsx3.init()

def speak(text):
    """Make the AI assistant talk."""
    engine.say(text)
    engine.runAndWait()

# --------------- VOICE RECOGNITION ---------------
def listen():
    """Listen for voice commands and convert them to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening... Speak now!")
        recognizer.adjust_for_ambient_noise(source)  # Reduce background noise
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio).lower()
            print(f"🗣️ You said: {text}")
            return text
        except sr.UnknownValueError:
            print("🤖 Sorry, I didn't catch that.")
            speak("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError:
            print("⚠️ Voice recognition service is down.")
            return ""

# --------------- SYSTEM COMMAND EXECUTION ---------------
def run_command(command):
    """Execute a PowerShell or CMD command."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return str(e)

# --------------- AI QUERY FUNCTION ---------------
def ask_ai(question):
    """Use OpenAI API to generate a response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Change to "gpt-3.5-turbo" if needed
            messages=[{"role": "user", "content": question}]
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        return f"AI Error: {e}"

# --------------- FLASK API ROUTES ---------------
@app.route("/")
def home():
    return "AI Assistant is Running!"

@app.route("/command", methods=["POST"])
def execute_command():
    """Run a system command via API."""
    data = request.json
    command = data.get("command", "")
    if not command:
        return jsonify({"error": "No command provided"}), 400

    output = run_command(command)
    return jsonify({"command": command, "output": output})

@app.route("/ai", methods=["POST"])
def ai_query():
    """Get AI-generated responses via API."""
    data = request.json
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    response = ask_ai(query)
    return jsonify({"query": query, "response": response})

# --------------- START FLASK WEB SERVER ---------------
if __name__ == "__main__":
    print("\n🌍 AI Assistant Web Server Started! Listening on port 5000.")
    app.run(host="0.0.0.0", port=5000)
