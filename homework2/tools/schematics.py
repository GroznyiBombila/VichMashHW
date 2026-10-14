"""Принципиальные схемы сумматора в SVG (schematics/01–04, 09).

Запуск из папки homework2.0:  python tools/schematics.py
Обозначения деталей (R1, Q1…) совпадают с платами из tools/boards.py.
"""
import os

from boards import GATES, J_NAMES, LED_ORDER, SW1_LABELS, NET_COLOR, net_color, esc

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schematics")
INK = "#263238"


class Svg:
    def __init__(self, w, h, title, sub=""):
        self.w, self.h = w, h
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
                  f'font-family="Segoe UI, Arial, sans-serif">', f'<rect width="{w}" height="{h}" fill="#ffffff"/>']
        self.text(24, 34, title, 20, weight="bold", anchor="start")
        if sub:
            self.text(24, 58, sub, 13, "#546e7a", anchor="start")

    def text(self, x, y, s, size=12, fill=INK, anchor="middle", weight="normal", extra=""):
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                      f'font-weight="{weight}" {extra}>{esc(s)}</text>')

    def line(self, *pts, color=INK, w=1.8, dash=""):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
                      f'stroke-linejoin="round"{da}/>')

    def dot(self, x, y, color=INK):
        self.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{color}"/>')

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1.8, rx=0):
        self.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
                      f'stroke="{stroke}" stroke-width="{sw}"/>')

    def flag(self, x, y, name, side="left"):
        """Метка цепи: провода с одинаковой меткой соединены."""
        w = 8 * len(name) + 14
        col = net_color(name)
        x0 = x - w if side == "left" else x
        self.o.append(f'<rect x="{x0:.1f}" y="{y - 9:.1f}" width="{w}" height="18" rx="9" fill="{col}"/>')
        self.text(x0 + w / 2, y + 4.5, name, 12, "#ffffff", weight="bold")

    # ---- элементы по ГОСТ 2.728 / 2.730
    def resistor(self, x, y1, y2, ref, value, lab_side=1):
        m = (y1 + y2) / 2
        self.line((x, y1), (x, m - 20))
        self.line((x, m + 20), (x, y2))
        self.rect(x - 7, m - 20, 14, 40, "#ffffff")
        self.text(x + 14 * lab_side, m - 3, ref, 12, anchor="start" if lab_side > 0 else "end", weight="bold")
        self.text(x + 14 * lab_side, m + 12, value, 12, anchor="start" if lab_side > 0 else "end")

    def nmos(self, x, yd, ys, ref):
        """n-МОП с индуцированным каналом: сток сверху (x, yd), исток снизу (x, ys), затвор слева."""
        m = (yd + ys) / 2
        c = x - 12            # линия канала
        self.line((x, yd), (x, m - 12), (c, m - 12))
        self.line((x, ys), (x, m + 12), (c, m + 12))
        self.line((c, m), (x, m), (x, m + 12))
        self.o.append(f'<polygon points="{c:.1f},{m} {c + 8:.1f},{m - 4:.1f} {c + 8:.1f},{m + 4:.1f}" fill="{INK}"/>')
        for dy in (-12, 0, 12):
            self.line((c, m + dy - 6), (c, m + dy + 6), w=2.6)
        self.line((c - 6, m - 14), (c - 6, m + 14), w=2.2)
        self.text(x + 8, m + 4, ref, 12, anchor="start", weight="bold")
        return (c - 6, m + 10)

    def gnd(self, x, y):
        self.line((x, y), (x, y + 8))
        for i, hw in enumerate((10, 6, 2.5)):
            self.line((x - hw, y + 8 + 4 * i), (x + hw, y + 8 + 4 * i), w=2)

    def vcc(self, x, y, label="+5 В"):
        self.line((x, y), (x, y - 10))
        self.line((x - 8, y - 10), (x + 8, y - 10), w=2.4)
        self.text(x, y - 16, label, 11, "#d32f2f", weight="bold")

    def nand(self, x, y, name, sub="", w=46, h=56):
        """И-НЕ по ГОСТ: прямоугольник с «&» и кружком инверсии на выходе. Возвращает (a, b, out)."""
        self.rect(x, y, w, h, "#ffffff", sw=2)
        self.text(x + w / 2, y + 20, "&", 16, weight="bold")
        self.o.append(f'<circle cx="{x + w + 5}" cy="{y + h / 2}" r="5" fill="#ffffff" stroke="{INK}" stroke-width="2"/>')
        self.text(x + w / 2, y + h + 16, name, 13, weight="bold")
        if sub:
            self.text(x + w / 2, y + h + 31, sub, 11, "#546e7a")
        return (x, y + 16), (x, y + h - 16), (x + w + 10, y + h / 2)

    def save(self, name):
        self.o.append("</svg>")
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write("\n".join(self.o))


