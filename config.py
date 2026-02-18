# Configuration for CareConnectHub

# Application Settings
APP_NAME = "CareConnectHub"
DEBUG = True
SECRET_KEY = "hospital_system_secret_key_2025"

# Database Settings
DATABASE = "hospital_system.db"

# Session Settings
SESSION_TIMEOUT_MINUTES = 1440  # 24 hours

# Security Settings
PASSWORD_MIN_LENGTH = 6
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS

# Doctor Specializations
SPECIALIZATIONS = [
    "Cardiology",
    "Neurology",
    "Orthopedics",
    "Pediatrics",
    "General Medicine",
    "Surgery",
    "Dermatology",
    "Psychiatry",
    "Oncology",
    "Radiology",
]

# Report Types
REPORT_TYPES = [
    "Blood Test",
    "X-Ray",
    "CT Scan",
    "MRI",
    "ECG",
    "Ultrasound",
    "Pathology",
    "Lab Results",
    "Other",
]

# Blood Groups
BLOOD_GROUPS = [
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
]

# Prescription Frequencies
FREQUENCIES = [
    "Once a day",
    "Twice a day",
    "Three times a day",
    "Every 4 hours",
    "Every 6 hours",
    "Every 8 hours",
    "Every 12 hours",
    "As needed",
    "Weekly",
    "Monthly",
]

# Gender Options
GENDERS = [
    "Male",
    "Female",
    "Other",
]

# Server Settings
HOST = "127.0.0.1"
PORT = 5000
