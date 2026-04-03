from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, random
import speech_recognition as sr
from pydub import AudioSegment
import shutil
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.config.from_object('config.Config')

# Optional fallback logic for secret key if not using env optimally
if not app.secret_key:
    app.secret_key = app.config.get('SECRET_KEY', 'super_secret_key_123')

db = SQLAlchemy(app)

from services.auth_service import hash_password, verify_password
from services.insight_service import generate_insight

REQUIRED_FOLDERS = [
    "static/recordings",
    "static/processed",
    "static/reports"
]

for folder in REQUIRED_FOLDERS:
    os.makedirs(folder, exist_ok=True)


# 🔥 AUTO-DETECT FFMPEG
ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

from pydub import AudioSegment
from pydub.utils import which

AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe   = which("ffprobe")


if ffmpeg_path:
    AudioSegment.converter = ffmpeg_path
else:
    print("[X] FFmpeg NOT FOUND. Audio conversion will not work.")

if ffprobe_path:
    AudioSegment.ffprobe = ffprobe_path
else:
    print("[X] FFprobe NOT FOUND. Audio conversion will not work.")

# --------------------- MODELS ---------------------
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    dob = db.Column(db.Date)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    dob = db.Column(db.Date)
    location = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    student_class = db.Column(db.String(20))
    dob = db.Column(db.Date)

class StudentTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    reading_score = db.Column(db.Integer)
    attention_score = db.Column(db.Integer)
    behavior_score = db.Column(db.Integer)
    reading_level = db.Column(db.String(10))
    attention_level = db.Column(db.String(10))
    behavior_level = db.Column(db.String(10))
    overall_risk = db.Column(db.String(10))
    recommendations = db.Column(db.Text)

# ------------------- UTILS -----------------------
def calculate_risk_level(value):
    if value == "1":
        return "Low"
    elif value == "2":
        return "Medium"
    else:
        return "High"

def map_score_level(score):
    if score < 40: return "Low"
    elif score < 70: return "Medium"
    else: return "High"

def generate_recommendation(overall_risk):
    if overall_risk == "High":
        return "Seek professional evaluation, use focused home activities."
    elif overall_risk == "Medium":
        return "Provide extra attention, practice reading and focus tasks."
    else:
        return "Continue regular learning, monitor progress."



def calculate_reading_score(original, spoken):
    original_words = original.lower().split()
    spoken_words = spoken.lower().split()
    correct = sum([1 for o, s in zip(original_words, spoken_words) if o == s])
    return int((correct / max(len(original_words),1)) * 100)

def calculate_attention_score(clicks, total_targets):
    """Simple attention score based on clicks accuracy"""
    return int((clicks / max(total_targets,1)) * 100)

def calculate_behavior_score(activity_level):
    """Placeholder: Use webcam analysis or AI to get behavior score"""
    return random.randint(30, 100)

# ------------------- ROUTES -----------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------- ADMIN ROUTES ----------------
@app.route("/admin_login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username).first()
        if admin and (verify_password(admin.password, password) or admin.password == password):
            session["admin_id"] = admin.id
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))
    teachers = Teacher.query.all()
    parents = Parent.query.all()
    students = Child.query.all()
    
    # Calculate Risk Distribution for Pie Chart
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for child in students:
        latest = StudentTest.query.filter_by(child_id=child.id).order_by(StudentTest.date.desc()).first()
        if latest and latest.overall_risk in risk_counts:
            risk_counts[latest.overall_risk] += 1
            
    return render_template("admin_dashboard.html", 
                           teachers=teachers, 
                           parents=parents, 
                           students=students, 
                           risk_counts=risk_counts,
                           low_count=risk_counts["Low"],
                           med_count=risk_counts["Medium"],
                           high_count=risk_counts["High"])