# ------------------------------------------------------------------ 01 структура

def structure():
    s = Svg(1100, 560, "Структура: плата ввода-вывода и 4 платы разряда",
            "Каждая плата разряда — полный сумматор из 9 вентилей И-НЕ. Перенос идёт справа налево: C1, C2, C3 — через плату ввода-вывода.")
    s.rect(40, 90, 1020, 150, "#f1f8e9", "#558b2f", 2, 10)
    s.text(60, 114, "Плата ввода-вывода", 15, weight="bold", anchor="start")
    s.rect(70, 130, 330, 70, "#1e63b5", "#0d3c73", 2, 6)
    s.text(235, 158, "SW1 (DIP-8):  A3 A2 A1 A0 | B3 B2 B1 B0", 13, "#ffffff", weight="bold")
    s.text(235, 180, "положение ON = 1, OFF = 0", 12, "#e3f2fd")
    s.rect(430, 130, 150, 70, "#1e63b5", "#0d3c73", 2, 6)
    s.text(505, 158, "SW2 (DIP-1)", 13, "#ffffff", weight="bold")
    s.text(505, 180, "Cin, входной перенос", 12, "#e3f2fd")
    leds = ["Cout", "S3", "S2", "S1", "S0"]
    for i, n in enumerate(leds):
        x = 640 + i * 62
        s.o.append(f'<circle cx="{x}" cy="160" r="17" fill="#ef5350" stroke="#b71c1c" stroke-width="2"/>')
        s.text(x, 198, n, 13, weight="bold")
    s.text(764, 222, "светодиоды: горит = 1; вес 16 8 4 2 1", 12, "#546e7a")
    s.text(960, 150, "MB102, 5 В →", 13, "#d32f2f", weight="bold")
    s.text(960, 168, "J1, C1 470 мкФ", 12, "#546e7a")
    xs = [860, 620, 380, 140]   # разряды 0..3 справа налево
    for i, x in enumerate(xs):
        s.rect(x, 330, 180, 130, "#fffde7", "#f9a825", 2, 10)
        s.text(x + 90, 356, f"Плата разряда {i}", 14, weight="bold")
        s.text(x + 90, 378, "9 × И-НЕ = 18 × 2N7000 + 9 × 10 кОм", 11, "#546e7a")
        s.text(x + 90, 404, f"A{i} + B{i} + {'Cin' if i == 0 else f'C{i}'}", 14, weight="bold")
        s.text(x + 90, 428, f"→ S{i}, {'Cout' if i == 3 else f'C{i + 1}'}", 14, weight="bold")
        s.line((x + 90, 240), (x + 90, 330), color="#78909c", w=6)
        s.text(x + 100, 290, f"кабель X{i} (7 проводов)", 11, "#455a64", anchor="start")
        if i < 3:
            s.line((x - 2, 440), (xs[i + 1] + 182, 440), color="#ef6c00", w=3)
            s.o.append(f'<polygon points="{xs[i + 1] + 182},{440} {xs[i + 1] + 194},{434} {xs[i + 1] + 194},{446}" fill="#ef6c00"/>')
            s.text((x + xs[i + 1] + 180) / 2, 478, f"C{i + 1}", 13, "#ef6c00", weight="bold")
    s.text(550, 500, "Физически перенос C1…C3 идёт по проводу кабеля (контакт 7 → контакт 5 соседнего) через плату ввода-вывода.", 12, "#546e7a")
    s.text(550, 520, "Разъём J1 платы разряда: 1 +5V, 2 GND, 3 A, 4 B, 5 Cin, 6 S, 7 Cout.", 12, "#546e7a")
    s.save("01_structure.svg")


