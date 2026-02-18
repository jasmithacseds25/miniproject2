# CareConnectHub - User Guide

## 🏥 System Overview

```
                    CareConnectHub
                            (Web Application)
                            
              ┌─────────────────────────────────┐
              │       HOME PAGE (index.html)     │
              │  - Features overview             │
              │  - Login buttons                 │
              │  - Registration links            │
              └────────────┬────────────────────┘
                           │
                 ┌─────────┴──────────┐
                 │                    │
         ┌───────▼─────┐      ┌──────▼────────┐
         │  DOCTOR      │      │   PATIENT     │
         │  PORTAL      │      │   PORTAL      │
         └──────┬──────┘      └───────┬────────┘
                │                     │
    ┌───────────┼───────┐         ┌──┴──────────┐
    │           │       │         │             │
  LOGIN    REGISTER  SEARCH    LOGIN        REGISTER
    │           │       │         │             │
    └─────┬─────┴───┬───┴─────────┴──┬──────────┘
          │         │                │
    ┌─────▼────┐ ┌──▼──────┐ ┌──────▼─────┐
    │DASHBOARD │ │DATABASE │ │ DASHBOARD  │
    │          │ │(SQLite) │ │            │
    └─────┬────┘ └─────────┘ └──────┬─────┘
          │                         │
    ┌─────┴─────────────────────────┴─────┐
    │  Data Management Features:           │
    │  - Medical Records                   │
    │  - Reports                           │
    │  - Prescriptions                     │
    │  - Patient Profiles                  │
    └──────────────────────────────────────┘
```

---

## 🔑 Login Pages

### Doctor Login Page
```
URL: http://127.0.0.1:5000/doctor/login

Fields:
- Email
- Password

After Login → Doctor Dashboard
```

### Patient Login Page
```
URL: http://127.0.0.1:5000/patient/login

Fields:
- Email
- Password

After Login → Patient Dashboard
```

---

## 👨‍⚕️ Doctor Features Flow

```
DOCTOR LOGIN
    ↓
┌────────────────────────────────────┐
│     DOCTOR DASHBOARD               │
│  - Total Patients                  │
│  - Medical Records Count           │
│  - Reports Created Count           │
│  - Quick Action Buttons            │
│  - Recent Records Table            │
└────────────────────────────────────┘
    ↓
    ├─→ View All Patients
    │      ↓
    │   ┌────────────────────┐
    │   │ PATIENTS LIST      │
    │   │ - Search bar       │
    │   │ - Patient table    │
    │   └────────────────────┘
    │      ↓
    │   SELECT PATIENT
    │      ↓
    │   ┌────────────────────┐
    │   │ PATIENT DETAILS    │
    │   │ - Personal info    │
    │   │ - Contact info     │
    │   │ - Medical history  │
    │   │ - 3 Tabs:          │
    │   │  • Records         │
    │   │  • Reports         │
    │   │  • Prescriptions   │
    │   └────────────────────┘
    │      ↓
    │   QUICK ACTIONS:
    │      ├─→ Add Medical Record
    │      │      ↓
    │      │   FORM:
    │      │   - Visit date
    │      │   - Diagnosis
    │      │   - Symptoms
    │      │   - Treatment
    │      │   - Medications
    │      │   - Notes
    │      │
    │      ├─→ Add Report
    │      │      ↓
    │      │   FORM:
    │      │   - Report type
    │      │   - Report date
    │      │   - Findings
    │      │   - Recommendations
    │      │   - Status
    │      │
    │      └─→ Add Prescription
    │             ↓
    │          FORM:
    │          - Medication name
    │          - Dosage
    │          - Frequency
    │          - Duration
    │          - Prescribed date
    │          - Notes
    │
    └─→ Logout
```

---

## 👤 Patient Features Flow

```
PATIENT LOGIN
    ↓
┌────────────────────────────────────┐
│     PATIENT DASHBOARD              │
│  - Doctor Visits Count             │
│  - Medical Reports Count           │
│  - Active Prescriptions Count      │
│  - Recent Medical Visits Table     │
│  - Personal Information Card       │
└────────────────────────────────────┘
    ↓
    ├─→ View Medical Records
    │      ↓
    │   ┌────────────────────┐
    │   │ RECORDS LIST       │
    │   │ - Sorted by date   │
    │   │ - Doctor name      │
    │   │ - Diagnosis        │
    │   │ - Symptoms         │
    │   │ - Treatment        │
    │   │ - Medications      │
    │   │ - Notes            │
    │   └────────────────────┘
    │
    ├─→ View Reports
    │      ↓
    │   ┌────────────────────┐
    │   │ REPORTS LIST       │
    │   │ - Report type      │
    │   │ - Report date      │
    │   │ - Status badge     │
    │   │ - Doctor name      │
    │   │ - Findings         │
    │   │ - Recommendations  │
    │   └────────────────────┘
    │
    ├─→ View Prescriptions
    │      ↓
    │   ┌────────────────────┐
    │   │ PRESCRIPTIONS      │
    │   │ - Medication       │
    │   │ - Dosage           │
    │   │ - Frequency        │
    │   │ - Duration         │
    │   │ - Doctor name      │
    │   │ - Notes            │
    │   └────────────────────┘
    │
    ├─→ Update Profile
    │      ↓
    │   ┌────────────────────┐
    │   │ PROFILE EDIT       │
│   │   ├─ Profile picture can be uploaded/updated on the profile page (will show default avatar if not set)
│   │   └─ Doctors can now edit their profile at `/doctor/profile` to update phone, specialization, license and profile picture
    │   │ - Phone            │
    │   │ - Address          │
    │   │ - Emergency contact│
    │   │ - Medical history  │
    │   └────────────────────┘
    │
    └─→ Logout
```

