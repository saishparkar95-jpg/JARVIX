# 🤖 JARVIS AI - Futuristic Windows Desktop Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20Qt-00f0ff.svg)](https://doc.qt.io/qtforpython-6/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078d7.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, voice-first personal AI assistant for Windows built in Python with **PySide6 (Qt)**, continuous hands-free speech recognition (Google Assistant style), multi-language support (**English, Hindi, Hinglish**), laptop hardware automation, local SQLite memory, and strict security sandboxing.

---

## 🌟 Key Features

- 🎙️ **Hands-Free Ambient Wake Word**: Listens continuously for `"Hey Jarvis"`, `"Jarvis"`, or `"Oye Jarvis"` with audio chime feedback.
- 🎨 **Futuristic Holographic Dashboard**: Real-time pulsing animated AI core, live telemetry (CPU %, RAM %, Battery %, Network status), and scrollable conversation bubbles.
- 🌐 **Multi-Language Intelligence**: Automatic detection and voice switching for **English**, **Hindi (`hi-IN`)**, and **Hinglish**.
- 💻 **Laptop OS & Hardware Controls**:
  - Volume control (e.g., *"Volume 50 percent karo"*, *"Volume badhao"*, *"Mute"*)
  - Media playback (*Play*, *Pause*, *Next track*)
  - Screen locking (*"Lock computer"*)
  - Application launcher & safe process termination (*"Chrome kholo"*, *"Notepad band karo"*)
  - Safe file and folder creation / search
- 🛡️ **Security Sandboxing**:
  - Application allowlist protection
  - Path traversal protection (protects `C:\Windows`, `C:\System32`, `C:\Program Files`)
  - Blocks dangerous system commands, partition formatting, and credential theft
  - Requires explicit confirmation before sensitive operations
- ⏰ **Local Reminders & Voice Notes**:
  - Natural time parser (*"Remind me in 10 minutes to submit assignment"*)
  - Scheduled background voice notifications
  - Local SQLite notes storage
- 🧠 **Controlled Long-Term Memory**: Remembers user preferences while strictly blocking passwords and secret tokens.
- 🪟 **Always-On Background Mode**: Runs in Windows System Tray and starts automatically with Windows.

---

## 📂 Project Structure

```text
JARVIS-AI/
│
├── main.py                   # Main application entry point (GUI / CLI)
├── config.py                 # Configuration loader and constants
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Protects secrets, DB, and builds
├── README.md                 # Project documentation
├── Run_JARVIS.vbs            # Silent background launcher
│
├── jarvis/
│   ├── assistant.py          # Central CLI orchestrator
│   ├── core/
│   │   ├── brain.py          # AI reasoning engine (OpenAI + offline fallback)
│   │   ├── context.py        # Context tracker for conversational follow-ups
│   │   ├── intent_router.py  # Comprehensive natural language dispatcher
│   │   ├── language.py       # English, Hindi, and Hinglish language engine
│   │   ├── memory.py         # SQLite memory database
│   │   ├── reminders.py      # Background reminder scheduler
│   │   ├── stt.py            # Continuous streaming speech recognition
│   │   ├── tts.py            # Offline Windows SAPI5 voice engine
│   │   └── wake_word.py      # Wake word detector & activation chime
│   │
│   ├── actions/
│   │   ├── safety.py         # Security manager and path guard
│   │   ├── app_actions.py    # Windows app launcher with allowlist
│   │   ├── computer_actions.py # Volume, media, screen lock, and files
│   │   ├── system_actions.py # Telemetry metrics, time, date, screenshot
│   │   └── web_actions.py    # Google search, YouTube, news, weather
│   │
│   └── ui/
│       ├── core_animation.py # Holographic animated glowing AI core widget
│       ├── main_window.py    # Futuristic PySide6 dashboard window
│       ├── system_tray.py    # Windows system tray integration
│       └── worker.py         # Non-blocking background QThread workers
│
├── scripts/
│   ├── build_exe.py          # Standalone Windows .exe builder (PyInstaller)
│   ├── create_shortcut.py    # 1-click Desktop shortcut creator
│   └── setup_startup.py      # Registers JARVIS into Windows Startup
│
└── tests/
    └── test_jarvis.py        # Automated test suite
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/saishparkar95-jpg/JARVIX.git
cd JARVIX
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configuration (Optional)
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
*(Optional: Add your `OPENAI_API_KEY` for open-domain cloud intelligence, or leave blank to use built-in offline smart responses).*

### 5. Launch JARVIS
```powershell
python main.py
```

---

## 🗣️ Example Voice Commands

| Intent | Hindi / Hinglish | English |
| :--- | :--- | :--- |
| **Wake Word** | *"Hey Jarvis"* | *"Hey Jarvis"* |
| **Open App** | *"Chrome kholo"* \| *"Notepad open karo"* | *"Open Chrome"* \| *"Open Notepad"* |
| **Close App** | *"Chrome band karo"* | *"Close Chrome"* |
| **Battery** | *"Battery kitni hai?"* | *"What's my battery percentage?"* |
| **Volume** | *"Volume 50 percent karo"* \| *"Volume badhao"* | *"Set volume to 50%"* \| *"Increase volume"* |
| **Web Search** | *"YouTube par Python tutorial search karo"* | *"Search Google for quantum computing"* |
| **Reminders** | *"Mujhe 8 baje medicine yaad dilana"* | *"Remind me in 10 minutes to submit assignment"* |
| **Lock** | *"Laptop lock karo"* | *"Lock computer"* |
| **Language Switch** | *"Jarvis Hindi mein baat karo"* | *"Jarvis speak in English"* |
| **Emergency Stop** | *"Ruko"* \| *"Cancel"* (or press <kbd>Esc</kbd>) | *"JARVIS stop"* (or press <kbd>Esc</kbd>) |

---

## 🧪 Running Tests
```powershell
python tests/test_jarvis.py
```

---

## 📄 License
This project is licensed under the MIT License.