# ------------------------------------------------------------------ 02 логика разряда

def logic():
    nets = ["A", "B", "Cin", "N1", "N2", "N3", "N4", "N5", "N6", "N7"]
    top, step = 100, 22
    ny = {n: top + i * step for i, n in enumerate(nets)}
    gy, x0, dx = 360, 150, 106
    s = Svg(1150, 520, "Разряд: полный сумматор из 9 вентилей И-НЕ",
            "Сверху — линии сигналов, точка = соединение, пересечение без точки = не соединены. Каждый вентиль = 2 транзистора + 1 резистор.")
    subs = {"N4": "= A⊕B", "N8": "= S", "N9": "= Cout"}
    gx = {}
    ends = {n: 0 for n in nets}
    pins = []
    for k, (out, a, b) in enumerate(GATES):
        name = f"N{k + 1}"
        x = x0 + k * dx
        gx[name] = x
        pa, pb, po = s.nand(x, gy, name, subs.get(name, ""))
        pins.append((name, out, a, b, pa, pb, po))
        for net in (a, b):
            ends[net] = max(ends[net], x - (14 if net == a else 26))
    # линии сигналов
    for n in nets:
        start = 40 if n in ("A", "B", "Cin") else gx[n] + 60
        s.line((start, ny[n]), (ends[n], ny[n]), color=net_color(n), w=2)
        s.text(start - 6 if n in ("A", "B", "Cin") else start + 4, ny[n] - 4, n, 12, net_color(n),
               anchor="end" if n in ("A", "B", "Cin") else "start", weight="bold")
    for name, out, a, b, pa, pb, po in pins:
        for net, (px, py), off in ((a, pa, 14), (b, pb, 26)):
            x = px - off
            col = net_color(net)
            s.line((x, ny[net]), (x, py), (px, py), color=col, w=2)
            s.dot(x, ny[net], col)
        if out in ny:
            s.line(po, (po[0] + 14, po[1]), (po[0] + 14, ny[out]), (po[0] + 14 + 1, ny[out]), color=net_color(out), w=2)
        elif out == "S":
            s.line(po, (po[0] + 12, po[1]), (po[0] + 12, gy + 120), color=net_color("S"), w=2.4)
            s.flag(po[0] + 12, gy + 132, "S", "right")
        else:
            s.line(po, (po[0] + 30, po[1]), color=net_color("Cout"), w=2.4)
            s.flag(po[0] + 30, po[1], "Cout", "right")
    s.text(40, 490, "N1 = NAND(A,B)   N2 = NAND(A,N1)   N3 = NAND(B,N1)   N4 = NAND(N2,N3) = A⊕B   N5 = NAND(N4,Cin)", 12, anchor="start")
    s.text(40, 508, "N6 = NAND(N4,N5)   N7 = NAND(Cin,N5)   S = NAND(N6,N7)   Cout = NAND(N1,N5)", 12, anchor="start")
    s.save("02_full_adder_logic.svg")


# ------------------------------------------------------------------ 03 разряд на транзисторах

