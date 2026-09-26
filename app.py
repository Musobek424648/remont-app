import os
import csv
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

OBJECTS_FILE = 'objects.txt'
EXPENSES_FILE = 'expenses.csv'

def init_files():
    if not os.path.exists(OBJECTS_FILE):
        open(OBJECTS_FILE, 'w', encoding='utf-8').close()
    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['obekt', 'nomi', 'summa'])

@app.route('/')
def index():
    return render_template('index.html')

# Ob'ektlarni olish va qo'shish
@app.route('/api/objects', methods=['GET', 'POST'])
def handle_objects():
    init_files()
    if request.method == 'POST':
        data = request.get_json() or {}
        nomi = str(data.get('nomi', '')).strip()
        if nomi:
            with open(OBJECTS_FILE, 'a', encoding='utf-8') as f:
                f.write(nomi + '\n')
        return jsonify({'status': 'ok'})
    else:
        objects = []
        if os.path.exists(OBJECTS_FILE):
            with open(OBJECTS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        objects.append({'nomi': line})
        return jsonify(objects)

# Xarajat qo'shish
@app.route('/api/expenses', methods=['POST'])
def add_expense():
    init_files()
    data = request.get_json() or {}
    obekt = str(data.get('obekt', '')).strip()
    nomi = str(data.get('nomi', '')).strip()
    summa = str(data.get('summa', '0')).strip()

    if obekt and nomi:
        with open(EXPENSES_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([obekt, nomi, summa])

    return jsonify({'status': 'ok'})

# Tanlangan ob'ekt xarajatlarini ekranga chiqarish (MUAMMO SHU YERDA HAL ETILDI)
@app.route('/api/expenses_by_param', methods=['GET'])
def get_expenses_param():
    init_files()
    obekt_nomi = request.args.get('obekt', '').strip().lower()
    expenses = []

    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Sarlavhani o'tkazib yuboramiz
            for row in reader:
                if len(row) >= 3:
                    row_obekt = str(row[0]).strip().lower()
                    if row_obekt == obekt_nomi:
                        expenses.append({
                            'nomi': str(row[1]).strip(),
                            'summa': str(row[2]).strip()
                        })

    return jsonify(expenses)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
