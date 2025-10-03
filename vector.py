class Vector:
    def __init__(self, m, r):
        self.m = m
        self.r = r

def odwrotna_redukcja(v):
    return Vector(0, v.r + 8 * v.m)

def redukcja(v):
    r, m = v.r, v.m
    while True:
        n = min(r // 8 + 1, 8)
        if r < 8 * n:
            break
        k = (r - 8 * (n-1)) // 8
        if k <= 64:
            r = r - 8 * k
            m = m + k
            break
        r = r - 8 * 64
        m = 0
    return Vector(m, r)

def dodawanie(v1, v2):
    v1_prime = odwrotna_redukcja(v1)
    v2_prime = odwrotna_redukcja(v2)
    r_sum = v1_prime.r + v2_prime.r
    return redukcja(Vector(0, r_sum))

def mnozenie(v1, v2):
    v1_prime = odwrotna_redukcja(v1)
    v2_prime = odwrotna_redukcja(v2)
    r_prod = v1_prime.r * v2_prime.r
    return redukcja(Vector(0, r_prod))

def dzielenie(v1, v2):
    v1_prime = odwrotna_redukcja(v1)
    v2_prime = odwrotna_redukcja(v2)
    if v2_prime.r == 0 or v1_prime.r % v2_prime.r != 0:
        return "Niezdefiniowane"
    r_div = v1_prime.r // v2_prime.r
    return redukcja(Vector(0, r_div))

def odejmowanie(v1, v2):
    v1_prime = odwrotna_redukcja(v1)
    v2_prime = odwrotna_redukcja(v2)
    r_diff = v1_prime.r - v2_prime.r
    if r_diff < 0:
        k = (-r_diff + 7) // 8  # ceil
        r_diff = r_diff + 8 * k
        m_diff = -k
    else:
        m_diff = 0
    return redukcja(Vector(m_diff, r_diff))