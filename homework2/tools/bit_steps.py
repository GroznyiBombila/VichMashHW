"""Плата разряда по шагам (schematics/16_bit_board_steps.svg).

Та же раскладка, что на чертежах 05/06 и в wiring.md, но разбитая на шаги:
детали → провода тремя группами → пайка снизу → проверка. На каждом шаге
нарисовано только то, что делается на этом шаге, поэтому линии не путаются.

Запуск из папки homework2.0:  python tools/bit_steps.py
"""
import copy
import os

from boards import ROWS, bit_board, esc, net_color, render_bottom, render_top, tag
from closeups import describe

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schematics")
INK, MUTED = "#263238", "#546e7a"
HALO = 'stroke="#ffffff" stroke-width="3" paint-order="stroke"'

P = 22                 # шаг отверстий
NR = 17                # рисуем ряды A..Q, ниже на плате разряда ничего нет
NC = 30
PW, PH = 780, 690      # размер одной панели
GROUPS = [
    ("Шаг 2. Провода от разъёма J1: питание и входы A, B, Cin", [1, 2, 3, 4, 5, 7, 12, 15]),
    ("Шаг 3. Провода между ячейками: выходы N1–N4", [6, 8, 19, 9, 10, 11, 13]),
    ("Шаг 4. Провода между ячейками: N5–N7, выходы S и Cout на J1", [14, 16, 20, 17, 18, 21, 22]),
]


class Sheet:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
                  f'font-family="Segoe UI, Arial, sans-serif">', f'<rect width="{w}" height="{h}" fill="#ffffff"/>']

    def text(self, x, y, s, size=11, fill=INK, anchor="middle", weight="normal", extra=""):
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                      f'font-weight="{weight}" {extra}>{esc(s)}</text>')

    def save(self, name):
        self.o.append("</svg>")
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write("\n".join(self.o))


def board(s, ox, oy, mirror=False):
    """Плата (ряды A..Q) с отверстиями и подписями. Возвращает функции X, Y."""
    X = (lambda c: ox + 40 + (NC + 1 - c) * P) if mirror else (lambda c: ox + 40 + c * P)
    Y = lambda r: oy + 30 + r * P
    x0, x1 = sorted((X(1), X(NC)))
    s.o.append(f'<rect x="{x0 - 0.75 * P}" y="{Y(1) - 0.75 * P}" width="{x1 - x0 + 1.5 * P}" '
               f'height="{(NR - 1 + 1.5) * P}" rx="8" fill="#2e7d4f" stroke="#1b5e20" stroke-width="2"/>')
    for c in range(1, NC + 1):
        s.text(X(c), Y(1) - 0.95 * P, str(c), 9, "#607d8b")
    for r in range(1, NR + 1):
        s.text(x0 - 1.15 * P, Y(r) + 3.5, ROWS[r - 1], 10, "#607d8b", weight="bold")
        s.text(x1 + 1.15 * P, Y(r) + 3.5, ROWS[r - 1], 10, "#607d8b", weight="bold")
        for c in range(1, NC + 1):
            s.o.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.31 * P:.1f}" fill="#d9a441" stroke="#9c6f1e" stroke-width="1"/>'
                       f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.11 * P:.1f}" fill="#123524"/>')
    return X, Y


def panel_title(s, ox, oy, title, sub):
    s.text(ox + 10, oy + 6, title, 15, anchor="start", weight="bold")
    for i, line in enumerate(sub):
        s.text(ox + 10, oy + 26 + 15 * i, line, 11, MUTED, anchor="start")


def tfun(s):
    return lambda x, y, txt, size=11, fill=INK, anchor="middle", weight="normal", extra="": s.text(
        x, y, txt, size, fill, anchor, weight, extra)


def parts(s, b, X, Y, opacity=1.0):
    b2 = copy.copy(b)
    b2.wires = []
    s.o.append(f'<g opacity="{opacity}">')
    render_top(b2, s.o, X, Y, P, tfun(s))
    s.o.append('</g>')


def cell_labels(s, b, X, Y):
    for c, r, text, kw in b.notes:
        if r < 1:
            s.text(X(c), Y(1) - 1.55 * P, text, 11, INK, weight="bold")