@app.route("/add_teacher", methods=["GET","POST"])
def add_teacher():
    if request.method == "POST":
        try:
            # Check for existing user
            existing = Teacher.query.filter_by(username=request.form["username"]).first()
            if existing:
                flash("Teacher with this username already exists.", "danger")
                return redirect(url_for("add_teacher"))
            
            teacher = Teacher(
                name=request.form["name"],
                email=request.form["email"],
                mobile=request.form["mobile"],
                dob=datetime.strptime(request.form["dob"], "%Y-%m-%d"),
                username=request.form["username"],
                password=hash_password(request.form["password"])
            )
            db.session.add(teacher)
            db.session.commit()
            flash("Teacher added successfully", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            db.session.rollback()
            print("Error adding teacher:", e)
            flash("Error creating teacher.", "danger")
    return render_template("add_teacher.html")

# ------------------- TEACHER ROUTES ----------------
@app.route("/teacher_login", methods=["GET","POST"])
def teacher_login():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and (verify_password(teacher.password, password) or teacher.password == password):
            session["teacher_id"] = teacher.id
            return redirect(url_for("teacher_dashboard"))
        else:
            flash("Invalid credentials","danger")
    return render_template("teacher_login.html")

@app.route("/teacher/dashboard")
def teacher_dashboard():
    if "teacher_id" not in session and "admin_id" not in session:
        return redirect(url_for("teacher_login"))
    children = Child.query.all()
    return render_template("teacher_dashboard.html", children=children)

@app.route("/teacher/delete_student/<int:child_id>", methods=["POST"])
def delete_student(child_id):
    if "teacher_id" not in session and "admin_id" not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("teacher_login"))
    
    child = Child.query.get_or_404(child_id)
    try:
        # Delete the child (SQLAlchemy CASCADE should handle orphaned StudentTests if configured, but let's be safe)
        StudentTest.query.filter_by(child_id=child.id).delete()
        db.session.delete(child)
        db.session.commit()
        flash(f"Student '{child.name}' and all associated test records have been permanently removed.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error removing student.", "danger")
        print("Delete error:", e)
        
    return redirect(request.referrer or url_for("teacher_dashboard"))

def generate_paragraph():
    words = ["reading","student","attention","focus","brain","learning","test","score","concentration","ADHD","dyslexia",
             "exercise","monitor","report","skill","level","practice","improve","memory","evaluation"]
    return ' '.join(random.choices(words, k=100))

def calculate_risk_level(value):
    if value == "1":
        return "Low"
    elif value == "2":
        return "Medium"
    else:
        return "High"

def generate_recommendation(overall_risk):
    if overall_risk == "High":
        return "Seek professional evaluation, use focused home activities."
    elif overall_risk == "Medium":
        return "Provide extra attention, practice reading and focus tasks."
    else:
        return "Continue regular learning, monitor progress."

