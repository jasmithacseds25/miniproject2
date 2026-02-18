from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta, timezone
import sqlite3
import os
import functools

# Optional ML/image dependencies — keep classify feature optional so app runs without them
try:
    from PIL import Image  # type: ignore
    import numpy as np  # type: ignore
    import joblib  # type: ignore
    HAS_ML_DEPS = True
except Exception:
    # If not installed, classification will be disabled at runtime and user can install via requirements
    Image = None
    np = None
    joblib = None
    HAS_ML_DEPS = False

app = Flask(__name__)
app.secret_key = 'hospital_system_secret_key_2025'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Utility: convert UTC timestamps to IST for display
def utc_to_ist_filter(value, fmt="%Y-%m-%d %H:%M IST"):
    if not value:
        return ''
    s = str(value)
    s2 = s.replace(' ', 'T')
    try:
        dt = datetime.fromisoformat(s2)
    except Exception:
        try:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                dt = datetime.strptime(s, "%Y-%m-%d")
            except Exception:
                return s
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ist = dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
    try:
        return ist.strftime(fmt)
    except Exception:
        return ist.strftime("%Y-%m-%d %H:%M IST")

# Register the filter for Jinja templates
app.jinja_env.filters['utc_to_ist'] = utc_to_ist_filter

DATABASE = 'hospital_system.db'
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'profiles')  # profile pics and temp files
REPORTS_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'reports')  # scans & reports
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'dcm'}

