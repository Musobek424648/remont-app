import os
import sqlite3
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)
app.secret_key = 'remont_maxfiy_kalit_soz'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_NAME = 'remont.db'

# Admin login va paroli
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS obektlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obekt TEXT NOT NULL,
            nomi TEXT NOT NULL,
            summa REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chek_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Login yoki parol xato!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

# --- OB'EKTLAR ---
@app.route('/api/objects', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_objects():
    if not session.get('logged_in'):
        return jsonify({'error': 'Ruxsat etilmagan'}), 401

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM obektlar')
        objects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(objects)

    elif request.method == 'POST':
        data = request.json
        nomi = data.get('nomi')
        if not nomi:
            return jsonify({'error': 'Nomi kiritilmadi'}), 400
        try:
            cursor.execute('INSERT INTO obektlar (nomi) VALUES (?)', (nomi,))
            conn.commit()
            conn.close()
            return jsonify({'status': 'ok'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Bu ob`ekt allaqachon mavjud!'}), 400

    elif request.method == 'PUT':
        data = request.json
        old_nomi = data.get('old_nomi')
        new_nomi = data.get('new_nomi')
        cursor.execute('UPDATE obektlar SET nomi = ? WHERE nomi = ?', (new_nomi, old_nomi))
        cursor.execute('UPDATE expenses SET obekt = ? WHERE obekt = ?', (new_nomi, old_nomi))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

    elif request.method == 'DELETE':
        data = request.json
        nomi = data.get('nomi')
        cursor.execute('DELETE FROM obektlar WHERE nomi = ?', (nomi,))
        cursor.execute('DELETE FROM expenses WHERE obekt = ?', (nomi,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

# --- XARAJATLAR ---
@app.route('/api/expenses/<path:nomi>', methods=['GET'])
def get_expenses(nomi):
    if not session.get('logged_in'):
        return jsonify({'error': 'Ruxsat etilmagan'}), 401
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses WHERE obekt = ? ORDER BY created_at DESC', (nomi,))
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(expenses)

@app.route('/api/expenses', methods=['POST', 'PUT', 'DELETE'])
def manage_expenses():
    if not session.get('logged_in'):
        return jsonify({'error': 'Ruxsat etilmagan'}), 401
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.json
        obekt = data.get('obekt')
        nomi = data.get('nomi')
        summa = data.get('summa')
        if not obekt or not nomi or not summa:
            return jsonify({'error': 'Ma`lumotlar to`liq emas'}), 400
        
        cursor.execute('INSERT INTO expenses (obekt, nomi, summa) VALUES (?, ?, ?)', (obekt, nomi, summa))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

    elif request.method == 'PUT':
        data = request.json
        exp_id = data.get('id')
        nomi = data.get('nomi')
        summa = data.get('summa')
        cursor.execute('UPDATE expenses SET nomi = ?, summa = ? WHERE id = ?', (nomi, summa, exp_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

    elif request.method == 'DELETE':
        data = request.json
        exp_id = data.get('id')
        cursor.execute('DELETE FROM expenses WHERE id = ?', (exp_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

# --- CHEK YUKLASH ---
@app.route('/api/upload-receipt', methods=['POST'])
def upload_receipt():
    if not session.get('logged_in'):
        return jsonify({'error': 'Ruxsat etilmagan'}), 401
    if 'chek' not in request.files:
        return jsonify({'error': 'Fayl topilmadi'}), 400
    
    file = request.files['chek']
    expense_id = request.form.get('expense_id')
    
    if file.filename == '':
        return jsonify({'error': 'Fayl tanlanmagan'}), 400
        
    if file and expense_id:
        filename = secure_filename(f"receipt_{expense_id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        chek_url = f"/{filepath}"
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE expenses SET chek_url = ? WHERE id = ?', (chek_url, expense_id))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'ok', 'chek_url': chek_url})
    
    return jsonify({'error': 'Xatolik yuz berdi'}), 400

# --- HISOBOT VA EXCEL ---
@app.route('/api/report', methods=['GET'])
def get_report():
    if not session.get('logged_in'):
        return jsonify({'error': 'Ruxsat etilmagan'}), 401
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT obekt, SUM(summa) as summa FROM expenses GROUP BY obekt')
    report = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(report)

@app.route('/download/excel', methods=['GET'])
def download_all_excel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT obekt, nomi, summa, created_at FROM expenses", conn)
    conn.close()
    
    file_path = "umumiy_hisobot.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route('/api/expenses/<path:nomi>/excel', methods=['GET'])
def download_object_excel(nomi):
    if not session.get('logged_in'):
        return jsonify({'error': 'Ruxsat etilmagan'}), 401
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT nomi, summa, created_at FROM expenses WHERE obekt = ?", conn, params=(nomi,))
    conn.close()
    
    file_path = f"{nomi}_xarajatlar.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