def wires(s, b, X, Y, nums):
    def length(i):
        p, q, _ = b.wires[i - 1]
        return abs(X(p[0]) - X(q[0])) + abs(Y(p[1]) - Y(q[1]))
    badges = []
    for i in sorted(nums, key=length, reverse=True):   # короткие поверх длинных
        p, q, net = b.wires[i - 1]
        xa, ya, xb, yb = X(p[0]), Y(p[1]), X(q[0]), Y(q[1])
        dx, dy = xb - xa, yb - ya
        L = max((dx * dx + dy * dy) ** 0.5, 1)
        k = min(0.18 * L, 40) * (1 if i % 2 else -1)
        cx, cy = (xa + xb) / 2 - dy / L * k, (ya + yb) / 2 + dx / L * k
        col = net_color(net)
        d = f"M{xa:.1f},{ya:.1f} Q{cx:.1f},{cy:.1f} {xb:.1f},{yb:.1f}"
        s.o.append(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>'
                   f'<path d="{d}" fill="none" stroke="{col}" stroke-width="4.5" stroke-linecap="round"/>')
        for x, y in ((xa, ya), (xb, yb)):
            s.o.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{col}" stroke="#ffffff" stroke-width="2"/>')
        mx, my = (xa + 2 * cx + xb) / 4, (ya + 2 * cy + yb) / 4
        if L < 2.5 * P:                                   # короткий провод: номер сбоку, с выноской
            bx = max(xa, xb) + 1.4 * P
            s.o.append(f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{bx:.1f}" y2="{my:.1f}" stroke="{col}" stroke-width="2"/>')
            mx = bx
        badges.append((mx, my, col, i))
    for mx, my, col, i in badges:                      # номера поверх всех проводов
        s.o.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="10" fill="{col}" stroke="#ffffff" stroke-width="2"/>')
        s.text(mx, my + 4, str(i), 11, "#ffffff", weight="bold")


def wire_table(s, b, x, y, nums):
    s.text(x, y, "№", 11, MUTED, weight="bold")
    s.text(x + 22, y, "цепь", 11, MUTED, anchor="start", weight="bold")
    s.text(x + 70, y, "откуда (что там)", 11, MUTED, anchor="start", weight="bold")
    s.text(x + 400, y, "куда (что там)", 11, MUTED, anchor="start", weight="bold")
    for j, i in enumerate(nums):
        p, q, net = b.wires[i - 1]
        yy = y + 20 + 19 * j
        col = net_color(net)
        if j % 2 == 0:
            s.o.append(f'<rect x="{x - 14}" y="{yy - 13}" width="{PW - 30}" height="19" fill="#f4f6f8"/>')
        s.o.append(f'<circle cx="{x}" cy="{yy - 4}" r="8" fill="{col}"/>')
        s.text(x, yy, str(i), 10, "#ffffff", weight="bold")
        s.text(x + 22, yy, net, 11, col, anchor="start", weight="bold")
        s.text(x + 70, yy, f"{hole(p)} — {describe(b, p)}", 11, anchor="start")
        s.text(x + 400, yy, f"{hole(q)} — {describe(b, q)}", 11, anchor="start")


def hole(p):
    return f"{ROWS[p[1] - 1]}{p[0]}"


def main():
    b = bit_board()
    W, H = 2 * PW + 40, 110 + 3 * PH
    s = Sheet(W, H)
    s.text(20, 34, "Плата разряда по шагам: что с чем паять", 22, anchor="start", weight="bold")
    s.text(20, 58, "Раскладка та же, что на чертежах 05/06 и в wiring.md (номера проводов совпадают). "
                   "На каждом шаге нарисовано только то, что делается на этом шаге.", 12, MUTED, anchor="start")
    s.text(20, 78, "Отверстие = буква ряда + номер столбца, вид сверху: F3 — ряд F, столбец 3. "
                   "Таких плат нужно 4, все одинаковые.", 12, MUTED, anchor="start")
    pos = [(20, 100), (20 + PW + 20, 100), (20, 100 + PH), (20 + PW + 20, 100 + PH),
           (20, 100 + 2 * PH), (20 + PW + 20, 100 + 2 * PH)]

    # шаг 1 — детали
    ox, oy = pos[0]
    panel_title(s, ox, oy, "Шаг 1. Детали: 9 одинаковых ячеек и разъём J1", [
        "Ячейка = резистор 10 кОм сверху, под ним два транзистора друг под другом, всё в одном столбце.",
        "Транзистор: плоская сторона ВПРАВО, ножки сверху вниз D, G, S. Резистор кладётся на плату плашмя."])
    X, Y = board(s, ox, oy + 50)
    parts(s, b, X, Y)
    cell_labels(s, b, X, Y)
    yt = Y(NR) + 40
    rows = [("R1…R9 (10 кОм)", "ряды A–E: верхняя ножка в A, нижняя в E; столбцы 3, 6, 9 … 27"),
            ("Q1, Q3 … Q17 (верхние)", "D в F, G в G, S в H — в том же столбце, что резистор"),
            ("Q2, Q4 … Q18 (нижние)", "D в I, G в J, S в K"),
            ("J1 (PLS-7)", "ряд O, столбцы 12–18: 1 +5V, 2 GND, 3 A, 4 B, 5 Cin, 6 S, 7 Cout")]
    for j, (a, t2) in enumerate(rows):
        s.text(ox + 20, yt + 19 * j, a, 11, anchor="start", weight="bold")
        s.text(ox + 200, yt + 19 * j, t2, 11, anchor="start")
    s.text(ox + 20, yt + 19 * 4 + 6, "Ножки пока НЕ загибать и не откусывать: они понадобятся на шаге 5.",
           11, "#c62828", anchor="start", weight="bold")

    # шаги 2–4 — провода
    for (title, nums), (ox, oy) in zip(GROUPS, pos[1:4]):
        panel_title(s, ox, oy, title, [
            "Провод зачистить на 4–5 мм, вставить сверху в указанное отверстие. Снизу пока не загибать.",
            "Цифра в кружке = строка таблицы ниже и строка в wiring.md. Детали нарисованы бледно."])
        X, Y = board(s, ox, oy + 50)
        parts(s, b, X, Y, opacity=0.35)
        cell_labels(s, b, X, Y)
        wires(s, b, X, Y, nums)
        j1 = next(c for c in b.comps if c["ref"] == "J1")
        for (px, py), name in zip(j1["pins"].values(), j1["names"]):
            s.text(X(px), Y(py) + 2.35 * P, name, 9, "#ffffff", weight="bold")
        wire_table(s, b, ox + 24, Y(NR) + 40, nums)

    # шаг 5 — снизу
    ox, oy = pos[4]
    panel_title(s, ox, oy, "Шаг 5. Пайка снизу (вид снизу — ЗЕРКАЛЬНО, столбец 1 справа)", [
        "Короткая серая перемычка: ножку или конец провода из одного отверстия загнуть на соседнюю площадку и спаять.",
        "Цветные кольца — где снизу торчат концы проводов. Длинные полосы A и L — шины: голый провод по ряду."])
    X, Y = board(s, ox, oy + 50, mirror=True)
    b2 = copy.copy(b)
    render_bottom(b2, s.o, X, Y, P, tfun(s))
    yt = Y(NR) + 40
    steps5 = [
        "1. В каждой ячейке: нижнюю ножку R на сток D верхнего транзистора (E→F), S верхнего на D нижнего (H→I),",
        "    S нижнего на шину GND (K→L).",
        "2. Концы проводов-входов — на ножку затвора рядом (G2→G3, J2→J3 и т.д.).",
        "3. Выходы ячеек: F4–E4–D4 и т.п. — цепочкой, каждый конец на соседа (как с N5: F15–F16–E16–D16).",
        "4. У J1: каждый штырёк на площадку провода над ним (O→N), у A, B, Cin ещё и под ним (O→P).",
        "5. В конце шины: голый лужёный провод по ряду A (+5V) и по ряду L (GND), пропаять у каждой ножки.",
        "Полный список перемычек с галочками — wiring.md, раздел «Соединения соседних отверстий».",
    ]
    for j, line in enumerate(steps5):
        s.text(ox + 20, yt + 18 * j, line, 11, INK if j < 6 else MUTED, anchor="start")

    # шаг 6 — проверка
    ox, oy = pos[5]
    panel_title(s, ox, oy, "Шаг 6. Проверка мультиметром до подключения", [
        "Плата без питания. Режим прозвонки (писк), затем режим сопротивления."])
    checks = [
        ("Питание", [
            "J1.1 (+5V) звонится с шиной в ряду A, J1.2 (GND) — с шиной в ряду L.",
            "Между J1.1 и J1.2 писка НЕТ. В режиме 200 кОм — больше нескольких кОм, не ноль.",
        ]),
        ("Входы", [
            "J1.3 (A) звонится с ножками G у Q1 и Q3; J1.4 (B) — у Q2 и Q5;",
            "J1.5 (Cin) — у Q10 и Q13.",
        ]),
        ("Связи ячеек", [
            "Для каждой строки таблиц шагов 2–4: «откуда» звонится с «куда».",
            "Ножки D/G/S соседних транзисторов НЕ звонятся между собой, кроме нарисованных перемычек.",
        ]),
        ("Выходы", [
            "J1.6 (S) звонится с D у Q15 (ячейка 8), J1.7 (Cout) — с D у Q17 (ячейка 9).",
        ]),
        ("Разъём", [
            "Контакт 1 = +5V. Отметь его маркером на плате у J1 и на гнезде платы ввода-вывода.",
            "Кабель не должен переворачивать порядок: 1→1, 2→2 … 7→7. Перевёрнутое питание сожжёт транзисторы.",
        ]),
        ("Флюс", [
            "Паять канифолью или нейтральным флюсом. Активный (хлориды цинка/аммония) — отмыть и высушить:",
            "затворы 2N7000 чувствительны к утечкам, налёт может открыть транзистор.",
        ]),
        ("Если паяешь провода снизу", [
            "Как на плате ввода-вывода — тоже можно: конец провода припаять прямо к ножке, которая указана",
            "в столбце «что там» (затвор, сток), а свободное отверстие рядом оставить пустым.",
        ]),
    ]
    yy = oy + 70
    for head, lines in checks:
        s.text(ox + 20, yy, head, 12, INK, anchor="start", weight="bold")
        yy += 18
        for line in lines:
            s.text(ox + 34, yy, line, 11, INK, anchor="start")
            yy += 17
        yy += 8
    s.save("16_bit_board_steps.svg")
    print("готово: 16_bit_board_steps.svg")


if __name__ == "__main__":
    main()