def bit_schematic():
    s = Svg(1480, 560, "Плата разряда: принципиальная схема на транзисторах",
            "Каждая ячейка — вентиль И-НЕ: выход = 0, только когда оба входа = 1 (оба транзистора открыты). "
            "Одинаковые метки = один провод.")
    y5, yg = 110, 440
    x0, dx = 90, 132
    s.line((40, y5), (x0 + 8 * dx + 60, y5), color="#d32f2f", w=2.4)
    s.text(40, y5 - 8, "+5V", 13, "#d32f2f", anchor="start", weight="bold")
    s.line((40, yg), (x0 + 8 * dx + 60, yg), color="#263238", w=2.4)
    s.text(40, yg + 18, "GND", 13, anchor="start", weight="bold")
    for k, (out, a, b) in enumerate(GATES):
        n = k + 1
        x = x0 + k * dx + 40
        s.dot(x, y5, "#d32f2f")
        s.resistor(x, y5, 210, f"R{n}", "10 кОм")
        s.dot(x, 222)
        s.line((x, 210), (x, 230))
        s.line((x, 222), (x + 26, 222))
        s.flag(x + 26, 222, out, "right")
        ga = s.nmos(x, 230, 300, f"Q{2 * n - 1}")
        gb = s.nmos(x, 300, 370, f"Q{2 * n}")
        s.line((x, 370), (x, yg))
        s.dot(x, yg)
        for (gx, gyy), net in ((ga, a), (gb, b)):
            s.line((gx, gyy), (gx - 16, gyy))
            s.flag(gx - 16, gyy, net, "left")
        s.text(x - 10, 150, f"N{n}", 14, weight="bold", anchor="end")
    # J1
    jx, jy = 60, 480
    s.text(jx, jy, "J1 (PLS-7):", 13, weight="bold", anchor="start")
    for i, name in enumerate(J_NAMES):
        x = jx + 110 + i * 90
        s.rect(x, jy - 13, 18, 18, "#ffd54f", "#8d6e00", 1.5)
        s.text(x + 9, jy + 1, str(i + 1), 11, weight="bold")
        s.flag(x + 24, jy - 4, name, "right")
    s.text(jx, 530, "Итого на плату: Q1–Q18 = 2N7000, R1–R9 = 10 кОм, J1 = PLS-7. Проверка: при A=B=Cin=0 на N1…N7 должно быть 1110111 (N1 ≈ 5 В, N4 ≈ 0 В).",
           12, "#546e7a", anchor="start")
    s.save("03_bit_board_schematic.svg")


# ------------------------------------------------------------------ 04 плата ввода-вывода

