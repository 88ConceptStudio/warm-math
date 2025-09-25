from flask import Flask, render_template
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/')
def home():
    # Przykładowe dane dla 1. pozycji (na podstawie 100 losowań Lotto)
    first_position = [5, 19, 2, 3, 9, 5, 1, 7, 14, 19] * 10  # Symulacja 100 losowań
    plt.hist(first_position, bins=range(1, 50), edgecolor='black')
    plt.title('Histogram: Pierwsza pozycja w Lotto')
    plt.xlabel('Liczba')
    plt.ylabel('Częstotliwość')
    plt.savefig('static/hist.png')  # Zapisuje wykres w folderze static
    plt.close()
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
