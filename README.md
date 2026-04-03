# 🧠 MindTrack: Neurodivergent Screening & Training Platform

MindTrack is an advanced, full-stack web application designed for early screening, tracking, and cognitive training of children with **ADHD** and **Dyslexia**. Built with Python/Flask, it leverages modern browser technologies and server-side algorithms to create an intelligent, clinical-grade assessment environment that feels like a game.

---

## 🚀 Key Features

### 🎙️ 1. Web Speech API Voice Diagnosis
Instead of a simple multiple-choice clicking tool, MindTrack utilizes the browser's native `webkitSpeechRecognition` to transcribe reading tests (Rapid Automized Naming). The system listens to the child read aloud and validates their phonetic accuracy in real-time, providing highly accurate clinical indicators for Dyslexia.

### 🖱️ 2. Behavioral Mouse-Tracking Algorithm
During focus examinations (Distraction Lab), MindTrack calculates the speed and rapid shifts in cursor coordinates. This tracks "micro-jitters," translating erratic physical movements into an impulsive behavior score to aid in ADHD assessment. 

### 🧬 3. Neural Risk Network Visualization
The typical static charts have been upgraded within the Admin dashboard. MindTrack boasts a high-performance **HTML5 Canvas Particle Engine**. It visually graphs student risk profiles (Low/Medium/High) as dynamically shifting neuro-nodes, giving data scientists and administrators a premium bird's-eye view of the cohort.

### 🤖 4. Advanced Clinical Insight Engine
MindTrack replaces static strings with an advanced Rules Engine (`insight_service.py`). It calculates overlapping arrays of reading, attention, and behavior scores, outputting beautifully tailored, multi-paragraph prescriptive plans customized down to the child's exact age and severity curve.

### 🧩 5. Interactive Cognitive Training Hub 
Screen time should be active, not passive. The `/cognitive_train` module uses dynamic logic to render random puzzles and activities that specifically target neurodivergent traits:
*   **Dyslexia Scramble Challenge**: A phonetic unscrambling game promoting visual-word form processing.
*   **ADHD Focus Sequence**: High-speed, numerical interval training to boost sustained attention under pressure.

---

## 🛠️ Technology Stack

*   **Backend System**: Python 3.8 / Flask 
*   **Database**: Flask-SQLAlchemy (sqlite)
*   **Frontend Technologies**: HTML5, Vanilla JavaScript, CSS3, Bootstrap 5.3
*   **Native Capabilities**: Web Speech API (`webkitSpeechRecognition`)
*   **Charting / Visualization**: Chart.js, HTML5 Dynamic Canvas API

---

## ⚙️ Installation & Usage

### 1. Prerequisites 
- Ensure you have **Python 3.8+** installed.
- (Optional but recommended) Set up a virtual environment.

### 2. Setup
Clone or navigate to the directory constraint and install the dependencies:
```bash
pip install flask flask-sqlalchemy python-dotenv
```
*(Optionally setup `SpeechRecognition` and `pydub` if you wish to run backend audio decoding, though modern UI tests bypass backend processing via the Browser features.)*

### 3. Running the Server

Run the application:
```bash
python adhd_dyslexia/app.py
```
*The default administrator login (admin/admin123) is automatically seeded.*

Access the platform at: `http://127.0.0.1:5000`

---