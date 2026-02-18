# CareConnectHub - Quick Start Guide

## 🚀 Quick Start (Windows PowerShell)

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Run the Application
```powershell
python app.py
```

### Step 3: Access the Website
Open your browser and go to:
```
http://127.0.0.1:5000
```

---

## 👨‍⚕️ Test Doctor Account (Quick Demo)

### Register a Doctor:
1. Click "Doctor Register" on home page
2. Fill in the form:
   - **Name**: Dr. John Smith
   - **Email**: dr.john@hospital.com
   - **Password**: password123
   - **Specialization**: Cardiology
   - **License Number**: MED123456
   - **Phone**: 555-0123

### Login as Doctor:
1. Click "Doctor Login"
2. **Email**: dr.john@hospital.com
3. **Password**: password123

---

## 👤 Test Patient Account (Quick Demo)

### Register a Patient:
1. Click "Patient Register" on home page
2. Fill in the form:
   - **Name**: John Doe
   - **Email**: john.doe@email.com
   - **Date of Birth**: 1990-05-15
   - **Password**: password123
   - **Blood Group**: O+
   - **Gender**: Male
   - **Phone**: 555-9999
   - **Address**: 123 Main St, City

### Login as Patient:
1. Click "Patient Login"
2. **Email**: john.doe@email.com
3. **Password**: password123

---

## 📋 Testing Workflow

### As a Doctor:
1. **Login** → Doctor Dashboard
2. **Click "View All Patients"** → Search or select patient
3. **View Patient Details** → Click patient from list
4. **Add Medical Record** → Fill in diagnosis, symptoms, treatment
5. **Add Report** → Choose report type, add findings
6. **Add Prescription** → Enter medication details
7. **View Dashboard** → See statistics and recent records

### As a Patient:
1. **Login** → Patient Dashboard
2. **View Medical Records** → See all visits and diagnoses
3. **View Reports** → Check lab results and medical reports
4. **View Prescriptions** → See current medications
5. **Update Profile** → Edit phone, address, medical history

---

## 🌐 Website Features Overview

### Home Page
- Welcome message
- Feature cards
- Quick navigation buttons
- Call-to-action buttons for login/register

### Doctor Features
- **Dashboard**: Statistics, recent records, quick actions
- **Patients List**: View all treated patients
- **Patient Details**: Complete patient information and history
- **Add Records**: Create medical records with diagnosis
- **Add Reports**: Generate medical reports
- **Add Prescriptions**: Prescribe medications
- **Search**: Find patients quickly

### Patient Features
- **Dashboard**: Health statistics overview
- **Medical Records**: View all doctor visits
- **Reports**: Access medical reports and test results
- **Prescriptions**: View current medications
- **Profile**: Update personal information

---

## 🗄️ Database

The system uses SQLite which automatically creates the database:
- **File**: `hospital_system.db`
- **Created**: Automatically on first run
- **Tables**: Doctors, Patients, Medical Records, Reports, Prescriptions

---

## 🛠️ Troubleshooting

### Error: "Port 5000 already in use"
Edit `app.py` line 330, change port number:
```python
app.run(debug=True, host='127.0.0.1', port=5001)  # Change 5000 to 5001
```

### Error: "Module flask not found"
Run:
```powershell
pip install -r requirements.txt
```

### Error: "Database is locked"
Delete `hospital_system.db` and restart:
```powershell
Remove-Item hospital_system.db
python app.py
```

---

## 📱 Browser Compatibility

- Chrome (Recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (responsive design)

---

## 💡 Key Features Summary

| Feature | Doctor | Patient |
|---------|--------|---------|
| Register | ✅ | ✅ |
| Login | ✅ | ✅ |
| View Dashboard | ✅ | ✅ |
| Add Medical Records | ✅ | ❌ |
| View Medical Records | ✅ | ✅ |
| Create Reports | ✅ | ❌ |
| View Reports | ✅ | ✅ |
| Prescribe Medicines | ✅ | ❌ |
| View Prescriptions | ✅ | ✅ |
| Update Profile | ✅ | ✅ |
| Search Patients | ✅ | ❌ |

---

## 📞 Support

For more information, see the main **README.md** file in the project directory.

**Happy Testing! 🏥**
