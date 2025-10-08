from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

app = Flask(__name__)

# Rejestracja czcionki obsługującej polskie znaki
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

@app.route('/', methods=['GET', 'POST'])
def index():
    choice = None
    co_data = {}
    cwu_data = {}
    calc_data = {}
    results = {}
    error = None
    show_calc_form = False

    if request.method == 'POST':
        print("=== Start POST request ===")
        print("Request form data:", dict(request.form))

        if 'reset' in request.form:
            print("Reset triggered")
            return render_template('index.html', choice=None, co_data={}, cwu_data={}, calc_data={}, results={}, error=None, show_calc_form=False)

        choice = request.form.get('choice')
        print("Selected choice:", choice)
        if not choice:
            error = "Proszę wybrać typ (CO lub CWU)."
            print("Error: No choice selected")
            return render_template('index.html', choice=None, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

        if choice == 'CO':
            print("Processing CO form")
            try:
                # Pobieranie danych z formularza lub _prev
                m2 = request.form.get('m2') or request.form.get('m2_prev')
                h = request.form.get('h') or request.form.get('h_prev')
                m3 = request.form.get('m3') or request.form.get('m3_prev')
                t_out = request.form.get('t_out') or request.form.get('t_out_prev')
                t_in = request.form.get('t_in') or request.form.get('t_in_prev')
                building_type = request.form.get('building_type') or request.form.get('building_type_prev')

                print("CO raw data:", {'m2': m2, 'h': h, 'm3': m3, 't_out': t_out, 't_in': t_in, 'building_type': building_type})

                # Konwersja i walidacja
                try:
                    m2 = float(m2) if m2 and m2.strip() else None
                    h = float(h) if h and h.strip() else None
                    m3 = float(m3) if m3 and m3.strip() else None
                    t_out = float(t_out) if t_out and t_out.strip() else None
                    t_in = float(t_in) if t_in and t_in.strip() else None
                except (ValueError, TypeError) as e:
                    error = f"Proszę wprowadzić prawidłowe wartości liczbowe dla CO: {str(e)}"
                    print(f"Error: Invalid numeric values for CO: {str(e)}")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                if not building_type:
                    error = "Proszę wybrać typ budynku dla CO."
                    print("Error: No building type for CO")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                # Obliczanie brakujących wartości
                if m2 and h and not m3:
                    m3 = m2 * h
                elif m2 and m3 and not h:
                    h = m3 / m2 if m2 != 0 else None
                elif h and m3 and not m2:
                    m2 = m3 / h if h != 0 else None

                print("CO after calculations:", {'m2': m2, 'h': h, 'm3': m3, 't_out': t_out, 't_in': t_in, 'building_type': building_type})

                if not all([m2, h, m3, t_out, t_in, building_type]):
                    error = f"Proszę wypełnić wszystkie pola dla CO. Brakujące: {', '.join([k for k, v in {'m2': m2, 'h': h, 'm3': m3, 't_out': t_out, 't_in': t_in, 'building_type': building_type}.items() if not v])}"
                    print(f"Error: Incomplete CO data: {error}")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                # Walidacja temperatur
                if t_in <= t_out:
                    error = f"Temperatura wewnętrzna (Temp-IN: {t_in}°C) musi być wyższa niż zewnętrzna (Temp-OUT: {t_out}°C) dla CO."
                    print(f"Error: Invalid temperature for CO: t_in ({t_in}) <= t_out ({t_out})")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                co_data = {
                    'm2': m2,
                    'h': h,
                    'm3': m3,
                    't_out': t_out,
                    't_in': t_in,
                    'building_type': building_type
                }
                print("CO validated data:", co_data)

                # Przejście do formularza wskaźników
                if 'kw_m3' not in request.form and 'print' not in request.form:
                    print("Showing calc form for CO")
                    return render_template('index.html', choice=choice, co_data=co_data, cwu_data={}, calc_data={}, results={}, error=None, show_calc_form=True)

            except Exception as e:
                error = f"Błąd w danych CO: {str(e)}"
                print(f"Error in CO processing: {error}")
                return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

        elif choice == 'CWU':
            print("Processing CWU form")
            try:
                people = request.form.get('people') or request.form.get('people_prev')
                t_wu = request.form.get('t_wu') or request.form.get('t_wu_prev')
                building_type = request.form.get('building_type') or request.form.get('building_type_prev')

                print("CWU raw data:", {'people': people, 't_wu': t_wu, 'building_type': building_type})

                try:
                    people = int(people) if people and people.strip() else None
                    t_wu = float(t_wu) if t_wu and t_wu.strip() else None
                except (ValueError, TypeError) as e:
                    error = f"Proszę wprowadzić prawidłowe wartości liczbowe dla CWU: {str(e)}"
                    print(f"Error: Invalid numeric values for CWU: {str(e)}")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                if not building_type:
                    error = "Proszę wybrać typ budynku dla CWU."
                    print("Error: No building type for CWU")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                if not all([people, t_wu, building_type]):
                    error = f"Proszę wypełnić wszystkie pola dla CWU. Brakujące: {', '.join([k for k, v in {'people': people, 't_wu': t_wu, 'building_type': building_type}.items() if not v])}"
                    print(f"Error: Incomplete CWU data: {error}")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                # Walidacja temperatury wody użytkowej
                if t_wu <= 10:
                    error = f"Temperatura wody użytkowej (Temp-WU: {t_wu}°C) musi być wyższa niż 10°C dla CWU."
                    print(f"Error: Invalid temperature for CWU: t_wu ({t_wu}) <= 10")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

                cwu_data = {
                    'people': people,
                    't_wu': t_wu,
                    'building_type': building_type
                }
                print("CWU validated data:", cwu_data)

                if 'kw_m3' not in request.form and 'print' not in request.form:
                    print("Showing calc form for CWU")
                    return render_template('index.html', choice=choice, co_data={}, cwu_data=cwu_data, calc_data={}, results={}, error=None, show_calc_form=True)

            except Exception as e:
                error = f"Błąd w danych CWU: {str(e)}"
                print(f"Error in CWU processing: {error}")
                return render_template('index.html', choice=choice, co_data={}, cwu_data={}, calc_data={}, results={}, error=error, show_calc_form=False)

        if 'kw_m3' in request.form or 'print' in request.form:
            print("Processing calculations")
            try:
                calc_data = {
                    'kw_m3': float(request.form.get('kw_m3', 10.5)),
                    'coal_mj_kg': float(request.form.get('coal_mj_kg', 25)),
                    'wood_mj_kg': float(request.form.get('wood_mj_kg', 15)),
                    'oil_mj_l': float(request.form.get('oil_mj_l', 38)),
                    'other_mj': float(request.form.get('other_mj', 0)),
                    'efficiency': float(request.form.get('efficiency', 100)) / 100,
                    'simultaneity': float(request.form.get('simultaneity', 1))
                }
                print("Calc data:", calc_data)

                if choice == 'CO':
                    building_factors = {
                        'Mieszkanie': 70,
                        'Dom': 90,
                        'Magazyn': 50,
                        'Biurowiec': 80,
                        'Obiekt': 100
                    }
                    if not all(key in co_data for key in ['m2', 'building_type', 't_in', 't_out']):
                        error = "Brakujące dane CO dla obliczeń."
                        print(f"Error: Missing CO data: {co_data}")
                        raise ValueError(error)
                    q = (co_data['m2'] * building_factors[co_data['building_type']] * (co_data['t_in'] - co_data['t_out'])) / 1000
                    q = q * calc_data['simultaneity'] / calc_data['efficiency']
                elif choice == 'CWU':
                    if not all(key in cwu_data for key in ['people', 't_wu']):
                        error = "Brakujące dane CWU dla obliczeń."
                        print(f"Error: Missing CWU data: {cwu_data}")
                        raise ValueError(error)
                    q = (cwu_data['people'] * 50 * (cwu_data['t_wu'] - 10) * 4.19) / (3600 * 1000)
                    q = q / calc_data['efficiency']

                print("Calculated q:", q)
                results = {
                    'heat_hour': round(q, 2),
                    'heat_day': round(q * 24, 2),
                    'heat_year': round(q * 24 * (180 if choice == 'CO' else 365), 2),
                    'gas_hour': round(q / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                    'gas_day': round((q * 24) / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                    'gas_year': round((q * 24 * (180 if choice == 'CO' else 365)) / calc_data['kw_m3'], 2) if calc_data['kw_m3'] > 0 else 0,
                    'coal_hour': round((q * 3600) / (calc_data['coal_mj_kg'] * 1000), 2) if calc_data['coal_mj_kg'] > 0 else 0,
                    'coal_day': round((q * 24 * 3600) / (calc_data['coal_mj_kg'] * 1000), 2) if calc_data['coal_mj_kg'] > 0 else 0,
                    'coal_year': round((q * 24 * (180 if choice == 'CO' else 365) * 3600) / (calc_data['coal_mj_kg'] * 1000), 2) if calc_data['coal_mj_kg'] > 0 else 0,
                    'wood_hour': round((q * 3600) / (calc_data['wood_mj_kg'] * 1000), 2) if calc_data['wood_mj_kg'] > 0 else 0,
                    'wood_day': round((q * 24 * 3600) / (calc_data['wood_mj_kg'] * 1000), 2) if calc_data['wood_mj_kg'] > 0 else 0,
                    'wood_year': round((q * 24 * (180 if choice == 'CO' else 365) * 3600) / (calc_data['wood_mj_kg'] * 1000), 2) if calc_data['wood_mj_kg'] > 0 else 0,
                    'oil_hour': round((q * 3600) / (calc_data['oil_mj_l'] * 1000), 2) if calc_data['oil_mj_l'] > 0 else 0,
                    'oil_day': round((q * 24 * 3600) / (calc_data['oil_mj_l'] * 1000), 2) if calc_data['oil_mj_l'] > 0 else 0,
                    'oil_year': round((q * 24 * (180 if choice == 'CO' else 365) * 3600) / (calc_data['oil_mj_l'] * 1000), 2) if calc_data['oil_mj_l'] > 0 else 0,
                    'other_hour': round((q * 3600) / (calc_data['other_mj'] * 1000), 2) if calc_data['other_mj'] > 0 else 0,
                    'other_day': round((q * 24 * 3600) / (calc_data['other_mj'] * 1000), 2) if calc_data['other_mj'] > 0 else 0,
                    'other_year': round((q * 24 * (180 if choice == 'CO' else 365) * 3600) / (calc_data['other_mj'] * 1000), 2) if calc_data['other_mj'] > 0 else 0
                }
                print("Results:", results)

                if 'print' in request.form:
                    print("Generating PDF")
                    buffer = io.BytesIO()
                    p = canvas.Canvas(buffer, pagesize=A4)
                    p.setFont('DejaVuSans', 12)
                    y = 750
                    line_height = 20
                    bottom_margin = 50

                    def add_line(text, y):
                        if y < bottom_margin:
                            p.showPage()
                            p.setFont('DejaVuSans', 12)
                            return 750
                        p.drawString(100, y, text)
                        return y - line_height

                    p.drawString(100, y, f"Wyniki dla {choice}")
                    y -= line_height
                    if choice == 'CO':
                        y = add_line(f"Powierzchnia: {co_data.get('m2', 'N/A')} [m²]", y)
                        y = add_line(f"Wysokość: {co_data.get('h', 'N/A')} [m]", y)
                        y = add_line(f"Kubatura: {co_data.get('m3', 'N/A')} [m³]", y)
                        y = add_line(f"Temp-OUT: {co_data.get('t_out', 'N/A')} [°C]", y)
                        y = add_line(f"Temp-IN: {co_data.get('t_in', 'N/A')} [°C]", y)
                        y = add_line(f"Typ budynku: {co_data.get('building_type', 'N/A')}", y)
                    elif choice == 'CWU':
                        y = add_line(f"Liczba osób: {cwu_data.get('people', 'N/A')}", y)
                        y = add_line(f"Temp-WU: {cwu_data.get('t_wu', 'N/A')} [°C]", y)
                        y = add_line(f"Typ budynku: {cwu_data.get('building_type', 'N/A')}", y)
                    y = add_line(f"Sprawność kotła: {calc_data['efficiency'] * 100} [%]", y)
                    y = add_line(f"Jednoczesność: {calc_data['simultaneity']}", y)
                    y = add_line("Wyniki:", y)
                    y = add_line("Olej:", y)
                    y = add_line(f"Wartość opałowa: {calc_data['oil_mj_l']} [MJ/l]", y)
                    y = add_line(f"godzina [l/h]", y)
                    y = add_line(f"{results['oil_hour']}", y)
                    y = add_line(f"doba (24h) [l/d]", y)
                    y = add_line(f"{results['oil_day']}", y)
                    y = add_line(f"rok ({'180d' if choice == 'CO' else '365d'}) [l/r]", y)
                    y = add_line(f"{results['oil_year']}", y)
                    y = add_line("Inne:", y)
                    y = add_line(f"Wartość opałowa: {calc_data['other_mj']} [MJ]", y)
                    y = add_line(f"godzina [jedn/h]", y)
                    y = add_line(f"{results['other_hour']}", y)
                    y = add_line(f"doba (24h) [jedn/d]", y)
                    y = add_line(f"{results['other_day']}", y)
                    y = add_line(f"rok ({'180d' if choice == 'CO' else '365d'}) [jedn/r]", y)
                    y = add_line(f"{results['other_year']}", y)
                    y = add_line("Gaz:", y)
                    y = add_line(f"Wartość opałowa: {calc_data['kw_m3']} [kW/m³]", y)
                    y = add_line(f"godzina [m³/h]", y)
                    y = add_line(f"{results['gas_hour']}", y)
                    y = add_line(f"doba (24h) [m³/d]", y)
                    y = add_line(f"{results['gas_day']}", y)
                    y = add_line(f"rok ({'180d' if choice == 'CO' else '365d'}) [m³/r]", y)
                    y = add_line(f"{results['gas_year']}", y)
                    y = add_line("Wartości ciepła:", y)
                    y = add_line(f"godzina [kW/h]", y)
                    y = add_line(f"{results['heat_hour']}", y)
                    y = add_line(f"doba (24h) [kW/d]", y)
                    y = add_line(f"{results['heat_day']}", y)
                    y = add_line(f"rok ({'180d' if choice == 'CO' else '365d'}) [kW/r]", y)
                    y = add_line(f"{results['heat_year']}", y)
                    y = add_line("Węgiel:", y)
                    y = add_line(f"Wartość opałowa: {calc_data['coal_mj_kg']} [MJ/kg]", y)
                    y = add_line(f"godzina [kg/h]", y)
                    y = add_line(f"{results['coal_hour']}", y)
                    y = add_line(f"doba (24h) [kg/d]", y)
                    y = add_line(f"{results['coal_day']}", y)
                    y = add_line(f"rok ({'180d' if choice == 'CO' else '365d'}) [kg/r]", y)
                    y = add_line(f"{results['coal_year']}", y)
                    y = add_line("Drewno:", y)
                    y = add_line(f"Wartość opałowa: {calc_data['wood_mj_kg']} [MJ/kg]", y)
                    y = add_line(f"godzina [kg/h]", y)
                    y = add_line(f"{results['wood_hour']}", y)
                    y = add_line(f"doba (24h) [kg/d]", y)
                    y = add_line(f"{results['wood_day']}", y)
                    y = add_line(f"rok ({'180d' if choice == 'CO' else '365d'}) [kg/r]", y)
                    y = add_line(f"{results['wood_year']}", y)
                    p.showPage()
                    p.save()
                    buffer.seek(0)
                    return send_file(buffer, as_attachment=True, download_name='wyniki.pdf', mimetype='application/pdf')

                print("Rendering results for", choice)
                return render_template('index.html', choice=choice, co_data=co_data, cwu_data=cwu_data, calc_data=calc_data, results=results, error=None, show_calc_form=True)

            except (ValueError, TypeError, KeyError) as e:
                error = f"Błąd w obliczeniach: {str(e)}"
                print(f"Error in calculations: {error}")
                return render_template('index.html', choice=choice, co_data=co_data, cwu_data=cwu_data, calc_data={}, results={}, error=error, show_calc_form=True)

    print("Rendering initial page")
    return render_template('index.html', choice=choice, co_data=co_data, cwu_data=cwu_data, calc_data=calc_data, results=results, error=error, show_calc_form=show_calc_form)

if __name__ == '__main__':
    app.run(debug=True)