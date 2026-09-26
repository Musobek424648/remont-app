import os
import csv
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd

app = Flask(__name__)

# Baza papkasi va fayllar manzili
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OBJECTS_FILE = os.path.join(DATA_DIR, 'objects.txt')
EXPENSES_FILE = os.path.join(DATA_DIR, 'expenses.csv')

def init_db():
    if not os.path.exists(DATA_DIR):
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
        data = request.json
        nomi = data.get('nomi', '').strip()
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

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    init_db()
    data = request.json
    obekt = data.get('obekt')
    nomi = data.get('nomi')
    summa = data.get('summa')
    
    if obekt and nomi and summa:
        with open(EXPENSES_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([obekt, nomi, summa])
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Noto`g`ri ma`lumot'}), 400

@app.route('/api/expenses/<path:obekt_nomi>', methods=['GET'])
def get_expenses(obekt_nomi):
    init_db()
    expenses = []
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('obekt') == obekt_nomi:
                    expenses.append({'nomi': row['nomi'], 'summa': int(row['summa'])})
    return jsonify(expenses)

@app.route('/api/report', methods=['GET'])
def get_report():
    init_db()
    report = {}
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                obekt = row.get('obekt')
                summa = int(row.get('summa', 0))
                report[obekt] = report.get(obekt, 0) + summa
    result = [{'obekt': k, 'summa': v} for k, v in report.items()]
    return jsonify(result)

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