# Ensure upload folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== DATABASE INITIALIZATION ====================
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables"""
    db = get_db()
    db.executescript('''
    -- Doctors Table
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        specialization TEXT NOT NULL,
        license_number TEXT UNIQUE NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Patients Table
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
        gender TEXT,
        blood_group TEXT,
        phone TEXT,
        address TEXT,
        emergency_contact TEXT,
        medical_history TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Medical Records Table
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        visit_date TEXT NOT NULL,
        diagnosis TEXT NOT NULL,
        symptoms TEXT,
        treatment TEXT,
        medications TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );

    -- Reports Table
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        report_type TEXT NOT NULL,
        report_date TEXT NOT NULL,
        findings TEXT NOT NULL,
        recommendations TEXT,
        status TEXT DEFAULT 'Completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );

    -- Prescriptions Table
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        medication_name TEXT NOT NULL,
        dosage TEXT NOT NULL,
        frequency TEXT NOT NULL,
        duration TEXT NOT NULL,
        prescribed_date TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );

    -- Messages Table (Patient-Doctor Chat)
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        sender_type TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );

    -- Appointments Table
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_datetime TEXT NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'Scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );

    -- Doctor Access Logs (for transparency)
    CREATE TABLE IF NOT EXISTS doctor_access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        accessed_at TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );
    ''')
    db.commit()
    db.close()

    # Ensure prescriptions table has schedule columns (timeslots, meal_relation)
    db = get_db()
    try:
        db.execute('ALTER TABLE prescriptions ADD COLUMN timeslots TEXT')
    except sqlite3.OperationalError:
        # column already exists
        pass

    try:
        db.execute("ALTER TABLE prescriptions ADD COLUMN meal_relation TEXT DEFAULT 'Any'")
    except sqlite3.OperationalError:
        pass

    # Table to store which medication was taken on which date and timeslot
    db.execute('''
    CREATE TABLE IF NOT EXISTS medication_taken (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prescription_id INTEGER NOT NULL,
        taken_date TEXT NOT NULL,
        timeslot TEXT NOT NULL,
        taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
    );
    ''')
    db.commit()

    # Ensure submitted column exists (0/1). Safe to run on existing DBs.
    try:
        db.execute('ALTER TABLE medication_taken ADD COLUMN submitted INTEGER DEFAULT 0')
        db.commit()
    except sqlite3.OperationalError:
        # column already exists
        pass

    # Table to store patient-uploaded files (scans/reports)
    db.execute('''
    CREATE TABLE IF NOT EXISTS patient_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        file_type TEXT NOT NULL,
        filename TEXT NOT NULL,
        original_filename TEXT,
        report_date TEXT,
        notes TEXT,
        uploaded_by TEXT DEFAULT 'patient',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    );
    ''')
    db.commit()

    db.close()

    # Ensure profile_pic column exists for patients and doctors (safe to run)
    db = get_db()
    try:
        db.execute("ALTER TABLE patients ADD COLUMN profile_pic TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        db.execute("ALTER TABLE doctors ADD COLUMN profile_pic TEXT")
    except sqlite3.OperationalError:
        pass
    # Ensure doctors have a gender column to support gender-aware defaults
    try:
        db.execute("ALTER TABLE doctors ADD COLUMN gender TEXT")
    except sqlite3.OperationalError:
        pass
    db.commit()
    db.close()

# ==================== AUTHENTICATION DECORATORS ====================
def login_required_doctor(f):
    """Decorator to require doctor login"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'doctor_id' not in session:
            flash('Please login as a doctor first', 'error')
            return redirect(url_for('doctor_login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_patient(f):
    """Decorator to require patient login"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'patient_id' not in session:
            flash('Please login as a patient first', 'error')
            return redirect(url_for('patient_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== HOME ROUTES ====================
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/avatars')
def avatars():
    """Preview avatar icons"""
    return render_template('avatars.html')


@app.route('/doctors')
def doctors_list():
    """List all registered doctors"""
    db = get_db()
    doctors = db.execute('SELECT id, name, specialization, profile_pic FROM doctors ORDER BY name').fetchall()
    db.close()
    return render_template('doctors.html', doctors=doctors)


@app.route('/classify', methods=['GET', 'POST'])
def classify():
    """Upload an image and run the baseline hair-shape classifier (if trained)"""
    result = None
    model_path = os.path.join(app.root_path, 'models', 'svm_hair_baseline.pkl')
    if request.method == 'POST':
        if not HAS_ML_DEPS:
            flash('Image classification packages not installed. Install "numpy", "Pillow", and "joblib" to enable this feature.', 'error')
        else:
            file = request.files.get('image')
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                tmp_path = os.path.join(UPLOAD_FOLDER, f"tmp_{uuid.uuid4().hex}_{filename}")
                file.save(tmp_path)
                try:
                    im = Image.open(tmp_path).convert('L').resize((32,32))
                    x = np.asarray(im, dtype=np.float32).flatten()/255.0
                    if os.path.exists(model_path):
                        obj = joblib.load(model_path)
                        scaler = obj['scaler']
                        clf = obj['model']
                        label_map = obj['label_map']
                        x_s = scaler.transform([x])
                        probs = clf.predict_proba(x_s)[0]
                        pred = int(clf.predict(x_s)[0])
                        result = {'label': label_map[pred], 'prob': float(probs[pred])}
                    else:
                        flash('Model not trained yet. Run the training script first.', 'warning')
                except Exception as e:
                    flash('Failed to process image: ' + str(e), 'error')
                finally:
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
            else:
                flash('No valid image uploaded', 'error')
    return render_template('classify.html', result=result)

# ==================== DOCTOR ROUTES ====================
@app.route('/doctor/register', methods=['GET', 'POST'])
def doctor_register():
    """Doctor registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        specialization = request.form.get('specialization')
        license_number = request.form.get('license_number')
        phone = request.form.get('phone')
        gender = request.form.get('gender')

        # Validation
        if not all([name, email, password, specialization, license_number]):
            flash('All fields are required', 'error')
            return redirect(url_for('doctor_register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('doctor_register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('doctor_register'))

        if not license_number.isdigit() or len(license_number) != 8:
            flash('License number must be exactly 8 digits', 'error')
            return redirect(url_for('doctor_register'))

        profile_file = request.files.get('profile_pic')
        db = get_db()
        try:
            cur = db.execute(
                'INSERT INTO doctors (name, email, password, specialization, license_number, phone, gender) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (name, email, generate_password_hash(password), specialization, license_number, phone, gender)
            )
            doctor_id = cur.lastrowid

            # handle profile image
            if profile_file and profile_file.filename and allowed_file(profile_file.filename):
                ext = secure_filename(profile_file.filename).rsplit('.', 1)[1].lower()
                filename = f"doctor_{doctor_id}_{uuid.uuid4().hex}.{ext}"
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                profile_file.save(save_path)
                db.execute('UPDATE doctors SET profile_pic = ? WHERE id = ?', (filename, doctor_id))

            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('doctor_login'))
        except sqlite3.IntegrityError:
            db.rollback()
            flash('Email or license number already exists', 'error')
        finally:
            db.close()

    return render_template('doctor_register.html')

@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    """Doctor login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password required', 'error')
            return redirect(url_for('doctor_login'))

        db = get_db()
        doctor = db.execute('SELECT * FROM doctors WHERE email = ?', (email,)).fetchone()
        db.close()

        if doctor and check_password_hash(doctor['password'], password):
            session.permanent = True
            session['doctor_id'] = doctor['id']
            session['doctor_name'] = doctor['name']
            session['doctor_profile_pic'] = doctor['profile_pic']
            # sqlite3.Row doesn't have .get() — use indexing and check keys() for presence
            session['doctor_gender'] = doctor['gender'] if 'gender' in doctor.keys() else None
            session['specialization'] = doctor['specialization'] if 'specialization' in doctor.keys() else None
            session['doctor_email'] = doctor['email']
            flash(f'Welcome, Dr. {doctor["name"]}!', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('doctor_login.html')

@app.route('/doctor/dashboard')
@login_required_doctor
def doctor_dashboard():
    """Doctor dashboard"""
    db = get_db()
    
    # Get statistics
    total_patients = db.execute(
        'SELECT COUNT(DISTINCT patient_id) as count FROM medical_records WHERE doctor_id = ?',
        (session['doctor_id'],)
    ).fetchone()['count']
    
    total_records = db.execute(
        'SELECT COUNT(*) as count FROM medical_records WHERE doctor_id = ?',
        (session['doctor_id'],)
    ).fetchone()['count']
    
    total_reports = db.execute(
        'SELECT COUNT(*) as count FROM reports WHERE doctor_id = ?',
        (session['doctor_id'],)
    ).fetchone()['count']
    
    # Get recent records
    recent_records = db.execute(
        '''SELECT mr.*, p.name as patient_name 
           FROM medical_records mr 
           JOIN patients p ON mr.patient_id = p.id 
           WHERE mr.doctor_id = ? 
           ORDER BY mr.visit_date DESC LIMIT 5''',
        (session['doctor_id'],)
    ).fetchall()
    
    # Get unread messages from patients
    unread_messages = db.execute(
        '''SELECT m.*, p.name as patient_name 
           FROM messages m 
           JOIN patients p ON m.patient_id = p.id 
           WHERE m.doctor_id = ? AND m.sender_type = 'patient' AND m.is_read = 0
           ORDER BY m.created_at DESC''',
        (session['doctor_id'],)
    ).fetchall()
    
    # Mark messages as read
    if unread_messages:
        db.execute(
            '''UPDATE messages 
               SET is_read = 1 
               WHERE doctor_id = ? AND sender_type = 'patient' AND is_read = 0''',
            (session['doctor_id'],)
        )
        db.commit()
    
    db.close()

    return render_template('doctor_dashboard.html',
                         total_patients=total_patients,
                         total_records=total_records,
                         total_reports=total_reports,
                         recent_records=recent_records,
                         unread_messages=unread_messages)

@app.route('/doctor/patients')
@login_required_doctor
def doctor_patients():
    """View all patients treated by the doctor"""
    db = get_db()
    
    # Get unique patients treated by this doctor
    patients = db.execute(
        '''SELECT DISTINCT p.* 
           FROM patients p 
           JOIN medical_records mr ON p.id = mr.patient_id 
           WHERE mr.doctor_id = ? 
           ORDER BY p.name''',
        (session['doctor_id'],)
    ).fetchall()
    
    db.close()
    return render_template('doctor_patients.html', patients=patients)

@app.route('/doctor/patient/<int:patient_id>')
@login_required_doctor
def doctor_patient_detail(patient_id):
    """View patient details and records"""
    db = get_db()
    
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    
    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_patients'))

    # Log doctor access for transparency
    try:
        accessed_at = datetime.utcnow().isoformat()
        db.execute(
            'INSERT INTO doctor_access_logs (patient_id, doctor_id, action, accessed_at) VALUES (?, ?, ?, ?)',
            (patient_id, session.get('doctor_id'), 'view_patient_detail', accessed_at)
        )
        db.commit()
    except Exception:
        # Don't break functionality if logging fails
        db.rollback()
    
    # Get medical records for this patient by this doctor
    records = db.execute(
        '''SELECT * FROM medical_records 
           WHERE patient_id = ? AND doctor_id = ? 
           ORDER BY visit_date DESC''',
        (patient_id, session['doctor_id'])
    ).fetchall()
    
    # Get reports
    reports = db.execute(
        '''SELECT * FROM reports 
           WHERE patient_id = ? AND doctor_id = ? 
           ORDER BY report_date DESC''',
        (patient_id, session['doctor_id'])
    ).fetchall()
    
    # Get prescriptions
    prescriptions = db.execute(
        '''SELECT * FROM prescriptions 
           WHERE patient_id = ? AND doctor_id = ? 
           ORDER BY prescribed_date DESC''',
        (patient_id, session['doctor_id'])
    ).fetchall()
    
    db.close()

    return render_template('doctor_patient_detail.html',
                         patient=patient,
                         records=records,
                         reports=reports,
                         prescriptions=prescriptions)

@app.route('/doctor/add-record/<int:patient_id>', methods=['GET', 'POST'])
@login_required_doctor
def add_medical_record(patient_id):
    """Add medical record for a patient"""
    db = get_db()
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    db.close()

    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_patients'))

    if request.method == 'POST':
        visit_date = request.form.get('visit_date')
        diagnosis = request.form.get('diagnosis')
        symptoms = request.form.get('symptoms')
        treatment = request.form.get('treatment')
        medications = request.form.get('medications')
        notes = request.form.get('notes')

        if not all([visit_date, diagnosis]):
            flash('Visit date and diagnosis are required', 'error')
            return redirect(url_for('add_medical_record', patient_id=patient_id))

        db = get_db()
        db.execute(
            '''INSERT INTO medical_records 
               (patient_id, doctor_id, visit_date, diagnosis, symptoms, treatment, medications, notes) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (patient_id, session['doctor_id'], visit_date, diagnosis, symptoms, treatment, medications, notes)
        )
        db.commit()
        db.close()

        flash('Medical record added successfully', 'success')
        return redirect(url_for('doctor_patient_detail', patient_id=patient_id))

    return render_template('add_medical_record.html', patient=patient)

@app.route('/doctor/add-report/<int:patient_id>', methods=['GET', 'POST'])
@login_required_doctor
def add_report(patient_id):
    """Add report for a patient"""
    db = get_db()
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    db.close()

    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_patients'))

    if request.method == 'POST':
        report_type = request.form.get('report_type')
        report_date = request.form.get('report_date')
        findings = request.form.get('findings')
        recommendations = request.form.get('recommendations')
        status = request.form.get('status', 'Completed')

        if not all([report_type, report_date, findings]):
            flash('Report type, date, and findings are required', 'error')
            return redirect(url_for('add_report', patient_id=patient_id))

        db = get_db()
        db.execute(
            '''INSERT INTO reports 
               (patient_id, doctor_id, report_type, report_date, findings, recommendations, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (patient_id, session['doctor_id'], report_type, report_date, findings, recommendations, status)
        )
        db.commit()
        db.close()

        flash('Report added successfully', 'success')
        return redirect(url_for('doctor_patient_detail', patient_id=patient_id))

    return render_template('add_report.html', patient=patient)

@app.route('/doctor/add-prescription/<int:patient_id>', methods=['GET', 'POST'])
@login_required_doctor
def add_prescription(patient_id):
    """Add prescription for a patient"""
    db = get_db()
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    db.close()

    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_patients'))

    if request.method == 'POST':
        medication_name = request.form.get('medication_name')
        dosage = request.form.get('dosage')
        frequency = request.form.get('frequency')
        duration = request.form.get('duration')
        prescribed_date = request.form.get('prescribed_date')
        notes = request.form.get('notes')
        timeslots = request.form.getlist('timeslots')  # e.g., ['morning','evening']
        meal_relation = request.form.get('meal_relation') or 'Any'

        if not all([medication_name, dosage, frequency, duration, prescribed_date]):
            flash('All fields are required', 'error')
            return redirect(url_for('add_prescription', patient_id=patient_id))

        # store timeslots as comma separated string
        timeslots_str = ','.join(timeslots) if timeslots else None

        db = get_db()
        db.execute(
            '''INSERT INTO prescriptions 
               (patient_id, doctor_id, medication_name, dosage, frequency, duration, prescribed_date, notes, timeslots, meal_relation) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (patient_id, session['doctor_id'], medication_name, dosage, frequency, duration, prescribed_date, notes, timeslots_str, meal_relation)
        )
        db.commit()
        db.close()

        flash('Prescription added successfully', 'success')
        return redirect(url_for('doctor_patient_detail', patient_id=patient_id))

    return render_template('add_prescription.html', patient=patient)


@app.route('/doctor/add-appointment/<int:patient_id>', methods=['GET', 'POST'])
@login_required_doctor
def add_appointment(patient_id):
    """Schedule an appointment for a patient"""
    db = get_db()
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        flash('Patient not found', 'error')
        db.close()
        return redirect(url_for('doctor_patients'))

    if request.method == 'POST':
        appointment_datetime = request.form.get('appointment_datetime')
        reason = request.form.get('reason')

        if not appointment_datetime:
            flash('Appointment date and time are required', 'error')
            return redirect(url_for('add_appointment', patient_id=patient_id))

        db.execute(
            '''INSERT INTO appointments (patient_id, doctor_id, appointment_datetime, reason) 
               VALUES (?, ?, ?, ?)''',
            (patient_id, session['doctor_id'], appointment_datetime, reason)
        )
        db.commit()
        db.close()

        flash('Appointment scheduled successfully', 'success')
        return redirect(url_for('doctor_patient_detail', patient_id=patient_id))

    db.close()
    return render_template('add_appointment.html', patient=patient)


@app.route('/patient/appointments')
@login_required_patient
def patient_appointments():
    """View a patient's appointments"""
    db = get_db()
    upcoming = db.execute(
        '''SELECT a.*, d.name as doctor_name 
           FROM appointments a 
           JOIN doctors d ON a.doctor_id = d.id 
           WHERE a.patient_id = ? AND a.appointment_datetime >= ? 
           ORDER BY a.appointment_datetime ASC''',
        (session['patient_id'], datetime.utcnow().isoformat())
    ).fetchall()

    past = db.execute(
        '''SELECT a.*, d.name as doctor_name 
           FROM appointments a 
           JOIN doctors d ON a.doctor_id = d.id 
           WHERE a.patient_id = ? AND a.appointment_datetime < ? 
           ORDER BY a.appointment_datetime DESC''',
        (session['patient_id'], datetime.utcnow().isoformat())
    ).fetchall()

    db.close()
    return render_template('patient_appointments.html', upcoming=upcoming, past=past)

@app.route('/patient/book-appointment', methods=['GET', 'POST'])
@login_required_patient
def book_appointment():
    """Allow a patient to book an appointment with a doctor"""
    db = get_db()

    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_datetime = request.form.get('appointment_datetime')
        reason = request.form.get('reason')

        if not doctor_id or not appointment_datetime:
            flash('Doctor and appointment date/time are required', 'error')
            return redirect(url_for('book_appointment'))

        # Validate datetime format and ensure it's not in the past
        try:
            dt = datetime.fromisoformat(appointment_datetime)
            if dt < datetime.utcnow():
                flash('Cannot book an appointment in the past', 'error')
                return redirect(url_for('book_appointment'))
        except Exception:
            flash('Invalid date/time format', 'error')
            return redirect(url_for('book_appointment'))

        # Ensure doctor exists
        doctor = db.execute('SELECT id FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
        if not doctor:
            flash('Selected doctor not found', 'error')
            return redirect(url_for('book_appointment'))

        # Basic conflict check: exact same datetime for doctor
        conflict = db.execute('SELECT id FROM appointments WHERE doctor_id = ? AND appointment_datetime = ?', (doctor_id, appointment_datetime)).fetchone()
        if conflict:
            flash('Selected time slot is already booked for this doctor', 'error')
            return redirect(url_for('book_appointment'))

        db.execute(
            'INSERT INTO appointments (patient_id, doctor_id, appointment_datetime, reason) VALUES (?, ?, ?, ?)',
            (session['patient_id'], doctor_id, appointment_datetime, reason)
        )
        db.commit()
        db.close()

        flash('Appointment booked successfully', 'success')
        return redirect(url_for('patient_appointments'))

    # GET: list doctors
    doctors = db.execute('SELECT id, name, specialization FROM doctors ORDER BY name').fetchall()
    db.close()
    return render_template('book_appointment.html', doctors=doctors)

@app.route('/doctor/logout')
def doctor_logout():
    """Doctor logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

# ==================== PATIENT ROUTES ====================
@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    """Patient registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        blood_group = request.form.get('blood_group')
        phone = request.form.get('phone')
        address = request.form.get('address')
        emergency_contact = request.form.get('emergency_contact')
        profile_file = request.files.get('profile_pic')

        # Validation
        if not all([name, email, password, date_of_birth]):
            flash('Required fields are missing', 'error')
            return redirect(url_for('patient_register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('patient_register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('patient_register'))

        db = get_db()
        try:
            cur = db.execute(
                '''INSERT INTO patients 
                   (name, email, password, date_of_birth, gender, blood_group, phone, address, emergency_contact) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, email, generate_password_hash(password), date_of_birth, gender, blood_group, phone, address, emergency_contact)
            )
            patient_id = cur.lastrowid

            # Handle profile image upload
            if profile_file and profile_file.filename and allowed_file(profile_file.filename):
                ext = secure_filename(profile_file.filename).rsplit('.', 1)[1].lower()
                filename = f"patient_{patient_id}_{uuid.uuid4().hex}.{ext}"
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                profile_file.save(save_path)
                db.execute('UPDATE patients SET profile_pic = ? WHERE id = ?', (filename, patient_id))

            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('patient_login'))
        except sqlite3.IntegrityError:
            db.rollback()
            flash('Email already exists', 'error')
            return redirect(url_for('patient_register'))
        finally:
            db.close()
    
    return render_template('patient_register.html')

@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    """Patient login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password required', 'error')
            return redirect(url_for('patient_login'))

        db = get_db()
        patient = db.execute('SELECT * FROM patients WHERE email = ?', (email,)).fetchone()
        db.close()

        if patient and check_password_hash(patient['password'], password):
            session.permanent = True
            session['patient_id'] = patient['id']
            session['patient_name'] = patient['name']
            session['patient_email'] = patient['email']
            session['patient_gender'] = patient['gender']
            session['patient_profile_pic'] = patient['profile_pic']
            flash(f'Welcome, {patient["name"]}!', 'success')
            return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('patient_login.html')

@app.route('/patient/dashboard')
@login_required_patient
def patient_dashboard():
    """Patient dashboard"""
    db = get_db()
    
    # Get patient info
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (session['patient_id'],)).fetchone()
    
    # Get statistics
    total_visits = db.execute(
        'SELECT COUNT(*) as count FROM medical_records WHERE patient_id = ?',
        (session['patient_id'],)
    ).fetchone()['count']
    
    total_reports = db.execute(
        'SELECT COUNT(*) as count FROM reports WHERE patient_id = ?',
        (session['patient_id'],)
    ).fetchone()['count']
    
    total_prescriptions = db.execute(
        'SELECT COUNT(*) as count FROM prescriptions WHERE patient_id = ?',
        (session['patient_id'],)
    ).fetchone()['count']
    
    # Get recent records
    recent_records = db.execute(
        '''SELECT mr.*, d.name as doctor_name, d.specialization 
           FROM medical_records mr 
           JOIN doctors d ON mr.doctor_id = d.id 
           WHERE mr.patient_id = ? 
           ORDER BY mr.visit_date DESC LIMIT 5''',
        (session['patient_id'],)
    ).fetchall()

    # Get next upcoming appointment
    now_iso = datetime.utcnow().isoformat()
    next_appointment = db.execute(
        '''SELECT a.*, d.name as doctor_name, d.specialization 
           FROM appointments a 
           JOIN doctors d ON a.doctor_id = d.id 
           WHERE a.patient_id = ? AND a.appointment_datetime >= ? 
           ORDER BY a.appointment_datetime ASC LIMIT 1''',
        (session['patient_id'], now_iso)
    ).fetchone()

    # Get recent access logs (who viewed patient's page)
    access_logs = db.execute(
        '''SELECT l.*, d.name as doctor_name 
           FROM doctor_access_logs l 
           JOIN doctors d ON l.doctor_id = d.id 
           WHERE l.patient_id = ? 
           ORDER BY l.accessed_at DESC LIMIT 10''',
        (session['patient_id'],)
    ).fetchall()

    # Today's scheduled medications (simple approach: any prescription with timeslots configured)
    scheduled_meds = []
    today = datetime.utcnow().date().isoformat()
    meds = db.execute(
        '''SELECT p.*, d.name as doctor_name 
           FROM prescriptions p 
           JOIN doctors d ON p.doctor_id = d.id 
           WHERE p.patient_id = ? AND p.timeslots IS NOT NULL AND p.timeslots != ''
           ORDER BY p.prescribed_date DESC''',
        (session['patient_id'],)
    ).fetchall()

    for m in meds:
        m = dict(m)
        timeslots = [t for t in (m.get('timeslots') or '').split(',') if t]
        taken_rows = db.execute('SELECT timeslot, submitted FROM medication_taken WHERE prescription_id = ? AND taken_date = ?', (m['id'], today)).fetchall()
        taken_set = set([r['timeslot'] for r in taken_rows])
        submitted_set = set([r['timeslot'] for r in taken_rows if r['submitted']])
        m['timeslot_list'] = timeslots
        m['taken_today'] = taken_set
        m['submitted'] = bool(submitted_set)
        m['submitted_timeslots'] = submitted_set
        scheduled_meds.append(m)
    
    db.close()

    return render_template('patient_dashboard.html',
                         patient=patient,
                         total_visits=total_visits,
                         total_reports=total_reports,
                         total_prescriptions=total_prescriptions,
                         recent_records=recent_records,
                         next_appointment=next_appointment,
                         access_logs=access_logs,
                         scheduled_meds=scheduled_meds)

@app.route('/patient/medical-records')
@login_required_patient
def patient_medical_records():
    """View patient's medical records"""
    db = get_db()
    
    records = db.execute(
        '''SELECT mr.*, d.name as doctor_name, d.specialization 
           FROM medical_records mr 
           JOIN doctors d ON mr.doctor_id = d.id 
           WHERE mr.patient_id = ? 
           ORDER BY mr.visit_date DESC''',
        (session['patient_id'],)
    ).fetchall()
    
    db.close()
    return render_template('patient_medical_records.html', records=records)

@app.route('/patient/reports')
@login_required_patient
def patient_reports():
    """View patient's reports"""
    db = get_db()
    
    reports = db.execute(
        '''SELECT r.*, d.name as doctor_name, d.specialization 
           FROM reports r 
           JOIN doctors d ON r.doctor_id = d.id 
           WHERE r.patient_id = ? 
           ORDER BY r.report_date DESC''',
        (session['patient_id'],)
    ).fetchall()

    # fetch patient-uploaded files
    uploads = db.execute(
        'SELECT * FROM patient_files WHERE patient_id = ? ORDER BY uploaded_at DESC',
        (session['patient_id'],)
    ).fetchall()
    
    db.close()
    return render_template('patient_reports.html', reports=reports, uploads=uploads)

@app.route('/patient/prescriptions')
@login_required_patient
def patient_prescriptions():
    """View patient's prescriptions"""
    db = get_db()
    
    prescriptions_raw = db.execute(
        '''SELECT p.*, d.name as doctor_name 
           FROM prescriptions p 
           JOIN doctors d ON p.doctor_id = d.id 
           WHERE p.patient_id = ? 
           ORDER BY p.prescribed_date DESC''',
        (session['patient_id'],)
    ).fetchall()

    # Convert to list of dicts and attach schedule + today's taken status
    prescriptions = []
    today = datetime.utcnow().date().isoformat()
    for p in prescriptions_raw:
        p = dict(p)
        timeslots = []
        if p.get('timeslots'):
            timeslots = [t for t in p['timeslots'].split(',') if t]
        p['timeslot_list'] = timeslots

        # fetch taken timeslots for today and submission flag
        taken_rows = db.execute(
            'SELECT timeslot, submitted FROM medication_taken WHERE prescription_id = ? AND taken_date = ?',
            (p['id'], today)
        ).fetchall()
        taken_set = set([r['timeslot'] for r in taken_rows])
        # set of timeslots that have been submitted already
        submitted_set = set([r['timeslot'] for r in taken_rows if r['submitted']])
        p['taken_today'] = taken_set
        p['submitted'] = bool(submitted_set)
        p['submitted_timeslots'] = submitted_set

        prescriptions.append(p)

    db.close()
    return render_template('patient_prescriptions.html', prescriptions=prescriptions)

@app.route('/patient/profile')
@login_required_patient
def patient_profile():
    """View patient's profile"""
    db = get_db()
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (session['patient_id'],)).fetchone()
    db.close()
    return render_template('patient_profile.html', patient=patient)


@app.route('/patient/upload-file', methods=['POST'])
@login_required_patient
def patient_upload_file():
    """Allow patient to upload scans/reports"""
    file_type = request.form.get('file_type') or 'Other'
    report_date = request.form.get('report_date') or datetime.utcnow().date().isoformat()
    notes = request.form.get('notes')
    files = request.files.getlist('files')

    if not files or (len(files) == 1 and files[0].filename == ''):
        flash('No file selected', 'error')
        return redirect(url_for('patient_profile'))

    db = get_db()
    patient_id = session['patient_id']
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            orig = secure_filename(f.filename)
            ext = orig.rsplit('.', 1)[1].lower()
            filename = f"patient_{patient_id}_{uuid.uuid4().hex}.{ext}"
            save_path = os.path.join(REPORTS_UPLOAD_FOLDER, filename)
            f.save(save_path)
            db.execute('INSERT INTO patient_files (patient_id, file_type, filename, original_filename, report_date, notes) VALUES (?, ?, ?, ?, ?, ?)',
                       (patient_id, file_type, filename, orig, report_date, notes))
    db.commit()
    db.close()
    flash('Files uploaded successfully', 'success')
    return redirect(url_for('patient_reports'))


@app.route('/patient/delete-file/<int:file_id>', methods=['POST'])
@login_required_patient
def patient_delete_file(file_id):
    """Delete an uploaded file (only by the owner)"""
    db = get_db()
    cur = db.execute('SELECT * FROM patient_files WHERE id = ? AND patient_id = ?', (file_id, session['patient_id'])).fetchone()
    if not cur:
        db.close()
        flash('File not found', 'error')
        return redirect(url_for('patient_reports'))

    try:
        os.remove(os.path.join(REPORTS_UPLOAD_FOLDER, cur['filename']))
    except Exception:
        pass

    db.execute('DELETE FROM patient_files WHERE id = ?', (file_id,))
    db.commit()
    db.close()
    flash('File deleted', 'success')
    return redirect(url_for('patient_reports'))


@app.route('/doctor/profile')
@login_required_doctor
def doctor_profile():
    """View doctor's profile"""
    db = get_db()
    doctor = db.execute('SELECT * FROM doctors WHERE id = ?', (session['doctor_id'],)).fetchone()
    db.close()
    return render_template('doctor_profile.html', doctor=doctor)


@app.route('/doctor/update-profile', methods=['POST'])
@login_required_doctor
def update_doctor_profile():
    """Update doctor profile"""
    name = request.form.get('name')
    phone = request.form.get('phone')
    specialization = request.form.get('specialization')
    license_number = request.form.get('license_number')
    gender = request.form.get('gender')
    remove_pic = request.form.get('remove_profile_pic')
    profile_file = request.files.get('profile_pic')

    # Validate license number
    if not license_number.isdigit() or len(license_number) != 8:
        flash('License number must be exactly 8 digits', 'error')
        return redirect(url_for('doctor_profile'))

    db = get_db()
    # Update fields including name and gender
    db.execute(
        '''UPDATE doctors SET name = ?, phone = ?, specialization = ?, license_number = ?, gender = ? WHERE id = ?''',
        (name, phone, specialization, license_number, gender, session['doctor_id'])
    )

    # Handle remove picture request
    if remove_pic:
        try:
            cur = db.execute('SELECT profile_pic FROM doctors WHERE id = ?', (session['doctor_id'],)).fetchone()
            if cur and cur['profile_pic']:
                old_path = os.path.join(UPLOAD_FOLDER, cur['profile_pic'])
                try:
                    os.remove(old_path)
                except Exception:
                    pass
        except Exception:
            pass
        db.execute('UPDATE doctors SET profile_pic = NULL WHERE id = ?', (session['doctor_id'],))
        session['doctor_profile_pic'] = None

    # Handle profile picture upload
    if profile_file and profile_file.filename and allowed_file(profile_file.filename):
        ext = secure_filename(profile_file.filename).rsplit('.', 1)[1].lower()
        filename = f"doctor_{session['doctor_id']}_{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        profile_file.save(save_path)
        db.execute('UPDATE doctors SET profile_pic = ? WHERE id = ?', (filename, session['doctor_id']))
        session['doctor_profile_pic'] = filename

    db.commit()
    db.close()

    # Update session specialization, gender and name
    session['specialization'] = specialization
    session['doctor_gender'] = gender
    if name:
        session['doctor_name'] = name

    flash('Profile updated successfully', 'success')
    return redirect(url_for('doctor_profile'))


@app.route('/patient/mark-medication', methods=['POST'])
@login_required_patient
def mark_medication():
    """Mark or unmark a medication timeslot as taken for today"""
    data = request.get_json() or {}
    prescription_id = data.get('prescription_id')
    timeslot = data.get('timeslot')
    taken = int(data.get('taken', 0))

    if not prescription_id or not timeslot:
        return jsonify({'success': False, 'error': 'prescription_id and timeslot required'}), 400

    today = datetime.utcnow().date().isoformat()
    db = get_db()

    # verify prescription belongs to this patient
    row = db.execute('SELECT * FROM prescriptions WHERE id = ? AND patient_id = ?', (prescription_id, session['patient_id'])).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'error': 'Prescription not found'}), 404

    # if this timeslot has already been submitted, do not allow changes for that timeslot
    submitted_exists = db.execute('SELECT 1 FROM medication_taken WHERE prescription_id = ? AND taken_date = ? AND timeslot = ? AND submitted = 1', (prescription_id, today, timeslot)).fetchone()
    if submitted_exists:
        db.close()
        return jsonify({'success': False, 'error': 'This timeslot has been submitted and cannot be changed'}), 409

    if taken:
        # insert if not exists
        exists = db.execute('SELECT id FROM medication_taken WHERE prescription_id = ? AND taken_date = ? AND timeslot = ?', (prescription_id, today, timeslot)).fetchone()
        if not exists:
            db.execute('INSERT INTO medication_taken (prescription_id, taken_date, timeslot) VALUES (?, ?, ?)', (prescription_id, today, timeslot))
            db.commit()
        db.close()
        return jsonify({'success': True, 'status': 'taken'})
    else:
        # remove record
        db.execute('DELETE FROM medication_taken WHERE prescription_id = ? AND taken_date = ? AND timeslot = ?', (prescription_id, today, timeslot))
        db.commit()
        db.close()
        return jsonify({'success': True, 'status': 'removed'})

@app.route('/patient/submit-medication', methods=['POST'])
@login_required_patient
def submit_medication():
    """Submit today's medication entries so they become read-only"""
    data = request.get_json() or {}
    prescription_id = data.get('prescription_id')
    if not prescription_id:
        return jsonify({'success': False, 'error': 'prescription_id required'}), 400

    today = datetime.utcnow().date().isoformat()
    db = get_db()
    # verify prescription ownership
    row = db.execute('SELECT id FROM prescriptions WHERE id = ? AND patient_id = ?', (prescription_id, session['patient_id'])).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'error': 'Prescription not found'}), 404

    timeslot = data.get('timeslot')
    if timeslot:
        # submit single timeslot
        taken_row = db.execute('SELECT id FROM medication_taken WHERE prescription_id = ? AND taken_date = ? AND timeslot = ?', (prescription_id, today, timeslot)).fetchone()
        if not taken_row:
            db.close()
            return jsonify({'success': False, 'error': 'No taken entry for the specified timeslot'}), 400

        db.execute('UPDATE medication_taken SET submitted = 1 WHERE prescription_id = ? AND taken_date = ? AND timeslot = ?', (prescription_id, today, timeslot))
        db.commit()
        db.close()
        return jsonify({'success': True, 'status': 'submitted', 'timeslot': timeslot})
    else:
        # submit all taken entries for this prescription (backwards compatible)
        taken_row = db.execute('SELECT id FROM medication_taken WHERE prescription_id = ? AND taken_date = ?', (prescription_id, today)).fetchone()
        if not taken_row:
            db.close()
            return jsonify({'success': False, 'error': 'No taken entries to submit'}), 400

        db.execute('UPDATE medication_taken SET submitted = 1 WHERE prescription_id = ? AND taken_date = ?', (prescription_id, today))
        db.commit()
        db.close()
        return jsonify({'success': True, 'status': 'submitted'})


@app.route('/patient/update-profile', methods=['POST'])
@login_required_patient
def update_patient_profile():
    """Update patient profile"""
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    emergency_contact = request.form.get('emergency_contact')
    medical_history = request.form.get('medical_history')
    gender = request.form.get('gender')
    remove_pic = request.form.get('remove_profile_pic')
    profile_file = request.files.get('profile_pic')

    db = get_db()

    # Update core fields first (including name and gender)
    db.execute(
        '''UPDATE patients 
           SET name = ?, phone = ?, address = ?, emergency_contact = ?, medical_history = ?, gender = ? 
           WHERE id = ?''',
        (name, phone, address, emergency_contact, medical_history, gender, session['patient_id'])
    )

    # Handle remove picture request
    if remove_pic:
        try:
            cur = db.execute('SELECT profile_pic FROM patients WHERE id = ?', (session['patient_id'],)).fetchone()
            if cur and cur['profile_pic']:
                old_path = os.path.join(UPLOAD_FOLDER, cur['profile_pic'])
                try:
                    os.remove(old_path)
                except Exception:
                    pass
        except Exception:
            pass
        db.execute('UPDATE patients SET profile_pic = NULL WHERE id = ?', (session['patient_id'],))
        session['patient_profile_pic'] = None

    # Handle profile picture upload
    if profile_file and profile_file.filename and allowed_file(profile_file.filename):
        ext = secure_filename(profile_file.filename).rsplit('.', 1)[1].lower()
        filename = f"patient_{session['patient_id']}_{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        profile_file.save(save_path)
        db.execute('UPDATE patients SET profile_pic = ? WHERE id = ?', (filename, session['patient_id']))
        # Update session value so nav updates
        session['patient_profile_pic'] = filename

    db.commit()
    db.close()

    # Update patient gender and name in session
    session['patient_gender'] = gender
    if name:
        session['patient_name'] = name

    flash('Profile updated successfully', 'success')
    return redirect(url_for('patient_profile'))

@app.route('/patient/chat', methods=['GET', 'POST'])
@login_required_patient
def patient_chat():
    """Patient chat with doctor"""
    db = get_db()
    
    # Get all doctors the patient has records with
    doctors = db.execute(
        '''SELECT DISTINCT d.* 
           FROM doctors d 
           JOIN medical_records mr ON d.id = mr.doctor_id 
           WHERE mr.patient_id = ? 
           ORDER BY d.name''',
        (session['patient_id'],)
    ).fetchall()
    
    selected_doctor_id = request.args.get('doctor_id')
    messages = []
    
    if selected_doctor_id:
        # Get conversation with selected doctor
        messages = db.execute(
            '''SELECT * FROM messages 
               WHERE patient_id = ? AND doctor_id = ? 
               ORDER BY created_at ASC''',
            (session['patient_id'], int(selected_doctor_id))
        ).fetchall()
    
    if request.method == 'POST':
        message_text = request.form.get('message', '').strip()
        doctor_id = request.form.get('doctor_id')
        
        if message_text and doctor_id:
            db.execute(
                '''INSERT INTO messages (patient_id, doctor_id, sender_type, message) 
                   VALUES (?, ?, ?, ?)''',
                (session['patient_id'], int(doctor_id), 'patient', message_text)
            )
            db.commit()
            flash('Message sent successfully', 'success')
            selected_doctor_id = doctor_id
        
        # Refresh messages after sending
        messages = db.execute(
            '''SELECT * FROM messages 
               WHERE patient_id = ? AND doctor_id = ? 
               ORDER BY created_at ASC''',
            (session['patient_id'], int(selected_doctor_id))
        ).fetchall()
    
    db.close()
    return render_template('patient_chat.html', 
                          doctors=doctors, 
                          selected_doctor_id=selected_doctor_id,
                          messages=messages)

# Doctor chat with patient - reply feature
@app.route('/doctor/chat', methods=['GET', 'POST'])
@login_required_doctor
def doctor_chat():
    """Doctor chat with a selected patient"""
    db = get_db()

    # Get patients that this doctor has records with
    patients = db.execute(
        """SELECT DISTINCT p.*
           FROM patients p
           JOIN medical_records mr ON p.id = mr.patient_id
           WHERE mr.doctor_id = ?
           ORDER BY p.name""",
        (session['doctor_id'],)
    ).fetchall()

    selected_patient_id = request.args.get('patient_id')
    messages = []
    patient = None

    if selected_patient_id:
        # Ensure selected patient belongs to this doctor
        patient = db.execute('SELECT * FROM patients WHERE id = ?', (int(selected_patient_id),)).fetchone()
        owned = db.execute(
            'SELECT COUNT(*) as cnt FROM medical_records WHERE patient_id = ? AND doctor_id = ?',
            (int(selected_patient_id), session['doctor_id'])
        ).fetchone()['cnt']

        if not patient or owned == 0:
            flash('Patient not found or not under your care', 'error')
            return redirect(url_for('doctor_chat'))

        # Get conversation with selected patient
        messages = db.execute(
            '''SELECT * FROM messages 
               WHERE patient_id = ? AND doctor_id = ? 
               ORDER BY created_at ASC''',
            (int(selected_patient_id), session['doctor_id'])
        ).fetchall()

    if request.method == 'POST':
        message_text = request.form.get('message', '').strip()
        patient_id = request.form.get('patient_id')

        if message_text and patient_id:
            # Ensure patient is under this doctor
            owned = db.execute(
                'SELECT COUNT(*) as cnt FROM medical_records WHERE patient_id = ? AND doctor_id = ?',
                (int(patient_id), session['doctor_id'])
            ).fetchone()['cnt']

            if owned == 0:
                flash('Cannot send message to this patient', 'error')
            else:
                db.execute(
                    '''INSERT INTO messages (patient_id, doctor_id, sender_type, message) 
                       VALUES (?, ?, ?, ?)''',
                    (int(patient_id), session['doctor_id'], 'doctor', message_text)
                )
                db.commit()
                flash('Reply sent successfully', 'success')
                return redirect(url_for('doctor_chat', patient_id=patient_id))

    db.close()
    return render_template('doctor_chat.html',
                          patients=patients,
                          selected_patient_id=selected_patient_id,
                          messages=messages,
                          patient=patient)

@app.route('/patient/logout')
def patient_logout():
    """Patient logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

# ==================== API ENDPOINTS ====================
@app.route('/api/search-patients')
@login_required_doctor
def search_patients():
    """Search for patients"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    db = get_db()
    patients = db.execute(
        'SELECT id, name, email, date_of_birth FROM patients WHERE name LIKE ? OR email LIKE ? LIMIT 10',
        (f'%{query}%', f'%{query}%')
    ).fetchall()
    db.close()
    
    return jsonify([dict(p) for p in patients])

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

# ==================== INITIALIZATION ====================
if __name__ == '__main__':
    # Ensure database tables exist (runs safely even if DB exists)
    init_db()
    
    app.run(debug=True, host='127.0.0.1', port=5000)
