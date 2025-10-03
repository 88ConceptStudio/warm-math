class Vector:
    def __init__(self, m, r):
        self.m = m
        self.r = r

    def dodawanie(self, other):
        return Vector(self.m + other.m, self.r + other.r)

    def odejmowanie(self, other):
        return Vector(self.m - other.m, self.r - other.r)

    def mnozenie(self, other):
        return Vector(self.m * other.m, self.r * other.r)

    def dzielenie(self, other):
        if other.m == 0 or other.r == 0:
            return "Niezdefiniowane"
        return Vector(self.m / other.m, self.r / other.r)