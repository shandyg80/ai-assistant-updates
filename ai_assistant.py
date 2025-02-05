import os
import subprocess
import openai
import requests
import time
import speech_recognition as sr
import pyttsx3
from flask import Flask, request, jsonify

# ✅ REPLACE THIS WITH YOUR RAW GITHUB FILE URL
GITHUB_RAW_URL = "https://raw.githubusercontent.com/shandyg80/ai-assistant-updates/refs/heads/main/ai_assistant.py?token=GHSAT0AAAAAAC6JEWFAQELSVKCQLXELUESSZ5CZRFQ"

# Load API Key from Environment Variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize Flask App
app = Flask(__name__)

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()

def speak(text):
    """Make the AI assistant talk."""
    engine.say(text)
    engine.runAndWait()

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

def run_command(command):
    """Execute a PowerShell or CMD command."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return str(e)

def ask_ai(question):
    """Use OpenAI API to generate a response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  
            messages=[{"role": "user", "content": question}]
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        return f"AI Error: {e}"

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

def update_script():
    """Check for updates from GitHub and restart if necessary."""
    print("🔄 Checking for updates...")
    
    try:
        response = requests.get(GITHUB_RAW_URL)
        if response.status_code == 200:
            with open(__file__, "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✅ Update successful! Restarting...")
            os.execv(__file__, ["python"] + sys.argv)
        else:
            print("❌ Failed to fetch update.")
    except Exception as e:
        print(f"❌ Error while updating: {e}")

if __name__ == "__main__":
    print("\n🌍 AI Assistant Web Server Started! Listening on port 5000.")
    
    # ✅ Auto-Update every hour
    while True:
        update_script()
        time.sleep(3600)  # Wait an hour before checking again
        
        # Start Flask Web Server
        app.run(host="0.0.0.0", port=5000)
