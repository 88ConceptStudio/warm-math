from flask import Flask, render_template, request
from vector import Vector
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result_str = None
    plot_url = None

    if request.method == 'POST':
        try:
            m1 = int(request.form['m1'])
            r1 = int(request.form['r1'])
            m2 = int(request.form['m2'])
            r2 = int(request.form['r2'])
            operation = request.form['operation']

            v1 = Vector(m1, r1)
            v2 = Vector(m2, r2)

            # Wykonaj operację
            if operation == 'Dodawanie':
                result = v1.dodawanie(v2)
            elif operation == 'Odejmowanie':
                result = v1.odejmowanie(v2)
            elif operation == 'Mnozenie':
                result = v1.mnozenie(v2)
            elif operation == 'Dzielenie':
                result = v1.dzielenie(v2)
            else:
                raise ValueError("Nieznana operacja")

            # Przygotuj wynik numeryczny
            result_str = f"({result.m}, {result.r})" if result != "Niezdefiniowane" else "Niezdefiniowane"

            # Generuj wykres
            if result != "Niezdefiniowane":
                plt.figure(figsize=(6, 6))
                plt.axhline(0, color='black', linewidth=0.5)
                plt.axvline(0, color='black', linewidth=0.5)
                plt.grid(True)

                # Rysuj wektory
                plt.quiver(0, 0, v1.m, v1.r, angles='xy', scale_units='xy', scale=1, color='blue', label='Wektor 1')
                plt.quiver(0, 0, v2.m, v2.r, angles='xy', scale_units='xy', scale=1, color='red', label='Wektor 2')
                plt.quiver(0, 0, result.m, result.r, angles='xy', scale_units='xy', scale=1, color='green', label='Wynik')

                # Ustaw granice osi
                max_val = max(abs(v1.m), abs(v1.r), abs(v2.m), abs(v2.r), abs(result.m), abs(result.r)) + 5
                plt.xlim(-max_val, max_val)
                plt.ylim(-max_val, max_val)

                plt.legend()

                # Zapisz wykres
                plot_path = os.path.join('static', 'plot.png')
                plt.savefig(plot_path)
                plt.close()
                plot_url = '/static/plot.png'

        except ValueError as e:
            result_str = f"Błąd: Wprowadź poprawne liczby całkowite lub wybierz prawidłową operację ({str(e)})"
        except Exception as e:
            result_str = f"Błąd: {str(e)}"

    return render_template('index.html', result=result_str, plot_url=plot_url)

if __name__ == '__main__':
    app.run(debug=True)