def io_schematic():
    s = Svg(1240, 640, "Плата ввода-вывода: принципиальная схема",
            "Вход: рычажок замкнут → на линии +5 В (1), разомкнут → резистор 10 кОм тянет к 0 В (0). "
            "Выход: 1 на затворе открывает транзистор, светодиод горит.")
    # питание
    s.text(40, 100, "Питание", 14, weight="bold", anchor="start")
    s.rect(40, 115, 60, 70, "#fafafa")
    for i, (lab, col) in enumerate((("1 +5V", "#d32f2f"), ("2 —", "#90a4ae"), ("3 GND", INK))):
        s.text(70, 135 + 20 * i, lab, 11, col, weight="bold")
    s.text(70, 200, "J1 PLS-3", 11, anchor="middle")
    s.line((100, 131), (170, 131), color="#d32f2f", w=2.2)
    s.line((100, 171), (170, 171), w=2.2)
    s.dot(150, 131, "#d32f2f"); s.dot(150, 171)
    s.line((150, 131), (150, 145)); s.line((140, 145), (160, 145), w=2.4)
    s.o.append('<path d="M140,155 Q150,149 160,155" fill="none" stroke="#263238" stroke-width="2.4"/>')
    s.line((150, 153), (150, 171))
    s.text(166, 143, "+", 13, anchor="start", weight="bold")
    s.text(166, 160, "C1 470 мкФ", 11, anchor="start")
    s.text(175, 135, "+5V", 12, "#d32f2f", anchor="start", weight="bold")
    s.text(175, 175, "GND", 12, anchor="start", weight="bold")
    s.text(40, 230, "от MB102: штырьки 5V и GND (перемычка на 5 В!)", 11, "#546e7a", anchor="start")
    # входы
    s.text(300, 100, "Входы ×9 (SW1 — DIP-8, SW2 — DIP-1)", 14, weight="bold", anchor="start")
    y5, yg = 130, 330
    names = SW1_LABELS + ["Cin"]
    s.line((300, y5), (300 + 9 * 100, y5), color="#d32f2f", w=2.2)
    s.line((300, yg), (300 + 9 * 100, yg), w=2.2)
    s.text(296, y5 + 4, "+5V", 12, "#d32f2f", anchor="end", weight="bold")
    s.text(296, yg + 4, "GND", 12, anchor="end", weight="bold")
    for i, n in enumerate(names):
        x = 340 + i * 100
        sw = "SW1" if i < 8 else "SW2"
        pos = i + 1 if i < 8 else 1
        s.dot(x, y5, "#d32f2f")
        s.line((x, y5), (x, 160))
        s.o.append(f'<circle cx="{x}" cy="162" r="3" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
        s.line((x, 164), (x + 14, 192))
        s.o.append(f'<circle cx="{x}" cy="196" r="3" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
        s.text(x - 8, 182, f"{sw}.{pos}", 10, anchor="end")
        s.line((x, 199), (x, 215))
        s.dot(x, 215)
        s.line((x, 215), (x + 20, 215))
        s.flag(x + 20, 215, n, "right")
        s.resistor(x, 215, yg, f"R{i + 1}", "10к", -1)
        s.dot(x, yg)
    # выходы
    s.text(40, 390, "Индикация ×5", 14, weight="bold", anchor="start")
    y5, yg = 420, 610
    s.line((80, y5), (80 + 5 * 150, y5), color="#d32f2f", w=2.2)
    s.line((80, yg), (80 + 5 * 150, yg), w=2.2)
    s.text(76, y5 + 4, "+5V", 12, "#d32f2f", anchor="end", weight="bold")
    s.text(76, yg + 4, "GND", 12, anchor="end", weight="bold")
    for i, n in enumerate(LED_ORDER):
        x = 170 + i * 150
        s.dot(x, y5, "#d32f2f")
        s.resistor(x, y5, 490, f"R{10 + i}", "470 Ом")
        # светодиод: треугольник вниз
        s.line((x, 490), (x, 498))
        s.o.append(f'<polygon points="{x - 9},{498} {x + 9},{498} {x},{514}" fill="#ef5350" stroke="{INK}" stroke-width="1.6"/>')
        s.line((x - 9, 514), (x + 9, 514), w=2)
        s.line((x + 11, 500), (x + 20, 492), color="#ef5350", w=1.4)
        s.line((x + 13, 507), (x + 22, 499), color="#ef5350", w=1.4)
        s.text(x - 14, 510, f"HL{i + 1}", 12, anchor="end", weight="bold")
        s.line((x, 514), (x, 530))
        g = s.nmos(x, 530, 590, f"Q{i + 1}")
        s.line((x, 590), (x, yg))
        s.dot(x, yg)
        s.line(g, (g[0] - 16, g[1]))
        s.flag(g[0] - 16, g[1], n, "left")
    # кабели
    s.text(880, 390, "Кабели X0–X3 к платам разрядов", 14, weight="bold", anchor="start")
    rows = [["X", "1", "2", "3", "4", "5", "6", "7"]]
    for i in range(4):
        rows.append([f"X{i}", "+5V", "GND", f"A{i}", f"B{i}", "Cin" if i == 0 else f"C{i}", f"S{i}",
                     "Cout" if i == 3 else f"C{i + 1}"])
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            x, y = 880 + c * 42, 420 + r * 26
            if r and c:
                s.text(x + 18, y + 4, v, 11, net_color(v), weight="bold")
            else:
                s.text(x + 18, y + 4, v, 11, "#546e7a", weight="bold")
    s.text(880, 560, "Контакт k кабеля Xi → контакт k J1 платы разряда i.", 11, "#546e7a", anchor="start")
    s.text(880, 578, "C1, C2, C3 — провод от контакта 7 кабеля Xi", 11, "#546e7a", anchor="start")
    s.text(880, 594, "к контакту 5 кабеля Xi+1 на этой плате.", 11, "#546e7a", anchor="start")
    s.save("04_io_board_schematic.svg")


# ------------------------------------------------------------------ 09 цоколёвка

def pinout():
    s = Svg(900, 400, "Цоколёвка 2N7000 (TO-92) и как ставить на плату",
            "Сверьте с даташитом своей партии. У BS170 и некоторых «аналогов» порядок другой: D-G-S.")
    # вид на плоскую сторону
    cx = 170
    s.rect(cx - 50, 100, 100, 110, "#37474f", "#101418", 2, 6)
    s.text(cx, 150, "2N7000", 14, "#ffffff", weight="bold")
    s.text(cx, 170, "плоская сторона", 11, "#cfd8dc")
    s.text(cx, 186, "к вам", 11, "#cfd8dc")
    for i, (num, name) in enumerate((("1", "S"), ("2", "G"), ("3", "D"))):
        x = cx - 30 + 30 * i
        s.line((x, 210), (x, 290), color="#9e9e9e", w=4)
        s.text(x, 310, num, 14, weight="bold")
        s.text(x, 330, name, 16, net_color({"S": "GND", "G": "A", "D": "N1"}[name]), weight="bold")
    s.text(cx, 360, "исток · затвор · сток", 12, "#546e7a")
    s.text(cx, 90, "Вид спереди, ножки вниз", 13, weight="bold")
    # вид сверху на плате
    bx = 560
    s.text(bx + 40, 90, "На плате (вид сверху, как на чертежах 05 и 07)", 13, weight="bold")
    s.rect(bx - 120, 100, 320, 250, "#2e7d4f", "#1b5e20", 2, 8)
    for r in range(5):
        for c in range(6):
            s.o.append(f'<circle cx="{bx - 90 + c * 52}" cy="{125 + r * 52}" r="8" fill="#d9a441" stroke="#9c6f1e"/>')
    px = bx - 90 + 2 * 52
    ys = [125 + 52, 125 + 104, 125 + 156]
    fx = px + 18
    s.o.append(f'<path d="M{fx},{ys[0] - 40} C{fx - 110},{ys[0] - 40} {fx - 110},{ys[2] + 40} {fx},{ys[2] + 40} Z" '
               f'fill="#37474f" fill-opacity=".85" stroke="#101418" stroke-width="2"/>')
    s.line((fx, ys[0] - 40), (fx, ys[2] + 40), color="#cfd8dc", w=4)
    for y, n in zip(ys, "DGS"):
        s.o.append(f'<circle cx="{px}" cy="{y}" r="6" fill="#ffd54f"/>')
        s.text(px - 24, y + 5, n, 16, "#ffffff", weight="bold")
    s.text(fx + 12, ys[1] - 6, "плоская", 12, "#ffffff", anchor="start", weight="bold")
    s.text(fx + 12, ys[1] + 10, "сторона →", 12, "#ffffff", anchor="start", weight="bold")
    s.text(bx + 40, 372, "Плоская сторона ВПРАВО (к столбцу 30): тогда D сверху, S снизу.", 12, "#c62828", weight="bold")
    s.text(bx + 40, 390, "Развернёте влево — S и D поменяются местами, вентиль работать не будет.", 12, "#546e7a")
    s.save("09_to92_pinout.svg")


if __name__ == "__main__":
    structure()
    logic()
    bit_schematic()
    io_schematic()
    pinout()
    print("готово:", ", ".join(sorted(f for f in os.listdir(OUT) if f.endswith(".svg"))))
