"""
Script to clear all doctors and patient details from the database
"""
import sqlite3
import os

DATABASE = 'hospital_system.db'

def clear_all_data():
    """Delete all doctors and patient details"""
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found.")
        return
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get initial counts
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        
        print(f"Found {patient_count} patients and {doctor_count} doctors")
        
        # Delete in order of dependencies (foreign keys)
        tables_to_clear = [
            'messages',
            'doctor_access_logs',
            'appointments',
            'prescriptions',
            'reports',
            'medical_records',
            'patients',
            'doctors'
        ]
        
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            print(f"Cleared table: {table}")
        
        conn.commit()
        conn.close()
        
        print("\n✓ All doctors and patient details have been successfully deleted!")
        print("  - Patients cleared")
        print("  - Doctors cleared")
        print("  - Medical records cleared")
        print("  - Appointments cleared")
        print("  - Prescriptions cleared")
        print("  - Reports cleared")
        print("  - Messages cleared")
        print("  - Access logs cleared")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    confirm = input("⚠️  WARNING: This will DELETE ALL doctors and patient information. Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_data()
    else:
        print("Operation cancelled.")