---

## 📊 Database Schema

```
┌─────────────────────────┐
│   DOCTORS TABLE         │
├─────────────────────────┤
│ id (PK)                 │
│ name                    │
│ email (UNIQUE)          │
│ password (hashed)       │
│ specialization          │
│ license_number (UNIQUE) │
│ phone                   │
│ created_at              │
└──────────────┬──────────┘
               │
               │ (doctor_id FK)
               │
    ┌──────────┼──────────┐
    │          │          │
    │          │          │
┌───▼───┐  ┌──▼──────┐ ┌─▼────────┐
│MEDICAL│  │ REPORTS │ │PRESCRIPT-│
│RECORDS│  │         │ │IONS      │
└───┬───┘  └──┬──────┘ └─┬────────┘
    │         │          │
    │ (patient_id FK)     │
    │         │          │
    └────┬────┴──────┬───┘
         │           │
    ┌────▼──────────▼────┐
    │  PATIENTS TABLE    │
    ├────────────────────┤
    │ id (PK)            │
    │ name               │
    │ email (UNIQUE)     │
    │ password (hashed)  │
    │ date_of_birth      │
    │ gender             │
    │ blood_group        │
    │ phone              │
    │ address            │
    │ emergency_contact  │
    │ medical_history    │
    │ created_at         │
    └────────────────────┘
```

---

## 🌐 URL Routes

### Public Routes
```
GET  /                          → Home page
GET  /about                     → About page
```

### Doctor Routes
```
GET/POST /doctor/register       → Doctor registration
GET/POST /doctor/login          → Doctor login
GET  /doctor/dashboard          → Dashboard
GET  /doctor/patients           → Patients list
GET  /doctor/patient/<id>       → Patient details
GET/POST /doctor/add-record/<id>    → Add medical record
GET/POST /doctor/add-report/<id>    → Add report
GET/POST /doctor/add-prescription/<id> → Add prescription
GET  /doctor/logout             → Logout
```

### Patient Routes
```
GET/POST /patient/register      → Patient registration
GET/POST /patient/login         → Patient login
GET  /patient/dashboard         → Dashboard
GET  /patient/medical-records   → View records
GET  /patient/reports           → View reports
GET  /patient/prescriptions     → View prescriptions
GET  /patient/profile           → View profile
POST /patient/update-profile    → Update profile
GET  /patient/logout            → Logout
```

### API Routes
```
GET  /api/search-patients?q=<query> → Search patients (AJAX)
```

---

## 📱 Page Navigation Map

```
HOME (index.html)
├── ABOUT (about.html)
├── Doctor Login (doctor_login.html)
│   └── Doctor Dashboard
│       ├── View Patients
│       │   └── Patient Details
│       │       ├── Add Record
│       │       ├── Add Report
│       │       └── Add Prescription
│       └── Logout
├── Doctor Register (doctor_register.html)
│   └── Doctor Login
├── Patient Login (patient_login.html)
│   └── Patient Dashboard
│       ├── Medical Records
│       ├── Reports
│       ├── Prescriptions
│       ├── Profile
│       └── Logout
└── Patient Register (patient_register.html)
    └── Patient Login
```

---

## 🎯 Key Workflows

### Workflow 1: Doctor Adding Patient Record
```
1. Login as Doctor
2. Click "View All Patients"
3. Search or select patient
4. Click "View Details"
5. Click "Add Medical Record"
6. Fill form (diagnosis, symptoms, treatment)
7. Submit
8. Record appears in patient's Medical Records tab
9. Patient can now see this record in their dashboard
```

### Workflow 2: Patient Checking Health Records
```
1. Login as Patient
2. Click "View Medical Records" OR
   Click "Medical Records" tab on dashboard
3. See all doctor visits
4. Each record shows:
   - Doctor name
   - Visit date
   - Diagnosis
   - Treatment details
   - Medications
   - Notes
```

### Workflow 3: Doctor Creating Report
```
1. Login as Doctor
2. Find patient
3. Click "Add Report"
4. Select report type (Blood Test, X-Ray, etc.)
5. Enter findings and recommendations
6. Submit
7. Patient receives notification (future feature)
8. Patient can view in "Reports" section
```

---

## 💾 Data Persistence

All data is stored in SQLite database:
```
File: hospital_system.db
Location: /patient_health/ directory
Size: Grows with usage
Backup: Make regular copies
```

---

## ⚠️ Important Notes

1. **First Login**: Database auto-creates on first run
2. **Passwords**: Never stored in plain text (hashed)
3. **Sessions**: Automatically expire after 24 hours
4. **Data Privacy**: Each user sees only their data
5. **Error Handling**: User-friendly error messages

---

## ✅ Ready to Use

Everything is installed and ready. Just:

```powershell
python app.py
```

---

## Avatars & Hair-shape Classifier (Experimental)

A small avatar pack and starter ML code are included for experimentation with hair-shape based gender inference (for prototyping only). Steps:

1. Generate PNG avatars (from the SVG pack):
   ```bash
   python scripts/generate_avatar_pngs.py
   ```
2. Create a synthetic dataset and labels:
   ```bash
   python scripts/create_synthetic_dataset.py
   ```
3. Train the baseline SVM classifier:
   ```bash
   python notebooks/hair_classifier_baseline.py
   ```
4. Visit `/classify` in the running app to upload an image and try the classifier.

Ethics & safety:
- This classifier uses **silhouette/grayscale features only** (color is ignored) and is highly experimental. It can misgender people, perpetuate bias, and cause harm; **do not** use for decision-making or any high‑stakes scenario. Obtain explicit consent for any real images and always display clear disclaimers when using or evaluating this feature.


Open: `http://127.0.0.1:5000`

**Enjoy your hospital management system! 🏥**