# -------------------- CONDUCT TEST ROUTE --------------------
@app.route("/teacher/conduct_test/<int:child_id>/<level>", methods=["GET","POST"])
def conduct_test(child_id, level):
    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    child = Child.query.get_or_404(child_id)

    def generate_game_data(age, level):
        import random
        data = {}
        if age <= 5:
            # Reading: Searching for Sounds
            phonemes = [
                {'sound': 'C', 'word': 'Cat', 'emoji': '🐱', 'prompt': "Which one starts with C like ca-ca?"},
                {'sound': 'B', 'word': 'Ball', 'emoji': '🏀', 'prompt': "Which one starts with B like buh-buh?"},
                {'sound': 'D', 'word': 'Dog', 'emoji': '🐶', 'prompt': "Which one starts with D like duh-duh?"},
                {'sound': 'M', 'word': 'Mouse', 'emoji': '🐭', 'prompt': "Which one starts with M like mmm-mmm?"},
                {'sound': 'S', 'word': 'Sun', 'emoji': '☀️', 'prompt': "Which one starts with S like sss-sss?"}
            ]
            target = random.choice(phonemes)
            distractors = random.sample([p for p in phonemes if p != target], 2)
            choices = [target] + distractors
            random.shuffle(choices)
            data['reading'] = {
                'target_sound': target['sound'],
                'target_prompt': target['prompt'],
                'target_emoji': target['emoji'],
                'choices': choices
            }
            
            # Behavior: The Memory Hide & Seek
            data['behavior'] = {'hidden_cup': random.randint(0, 2)}
            
            # Attention: The Bubble Catch
            colors = ["RED", "BLUE", "GREEN", "YELLOW"]
            target_color = random.choice(colors)
            data['attention'] = {
                'target_color': target_color,
                'target_prompt': f"Pop the {target_color} ones!"
            }
            
            return data, "1-5"
            
        elif age <= 10:
            # Reading: Alien Word Decoder
            consonants = "bdfghklmnprstwyz"
            vowels = "aeiou"
            def make_nonsense():
                return random.choice(consonants) + random.choice(vowels) + random.choice(consonants) + random.choice(consonants)
            target_word = make_nonsense()
            choices = [target_word, make_nonsense(), make_nonsense()]
            random.shuffle(choices)
            data['reading'] = {
                'target': target_word,
                'choices': choices
            }
            # Behavior: Virtual Day Planner
            tasks = [
                {"id": 1, "name": "Brush Teeth", "energy": 1},
                {"id": 2, "name": "Pack Bag", "energy": 2},
                {"id": 3, "name": "Eat Breakfast", "energy": 2},
                {"id": 4, "name": "Find Keys", "energy": 1},
                {"id": 5, "name": "Put on Shoes", "energy": 1}
            ]
            random.shuffle(tasks)
            data['behavior'] = {'tasks': tasks}
            return data, "6-10"
            
        else:
            # Reading: Rapid Naming Sprint (Voice)
            items = ["CAT", "DOG", "SUN", "RED", "ONE", "TWO", "DAY", "CAR", "BAT", "PEN"]
            grid = random.choices(items, k=16)
            data['reading'] = {'grid': grid}
            # Behavior: Social Scenario Simulator
            scenarios = [
                {
                    "context": "Your friend is an hour late to meet you at the mall.",
                    "choices": [
                        {"text": "Text them angrily and leave.", "type": "Impulsive"},
                        {"text": "Wait silently and feel sad.", "type": "Passive"},
                        {"text": "Call them to check if they are okay, then decide to wait or leave.", "type": "Regulated"}
                    ]
                },
                {
                    "context": "You just got a bad grade on a test you studied hard for.",
                    "choices": [
                        {"text": "Tear up the test and yell at the teacher.", "type": "Impulsive"},
                        {"text": "Hide it and never talk about it.", "type": "Passive"},
                        {"text": "Ask the teacher for feedback after class.", "type": "Regulated"}
                    ]
                }
            ]
            scenario = random.choice(scenarios)
            random.shuffle(scenario["choices"])
            data['behavior'] = {'scenario': scenario}
            return data, "11-15"

    game_data, age_group = generate_game_data(child.age, level)

    if request.method=="POST":
        data = request.get_json()
        # --- Convert numeric/percentage scores to level ---
        def map_level(score):
            # score can be 0-100 (reading/attention/behavior)
            if score < 40:
                return "Low"
            elif score < 70:
                return "Medium"
            else:
                return "High"

        reading_level = map_level(data['reading_score'])
        attention_level = map_level(data['attention_score'])
        behavior_level = map_level(data['behavior_score'])

        risk_order = {"Low":0, "Medium":1, "High":2}
        overall_risk = max([reading_level, attention_level, behavior_level], key=lambda x: risk_order[x])
        dyslexia_score = max([reading_level, attention_level], key=lambda x: risk_order[x])
        adhd_score = max([attention_level, behavior_level], key=lambda x: risk_order[x])

        def recommendation(score):
            return {
                "High": "Seek professional evaluation and intensive support.",
                "Medium": "Provide extra attention and practice activities.",
                "Low": "Continue regular learning, monitor progress."
            }[score]

        rec_text = generate_insight(reading_level, attention_level, behavior_level, child.age)

        # Save to DB
        test = StudentTest(
            child_id=child.id,
            teacher_id=session["teacher_id"],
            reading_score=int(data['reading_score']),
            attention_score=int(data['attention_score']),
            behavior_score=int(data['behavior_score']),
            reading_level=reading_level,
            attention_level=attention_level,
            behavior_level=behavior_level,
            overall_risk=overall_risk,
            recommendations=rec_text
        )
        db.session.add(test)
        db.session.commit()

        # Next level
        next_level_map = {"low":"medium","medium":"high","high":None}
        next_level = next_level_map[level]

        redirect_url = url_for("conduct_test", child_id=child.id, level=next_level) if next_level else url_for("overall_report", child_id=child.id)

        return jsonify({
            "reading_level": reading_level,
            "attention_level": attention_level,
            "behavior_level": behavior_level,
            "dyslexia_score": dyslexia_score,
            "adhd_score": adhd_score,
            "overall_risk": overall_risk,
            "recommendations": rec_text,
            "redirect": redirect_url
        })

    return render_template("conduct_test.html", child=child, level=level, game_data=game_data, age_group=age_group)



