import os
import csv
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OBJECTS_FILE = os.path.join(DATA_DIR, 'objects.txt')
EXPENSES_FILE = os.path.join(DATA_DIR, 'expenses.csv')

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(OBJECTS_FILE):
        with open(OBJECTS_FILE, 'w', encoding='utf-8') as f:
            pass
    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['obekt', 'nomi', 'summa'])

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/objects', methods=['GET', 'POST'])
def handle_objects():
    init_db()
    if request.method == 'POST':
        data = request.get_json(force=True) or {}
        nomi = str(data.get('nomi', '')).strip()
        if nomi:
            with open(OBJECTS_FILE, 'a', encoding='utf-8') as f:
                f.write(nomi + '\n')
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'Nomi bo`sh'}), 400
    else:
        objects = []
        if os.path.exists(OBJECTS_FILE):
            with open(OBJECTS_FILE, 'r', encoding='utf-8') as f:
                objects = [{'nomi': line.strip()} for line in f if line.strip()]
        return jsonify(objects)

@app.route('/api/objects/edit', methods=['POST'])
def edit_object():
    init_db()
    data = request.get_json(force=True) or {}
    old_name = str(data.get('old_name', '')).strip()
    new_name = str(data.get('new_name', '')).strip()

    if not old_name or not new_name:
        return jsonify({'error': 'Ma`lumot to`liq emas'}), 400

    if os.path.exists(OBJECTS_FILE):
        with open(OBJECTS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        updated_lines = [new_name if line == old_name else line for line in lines]
        with open(OBJECTS_FILE, 'w', encoding='utf-8') as f:
            for line in updated_lines:
                f.write(line + '\n')

    if os.path.exists(EXPENSES_FILE):
        rows = []
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                rows.append(header)
            for row in reader:
                if row and len(row) >= 3:
                    if row[0] == old_name:
                        row[0] = new_name
                    rows.append(row)
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    return jsonify({'status': 'ok'})

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    init_db()
    data = request.get_json(force=True) or {}
    obekt = str(data.get('obekt', '')).strip()
    nomi = str(data.get('nomi', '')).strip()
    summa = str(data.get('summa', '')).strip()
    
    if obekt and nomi and summa:
        with open(EXPENSES_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([obekt, nomi, summa])
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Ma`lumotlar to`liq kiritilmadi'}), 400

@app.route('/api/expenses/<path:obekt_nomi>', methods=['GET'])
def get_expenses(obekt_nomi):
    init_db()
    expenses = []
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('obekt') == obekt_nomi:
                    try:
                        val = int(float(row.get('summa', 0)))
                    except:
                        val = 0
                    expenses.append({'nomi': row.get('nomi', ''), 'summa': val})
    return jsonify(expenses)

@app.route('/download/excel')
def download_excel():
    init_db()
    excel_path = os.path.join(DATA_DIR, 'hisobot.xlsx')
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
        df.to_excel(excel_path, index=False)
        return send_file(excel_path, as_attachment=True)
    return "Fayl topilmadi", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
