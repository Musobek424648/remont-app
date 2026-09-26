import os
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd

app = Flask(__name__)

# Ma'lumotlarni saqlash uchun fayllar
DATA_DIR = 'data'
OBJECTS_FILE = os.path.join(DATA_DIR, 'objects.txt')
EXPENSES_FILE = os.path.join(DATA_DIR, 'expenses.csv')

# Papka va fayllarni yaratish
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(OBJECTS_FILE):
    with open(OBJECTS_FILE, 'w', encoding='utf-8') as f:
        pass

if not os.path.exists(EXPENSES_FILE):
    df = pd.DataFrame(columns=['obekt', 'nomi', 'summa'])
    df.to_csv(EXPENSES_FILE, index=False, encoding='utf-8')


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/objects', methods=['GET', 'POST'])
def handle_objects():
    if request.method == 'POST':
        data = request.json
        nomi = data.get('nomi')
        if nomi:
            with open(OBJECTS_FILE, 'r', encoding='utf-8') as f:
                existing = [line.strip() for line in f.readlines()]
            if nomi in existing:
                return jsonify({'error': "Bu ob'ekt allaqachon mavjud!"}), 400
            
            with open(OBJECTS_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{nomi}\n")
            return jsonify({'message': "Ob'ekt muvaffaqiyatli qo'shildi!"})
        return jsonify({'error': "Ob'ekt nomi kiritilmadi!"}), 400

    if os.path.exists(OBJECTS_FILE):
        with open(OBJECTS_FILE, 'r', encoding='utf-8') as f:
            objects = [line.strip() for line in f.readlines() if line.strip()]
        return jsonify([{'nomi': obj} for obj in objects])
    return jsonify([])


@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    obekt = data.get('obekt')
    nomi = data.get('nomi')
    summa = data.get('summa')

    if not all([obekt, nomi, summa]):
        return jsonify({'error': "Barcha maydonlarni to'ldiring!"}), 400

    try:
        summa = float(summa)
    except ValueError:
        return jsonify({'error': "Summa raqam bo'lishi kerak!"}), 400

    df = pd.read_csv(EXPENSES_FILE, encoding='utf-8')
    new_row = pd.DataFrame([{'obekt': obekt, 'nomi': nomi, 'summa': summa}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(EXPENSES_FILE, index=False, encoding='utf-8')

    return jsonify({'message': "Xarajat saqlandi!"})


@app.route('/api/expenses/<obekt_nomi>', methods=['GET'])
def get_object_expenses(obekt_nomi):
    if not os.path.exists(EXPENSES_FILE):
        return jsonify([])
    
    df = pd.read_csv(EXPENSES_FILE, encoding='utf-8')
    filtered = df[df['obekt'] == obekt_nomi]
    return jsonify(filtered.to_dict(orient='records'))


@app.route('/api/report', methods=['GET'])
def get_report():
    if not os.path.exists(EXPENSES_FILE):
        return jsonify([])
    
    df = pd.read_csv(EXPENSES_FILE, encoding='utf-8')
    if df.empty:
        return jsonify([])
    
    report = df.groupby('obekt')['summa'].sum().reset_index()
    return jsonify(report.to_dict(orient='records'))


@app.route('/download/excel', methods=['GET'])
def download_excel():
    excel_path = os.path.join(DATA_DIR, 'hisobot.xlsx')
    
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE, encoding='utf-8')
    else:
        df = pd.DataFrame(columns=['obekt', 'nomi', 'summa'])

    # Excel fayl ko'rinishida saqlash
    df.to_excel(excel_path, index=False, engine='openpyxl')
    return send_file(excel_path, as_attachment=True, download_name='remont_xarajatlari.xlsx')


if __name__ == '__main__':
    app.run(debug=True, port=5000)