@app.route("/teacher/overall_report/<int:child_id>")
def overall_report(child_id):
    child = Child.query.get_or_404(child_id)
    # Get all tests for this child, ordered by date
    tests = StudentTest.query.filter_by(child_id=child.id).order_by(StudentTest.date).all()
    return render_template("overall_report.html", child=child, tests=tests)



@app.route("/teacher/test_report/<int:child_id>")
def test_report(child_id):
    result = test_results.get(child_id)
    if not result:
        return "Test not found", 404
    return render_template("test_report.html",
                           child=result["child"],
                           reading_score=result["reading_score"],
                           attention_score=result["attention_score"],
                           behavior_score=result["behavior_score"],
                           dyslexia_score=result["dyslexia_score"],
                           adhd_score=result["adhd_score"],
                           overall_risk=result["overall_risk"],
                           recommendations=result["recommendations"])

# ------------------- REGENERATE GAME DATA -------------------
@app.route("/teacher/regenerate_game_data/<int:child_id>/<level>")
def regenerate_game_data_api(child_id, level):
    child = Child.query.get_or_404(child_id)
    # Re-use the data generator (extract it to global scope if needed, or just duplicate the logic briefly)
    # Simply redirect back to conduct_test to reload everything cleanly with new random values
    return redirect(url_for('conduct_test', child_id=child.id, level=level))


import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from pydub import AudioSegment



