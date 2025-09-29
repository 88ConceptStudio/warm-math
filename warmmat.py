from flask import Flask, render_template, request, Response
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import os

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
        if 'reset' in request.form:
            return render_template('index.html', choice='', co_data={}, cwu_data={}, calc_data={}, results={}, show_calc_form=False, error=None)
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
                    if not all([co_data['m3'], co_data['t_out'], co_data['t_in'], co_data['building_type']]):
                        error = "Wypełnij wszystkie pola dla CO!"
                    else:
                        show_calc_form = True
                except ValueError:
                    error = "Wprowadź poprawne liczby dla CO!"
            elif 'kw_m3' in request.form:
                try:
                    calc_data = {
                        'kw_m3': float(request.form.get('kw_m3', '10.5')),
                        'coal_mj_kg': float(request.form.get('coal_mj_kg', '25')),
                        'wood_mj_kg': float(request.form.get('wood_mj_kg', '15')),
                        'oil_mj_l': float(request.form.get('oil_mj_l', '38')),
                        'other_mj': float(request.form.get('other_mj', '0') or 0),
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
                    u_values = {
                        'Mieszkanie': 0.5,
                        'Dom': 0.8,
                        'Magazyn': 1.2,
                        'Biurowiec': 1.0,
                        'Obiekt': 0.9
                    }
                    u = u_values.get(co_data['building_type'], 1.0)
                    delta_t = co_data['t_in'] - co_data['t_out']
                    q = u * co_data['m3'] * delta_t * calc_data['simultaneity'] / calc_data['efficiency'] / 1000
                    results = {
                        'heat_hour': round(q, 2),
                        'heat_day': round(q * 24, 2),
                        'heat_year': round(q * 24 * 180, 2),
                        'gas_hour': round(q / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                        'gas_day': round((q * 24) / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                        'gas_year': round((q * 24 * 180) / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                        'coal_hour': round(q * 3.6 / calc_data['coal_mj_kg'], 2) if calc_data['coal_mj_kg'] > 0 else 0,
                        'coal_day': round((q * 24 * 3.6) / calc_data['coal_mj_kg'], 2) if calc_data['coal_mj_kg'] > 0 else 0,
                        'coal_year': round((q * 24 * 180 * 3.6) / calc_data['coal_mj_kg'], 2) if calc_data['coal_mj_kg'] > 0 else 0,
                        'wood_hour': round(q * 3.6 / calc_data['wood_mj_kg'], 2) if calc_data['wood_mj_kg'] > 0 else 0,
                        'wood_day': round((q * 24 * 3.6) / calc_data['wood_mj_kg'], 2) if calc_data['wood_mj_kg'] > 0 else 0,
                        'wood_year': round((q * 24 * 180 * 3.6) / calc_data['wood_mj_kg'], 2) if calc_data['wood_mj_kg'] > 0 else 0,
                        'oil_hour': round(q * 3.6 / calc_data['oil_mj_l'], 2) if calc_data['oil_mj_l'] > 0 else 0,
                        'oil_day': round((q * 24 * 3.6) / calc_data['oil_mj_l'], 2) if calc_data['oil_mj_l'] > 0 else 0,
                        'oil_year': round((q * 24 * 180 * 3.6) / calc_data['oil_mj_l'], 2) if calc_data['oil_mj_l'] > 0 else 0,
                        'other_hour': round(q * 3.6 / calc_data['other_mj'], 2) if calc_data['other_mj'] > 0 else 0,
                        'other_day': round((q * 24 * 3.6) / calc_data['other_mj'], 2) if calc_data['other_mj'] > 0 else 0,
                        'other_year': round((q * 24 * 180 * 3.6) / calc_data['other_mj'], 2) if calc_data['other_mj'] > 0 else 0
                    }
                except ValueError:
                    error = "Wprowadź poprawne liczby w formularzu wskaźników dla CO!"
        elif choice == 'CWU':
            if 'people' in request.form:
                try:
                    cwu_data = {
                        'people': request.form.get('people', ''),
                        't_wu': request.form.get('t_wu', ''),
                        'building_type': request.form.get('building_type', '')
                    }
                    if not all([cwu_data['people'], cwu_data['t_wu'], cwu_data['building_type']]):
                        error = "Wypełnij wszystkie pola dla CWU!"
                    else:
                        show_calc_form = True
                except ValueError:
                    error = "Wprowadź poprawne liczby dla CWU!"
            elif 'kw_m3' in request.form:
                try:
                    calc_data = {
                        'kw_m3': float(request.form.get('kw_m3', '10.5')),
                        'coal_mj_kg': float(request.form.get('coal_mj_kg', '25')),
                        'wood_mj_kg': float(request.form.get('wood_mj_kg', '15')),
                        'oil_mj_l': float(request.form.get('oil_mj_l', '38')),
                        'other_mj': float(request.form.get('other_mj', '0') or 0),
                        'efficiency': float(request.form.get('efficiency', '100')) / 100,
                        'simultaneity': float(request.form.get('simultaneity', '1'))
                    }
                    cwu_data = {
                        'people': float(request.form.get('people_prev', '0') or 0),
                        't_wu': float(request.form.get('t_wu_prev', '0') or 0),
                        'building_type': request.form.get('building_type_prev', '')
                    }
                    q = cwu_data['people'] * 50 * (cwu_data['t_wu'] - 10) * calc_data['simultaneity'] / calc_data['efficiency'] / 1000
                    results = {
                        'heat_hour': round(q / 24, 2),
                        'heat_day': round(q, 2),
                        'heat_year': round(q * 365, 2),
                        'gas_hour': round((q / 24) / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                        'gas_day': round(q / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                        'gas_year': round((q * 365) / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                        'coal_hour': round((q / 24) * 3.6 / calc_data['coal_mj_kg'], 2) if calc_data['coal_mj_kg'] > 0 else 0,
                        'coal_day': round(q * 3.6 / calc_data['coal_mj_kg'], 2) if calc_data['coal_mj_kg'] > 0 else 0,
                        'coal_year': round((q * 365) * 3.6 / calc_data['coal_mj_kg'], 2) if calc_data['coal_mj_kg'] > 0 else 0,
                        'wood_hour': round((q / 24) * 3.6 / calc_data['wood_mj_kg'], 2) if calc_data['wood_mj_kg'] > 0 else 0,
                        'wood_day': round(q * 3.6 / calc_data['wood_mj_kg'], 2) if calc_data['wood_mj_kg'] > 0 else 0,
                        'wood_year': round((q * 365) * 3.6 / calc_data['wood_mj_kg'], 2) if calc_data['wood_mj_kg'] > 0 else 0,
                        'oil_hour': round((q / 24) * 3.6 / calc_data['oil_mj_l'], 2) if calc_data['oil_mj_l'] > 0 else 0,
                        'oil_day': round(q * 3.6 / calc_data['oil_mj_l'], 2) if calc_data['oil_mj_l'] > 0 else 0,
                        'oil_year': round((q * 365) * 3.6 / calc_data['oil_mj_l'], 2) if calc_data['oil_mj_l'] > 0 else 0,
                        'other_hour': round((q / 24) * 3.6 / calc_data['other_mj'], 2) if calc_data['other_mj'] > 0 else 0,
                        'other_day': round(q * 3.6 / calc_data['other_mj'], 2) if calc_data['other_mj'] > 0 else 0,
                        'other_year': round((q * 365) * 3.6 / calc_data['other_mj'], 2) if calc_data['other_mj'] > 0 else 0
                    }
                except ValueError:
                    error = "Wprowadź poprawne liczby w formularzu wskaźników dla CWU!"
        elif 'print' in request.form:
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.setFont("Helvetica", 12)
            y = 800
            c.drawString(100, y, f"WARM-MATH - Wyniki dla {choice}")
            y -= 20
            if choice == 'CO':
                c.drawString(100, y, f"Powierzchnia: {request.form.get('m2_prev', '')} [m²]")
                y -= 20
                c.drawString(100, y, f"Wysokość: {request.form.get('h_prev', '')} [m]")
                y -= 20
                c.drawString(100, y, f"Kubatura: {request.form.get('m3_prev', '')} [m³]")
                y -= 20
                c.drawString(100, y, f"Temp-OUT: {request.form.get('t_out_prev', '')} [°C]")
                y -= 20
                c.drawString(100, y, f"Temp-IN: {request.form.get('t_in_prev', '')} [°C]")
                y -= 20
                c.drawString(100, y, f"Typ budynku: {request.form.get('building_type_prev', '')}")
                y -= 20
            elif choice == 'CWU':
                c.drawString(100, y, f"Liczba osób: {request.form.get('people_prev', '')}")
                y -= 20
                c.drawString(100, y, f"Temp-WU: {request.form.get('t_wu_prev', '')} [°C]")
                y -= 20
                c.drawString(100, y, f"Typ budynku: {request.form.get('building_type_prev', '')}")
                y -= 20
            c.drawString(100, y, f"Wartość opałowa gazu: {request.form.get('kw_m3', '')} [kW/m³]")
            y -= 20
            c.drawString(100, y, f"Wartość opałowa węgla: {request.form.get('coal_mj_kg', '')} [MJ/kg]")
            y -= 20
            c.drawString(100, y, f"Wartość opałowa drewna: {request.form.get('wood_mj_kg', '')} [MJ/kg]")
            y -= 20
            c.drawString(100, y, f"Wartość opałowa oleju: {request.form.get('oil_mj_l', '')} [MJ/l]")
            y -= 20
            c.drawString(100, y, f"Wartość opałowa inne: {request.form.get('other_mj', '')} [MJ]")
            y -= 20
            c.drawString(100, y, f"Sprawność kotła: {float(request.form.get('efficiency', '100'))} [%]")
            y -= 20
            c.drawString(100, y, f"Jednoczesność: {request.form.get('simultaneity', '')}")
            y -= 40
            c.drawString(100, y, "Wyniki:")
            y -= 20
            c.drawString(100, y, f"Ciepło na godzinę: {request.form.get('heat_hour', '')} [kW/h]")
            y -= 20
            c.drawString(100, y, f"Ciepło na dobę: {request.form.get('heat_day', '')} [kW/d]")
            y -= 20
            c.drawString(100, y, f"Ciepło na rok: {request.form.get('heat_year', '')} [kW/r]")
            y -= 20
            if float(request.form.get('kw_m3', '0') or 0) > 0:
                c.drawString(100, y, f"Gaz na godzinę: {request.form.get('gas_hour', '')} [m³/h]")
                y -= 20
                c.drawString(100, y, f"Gaz na dobę: {request.form.get('gas_day', '')} [m³/d]")
                y -= 20
                c.drawString(100, y, f"Gaz na rok: {request.form.get('gas_year', '')} [m³/r]")
                y -= 20
            if float(request.form.get('coal_mj_kg', '0') or 0) > 0:
                c.drawString(100, y, f"Węgiel na godzinę: {request.form.get('coal_hour', '')} [kg/h]")
                y -= 20
                c.drawString(100, y, f"Węgiel na dobę: {request.form.get('coal_day', '')} [kg/d]")
                y -= 20
                c.drawString(100, y, f"Węgiel na rok: {request.form.get('coal_year', '')} [kg/r]")
                y -= 20
            if float(request.form.get('wood_mj_kg', '0') or 0) > 0:
                c.drawString(100, y, f"Drewno na godzinę: {request.form.get('wood_hour', '')} [kg/h]")
                y -= 20
                c.drawString(100, y, f"Drewno na dobę: {request.form.get('wood_day', '')} [kg/d]")
                y -= 20
                c.drawString(100, y, f"Drewno na rok: {request.form.get('wood_year', '')} [kg/r]")
                y -= 20
            if float(request.form.get('oil_mj_l', '0') or 0) > 0:
                c.drawString(100, y, f"Olej na godzinę: {request.form.get('oil_hour', '')} [l/h]")
                y -= 20
                c.drawString(100, y, f"Olej na dobę: {request.form.get('oil_day', '')} [l/d]")
                y -= 20
                c.drawString(100, y, f"Olej na rok: {request.form.get('oil_year', '')} [l/r]")
                y -= 20
            if float(request.form.get('other_mj', '0') or 0) > 0:
                c.drawString(100, y, f"Inne na godzinę: {request.form.get('other_hour', '')} [jedn/h]")
                y -= 20
                c.drawString(100, y, f"Inne na dobę: {request.form.get('other_day', '')} [jedn/d]")
                y -= 20
                c.drawString(100, y, f"Inne na rok: {request.form.get('other_year', '')} [jedn/r]")
            c.showPage()
            c.save()
            buffer.seek(0)
            return Response(buffer.getvalue(), mimetype='application/pdf', headers={'Content-Disposition': 'attachment;filename=wyniki.pdf'})
    return render_template('index.html', choice=choice, co_data=co_data, cwu_data=cwu_data, calc_data=calc_data, results=results, show_calc_form=show_calc_form, error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)