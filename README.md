# CareConnectHub

A comprehensive web-based hospital management system for managing patient health records, doctor logins, and medical reports.

## Features

### 🏥 Core Features
- **Doctor Portal**: Manage patient records, add diagnoses, prescriptions, and medical reports
- **Patient Portal**: Access personal medical history, reports, and prescriptions
- **Secure Authentication**: Password-protected accounts with session management
- **Medical Records Management**: Comprehensive digital medical records
- **Report Generation**: Create and view detailed medical reports
- **Prescription Tracking**: Manage medications with dosage and frequency information

### 👨‍⚕️ Doctor Features
- Register with license number and specialization
- View list of patients
- Add medical records for patients
- Create medical reports (Blood Test, X-Ray, MRI, etc.)
- Prescribe medications with dosage and frequency
- Dashboard with statistics and recent records
- Search functionality to find patients

### 👤 Patient Features
- Register with personal health information
- View medical history and records
- Access medical reports from doctors
- View current prescriptions
- Update personal profile and emergency contact
- Track all health-related information

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Server**: Python built-in server (development)

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone/Extract the project**
   ```bash
   cd patient_health
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and go to: `http://127.0.0.1:5000`

## Usage

### Doctor Registration
1. Go to Home page
2. Click "Doctor Register"
3. Fill in details: Name, Email, Specialization, License Number, Password
4. Click Register

### Doctor Login
1. Go to Home page
2. Click "Doctor Login"
3. Enter Email and Password
4. Access your dashboard

### Patient Registration
1. Go to Home page
2. Click "Patient Register"
3. Fill in personal health information
4. Create a password
5. Click Register

### Patient Login
1. Go to Home page
2. Click "Patient Login"
3. Enter Email and Password
4. Access your health records

### Adding Medical Records (Doctor)
1. Login as a doctor
2. Click "View All Patients"
3. Select a patient
4. Click "Add Medical Record"
5. Fill in diagnosis, symptoms, treatment, medications
6. Save

### Adding Reports (Doctor)
1. In Patient Details view
2. Click "Add Report"
3. Select report type (Blood Test, X-Ray, MRI, etc.)
4. Add findings and recommendations
5. Save

### Adding Prescriptions (Doctor)
1. In Patient Details view
2. Click "Add Prescription"
3. Enter medication details: name, dosage, frequency, duration
4. Add any special notes
5. Save

## Project Structure

```
patient_health/
├── app.py                      # Flask application (main file)
├── hospital_system.db          # SQLite database (auto-created)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/                  # HTML templates
│   ├── base.html              # Base template with navbar
│   ├── index.html             # Home page
│   ├── about.html             # About page
│   ├── doctor_register.html   # Doctor registration
│   ├── doctor_login.html      # Doctor login
│   ├── doctor_dashboard.html  # Doctor dashboard
│   ├── doctor_patients.html   # Patient list (doctor view)
│   ├── doctor_patient_detail.html  # Patient details
│   ├── add_medical_record.html     # Add medical record
│   ├── add_report.html        # Add medical report
│   ├── add_prescription.html  # Add prescription
│   ├── patient_register.html  # Patient registration
│   ├── patient_login.html     # Patient login
│   ├── patient_dashboard.html # Patient dashboard
│   ├── patient_medical_records.html # View records
│   ├── patient_reports.html   # View reports
│   ├── patient_prescriptions.html   # View prescriptions
│   ├── patient_profile.html   # Patient profile
│   ├── 404.html              # 404 error page
│   └── 500.html              # 500 error page
├── static/                     # Static files
│   ├── style.css             # CSS styling
│   └── script.js             # JavaScript functions
└── hospital_system.db          # SQLite database
```

## Database Schema

### Tables
- **doctors**: Doctor information and credentials
- **patients**: Patient information and health data
- **medical_records**: Doctor visit records with diagnosis and treatment
- **reports**: Medical reports (lab tests, imaging, etc.)
- **prescriptions**: Medication prescriptions with dosage information

## Security Features

- Password hashing using werkzeug.security
- Session-based authentication
- HTTP-only cookies
- Input validation on forms
- SQL injection prevention through parameterized queries

## Features in Detail

### Doctor Dashboard
- Total patients treated
- Total medical records created
- Total reports generated
- Quick access to recent records
- Patient search functionality

### Patient Dashboard
- Quick statistics (visits, reports, prescriptions)
- Recent medical visits
- Quick links to records, reports, prescriptions
- Profile summary

### Medical Records
- Visit date and diagnosis
- Symptoms and treatment details
- Medications prescribed
- Additional medical notes

### Reports
- Multiple report types (Blood Test, X-Ray, CT Scan, MRI, ECG, etc.)
- Detailed findings
- Recommendations
- Status tracking (Completed, Pending, In Progress)

### Prescriptions
- Medication name and dosage
- Frequency of administration
- Duration of treatment
- Special notes and instructions

## Common Issues & Solutions

### Database Error
- Delete `hospital_system.db` and restart the app to recreate the database

### Port Already in Use
- The app runs on port 5000. If it's in use, modify `app.py` line 330: `port=5000` to another port

### Module Not Found
- Ensure you've run `pip install -r requirements.txt`

## Future Enhancements

- Email notifications for new records
- Appointment scheduling
- Lab test tracking with results
- File upload for medical reports
- Appointment reminders
- Multi-language support
- Mobile app
- API documentation
- Advanced reporting and analytics

## License

This project is provided as-is for educational and healthcare management purposes.

## Support

For support or questions, please refer to the About page or contact the development team.

---

**Created**: December 2025
**Version**: 1.0

## Avatars & Hair-based Classifier (experimental)

This project includes a small avatar pack and starter code to experiment with hair-shape based gender classification (strictly for research/prototyping and with ethical cautions — see USERGUIDE).

Quick start:

1. Generate PNG avatars (from SVG approximations):
   ```bash
   python scripts/generate_avatar_pngs.py
   ```
2. Create a small synthetic dataset and split by label:
   ```bash
   python scripts/create_synthetic_dataset.py
   ```
3. Train a baseline SVM classifier on the synthetic silhouettes:
   ```bash
   python notebooks/hair_classifier_baseline.py
   ```
4. Use the web demo at `/classify` to upload an image and try the classifier (the app will load `models/svm_hair_baseline.pkl` when present).

Notes & ethics:
- The classifier only uses silhouette and grayscale features (color is ignored). Results are likely imperfect and biased; do not use for high‑stakes decisions and obtain consent for any real images.

