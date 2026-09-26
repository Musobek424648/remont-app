import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

url: str = os.environ.get("SUPABASE_URL", "https://kkgfktwrikjlcejmddqa.supabase.co")
key: str = os.environ.get("SUPABASE_KEY", "sb_publishable_nIuLaUVAV42ihPsAyOLFCw_XV7nns5j")

supabase: Client = create_client(url, key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/objects', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_objects():
    if request.method == 'POST':
        data = request.get_json() or {}
        nomi = str(data.get('nomi', '')).strip()
        if nomi:
            try:
                supabase.table('objects').insert({'nomi': nomi}).execute()
            except Exception as e:
                print("Error inserting object:", e)
        return jsonify({'status': 'ok'})

    elif request.method == 'PUT':
        # Obyekt nomini yangilash
        data = request.get_json() or {}
        old_nomi = str(data.get('old_nomi', '')).strip()
        new_nomi = str(data.get('new_nomi', '')).strip()

        if old_nomi and new_nomi:
            try:
                supabase.table('objects').update({'nomi': new_nomi}).eq('nomi', old_nomi).execute()
                supabase.table('expenses').update({'obekt': new_nomi}).eq('obekt', old_nomi).execute()
                return jsonify({'status': 'ok'})
            except Exception as e:
                print("Error updating object:", e)
                return jsonify({'status': 'error', 'message': str(e)}), 500
        return jsonify({'status': 'invalid data'}), 400

    elif request.method == 'DELETE':
        # Obyektni va unga tegishli xarajatlarni o'chirish
        data = request.get_json() or {}
        nomi = str(data.get('nomi', '')).strip()
        if nomi:
            try:
                supabase.table('expenses').delete().eq('obekt', nomi).execute()
                supabase.table('objects').delete().eq('nomi', nomi).execute()
                return jsonify({'status': 'ok'})
            except Exception as e:
                print("Error deleting object:", e)
                return jsonify({'status': 'error', 'message': str(e)}), 500
        return jsonify({'status': 'invalid data'}), 400

    else:
        try:
            res = supabase.table('objects').select('nomi').order('id', desc=True).execute()
            return jsonify(res.data)
        except Exception as e:
            print("Error fetching objects:", e)
            return jsonify([])

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.get_json() or {}
    obekt = str(data.get('obekt', '')).strip()
    nomi = str(data.get('nomi', '')).strip()
    raw_sum = str(data.get('summa', '0')).strip()
    
    try:
        summa = int(float(raw_sum))
    except (ValueError, TypeError):
        summa = 0

    if obekt and nomi:
        try:
            supabase.table('expenses').insert({
                'obekt': obekt,
                'nomi': nomi,
                'summa': summa
            }).execute()
        except Exception as e:
            print("Error inserting expense:", e)

    return jsonify({'status': 'ok'})

@app.route('/api/expenses_by_param', methods=['GET'])
def get_expenses_param():
    obekt_nomi = request.args.get('obekt', '').strip()
    try:
        res = supabase.table('expenses').select('nomi, summa').ilike('obekt', obekt_nomi).order('id', desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        print("Error fetching expenses:", e)
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
