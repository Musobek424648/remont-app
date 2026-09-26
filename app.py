import sqlite3
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DB_NAME = 'remont.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Ob'ektlar jadvali
    conn.execute('''
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT NOT NULL UNIQUE
        )
    ''')
    # Xarajatlar jadvali
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obekt TEXT NOT NULL,
            nomi TEXT NOT NULL,
            summa INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

# Ob'ektlarni olish va qo'shish
@app.route('/api/objects', methods=['GET', 'POST'])
def handle_objects():
    init_db()
    conn = get_db()
    if request.method == 'POST':
        data = request.get_json() or {}
        nomi = str(data.get('nomi', '')).strip()
        if nomi:
            try:
                conn.execute('INSERT INTO objects (nomi) VALUES (?)', (nomi,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass  # Ob'ekt avval qo'shilgan bo'lsa
        conn.close()
        return jsonify({'status': 'ok'})
    else:
        cursor = conn.execute('SELECT nomi FROM objects ORDER BY id DESC')
        objects = [{'nomi': row['nomi']} for row in cursor.fetchall()]
        conn.close()
        return jsonify(objects)

# Xarajat qo'shish
@app.route('/api/expenses', methods=['POST'])
def add_expense():
    init_db()
    data = request.get_json() or {}
    obekt = str(data.get('obekt', '')).strip()
    nomi = str(data.get('nomi', '')).strip()
    raw_sum = str(data.get('summa', '0')).strip()
    
    try:
        summa = int(float(raw_sum))
    except (ValueError, TypeError):
        summa = 0

    if obekt and nomi:
        conn = get_db()
        conn.execute('INSERT INTO expenses (obekt, nomi, summa) VALUES (?, ?, ?)', (obekt, nomi, summa))
        conn.commit()
        conn.close()

    return jsonify({'status': 'ok'})

# Xarajatlarni ekranga chiqarish
@app.route('/api/expenses_by_param', methods=['GET'])
def get_expenses_param():
    init_db()
    obekt_nomi = request.args.get('obekt', '').strip()
    conn = get_db()
    
    cursor = conn.execute('SELECT nomi, summa FROM expenses WHERE LOWER(obekt) = LOWER(?) ORDER BY id DESC', (obekt_nomi,))
    expenses = [{'nomi': row['nomi'], 'summa': row['summa']} for row in cursor.fetchall()]
    conn.close()

    return jsonify(expenses)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
