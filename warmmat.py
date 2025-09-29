from flask import Flask, request, render_template, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    choice = request.form.get('choice', '')
    co_data = {}
    cwu_data = {}
    calc_data = {}
    results = {}
    show_calc_form = False

    if request.method == 'POST':
        print("POST request received:", request.form)  # Debug: Logowanie danych formularza
        if 'reset' in request.form:
            print("Reset clicked")
            return render_template('index.html', choice='', co_data={}, cwu_data={}, calc_data={}, results={}, show_calc_form=False)

        # Obsługa formularza wyboru typu (CO/CWU)
        if choice in ['CO', 'CWU'] and not request.form.get('m2_prev') and not request.form.get('people_prev'):
            if choice == 'CO':
                co_data = {
                    'm2': request.form.get('m2', ''),
                    'h': request.form.get('h', ''),
                    'm3': request.form.get('m3', ''),
                    't_out': request.form.get('t_out', ''),
                    't_in': request.form.get('t_in', ''),
                    'building_type': request.form.get('building_type', '')
                }
                print("CO data:", co_data)  # Debug
                if all(co_data.values()):
                    show_calc_form = True
            elif choice == 'CWU':
                cwu_data = {
                    'people': request.form.get('people', ''),
                    't_wu': request.form.get('t_wu', ''),
                    'building_type': request.form.get('building_type', '')
                }
                print("CWU data:", cwu_data)  # Debug
                if all(cwu_data.values()):
                    show_calc_form = True

        # Obsługa formularza wskaźników i wyników
        if request.form.get('m2_prev') or request.form.get('people_prev'):
            calc_data = {
                'kw_m3': request.form.get('kw_m3', '10.5'),
                'coal_mj_kg': request.form.get('coal_mj_kg', '25'),
                'wood_mj_kg': request.form.get('wood_mj_kg', '15'),
                'oil_mj_l': request.form.get('oil_mj_l', '38'),
                'other_mj': request.form.get('other_mj', '0'),
                'efficiency': request.form.get('efficiency', '100'),
                'simultaneity': request.form.get('simultaneity', '1')
            }
            print("Calc data:", calc_data)  # Debug
            if choice == 'CO':
                co_data = {
                    'm2': request.form.get('m2_prev', ''),
                    'h': request.form.get('h_prev', ''),
                    'm3': request.form.get('m3_prev', ''),
                    't_out': request.form.get('t_out_prev', ''),
                    't_in': request.form.get('t_in_prev', ''),
                    'building_type': request.form.get('building_type_prev', '')
                }
                print("CO data (prev):", co_data)  # Debug
            elif choice == 'CWU':
                cwu_data = {
                    'people': request.form.get('people_prev', ''),
                    't_wu': request.form.get('t_wu_prev', ''),
                    'building_type': request.form.get('building_type_prev', '')
                }
                print("CWU data (prev):", cwu_data)  # Debug

            # Obliczenia
            try:
                efficiency = float(calc_data['efficiency']) / 100
                simultaneity = float(calc_data['simultaneity'])
                kw_m3 = float(calc_data['kw_m3'])
                coal_mj_kg = float(calc_data['coal_mj_kg'])
                wood_mj_kg = float(calc_data['wood_mj_kg'])
                oil_mj_l = float(calc_data['oil_mj_l'])
                other_mj = float(calc_data['other_mj'])

                if choice == 'CO':
                    m2 = float(co_data['m2'])
                    t_out = float(co_data['t_out'])
                    t_in = float(co_data['t_in'])
                    building_type = co_data['building_type']
                    building_factors = {
                        'Mieszkanie': 0.04,
                        'Dom': 0.06,
                        'Magazyn': 0.03,
                        'Biurowiec': 0.05,
                        'Obiekt': 0.07
                    }
                    q = m2 * (t_in - t_out) * building_factors.get(building_type, 0.05) * simultaneity / efficiency
                    print("CO calculation: q =", q)  # Debug

                elif choice == 'CWU':
                    people = float(cwu_data['people'])
                    t_wu = float(cwu_data['t_wu'])
                    building_type = cwu_data['building_type']
                    water_usage = {
                        'Mieszkanie': 50,
                        'Dom': 60,
                        'Magazyn': 20,
                        'Biurowiec': 30,
                        'Obiekt': 40
                    }
                    q = (people * water_usage.get(building_type, 40) * 4.19 * (t_wu - 10) / 3600) * simultaneity / efficiency
                    print("CWU calculation: q =", q)  # Debug

                results = {
                    'heat_hour': round(q, 2),
                    'heat_day': round(q * 24, 2),
                    'heat_year': round(q * 24 * (180 if choice == 'CO' else 365), 2),
                    'gas_hour': round(q / kw_m3, 2) if kw_m3 > 0 else 0,
                    'gas_day': round(q * 24 / kw_m3, 2) if kw_m3 > 0 else 0,
                    'gas_year': round(q * 24 * (180 if choice == 'CO' else 365) / kw_m3, 2) if kw_m3 > 0 else 0,
                    'coal_hour': round(q * 3.6 / coal_mj_kg, 2) if coal_mj_kg > 0 else 0,
                    'coal_day': round(q * 24 * 3.6 / coal_mj_kg, 2) if coal_mj_kg > 0 else 0,
                    'coal_year': round(q * 24 * (180 if choice == 'CO' else 365) * 3.6 / coal_mj_kg, 2) if coal_mj_kg > 0 else 0,
                    'wood_hour': round(q * 3.6 / wood_mj_kg, 2) if wood_mj_kg > 0 else 0,
                    'wood_day': round(q * 24 * 3.6 / wood_mj_kg, 2) if wood_mj_kg > 0 else 0,
                    'wood_year': round(q * 24 * (180 if choice == 'CO' else 365) * 3.6 / wood_mj_kg, 2) if wood_mj_kg > 0 else 0,
                    'oil_hour': round(q * 3.6 / oil_mj_l, 2) if oil_mj_l > 0 else 0,
                    'oil_day': round(q * 24 * 3.6 / oil_mj_l, 2) if oil_mj_l > 0 else 0,
                    'oil_year': round(q * 24 * (180 if choice == 'CO' else 365) * 3.6 / oil_mj_l, 2) if oil_mj_l > 0 else 0,
                    'other_hour': round(q * 3.6 / other_mj, 2) if other_mj > 0 else 0,
                    'other_day': round(q * 24 * 3.6 / other_mj, 2) if other_mj > 0 else 0,
                    'other_year': round(q * 24 * (180 if choice == 'CO' else 365) * 3.6 / other_mj, 2) if other_mj > 0 else 0
                }
                print("Results:", results)  # Debug
            except (ValueError, ZeroDivisionError) as e:
                error = f"Nieprawidłowe dane wejściowe: {str(e)}"
                print("Error:", error)  # Debug

        # Obsługa przycisku Drukuj
        if 'print' in request.form:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            p.setFont("Helvetica", 12)
            y = 800
            p.drawString(100, y, f"Wyniki dla {choice}")
            y -= 20
            if choice == 'CO':
                for key, value in co_data.items():
                    p.drawString(100, y, f"{key}: {value}")
                    y -= 20
            elif choice == 'CWU':
                for key, value in cwu_data.items():
                    p.drawString(100, y, f"{key}: {value}")
                    y -= 20
            for key, value in calc_data.items():
                p.drawString(100, y, f"{key}: {value}")
                y -= 20
            for key, value in results.items():
                p.drawString(100, y, f"{key}: {value}")
                y -= 20
            p.showPage()
            p.save()
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='wyniki.pdf', mimetype='application/pdf')

    print("Rendering template with:", {"choice": choice, "co_data": co_data, "cwu_data": cwu_data, "calc_data": calc_data, "results": results, "show_calc_form": show_calc_form})  # Debug
    return render_template('index.html', error=error, choice=choice, co_data=co_data, cwu_data=cwu_data, calc_data=calc_data, results=results, show_calc_form=show_calc_form)

if __name__ == '__main__':
    app.run(debug=True)
