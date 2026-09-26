@app.route('/api/expenses_by_param', methods=['GET'])
def get_expenses_param():
    init_db()
    obekt_nomi = request.args.get('obekt', '').strip()
    expenses = []
    
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ob'ekt nomini katta-kichik harflar va bo'sh joylarsiz solishtiramiz
                row_obekt = str(row.get('obekt', '')).strip()
                if row_obekt.lower() == obekt_nomi.lower():
                    # Summani xavfsiz songa aylantiramiz
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
