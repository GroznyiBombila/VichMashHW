"""Генерирует схему 4-битного сумматора на NMOS (2N7000) для Falstad CircuitJS.

Использование: python gen_falstad.py [биты входов]
  без аргументов  - все переключатели разомкнуты (все входы = 0);
  "A=5 B=3 CIN=0" - выставить положения переключателей (для тестов).
"""
import sys

VT, BETA = 2.1, 0.2          # порог и крутизна модели MOSFET (близко к 2N7000)
R_PULL, R_IN, R_LED = 10000, 10000, 470

out = ["$ 1 0.000005 10.20027730826997 50 5 50 5e-11"]


def esc(s):
    return (s.replace("\\", "\\\\").replace(" ", "\\s").replace("+", "\\p")
             .replace("=", "\\q").replace("#", "\\h").replace("&", "\\a"))


def wire(x1, y1, x2, y2):   out.append(f"w {x1} {y1} {x2} {y2} 0")
def bus(xs, y):
    """Шина из отрезков: в Falstad провод соединяется только своими концами."""
    for a, b in zip(xs, xs[1:]):
        wire(a, y, b, y)


def res(x1, y1, x2, y2, r): out.append(f"r {x1} {y1} {x2} {y2} 0 {r}")
def gnd(x, y):              out.append(f"g {x} {y} {x} {y + 16} 0 0")
def rail(x, y, x2, y2):     out.append(f"R {x} {y} {x2} {y2} 0 0 40 5 0 0 0.5")
def label(x, y, x2, name):  out.append(f"207 {x} {y} {x2} {y} 4 {esc(name)}")
def text(x, y, s, size=16): out.append(f"x {x} {y} {x + 100} {y} 4 {size} {esc(s)}")


def nmos(xg, y, xd):
    """NMOS: затвор слева в (xg, y); сток в (xd, y-16), исток в (xd, y+16)."""
    out.append(f"f {xg} {y} {xd} {y} 0 {VT} {BETA}")


def nand(X, Y, a, b, y, title):
    """Вентиль И-НЕ: 10к от шины +5 В (на высоте Y) к выходу, 2 NMOS последовательно."""
    res(X, Y, X, Y + 64, R_PULL)
    nmos(X - 32, Y + 80, X)            # Q1: сток = выход Y
    nmos(X - 32, Y + 112, X)           # Q2: исток на GND
    gnd(X, Y + 128)
    label(X - 32, Y + 80, X - 48, a)
    label(X - 32, Y + 112, X - 48, b)
    label(X, Y + 64, X + 16, y)
    text(X + 10, Y + 34, title, 14)


def parse_args():
    v = {"A": 0, "B": 0, "CIN": 0}
    for arg in sys.argv[1:]:
        k, val = arg.split("=")
        v[k.upper()] = int(val)
    return v


vals = parse_args()
bit = {**{f"A{i}": (vals["A"] >> i) & 1 for i in range(4)},
       **{f"B{i}": (vals["B"] >> i) & 1 for i in range(4)},
       "Cin": vals["CIN"] & 1}

text(16, 24, "4-битный сумматор с последовательным переносом на NMOS 2N7000 (И-НЕ = 2 транзистора + 10 кОм)", 20)
text(16, 52, "Щёлкните по переключателю: замкнут = 1. Результат: светодиоды Cout S3 S2 S1 S0 внизу. Зелёный провод = 5 В, серый = 0 В.", 14)

# ---- Ввод: +5 В -> переключатель -> узел (стяжка 10 кОм на GND)
Y_IN = 128
inputs = ["A3", "A2", "A1", "A0", "B3", "B2", "B1", "B0", "Cin"]
xs = [160 + j * 112 + (48 if j >= 4 else 0) + (48 if j >= 8 else 0) for j in range(9)]
rail(xs[0] - 64, Y_IN, xs[0] - 96, Y_IN)
bus([xs[0] - 64] + xs, Y_IN)
for x, name in zip(xs, inputs):
    pos = 0 if bit[name] else 1          # 0 = замкнут, 1 = разомкнут
    out.append(f"s {x} {Y_IN} {x} {Y_IN + 64} 0 {pos} false")
    label(x, Y_IN + 64, x + 16, name)
    res(x, Y_IN + 64, x, Y_IN + 128, R_IN)
    gnd(x, Y_IN + 128)
text(xs[0] - 16, Y_IN + 190, "Число A", 16)
text(xs[4] - 16, Y_IN + 190, "Число B", 16)
text(xs[8] - 16, Y_IN + 190, "Перенос", 16)

# ---- 4 полных сумматора, по 9 вентилей И-НЕ
Y0, DY, X0, DX = 400, 256, 176, 176
for i in range(4):
    Y = Y0 + i * DY
    cin = "Cin" if i == 0 else f"C{i}"
    cout = "Cout" if i == 3 else f"C{i + 1}"
    n = lambda k: f"N{k}_{i}"
    A, B = f"A{i}", f"B{i}"
    gates = [
        (A, B, n(1), "N1"), (A, n(1), n(2), "N2"), (B, n(1), n(3), "N3"),
        (n(2), n(3), n(4), "N4=A⊕B"), (n(4), cin, n(5), "N5"),
        (n(4), n(5), n(6), "N6"), (cin, n(5), n(7), "N7"),
        (n(6), n(7), f"S{i}", "N8=S"), (n(1), n(5), cout, "N9=Cout"),
    ]
    text(16, Y - 36, f"Разряд {i}: A{i} + B{i} + {cin}  →  S{i}, {cout}", 16)
    rail(X0 - 80, Y, X0 - 112, Y)
    bus([X0 - 80] + [X0 + k * DX for k in range(9)], Y)
    for k, (a, b, y, t) in enumerate(gates):
        nand(X0 + k * DX, Y, a, b, y, t)

# ---- Вывод: +5 В -> 470 Ом -> LED -> сток 2N7000, затвор = выход сумматора
Y_OUT = Y0 + 4 * DY
outs = ["Cout", "S3", "S2", "S1", "S0"]
xo = [256 + j * 144 for j in range(5)]
text(16, Y_OUT - 36, "Индикация (светодиод горит = 1)", 16)
rail(xo[0] - 80, Y_OUT, xo[0] - 112, Y_OUT)
bus([xo[0] - 80] + xo, Y_OUT)
for x, name in zip(xo, outs):
    res(x, Y_OUT, x, Y_OUT + 64, R_LED)
    out.append(f"162 {x} {Y_OUT + 64} {x} {Y_OUT + 128} 2 default-led 0 1 0 0.01")
    nmos(x - 32, Y_OUT + 144, x)
    label(x - 32, Y_OUT + 144, x - 48, name)
    gnd(x, Y_OUT + 160)
    text(x - 16, Y_OUT + 216, name, 20)

sys.stdout.write("\n".join(out) + "\n")
