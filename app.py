import os
import csv
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

OBJECTS_FILE = 'objects.csv'
EXPENSES_FILE = 'expenses.csv'

def init_db():
    if not os.path.exists(OBJECTS_FILE):
        with open(OBJECTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['nomi'])

    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['obekt', 'nomi', 'summa'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/objects', methods=['GET', 'POST'])
def handle_objects():
    init_db()
    if request.method == 'POST':
        data = request.json or {}
        nomi = str(data.get('nomi', '')).strip()
        if nomi:
            with open(OBJECTS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([nomi])
        return jsonify({'status': 'ok'})
    else:
        objects = []
        if os.path.exists(OBJECTS_FILE):
            with open(OBJECTS_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('nomi'):
                        objects.append({'nomi': row['nomi'].strip()})
        return jsonify(objects)

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    init_db()
    data = request.json or {}
    obekt = str(data.get('obekt', '')).strip()
    nomi = str(data.get('nomi', '')).strip()
    summa = str(data.get('summa', '0')).strip()

    if obekt and nomi:
        with open(EXPENSES_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([obekt, nomi, summa])

    return jsonify({'status': 'ok'})

@app.route('/api/expenses_by_param', methods=['GET'])
def get_expenses_param():
    init_db()
    obekt_nomi = request.args.get('obekt', '').strip()
    expenses = []
    
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_obekt = str(row.get('obekt', '')).strip()
                if row_obekt.lower() == obekt_nomi.lower():
                    raw_sum = str(row.get('summa', '0')).strip()
                    try:
                        val = int(float(raw_sum))
                    except (ValueError, TypeError):
                        val = 0
                    
                    expenses.append({
                        'nomi': str(row.get('nomi', '')).strip(),
                        'summa': val
                    })
                    
    return jsonify(expenses)

@app.route('/download/excel', methods=['GET'])
def download_excel():
    init_db()
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Xarajatlar"
    
    ws.append(['Ob'ekt', 'Xarajat Nomi', 'Summa'])

    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    s = float(row.get('summa', 0))
                except:
                    s = 0
                ws.append([row.get('obekt', ''), row.get('nomi', ''), s])

    file_path = "xarajatlar_hisoboti.xlsx"
    wb.save(file_path)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
