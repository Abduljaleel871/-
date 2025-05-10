from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'secret-key'

hospitals = ["مستشفى طرابلس المركزي", "مستشفى بنغازي الطبي", "مستشفى مصراتة العام"]
departments = ["قسم الباطنة", "قسم الجراحة", "قسم الأطفال", "قسم النساء والتوليد"]
patient_types = ["بالغ", "طفل", "مسن"]
antibiotics = ["Amoxicillin", "Ciprofloxacin", "Azithromycin", "Doxycycline", "Metronidazole"]

def get_db_connection():
    conn = sqlite3.connect('patients.db')
    conn.row_factory = sqlite3.Row
    return conn

# إنشاء الجدول إذا لم يكن موجوداً
with get_db_connection() as conn:
    conn.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        file_number TEXT,
        hospital TEXT,
        department TEXT,
        patient_type TEXT,
        antibiotic TEXT,
        admission_date TEXT
    )''')
    conn.commit()

@app.route('/')
def index():
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    conn.close()
    return render_template('index.html', patients=patients, hospitals=hospitals,
                           departments=departments, patient_types=patient_types, antibiotics=antibiotics)

@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form['name'].strip()
    file_number = request.form['file_number'].strip()
    hospital = request.form['hospital']
    department = request.form['department']
    patient_type = request.form['patient_type']
    antibiotic = request.form['antibiotic']
    admission_date = request.form['admission_date'].strip()
    if not (name and file_number and hospital and department and patient_type and antibiotic and admission_date):
        flash('يرجى ملء جميع الحقول!', 'warning')
        return redirect(url_for('index'))
    if not file_number.isdigit():
        flash('رقم الملف يجب أن يحتوي على أرقام فقط!', 'danger')
        return redirect(url_for('index'))
    try:
        pd.to_datetime(admission_date, format="%d-%m-%Y")
    except ValueError:
        flash('تاريخ الدخول يجب أن يكون بالتنسيق DD-MM-YYYY!', 'danger')
        return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute('''
    INSERT INTO patients (name, file_number, hospital, department, patient_type, antibiotic, admission_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)''',
    (name, file_number, hospital, department, patient_type, antibiotic, admission_date))
    conn.commit()
    conn.close()
    flash('تمت إضافة المريض بنجاح!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_patient/<int:id>', methods=['POST'])
def delete_patient(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM patients WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('تم حذف المريض بنجاح!', 'success')
    return redirect(url_for('index'))

@app.route('/add_hospital', methods=['POST'])
def add_hospital():
    new_hospital = request.form['new_hospital'].strip()
    if new_hospital and new_hospital not in hospitals:
        hospitals.append(new_hospital)
        flash('تمت إضافة المستشفى بنجاح!', 'success')
    else:
        flash('يرجى إدخال اسم صحيح أو المستشفى موجود بالفعل.', 'warning')
    return redirect(url_for('index'))

@app.route('/add_antibiotic', methods=['POST'])
def add_antibiotic():
    new_antibiotic = request.form['new_antibiotic'].strip()
    if new_antibiotic and new_antibiotic not in antibiotics:
        antibiotics.append(new_antibiotic)
        flash('تمت إضافة المضاد الحيوي بنجاح!', 'success')
    else:
        flash('يرجى إدخال اسم صحيح أو المضاد الحيوي موجود بالفعل.', 'warning')
    return redirect(url_for('index'))

@app.route('/export_excel')
def export_excel():
    conn = get_db_connection()
    patients = conn.execute('SELECT id, name, file_number, hospital, department, patient_type, antibiotic, admission_date FROM patients').fetchall()
    conn.close()
    if not patients:
        flash('لا توجد بيانات للتصدير!', 'warning')
        return redirect(url_for('index'))
    df = pd.DataFrame(patients, columns=["ID", "اسم المريض", "رقم الملف", "المستشفى", "القسم", "نوع المريض", "المضاد الحيوي", "تاريخ الدخول"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="patients.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
