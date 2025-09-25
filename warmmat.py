from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    choice = ''
    co_data = {}
    cwu_data = {}
    calc_data = {}
    results = {}
    show_calc_form = False
    error = None
    if request.method == 'POST':
        choice = request.form.get('choice', '')
        if choice == 'CO':
            if 'm2' in request.form:
                try:
                    co_data = {
                        'm2': request.form.get('m2', ''),
                        'h': request.form.get('h', ''),
                        'm3': request.form.get('m3', ''),
                        't_out': request.form.get('t_out', ''),
                        't_in': request.form.get('t_in', ''),
                        'building_type': request.form.get('building_type', '')
                    }
                    if not co_data['m3'] or not co_data['t_out'] or not co_data['t_in'] or not co_data['building_type']:
                        error = "Wypełnij wszystkie pola dla CO!"
                    else:
                        show_calc_form = True
                except ValueError:
                    error = "Wprowadź poprawne liczby dla CO!"
            elif 'kw_m3' in request.form:
                try:
                    calc_data = {
                        'kw_m3': float(request.form.get('kw_m3', '10.5')),
                        'efficiency': float(request.form.get('efficiency', '100')) / 100,
                        'simultaneity': float(request.form.get('simultaneity', '1'))
                    }
                    co_data = {
                        'm2': request.form.get('m2_prev', ''),
                        'h': request.form.get('h_prev', ''),
                        'm3': float(request.form.get('m3_prev', '0') or 0),
                        't_out': float(request.form.get('t_out_prev', '0') or 0),
                        't_in': float(request.form.get('t_in_prev', '0') or 0),
                        'building_type': request.form.get('building_type_prev', '')
                    }
                    # Obliczenia dla CO
                    u_values = {
                        'Mieszkanie': 0.5,
                        'Dom': 0.8,
                        'Magazyn': 1.2,
                        'Biurowiec': 1.0,
                        'Obiekt': 0.9
                    }
                    u = u_values.get(co_data['building_type'], 1.0)
                    delta_t = co_data['t_in'] - co_data['t_out']
                    q = u * co_data['m3'] * delta_t * calc_data['simultaneity'] / calc_data['efficiency'] / 1000  # Przelicz na kW
                    results = {
                        'heat_hour': round(q, 2),
                        'heat_day': round(q * 24, 2),
                        'heat_year': round(q * 24 * 180, 2),  # Rok opałowy: 180 dni
                        'gas_hour': round(q / calc_data['kw_m3'], 2),
                        'gas_day': round((q * 24) / calc_data['kw_m3'], 2),
                        'gas_year': round((q * 24 * 180) / calc_data['kw_m3'], 2)  # Rok opałowy: 180 dni
                    }
                except ValueError:
                    error = "Wprowadź poprawne liczby w formularzu wskaźników dla CO!"
        elif choice == 'CWU':
            if 'people' in request.form and 'kw_m3' not in request.form:
                try:
                    cwu_data = {
                        'people': request.form.get('people', ''),
                        't_wu': request.form.get('t_wu', ''),
                        'building_type': request.form.get('building_type', '')
                    }
                    if not cwu_data['people'] or not cwu_data['t_wu'] or not cwu_data['building_type']:
                        error = "Wypełnij wszystkie pola dla CWU!"
                    else:
                        show_calc_form = True
                except ValueError:
                    error = "Wprowadź poprawne liczby dla CWU!"
            elif 'kw_m3' in request.form:
                try:
                    calc_data = {
                        'kw_m3': float(request.form.get('kw_m3', '10.5')),
                        'efficiency': float(request.form.get('efficiency', '100')) / 100,
                        'simultaneity': float(request.form.get('simultaneity', '1'))
                    }
                    cwu_data = {
                        'people': float(request.form.get('people_prev', '0') or 0),
                        't_wu': float(request.form.get('t_wu_prev', '0') or 0),
                        'building_type': request.form.get('building_type_prev', '')
                    }
                    # Obliczenia dla CWU
                    q = cwu_data['people'] * 50 * (cwu_data['t_wu'] - 10) * calc_data['simultaneity'] / calc_data['efficiency'] / 1000  # Przelicz na kW
                    results = {
                        'heat_hour': round(q / 24, 2),
                        'heat_day': round(q, 2),
                        'heat_year': round(q * 365, 2),  # Pełny rok: 365 dni
                        'gas_hour': round((q / 24) / calc_data['kw_m3'], 2),
                        'gas_day': round(q / calc_data['kw_m3'], 2),
                        'gas_year': round((q * 365) / calc_data['kw_m3'], 2)  # Pełny rok: 365 dni
                    }
                except ValueError:
                    error = "Wprowadź poprawne liczby w formularzu wskaźników dla CWU!"
    return render_template('index.html', choice=choice, co_data=co_data, cwu_data=cwu_data, calc_data=calc_data, results=results, show_calc_form=show_calc_form, error=error)

if __name__ == '__main__':
    app.run(debug=True)
