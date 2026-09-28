import os
import io
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from supabase import create_client, Client

app = Flask(__name__)

# Supabase ma'lumotlari (Render'dagi Environment variables yoki to'g'ridan-to'g'ri)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "SIZNING_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "SIZNING_SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

# Ob'ektlarni olish va qo'shish
@app.route('/api/objects', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_objects():
    if request.method == 'GET':
        try:
            res = supabase.table('objects').select('*').execute()
            return jsonify(res.data or [])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        data = request.json
        nomi = data.get('nomi')
        if not nomi:
            return jsonify({'error': 'Ob\'ekt nomi bo\'sh bo\'lishi mumkin emas'}), 400
        try:
            res = supabase.table('objects').insert({'nomi': nomi}).execute()
            return jsonify(res.data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        data = request.json
        old_nomi = data.get('old_nomi')
        new_nomi = data.get('new_nomi')
        if not old_nomi or not new_nomi:
            return jsonify({'status': 'error', 'message': 'Ma\'lumotlar yetishmayapti'}), 400
        try:
            supabase.table('objects').update({'nomi': new_nomi}).eq('nomi', old_nomi).execute()
            supabase.table('expenses').update({'obekt': new_nomi}).eq('obekt', old_nomi).execute()
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    elif request.method == 'DELETE':
        data = request.json
        nomi = data.get('nomi')
        if not nomi:
            return jsonify({'status': 'error', 'message': 'Nomi ko\'rsatilmagan'}), 400
        try:
            supabase.table('expenses').delete().eq('obekt', nomi).execute()
            supabase.table('objects').delete().eq('nomi', nomi).execute()
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

# Xarajatlar bo'yicha amallar
@app.route('/api/expenses', methods=['POST', 'PUT', 'DELETE'])
def manage_expenses():
    if request.method == 'POST':
        data = request.json
        obekt = data.get('obekt')
        nomi = data.get('nomi')
        summa = data.get('summa')
        if not obekt or not nomi or not summa:
            return jsonify({'error': 'Barcha maydonlarni to\'ldiring'}), 400
        try:
            res = supabase.table('expenses').insert({
                'obekt': obekt,
                'nomi': nomi,
                'summa': float(summa)
            }).execute()
            return jsonify(res.data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'PUT':
        data = request.json
        exp_id = data.get('id')
        nomi = data.get('nomi')
        summa = data.get('summa')
        try:
            res = supabase.table('expenses').update({
                'nomi': nomi,
                'summa': float(summa)
            }).eq('id', exp_id).execute()
            return jsonify({'status': 'ok', 'data': res.data})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    elif request.method == 'DELETE':
        data = request.json
        exp_id = data.get('id')
        try:
            supabase.table('expenses').delete().eq('id', exp_id).execute()
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

# Muayyan ob'ekt xarajatlarini olish
@app.route('/api/expenses/<path:obekt_nomi>', methods=['GET'])
def get_object_expenses(obekt_nomi):
    try:
        res = supabase.table('expenses').select('*').eq('obekt', obekt_nomi).order('id', desc=True).execute()
        return jsonify(res.data or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Umumiy hisobot
@app.route('/api/report', methods=['GET'])
def get_report():
    try:
        res = supabase.table('expenses').select('obekt, summa').execute()
        data = res.data or []
        
        report_dict = {}
        for item in data:
            obj = item.get('obekt')
            summa = float(item.get('summa', 0))
            report_dict[obj] = report_dict.get(obj, 0) + summa
            
        report_list = [{'obekt': k, 'summa': v} for k, v in report_dict.items()]
        return jsonify(report_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Barcha xarajatlarni Excelga yuklab olish
@app.route('/download/excel', methods=['GET'])
def download_excel():
    try:
        res = supabase.table('expenses').select('obekt, nomi, summa, created_at').execute()
        data = res.data or []
        
        formatted_data = []
        for item in data:
            formatted_data.append({
                'Ob\'ekt': item.get('obekt', ''),
                'Sana va Vaqt': item.get('created_at', ''),
                'Xarajat Nomi': item.get('nomi', ''),
                'Summa (so\'m)': item.get('summa', 0)
            })
            
        df = pd.DataFrame(formatted_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Barcha Xarajatlar')
        output.seek(0)
        
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='umumiy_xarajatlar.xlsx')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# HAR BIR OB'EKT UCHUN ALOHIDA EXCEL YUKLAB OLISH (Siz so'ragan qism)
@app.route('/api/expenses/<path:obekt_nomi>/excel', methods=['GET'])
def download_object_excel(obekt_nomi):
    try:
        res = supabase.table('expenses').select('nomi, summa, created_at').eq('obekt', obekt_nomi).order('id', desc=True).execute()
        data = res.data or []
        
        formatted_data = []
        for item in data:
            formatted_data.append({
                'Sana va Vaqt': item.get('created_at', ''),
                'Xarajat Nomi': item.get('nomi', ''),
                'Summa (so\'m)': item.get('summa', 0)
            })
            
        df = pd.DataFrame(formatted_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Xarajatlar')
        output.seek(0)
        
        filename = f"{obekt_nomi}_xarajatlari.xlsx"
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