# Ensure upload folder exists
UPLOAD_FOLDER = "static/recordings"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions
ALLOWED_EXTENSIONS = {'webm', 'wav', 'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Reading Audio Endpoint ----------
@app.route('/process_reading_audio', methods=['POST'])
def process_reading_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if audio_file and allowed_file(audio_file.filename):
        filename = secure_filename(audio_file.filename)
        webm_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(webm_path)

        # Convert to WAV
        try:
            wav_filename = filename.rsplit('.', 1)[0] + ".wav"
            wav_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
            audio = AudioSegment.from_file(webm_path, format="webm")
            audio.export(wav_path, format="wav")
        except Exception as e:
            return jsonify({'error': f'Error converting audio: {str(e)}'}), 500

        # --- Dummy scoring logic ---
        # Replace with your speech recognition / scoring
        import random
        score_level = random.randint(1, 3)  # 1=Low, 2=Medium, 3=High

        return jsonify({'score_level': score_level, 'recognized_text': 'Dummy text'})

    return jsonify({'error': 'Invalid file type'}), 400


@app.route("/test_ffmpeg")
def test_ffmpeg():
    return jsonify({
        "ffmpeg": ffmpeg_path or "NOT FOUND",
        "ffprobe": ffprobe_path or "NOT FOUND"
    })


@app.route('/process_attention', methods=['POST'])
def process_attention():
    clicks = int(request.json.get('clicks',0))
    total_targets = int(request.json.get('total_targets',10))
    score = calculate_attention_score(clicks, total_targets)
    return jsonify({'score':score})

@app.route('/process_behavior', methods=['POST'])
def process_behavior():
    # Placeholder for behavior score, real implementation would use webcam AI
    score = calculate_behavior_score(activity_level=1)
    return jsonify({'score':score})

# ------------------- PARENT ROUTES ----------------
@app.route("/parent_register", methods=["GET","POST"])
def parent_register():
    if request.method=="POST":
        try:
            # Check for existing user
            existing = Parent.query.filter_by(username=request.form["username"]).first()
            if existing:
                flash("Parent with this username already exists.", "danger")
                return redirect(url_for("parent_register"))

            parent = Parent(
                name=request.form["name"],
                email=request.form["email"],
                mobile=request.form["mobile"],
                dob=datetime.strptime(request.form["dob"], "%Y-%m-%d"),
                location=request.form["location"],
                username=request.form["username"],
                password=hash_password(request.form["password"])
            )
            db.session.add(parent)
            db.session.commit()
            flash("Parent registered successfully. Please login.","success")
            return redirect(url_for("parent_login"))
        except Exception as e:
            db.session.rollback()
            print("Error registering parent:", e)
            flash("Error during registration.", "danger")
            return redirect(url_for("parent_register"))
    return render_template("parent_register.html")

@app.route("/parent_login", methods=["GET","POST"])
def parent_login():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        parent = Parent.query.filter_by(username=username).first()
        if parent and (verify_password(parent.password, password) or parent.password == password):
            session["parent_id"] = parent.id
            return redirect(url_for("parent_dashboard"))
        else:
            flash("Invalid credentials","danger")
    return render_template("parent_login.html")

@app.route("/parent/dashboard")
def parent_dashboard():
    if "parent_id" not in session:
        return redirect(url_for("parent_login"))
    children = Child.query.filter_by(parent_id=session["parent_id"]).all()
    return render_template("parent_dashboard.html", children=children)

@app.route("/parent/add_child", methods=["GET","POST"])
def add_child():
    if "parent_id" not in session:
        return redirect(url_for("parent_login"))
    if request.method=="POST":
        child = Child(
            parent_id=session["parent_id"],
            name=request.form["name"],
            email=request.form["email"],
            mobile=request.form["mobile"],
            age=int(request.form["age"]),
            gender=request.form["gender"],
            student_class=request.form["student_class"],
            dob=datetime.strptime(request.form["dob"], "%Y-%m-%d")
        )
        db.session.add(child)
        db.session.commit()
        flash("Child added successfully","success")
        return redirect("/parent/dashboard")
    return render_template("add_child.html")


@app.route("/teacher/submit_test/<int:child_id>/<level>", methods=["POST"])
def submit_test(child_id, level):
    if "teacher_id" not in session:
        return redirect(url_for("teacher_login"))

    child = Child.query.get_or_404(child_id)
    data = request.get_json()

    # Convert numeric score (1-3) to Risk Level. 
    # 1 (Low Performance) = High Risk of Disorder
    # 3 (High Performance) = Low Risk of Disorder
    def risk_level(value):
        if value == 1:
            return "High"
        elif value == 2:
            return "Medium"
        else:
            return "Low"

    # Calculate individual scores
    reading_score = risk_level(data['reading_score'])
    attention_score = risk_level(data['attention_score'])
    behavior_score = risk_level(data['behavior_score'])

    # Overall risk = highest among the three
    risk_order = {"Low":0, "Medium":1, "High":2}
    overall_risk = max([reading_score, attention_score, behavior_score], key=lambda x: risk_order[x])

    # Recommendations
    def generate_recommendation(score):
        return {
            "High":"Seek professional evaluation, use focused home activities.",
            "Medium":"Provide extra attention, practice reading and focus tasks.",
            "Low":"Continue regular learning, monitor progress."
        }[score]

    recommendations = generate_insight(reading_score, attention_score, behavior_score, child.age)

    # Save test in DB with levels
    test = StudentTest(
        child_id=child.id,
        teacher_id=session["teacher_id"],
        reading_score=risk_order[reading_score]*50,  # optional numeric representation
        attention_score=risk_order[attention_score]*50,
        behavior_score=risk_order[behavior_score]*50,
        reading_level=reading_score,
        attention_level=attention_score,
        behavior_level=behavior_score,
        overall_risk=overall_risk,
        recommendations=recommendations
    )
    db.session.add(test)
    db.session.commit()

    # Determine next level
    next_level_map = {"low":"medium","medium":"high","high":None}
    next_level = next_level_map[level]

    # Return redirect info
    if next_level:
        redirect_url = url_for('conduct_test', child_id=child.id, level=next_level)
    else:
        redirect_url = url_for('overall_report', child_id=child.id)

    return jsonify({
        "redirect": redirect_url,
        "overall_risk": overall_risk,
        "recommendations": recommendations
    })


@app.route("/parent/child_report/<int:child_id>")
def parent_child_report(child_id):
    if "parent_id" not in session:
        return redirect(url_for("parent_login"))
    
    # Fetch the child
    child = Child.query.get_or_404(child_id)
    
    # Ensure this child belongs to the logged-in parent
    if child.parent_id != session["parent_id"]:
        return "Unauthorized access", 403

    # Get all tests for chart
    tests = StudentTest.query.filter_by(child_id=child.id)\
                             .order_by(StudentTest.date)\
                             .all()
    latest_test = tests[-1] if tests else None
    
    return render_template("parent_child_report.html", child=child, latest_test=latest_test, tests=tests)

# -------------------------------
# ADMIN → VIEW ALL OVERALL REPORTS
# -------------------------------
@app.route("/admin/overall_reports")
def admin_overall_reports():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    # Fetch latest test per child
    from sqlalchemy import func

    latest_tests = (
        db.session.query(
            StudentTest.child_id,
            func.max(StudentTest.date).label("latest_date")
        )
        .group_by(StudentTest.child_id)
        .subquery()
    )

    reports = (
        db.session.query(StudentTest, Child, Parent)
        .join(latest_tests,
              (StudentTest.child_id == latest_tests.c.child_id) &
              (StudentTest.date == latest_tests.c.latest_date))
        .join(Child, StudentTest.child_id == Child.id)
        .join(Parent, Child.parent_id == Parent.id)
        .order_by(StudentTest.date.desc())
        .all()
    )

    return render_template("admin_overall_reports.html", reports=reports)

# ------------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ------------------- TRAINING RESOURCES ----------------
@app.route("/training_resources")
def training_resources():
    if "parent_id" not in session and "teacher_id" not in session and "admin_id" not in session:
        flash("Please log in to view training resources.", "danger")
        return redirect(url_for("index"))
    return render_template("training_resources.html")

@app.route("/cognitive_train")
def cognitive_train():
    if "parent_id" not in session and "teacher_id" not in session and "admin_id" not in session:
        flash("Please log in to access interactive training.", "danger")
        return redirect(url_for("index"))
    
    # Dynamic Dyslexia Scramble Challenge
    words = ["APPLE", "TRAIN", "HOUSE", "BRAIN", "FOCUS", "WATER"]
    target_word = random.choice(words)
    # create a subtle scramble
    letters = list(target_word)
    random.shuffle(letters)
    scrambled = "".join(letters)

    # Interactive ADHD Focus Math (Find the missing number in sequence)
    start = random.randint(2, 10)
    step = random.randint(2, 5)
    sequence = [start + i*step for i in range(5)]
    missing_index = random.randint(1, 3)
    answer = sequence[missing_index]
    sequence[missing_index] = "?"
    
    return render_template("train_mind.html", 
                           scrambled=scrambled, 
                           target_word=target_word,
                           sequence=sequence,
                           answer=answer)

# ------------------- RUN APP ----------------
if __name__=="__main__":
    with app.app_context():
        db.create_all()
        
        # Seed a default admin if none exists so you can log in immediately
        if not Admin.query.first():
            default_admin = Admin(
                username="admin", 
                password=hash_password("admin123")
            )
            db.session.add(default_admin)
            db.session.commit()
            print("=====================================================")
            print("[SUCCESS] DEFAULT ADMIN CREATED:")
            print("Username: admin")
            print("Password: admin123")
            print("=====================================================")
            
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
