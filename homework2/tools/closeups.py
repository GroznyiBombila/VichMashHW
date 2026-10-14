"""Пояснительные чертежи монтажа (schematics/10–13).

10 — одна ячейка крупно: вид сверху, снизу и разрезы сбоку.
11, 12 — платы «на просвет»: провода пронумерованными стрелками и таблица «откуда → куда».
13 — плата ввода-вывода по частям: шины питания, MB102, C1, входная и выходная цепочки.
Данные берутся из tools/boards.py, поэтому номера отверстий совпадают с чертежами 05–08.

Запуск из папки homework2.0:  python tools/closeups.py
"""
import os

from boards import GATES, ROWS, BANDS, CABLE_ROW, bit_board, io_board, hn, net_color, esc

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schematics")
INK, MUTED = "#263238", "#546e7a"
PCB, PAD, PAD_EDGE = "#2e7d4f", "#d9a441", "#9c6f1e"
SOLDER = "#b0bec5"


class Svg:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
                  f'font-family="Segoe UI, Arial, sans-serif">', f'<rect width="{w}" height="{h}" fill="#ffffff"/>']

    def add(self, s):
        self.o.append(s)

    def text(self, x, y, s, size=12, fill=INK, anchor="middle", weight="normal", extra=""):
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                      f'font-weight="{weight}" {extra}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, color=INK, w=2, cap="round", extra=""):
        self.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
                      f'stroke-width="{w}" stroke-linecap="{cap}" {extra}/>')

    def badge(self, x, y, n, color="#c62828", r=11):
        self.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="#ffffff" stroke-width="2"/>')
        self.text(x, y + 4.5, str(n), 12 if r >= 11 else 10, "#ffffff", weight="bold")

    def arrow_head(self, x, y, dx, dy, color, size=9):
        L = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        ux, uy = dx / L, dy / L
        bx, by = x - ux * size, y - uy * size
        px, py = -uy * size * 0.55, ux * size * 0.55
        self.o.append(f'<polygon points="{x:.1f},{y:.1f} {bx + px:.1f},{by + py:.1f} {bx - px:.1f},{by - py:.1f}" '
                      f'fill="{color}" stroke="#ffffff" stroke-width="1"/>')

    def save(self, name):
        self.o.append("</svg>")
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write("\n".join(self.o))


# ---------------------------------------------------------------- что стоит в отверстии

def describe(b, p):
    """Человеческое описание медной группы, в которую входит отверстие p."""
    find = b.finder(wires=False)
    g = find(p)
    items = [(c, n) for c in b.comps for n, q in c["pins"].items() if find(q) == g]
    for name, pads in b.rails:
        if any(find(q) == g for q in pads):
            return f"шина {name}"
    for c, n in items:
        if c["kind"] == "J":
            return f"штырёк J1.{n} ({c['names'][int(n) - 1]})"
        if c["kind"] == "X":
            return f"кабель X{c['bit']}, жила {n} ({c['names'][int(n) - 1]})"
        if c["kind"] == "SW":
            return f"рычажок {c['labels'][int(n.rstrip(chr(39))) - 1]} ({c['ref']}.{n.rstrip(chr(39))})"
    if b.key == "bit":
        for c, n in items:
            if c["kind"] == "R":
                k = int(c["ref"][1:])
                return f"выход {gate_name(k)} (R{k} + сток Q{2 * k - 1})"
        for c, n in items:
            if c["kind"] == "Q" and n == "G":
                m = int(c["ref"][1:])
                k = (m + 1) // 2
                return f"затвор Q{m} ({'верхний' if m % 2 else 'нижний'}), вход {gate_name(k)}"
    else:
        for c, n in items:
            if c["kind"] == "Q" and n == "G":
                m = int(c["ref"][1:])
                led = next(x for x in b.comps if x["ref"] == f"HL{m}")
                return f"затвор Q{m} → светодиод HL{m} ({led['net']})"
    return ", ".join(f"{c['ref']}.{n}" for c, n in items) or "свободно"


def gate_name(k):
    out = GATES[k - 1][0]
    return f"N{k}" + (f" = {out}" if out in ("S", "Cout") else "")


# ---------------------------------------------------------------- 10: ячейка крупно

def closeup():
    b = bit_board()
    find = b.finder()
    P = 44
    COLS, NROWS = 10, 12
    s = Svg(1560, 1200)
    s.text(24, 34, "Как спаяна одна ячейка (вентиль И-НЕ) и как ячейки соединяются между собой", 20, anchor="start", weight="bold")
    s.text(24, 58, "Крупно левый верхний угол платы разряда: ячейки N1, N2, N3 (столбцы 1–10, ряды A–L). "
           "Цифры в красных кружках объяснены справа.", 13, MUTED, anchor="start")

    def panel(ox, oy, mirror):
        X = (lambda c: ox + (COLS - c + 0.5) * P) if mirror else (lambda c: ox + (c - 0.5) * P)
        Y = lambda r: oy + (r - 0.5) * P
        s.add(f'<rect x="{ox}" y="{oy}" width="{COLS * P}" height="{NROWS * P}" fill="{PCB}" rx="6"/>')
        for c in range(1, COLS + 1):
            s.text(X(c), oy - 8, str(c), 11, MUTED, weight="bold")
        for r in range(1, NROWS + 1):
            s.text(ox - 12, Y(r) + 4, ROWS[r - 1], 12, MUTED, weight="bold")
        for c in range(1, COLS + 1):
            for r in range(1, NROWS + 1):
                s.add(f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.3 * P:.1f}" fill="{PAD}" stroke="{PAD_EDGE}"/>'
                      f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.1 * P:.1f}" fill="#123524"/>')
        return X, Y

    inside = lambda p: 1 <= p[0] <= COLS and 1 <= p[1] <= NROWS

    # ---- вид сверху
    ox, oy = 50, 130
    s.text(ox, oy - 34, "ВИД СВЕРХУ (сторона деталей)", 15, anchor="start", weight="bold")
    X, Y = panel(ox, oy, False)
    for c in b.comps:
        if not all(inside(p) for p in c["pins"].values()):
            continue
        if c["kind"] == "R":
            (x, r1), (_, r2) = c["pins"]["1"], c["pins"]["2"]
            s.line(X(x), Y(r1), X(x), Y(r2), "#b0bec5", 3)
            bt, bb = Y(r1) + 0.6 * P, Y(r2) - 0.6 * P
            s.add(f'<rect x="{X(x) - 0.3 * P:.1f}" y="{bt:.1f}" width="{0.6 * P:.1f}" height="{bb - bt:.1f}" rx="8" '
                  f'fill="#e9d3a4" stroke="#8d6e63" stroke-width="1.5"/>')
            for i, col in enumerate(BANDS["10k"]):
                yy = bt + (bb - bt) * (0.15 + 0.2 * i + (0.08 if i == 3 else 0))
                s.add(f'<rect x="{X(x) - 0.3 * P:.1f}" y="{yy:.1f}" width="{0.6 * P:.1f}" height="5" fill="{col}"/>')
            for p in c["pins"].values():
                s.add(f'<circle cx="{X(p[0])}" cy="{Y(p[1])}" r="5" fill="#90a4ae" stroke="#455a64"/>')
            s.text(X(x) - 0.5 * P, (Y(r1) + Y(r2)) / 2 + 4, c["ref"], 12, "#ffffff", anchor="end", weight="bold")
        elif c["kind"] == "Q":
            xg, yg = X(c["pins"]["G"][0]), Y(c["pins"]["G"][1])
            fx = xg + 0.4 * P
            y1, y2 = yg - 1.05 * P, yg + 1.05 * P
            s.add(f'<path d="M{fx:.1f},{y1:.1f} C{fx - 1.7 * P:.1f},{y1:.1f} {fx - 1.7 * P:.1f},{y2:.1f} {fx:.1f},{y2:.1f} Z" '
                  f'fill="#37474f" fill-opacity=".72" stroke="#101418" stroke-width="1.5"/>')
            s.line(fx, y1, fx, y2, "#eceff1", 3)
            for n, (px, py) in c["pins"].items():
                s.add(f'<circle cx="{X(px)}" cy="{Y(py)}" r="5" fill="#90a4ae" stroke="#455a64"/>')
                s.text(X(px) - 0.38 * P, Y(py) + 4.5, n, 12, "#ffffff", weight="bold")
            s.text(xg - 0.5 * P, Y(c["pins"]["S"][1]) + 0.72 * P, c["ref"], 11, "#ffffff", weight="bold")

    def clip(p, q):
        """Отрезок p→q, обрезанный рамкой панели (в единицах отверстий)."""
        lo_c, hi_c, lo_r, hi_r = 0.5, COLS + 0.5, 0.5, NROWS + 0.5
        (x1, y1), (x2, y2) = p, q
        t = 1.0
        for v1, v2, lo, hi in ((x1, x2, lo_c, hi_c), (y1, y2, lo_r, hi_r)):
            if v2 > hi:
                t = min(t, (hi - v1) / (v2 - v1))
            if v2 < lo:
                t = min(t, (lo - v1) / (v2 - v1))
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    Xf = lambda c: ox + (c - 0.5) * P
    Yf = lambda r: oy + (r - 0.5) * P
    for p, q, net in b.wires:
        if not (inside(p) or inside(q)):
            continue
        col = net_color(net)
        if inside(p) and inside(q):
            s.line(Xf(p[0]), Yf(p[1]), Xf(q[0]), Yf(q[1]), "#000000", 8, extra='stroke-opacity=".3"')
            s.line(Xf(p[0]), Yf(p[1]), Xf(q[0]), Yf(q[1]), col, 5)
            for e in (p, q):
                s.add(f'<circle cx="{Xf(e[0])}" cy="{Yf(e[1])}" r="7" fill="{col}" stroke="#ffffff" stroke-width="2"/>')
            s.arrow_head(Xf(q[0]), Yf(q[1]), Xf(q[0]) - Xf(p[0]), Yf(q[1]) - Yf(p[1]), col, 13)
            continue
        # провод уходит за кадр: бледная линия в его сторону и метка у отверстия
        e, far = (p, q) if inside(p) else (q, p)
        z = clip(e, far)
        s.line(Xf(e[0]), Yf(e[1]), Xf(z[0]), Yf(z[1]), col, 3, extra='stroke-opacity=".35" stroke-dasharray="6 5"')
        s.add(f'<circle cx="{Xf(e[0])}" cy="{Yf(e[1])}" r="7" fill="{col}" stroke="#ffffff" stroke-width="2"/>')
        lab = f"{net} → {hn(far)}" if e == p else f"{net} ← от {hn(far)}"
        w = 7 * len(lab) + 10
        ty = Yf(e[1]) + (0.5 * P if e[1] == 1 else -0.5 * P)
        s.add(f'<rect x="{Xf(e[0]) - w / 2:.1f}" y="{ty - 9:.1f}" width="{w}" height="17" rx="4" fill="{col}" stroke="#ffffff"/>')
        s.text(Xf(e[0]), ty + 4, lab, 11, "#ffffff", weight="bold")

    top_badges = [(1, 3.72, 2.3), (2, 1.3, 5.6), (3, 1.3, 8.6), (4, 1.3, 7.0), (5, 1.3, 10.0),
                  (6, 4.62, 4.2), (7, 4.35, 8.3)]
    for n, c, r in top_badges:
        s.badge(Xf(c), Yf(r), n)

    # ---- вид снизу
    ox2 = ox + COLS * P + 90
    s.text(ox2, oy - 34, "ВИД СНИЗУ (сторона пайки, зеркально: столбец 1 справа)", 15, anchor="start", weight="bold")
    X2, Y2 = panel(ox2, oy, True)
    for name, pads in b.rails:
        ps = [p for p in pads if inside(p)]
        if ps:
            s.line(X2(ps[0][0]) + 0.35 * P, Y2(ps[0][1]), X2(ps[-1][0]) - 0.35 * P, Y2(ps[-1][1]), "#5f6a73", 13)
            s.line(X2(ps[0][0]) + 0.35 * P, Y2(ps[0][1]), X2(ps[-1][0]) - 0.35 * P, Y2(ps[-1][1]), "#e0e0e0", 8)
    for p, q in b.bridges:
        if inside(p) and inside(q):
            s.line(X2(p[0]), Y2(p[1]), X2(q[0]), Y2(q[1]), "#5f6a73", 0.55 * P)
            s.line(X2(p[0]), Y2(p[1]), X2(q[0]), Y2(q[1]), SOLDER, 0.4 * P)
    for c in b.comps:
        for n, p in c["pins"].items():
            if inside(p):
                s.add(f'<circle cx="{X2(p[0])}" cy="{Y2(p[1])}" r="5" fill="#455a64"/>')
                if c["kind"] == "Q":
                    s.text(X2(p[0]) + 0.02 * P, Y2(p[1]) - 7, f"{n}", 10, INK, weight="bold")
    for p, q, net in b.wires:
        for e in (p, q):
            if inside(e):
                s.add(f'<circle cx="{X2(e[0])}" cy="{Y2(e[1])}" r="{0.27 * P:.1f}" fill="none" stroke="{net_color(net)}" stroke-width="4"/>')
    s.text(X2(1) + 0.6 * P, Y2(1) + 4, "+5V", 12, "#d32f2f", anchor="start", weight="bold")
    s.text(X2(1) + 0.6 * P, Y2(12) + 4, "GND", 12, INK, anchor="start", weight="bold")
    bot_badges = [(8, 7.5, 1.6), (9, 2.4, 5.5), (10, 2.4, 8.5), (11, 2.4, 11.5), (12, 1.45, 7.0),
                  (13, 4.6, 4.5), (14, 7.5, 11.4)]
    for n, c, r in bot_badges:
        s.badge(X2(c), Y2(r), n)

    # ---- пояснения
    lx = ox2 + COLS * P + 40
    notes = [
        (None, "Сверху (детали и провода):"),
        (1, "R1 лежит на плате, ножки в A3 и E3."),
        (2, "Q1, верхний транзистор: D→F3, G→G3, S→H3."),
        (3, "Q2, нижний: D→I3, G→J3, S→K3. Плоская сторона вправо."),
        (4, "Провод A (от штырька J1). Входит в G2, соседнее отверстие с затвором Q1."),
        (5, "Провод B. Входит в J2, рядом с затвором Q2."),
        (6, "Выход N1: F4, E4, D4 — три отверстия под три провода к другим ячейкам."),
        (7, "Пример связи ячеек: провод из F4 (выход N1) в J5 — к затвору Q4, вход N2."),
        (None, ""),
        (None, "Снизу (пайка):"),
        (8, "Шина +5V: голый провод по ряду A, спаян с ножкой каждого резистора."),
        (9, "E3–F3: ножку D транзистора Q1 загнуть на площадку E3 (там ножка R1) и спаять. Это выход ячейки."),
        (10, "H3–I3: ножку D транзистора Q2 загнуть на H3 (там ножка S от Q1) и спаять. Так транзисторы стоят подряд."),
        (11, "K3–L3: ножку S транзистора Q2 загнуть на шину GND и спаять."),
        (12, "G2–G3: конец провода A загнуть к ножке G транзистора Q1 и спаять. Так же J2–J3 для B и Q2."),
        (13, "F3–F4–E4–D4: концы трёх проводов загнуть друг к другу и к ножке D транзистора Q1."),
        (14, "Шина GND: голый провод по ряду L."),
    ]
    y = oy + 6
    for n, t in notes:
        if n is None:
            s.text(lx, y + 4, t, 14, anchor="start", weight="bold")
        else:
            s.badge(lx + 11, y, n)
            words, line = t.split(), ""
            lines = []
            for w in words:
                if len(line) + len(w) > 44:
                    lines.append(line)
                    line = w
                else:
                    line = (line + " " + w).strip()
            lines.append(line)
            for i, ln in enumerate(lines):
                s.text(lx + 30, y + 4 + i * 16, ln, 12, anchor="start")
            y += 16 * (len(lines) - 1)
        y += 30

    # ---- разрезы
    cut_y = oy + NROWS * P + 150
    s.text(24, cut_y - 30, "РАЗРЕЗЫ СБОКУ (упрощённо): как ножка, провод и припой встречаются в отверстиях", 15, anchor="start", weight="bold")

    def board_strip(x0, holes, by, pp, labels):
        """Плата в разрезе: верх на by. holes — x центров отверстий."""
        s.add(f'<rect x="{x0}" y="{by}" width="{holes[-1] - x0 + 0.6 * pp:.1f}" height="14" fill="{PCB}"/>')
        for x, lab in zip(holes, labels):
            s.add(f'<rect x="{x - 4}" y="{by}" width="8" height="14" fill="#ffffff"/>')
            s.add(f'<rect x="{x - 0.34 * pp:.1f}" y="{by + 14}" width="{0.68 * pp:.1f}" height="4" fill="{PAD}"/>')
            s.add(f'<rect x="{x - 4}" y="{by + 14}" width="8" height="4" fill="#ffffff"/>')
            s.text(x, by + 52, lab, 12, MUTED, weight="bold")

    def lead(x, ytop, by, color="#9e9e9e"):
        s.line(x, ytop, x, by + 26, color, 3.2)

    def blob(xa, xb, by):
        s.add(f'<path d="M{xa - 14:.1f},{by + 18} Q{(xa + xb) / 2:.1f},{by + 44} {xb + 14:.1f},{by + 18} Z" '
              f'fill="{SOLDER}" stroke="#78909c" stroke-width="1.5"/>')

    def callout(x, y, tx, ty, t, anchor="start"):
        s.line(x, y, tx, ty, MUTED, 1.2)
        s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{MUTED}"/>')
        s.text(tx + (4 if anchor == "start" else -4), ty + 4, t, 12, INK, anchor=anchor)

    # разрез 1: ряд G, столбцы 1–4 — провод A к затвору Q1
    pp, x0, by = 64, 60, cut_y + 150
    xs = [x0 + (i + 0.5) * pp for i in range(4)]
    s.text(x0, cut_y, "Разрез по ряду G: провод A → затвор Q1", 13, anchor="start", weight="bold")
    board_strip(x0, xs, by, pp, ["G1", "G2", "G3", "G4"])
    s.add(f'<rect x="{xs[2] - 18:.1f}" y="{by - 95}" width="36" height="52" rx="4" fill="#37474f"/>')
    s.line(xs[2] + 18, by - 95, xs[2] + 18, by - 43, "#eceff1", 3)
    s.text(xs[2], by - 64, "Q1", 12, "#ffffff", weight="bold")
    lead(xs[2], by - 43, by)
    col = net_color("A")
    s.add(f'<path d="M{xs[0] - 30:.1f},{by - 120} Q{xs[1]:.1f},{by - 110} {xs[1]:.1f},{by - 20}" fill="none" '
          f'stroke="{col}" stroke-width="7" stroke-linecap="round"/>')
    s.line(xs[1], by - 20, xs[1], by + 24, "#9e9e9e", 3.2)
    s.add(f'<path d="M{xs[1]:.1f},{by + 24} Q{xs[1] + 6:.1f},{by + 30} {xs[2] - 6:.1f},{by + 26}" fill="none" stroke="#9e9e9e" stroke-width="3"/>')
    blob(xs[1], xs[2], by)
    callout(xs[0] + 20, by - 112, xs[3] + 60, by - 140, "провод A сверху, в изоляции")
    callout(xs[1] + 3, by - 8, xs[3] + 60, by - 110, "зачищенный конец (5 мм) через отверстие G2")
    callout(xs[2] + 3, by - 30, xs[3] + 60, by - 80, "ножка затвора Q1 в соседнем отверстии G3")
    callout((xs[1] + xs[2]) / 2, by + 34, xs[3] + 60, by + 30, "снизу: конец провода загнуть к ножке и")
    s.text(xs[3] + 64, by + 48, "спаять обе площадки вместе", 12, INK, anchor="start")

    # разрез 2: столбец 3, ряды A–L — ячейка целиком
    pp2, x02 = 50, 640
    by2 = cut_y + 150
    rows = [ROWS[i] + "3" for i in range(12)]
    xs2 = [x02 + (i + 0.5) * pp2 for i in range(12)]
    s.text(x02, cut_y, "Разрез по столбцу 3: вся ячейка N1 сверху вниз", 13, anchor="start", weight="bold")
    board_strip(x02, xs2, by2, pp2, rows)
    # резистор A3–E3
    s.add(f'<path d="M{xs2[0]:.1f},{by2 + 24} L{xs2[0]:.1f},{by2 - 22} L{xs2[4]:.1f},{by2 - 22} L{xs2[4]:.1f},{by2 + 24}" '
          f'fill="none" stroke="#9e9e9e" stroke-width="3.2"/>')
    s.add(f'<rect x="{xs2[1] - 10:.1f}" y="{by2 - 33}" width="{xs2[3] - xs2[1] + 20:.1f}" height="22" rx="10" fill="#e9d3a4" stroke="#8d6e63"/>')
    s.text((xs2[0] + xs2[4]) / 2, by2 - 18, "R1 10 кОм", 11, weight="bold")
    for i0, ref in ((5, "Q1"), (8, "Q2")):
        s.add(f'<rect x="{xs2[i0] - 20:.1f}" y="{by2 - 100}" width="{xs2[i0 + 2] - xs2[i0] + 40:.1f}" height="54" rx="6" fill="#37474f"/>')
        s.text(xs2[i0 + 1], by2 - 70, ref, 12, "#ffffff", weight="bold")
        for j, n in enumerate("DGS"):
            lead(xs2[i0 + j], by2 - 46, by2)
            s.text(xs2[i0 + j] + 9, by2 - 30, n, 11, INK, anchor="start", weight="bold")
    # шины видны торцом, капли
    for i, name, color in ((0, "+5V", "#d32f2f"), (11, "GND", INK)):
        s.add(f'<circle cx="{xs2[i] + 13:.1f}" cy="{by2 + 24}" r="5.5" fill="#e0e0e0" stroke="#5f6a73" stroke-width="2"/>')
        blob(xs2[i], xs2[i], by2)
        s.text(xs2[i], by2 + 70, f"шина {name}", 11, color, weight="bold")
    for frm, to in ((5, 4), (8, 7), (10, 11)):      # какую ножку куда загибаем
        xf, xt = xs2[frm], xs2[to]
        s.add(f'<path d="M{xf:.1f},{by2 + 18} L{xf:.1f},{by2 + 24} Q{xf:.1f},{by2 + 28} {xf + (xt - xf) * 0.3:.1f},{by2 + 28} '
              f'L{xt:.1f},{by2 + 26}" fill="none" stroke="#9e9e9e" stroke-width="3"/>')
        blob(xs2[min(frm, to)], xs2[max(frm, to)], by2)
    for i in (6, 9):
        blob(xs2[i], xs2[i], by2)
    for (a_, b_), t in (((4, 5), "R1 + сток Q1 = выход N1"), ((7, 8), "исток Q1 → сток Q2"),
                        ((10, 11), "исток Q2 → GND")):
        s.text((xs2[a_] + xs2[b_]) / 2, by2 + 88 + (14 if a_ == 7 else 0), t, 11, "#c62828", weight="bold")
    s.text(x02, by2 + 130, "Правило: сначала вставить обе детали, потом снизу загнуть ножку одной на площадку другой и спаять. Не загибайте над пустым отверстием.",
           12, "#c62828", anchor="start", weight="bold")
    s.text(x02, by2 + 148, "Затворы G3 и J3 припаяны к своим площадкам, а провода A и B подходят к ним сбоку из столбца 2 (разрез слева).",
           12, MUTED, anchor="start")
    s.text(x02, by2 + 166, "Путь тока, когда оба входа = 1: +5V → R1 → Q1 → Q2 → GND, выход N1 падает в 0.", 12, MUTED, anchor="start")
    s.save("10_cell_closeup.svg")


# ---------------------------------------------------------------- 11, 12: платы на просвет

def wiring_map(b, name, title):
    P, ML, MT = 26, 50, 110
    TW = 640
    W = ML + (b.cols + 1) * P + 30 + (70 if b.key == "io" else 0) + TW
    H = max(MT + (b.rows + 1) * P + 70, MT + 60 + 26 * (len(b.wires) + 1) + 190)
    s = Svg(W, H)
    s.text(24, 34, title, 20, anchor="start", weight="bold")
    s.text(24, 58, "Вид сверху «на просвет». Серые полосы — соединения снизу (шины и загнутые ножки). "
           "Цветные стрелки — провода сверху: от источника сигнала к входу.", 13, MUTED, anchor="start")
    s.text(24, 78, "Номер у стрелки = строка таблицы справа. В каждом отверстии ровно один конец провода или одна ножка.",
           13, MUTED, anchor="start")
    X = lambda c: ML + c * P
    Y = lambda r: MT + r * P
    s.add(f'<rect x="{X(1) - 0.75 * P}" y="{Y(1) - 0.75 * P}" width="{(b.cols - 1 + 1.5) * P}" height="{(b.rows - 1 + 1.5) * P}" '
          f'rx="8" fill="{PCB}"/>')
    for c in range(1, b.cols + 1):
        s.text(X(c), Y(1) - 0.95 * P, str(c), 9, MUTED)
    for r in range(1, b.rows + 1):
        s.text(X(1) - 1.15 * P, Y(r) + 3.5, ROWS[r - 1], 10, MUTED, weight="bold")
    for c in range(1, b.cols + 1):
        for r in range(1, b.rows + 1):
            s.add(f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.28 * P:.1f}" fill="{PAD}" fill-opacity=".55"/>')
    # снизу: шины и перемычки
    for nm, pads in b.rails:
        (c1, r1), (c2, r2) = pads[0], pads[-1]
        s.line(X(c1), Y(r1), X(c2), Y(r2), "#d32f2f" if nm == "+5V" else "#263238", 0.36 * P, extra='stroke-opacity=".45"')
    for p, q in b.bridges:
        s.line(X(p[0]), Y(p[1]), X(q[0]), Y(q[1]), "#eceff1", 0.42 * P, extra='stroke-opacity=".85"')
    # детали — контуром
    for c in b.comps:
        k, pins = c["kind"], c["pins"]
        if k == "R":
            (x, r1), (_, r2) = pins["1"], pins["2"]
            s.add(f'<rect x="{X(x) - 0.3 * P:.1f}" y="{Y(r1) + 0.55 * P:.1f}" width="{0.6 * P:.1f}" '
                  f'height="{Y(r2) - Y(r1) - 1.1 * P:.1f}" rx="5" fill="#e9d3a4" fill-opacity=".8" stroke="#8d6e63"/>')
            s.text(X(x) + 0.5 * P, (Y(r1) + Y(r2)) / 2 + 3, c["ref"], 9, "#ffffff", anchor="start", weight="bold")
        elif k == "Q":
            xg, yg = X(pins["G"][0]), Y(pins["G"][1])
            fx = xg + 0.42 * P
            s.add(f'<path d="M{fx:.1f},{yg - 1.02 * P:.1f} C{fx - 1.7 * P:.1f},{yg - 1.02 * P:.1f} {fx - 1.7 * P:.1f},'
                  f'{yg + 1.02 * P:.1f} {fx:.1f},{yg + 1.02 * P:.1f} Z" fill="#37474f" fill-opacity=".55" stroke="#101418"/>')
            for n, (px, py) in pins.items():
                s.text(X(px) - 0.36 * P, Y(py) + 3.5, n, 8.5, "#ffffff", weight="bold")
            s.text(xg - 0.3 * P, Y(pins["S"][1]) + 0.68 * P, c["ref"], 8.5, "#ffffff", weight="bold")
        elif k == "LED":
            (x, ra), (_, rk) = pins["A"], pins["K"]
            s.add(f'<circle cx="{X(x)}" cy="{(Y(ra) + Y(rk)) / 2}" r="{1.05 * P:.1f}" fill="#ef5350" fill-opacity=".5" stroke="#b71c1c"/>')
            s.text(X(x) + 1.2 * P, (Y(ra) + Y(rk)) / 2 + 3, f"{c['ref']} {c['net']}", 9, "#ffffff", anchor="start", weight="bold")
        elif k == "SW":
            c0, r = pins["1"]
            s.add(f'<rect x="{X(c0) - 0.6 * P:.1f}" y="{Y(r) - 0.5 * P:.1f}" width="{(c["n"] - 1 + 1.2) * P:.1f}" '
                  f'height="{4 * P:.1f}" rx="3" fill="#1e63b5" fill-opacity=".55" stroke="#0d3c73"/>')
            for i, lab in enumerate(c["labels"]):
                if lab:
                    s.text(X(c0 + i), Y(r) - 0.75 * P, lab, 9.5, "#ffffff", weight="bold")
            s.text(X(c0 + c["n"] - 1) + 0.5 * P, Y(r) + 1.6 * P, c["ref"], 9, "#ffffff", anchor="end", weight="bold")
        elif k == "C":
            (xp, yp), (xm, ym) = pins["+"], pins["-"]
            s.add(f'<circle cx="{(X(xp) + X(xm)) / 2}" cy="{Y(yp)}" r="{1.5 * P:.1f}" fill="#1f3c88" fill-opacity=".5" stroke="#0d1b45"/>')
            s.text((X(xp) + X(xm)) / 2, Y(yp) + 3, "C1", 9, "#ffffff", weight="bold")
        elif k in ("J", "X"):
            pts = list(pins.values())
            for (px, py), nm in zip(pts, c["names"]):
                if k == "J":
                    s.add(f'<rect x="{X(px) - 5}" y="{Y(py) - 5}" width="10" height="10" fill="#ffd54f" stroke="#212121"/>')
                else:
                    s.add(f'<circle cx="{X(px)}" cy="{Y(py)}" r="5" fill="#90a4ae" stroke="#37474f"/>')
                if nm != "—":
                    dy = 1.25 * P if (k == "J" and b.key == "bit") else -0.55 * P if k == "X" else 1.1 * P
                    s.text(X(px), Y(py) + dy, nm, 8, "#ffffff", weight="bold")
            if k == "J":
                s.text(X(pts[0][0]) - 0.6 * P, Y(pts[0][1]) + 3.5, c["ref"], 9, "#ffffff", anchor="end", weight="bold")
            else:
                s.add(f'<path d="M{X(pts[-1][0]) + 0.3 * P:.1f},{Y(pts[0][1])} L{X(b.cols) + 1.5 * P:.1f},{Y(pts[0][1])}" '
                      f'stroke="#90a4ae" stroke-width="6"/>')
                s.text(X(b.cols) + 1.6 * P, Y(pts[0][1]) + 4, f"к разряду {c['bit']}", 9, INK, anchor="start", weight="bold")
    # провода
    for i, (p, q, net) in enumerate(b.wires, 1):
        xa, ya, xb, yb = X(p[0]), Y(p[1]), X(q[0]), Y(q[1])
        dx, dy = xb - xa, yb - ya
        L = max((dx * dx + dy * dy) ** 0.5, 1)
        k = min(0.14 * L, 30) * (1 if i % 2 else -1)
        cx, cy = (xa + xb) / 2 - dy / L * k, (ya + yb) / 2 + dx / L * k
        col = net_color(net)
        d = f"M{xa:.1f},{ya:.1f} Q{cx:.1f},{cy:.1f} {xb:.1f},{yb:.1f}"
        s.add(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="5.5"/>'
              f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3"/>')
        s.add(f'<circle cx="{xa}" cy="{ya}" r="4.5" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
        s.arrow_head(xb, yb, xb - cx, yb - cy, col, 11)
        mx, my = (xa + 2 * cx + xb) / 4, (ya + 2 * cy + yb) / 4
        s.badge(mx, my, i, col, 9)
    # таблица
    tx = ML + (b.cols + 1) * P + 30 + (70 if b.key == "io" else 0)
    ty = MT - 10
    s.text(tx, ty, "Провода сверху: что с чем соединяет", 15, anchor="start", weight="bold")
    cols_x = [tx, tx + 34, tx + 84, tx + 356]
    ty += 26
    for x, h in zip(cols_x, ["№", "цепь", "откуда (что там)", "куда (что там)"]):
        s.text(x, ty, h, 12, MUTED, anchor="start", weight="bold")
    for i, (p, q, net) in enumerate(b.wires, 1):
        y = ty + 24 * i
        if i % 2:
            s.add(f'<rect x="{tx - 6}" y="{y - 15}" width="{TW - 20}" height="24" fill="#f5f7f8"/>')
        s.badge(tx + 10, y - 4, i, net_color(net), 9)
        s.text(cols_x[1], y, net, 12, net_color(net), anchor="start", weight="bold")
        s.text(cols_x[2], y, f"{hn(p)} — {describe(b, p)}", 11, anchor="start")
        s.text(cols_x[3], y, f"{hn(q)} — {describe(b, q)}", 11, anchor="start")
    y = ty + 24 * (len(b.wires) + 1) + 10
    hints = ["Как паять провод: зачистить 5 мм, вставить сверху в отверстие, снизу", "загнуть к соседней ножке и спаять (см. чертёж 10).",
             "Серая полоса между двумя отверстиями: снизу загнуть ножку", "из одного отверстия на площадку соседнего и спаять.",
             "Сверьте каждую строку с чертежом и поставьте галочку в wiring.md."]
    for j, h in enumerate(hints):
        s.text(tx, y + 18 * j + (8 if j >= 2 else 0) + (8 if j >= 4 else 0), h, 12, MUTED, anchor="start")
    s.save(name)


# ---------------------------------------------------------------- 13: плата ввода-вывода по частям

def io_explained():
    b = io_board()
    RED, GNDC = net_color("+5V"), net_color("GND")
    s = Svg(1720, 1500)
    s.text(24, 34, "Плата ввода-вывода по частям: куда идут резисторы, конденсатор и питание MB102", 20, anchor="start", weight="bold")
    s.text(24, 58, "Слева — вся плата, видны только шины питания (снизу, «на просвет»). Справа — две цепочки крупно, "
           "по отверстиям. Все остальные столбцы устроены так же.", 13, MUTED, anchor="start")

    # ---------- 1. вся плата: шины питания + MB102
    P, ox, oy = 26, 60, 300
    X = lambda c: ox + (c - 0.5) * P
    Y = lambda r: oy + (r - 0.5) * P
    s.text(ox, 100, "1. ПИТАНИЕ: MB102 → плата → шины", 15, anchor="start", weight="bold")
    s.add(f'<rect x="{ox}" y="{oy}" width="{30 * P}" height="{24 * P}" fill="{PCB}" rx="6"/>')
    for c in range(1, 31):
        if c % 2 == 0 or c in (1, 3):
            s.text(X(c), oy - 6, str(c), 9, MUTED)
        for r in range(1, 25):
            s.add(f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.27 * P:.1f}" fill="{PAD}" fill-opacity=".55"/>')
    for r in range(1, 25):
        s.text(ox - 10, Y(r) + 4, ROWS[r - 1], 10, MUTED, weight="bold")
    # провода сверху бледно
    for p, q, net in b.wires:
        if net not in ("+5V", "GND"):
            s.line(X(p[0]), Y(p[1]), X(q[0]), Y(q[1]), net_color(net), 2, extra='stroke-opacity=".22"')
    # детали бледно
    for c in b.comps:
        k, pins = c["kind"], list(c["pins"].values())
        if k == "R":
            (x, r1), (_, r2) = pins
            s.add(f'<rect x="{X(x) - 6}" y="{Y(r1) + 6}" width="12" height="{Y(r2) - Y(r1) - 12}" rx="4" fill="#e9d3a4" fill-opacity=".8"/>')
        elif k == "SW":
            cs = [p[0] for p in pins]
            s.add(f'<rect x="{X(min(cs)) - 10}" y="{Y(pins[0][1]) - 8}" width="{X(max(cs)) - X(min(cs)) + 20}" '
                  f'height="{3 * P + 16}" rx="3" fill="#1e64c8" fill-opacity=".75"/>')
            s.text((X(min(cs)) + X(max(cs))) / 2, Y(pins[0][1]) + 1.6 * P, c["ref"], 11, "#ffffff", weight="bold")
        elif k == "LED":
            s.add(f'<circle cx="{X(pins[0][0])}" cy="{(Y(pins[0][1]) + Y(pins[1][1])) / 2}" r="11" fill="#e53935" fill-opacity=".6"/>')
        elif k == "Q":
            s.add(f'<rect x="{X(pins[0][0]) - 10}" y="{Y(pins[0][1]) - 6}" width="16" height="{2 * P + 12}" rx="6" fill="#37474f" fill-opacity=".7"/>')
        elif k == "X":
            for q in pins:
                s.add(f'<circle cx="{X(q[0])}" cy="{Y(q[1])}" r="5" fill="#90a4ae"/>')
    for i, r in CABLE_ROW.items():
        s.text(X(30) + 18, Y(r) + 4, f"X{i} → разряд {i}", 10, MUTED, anchor="start", weight="bold")
    # шины
    for name, pads in b.rails:
        col = RED if name == "+5V" else GNDC
        a, z = pads[0], pads[-1]
        s.line(X(a[0]), Y(a[1]), X(z[0]), Y(z[1]), "#ffffff", 11)
        s.line(X(a[0]), Y(a[1]), X(z[0]), Y(z[1]), col, 7)
    w = next(w for w in b.wires if w[2] == "GND")
    s.line(X(w[0][0]), Y(w[0][1]), X(w[1][0]), Y(w[1][1]), GNDC, 5, extra='stroke-dasharray="7 4"')
    # C1
    cp, cm = b.pin("C1", "+"), b.pin("C1", "-")
    cx, cy = (X(cp[0]) + X(cm[0])) / 2, Y(cp[1])
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{1.25 * P:.1f}" fill="#283593" stroke="#ffffff" stroke-width="2"/>'
          f'<path d="M{cx + 0.75 * P:.1f},{cy - 1.0 * P:.1f} A{1.25 * P:.1f},{1.25 * P:.1f} 0 0 1 {cx + 0.75 * P:.1f},{cy + 1.0 * P:.1f} Z" fill="#c5cae9"/>')
    s.text(cx - 0.55 * P, cy + 5, "+", 15, "#ffffff", weight="bold")
    s.text(cx + 0.95 * P, cy + 5, "−", 15, "#283593", weight="bold")
    for q in (cp, cm):
        s.add(f'<circle cx="{X(q[0])}" cy="{Y(q[1])}" r="4" fill="#ffd54f"/>')
    # MB102 -> A22 / A24 (место J1)
    j1, j3 = b.pin("J1", "1"), b.pin("J1", "3")
    for q, col in ((j1, RED), (j3, GNDC)):
        s.add(f'<circle cx="{X(q[0])}" cy="{Y(q[1])}" r="7" fill="{col}" stroke="#ffffff" stroke-width="2"/>')
    mx, my, mw, mh = X(17), 128, 300, 100
    s.add(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="6" fill="#b71c1c" stroke="#7f0000" stroke-width="2"/>')
    s.add(f'<rect x="{mx - 18}" y="{my + 30}" width="34" height="40" rx="3" fill="#9e9e9e"/>')
    s.text(mx + 60, my + 22, "MB102", 14, "#ffffff", anchor="start", weight="bold")
    s.text(mx + 60, my + 40, "вход: USB или штекер", 10, "#ffffff", anchor="start")
    s.add(f'<rect x="{mx + 200}" y="{my + 12}" width="80" height="30" rx="3" fill="#212121"/>')
    s.add(f'<rect x="{mx + 204}" y="{my + 16}" width="36" height="22" rx="2" fill="#ffd54f"/>')
    s.text(mx + 222, my + 31, "5V", 10, "#212121", weight="bold")
    s.text(mx + 262, my + 31, "3.3", 9, "#9e9e9e")
    s.text(mx + 240, my + 58, "перемычка на 5V!", 11, "#ffffff", weight="bold")
    p5, pg = (mx + 120, my + mh), (mx + 165, my + mh)
    s.text(p5[0], p5[1] - 10, "5V", 11, "#ffffff", weight="bold")
    s.text(pg[0], pg[1] - 10, "GND", 11, "#ffffff", weight="bold")
    for (px, py), q, col in ((p5, j1, RED), (pg, j3, GNDC)):
        s.add(f'<rect x="{px - 4}" y="{py - 4}" width="8" height="12" fill="#ffd54f"/>')
        d = f"M{px},{py + 8} C{px},{py + 40} {X(q[0])},{Y(q[1]) - 50} {X(q[0])},{Y(q[1])}"
        s.add(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="7"/>'
              f'<path d="{d}" fill="none" stroke="{col}" stroke-width="4.5"/>')
    s.text(mx - 30, my + 40, "два провода: припаять к штырькам", 12, anchor="end")
    s.text(mx - 30, my + 58, "5V и GND модуля, другие концы —", 12, anchor="end")
    s.text(mx - 30, my + 76, "в A22 (+5V) и A24 (GND)", 12, anchor="end", weight="bold")
    # номера шин
    for n, tx, ty in [(1, X(22) + 14, Y(10)), (2, X(24) + 14, Y(22.4)), (3, X(14), Y(3) - 13),
                      (4, X(16), Y(12) + 14), (5, X(21), Y(14) - 13), (6, X(21), Y(24) + 15),
                      (7, cx - 1.5 * P, cy - 1.0 * P), (8, X(20.3), Y(-2.2))]:
        s.badge(tx, ty, n)

    lx, ly = ox, oy + 24 * P + 50
    legend = [
        (8, RED, "MB102 → A22 (+5V) и A24 (GND). Это место J1: штырьки можно не ставить, провода прямо в отверстия."),
        (1, RED, "Столбец 22 (A22…T22) — главная шина +5V, от неё питаются ряды C и N."),
        (2, GNDC, "Столбец 24 (A24…X24) — главная шина GND, от неё ряды X и L (ряд L — через провод L20→L24, пунктир)."),
        (3, RED, "Ряд C (+5V) — верхние выводы всех 9 рычажков SW1 и SW2."),
        (4, GNDC, "Ряд L (GND) — нижние ножки резисторов R1–R9 (10 кОм)."),
        (5, RED, "Ряд N (+5V) — верхние ножки резисторов R10–R14 (470 Ом)."),
        (6, GNDC, "Ряд X (GND) — ножки S транзисторов Q1–Q5."),
        (7, "#283593", "C1 470 мкФ: «+» в G22 (шина +5V), «−» в G24 (шина GND). Полоса «−» на корпусе — к столбцу 24."),
        (None, MUTED, "Кабели X0–X3 берут +5V и GND со столбцов 22 и 24 (жилы 1 и 2)."),
    ]
    for i, (n, col, t) in enumerate(legend):
        y = ly + 24 * i
        if n:
            s.badge(lx + 10, y - 4, n, col, 10)
        s.text(lx + 28, y, t, 12, anchor="start")

    # ---------- 2 и 3: цепочки крупно
    def strip(ox2, oy2, r0, r1, title, sub):
        Q = 38
        Xs = lambda c: ox2 + (c - 0.5) * Q
        Ys = lambda r: oy2 + (r - r0 + 0.5) * Q
        s.text(ox2 - 20, oy2 - 56, title, 15, anchor="start", weight="bold")
        s.text(ox2 - 20, oy2 - 36, sub, 12, MUTED, anchor="start")
        s.add(f'<rect x="{ox2}" y="{oy2}" width="{3 * Q}" height="{(r1 - r0 + 1) * Q}" fill="{PCB}" rx="5"/>')
        for c in range(1, 4):
            s.text(Xs(c), oy2 - 8, str(c), 11, MUTED, weight="bold")
            for r in range(r0, r1 + 1):
                s.add(f'<circle cx="{Xs(c)}" cy="{Ys(r)}" r="{0.29 * Q:.1f}" fill="{PAD}" stroke="{PAD_EDGE}"/>'
                      f'<circle cx="{Xs(c)}" cy="{Ys(r)}" r="{0.09 * Q:.1f}" fill="#123524"/>')
        for r in range(r0, r1 + 1):
            s.text(ox2 - 10, Ys(r) + 4, ROWS[r - 1], 12, MUTED, weight="bold")
        return Xs, Ys, Q

    def hrail(Xs, Ys, Q, r, col):
        s.line(Xs(1) - 0.45 * Q, Ys(r), Xs(3) + 0.45 * Q, Ys(r), "#ffffff", 12)
        s.line(Xs(1) - 0.45 * Q, Ys(r), Xs(3) + 0.45 * Q, Ys(r), col, 8)

    def bridge(Xs, Ys, Q, p, q):
        s.line(Xs(p[0]), Ys(p[1]), Xs(q[0]), Ys(q[1]), "#5f6a73", 0.5 * Q)
        s.line(Xs(p[0]), Ys(p[1]), Xs(q[0]), Ys(q[1]), SOLDER, 0.36 * Q)

    def leg(Xs, Ys, p):
        s.add(f'<circle cx="{Xs(p[0])}" cy="{Ys(p[1])}" r="5" fill="#455a64" stroke="#ffffff"/>')

    def resistor(Xs, Ys, Q, c, r1, r2, bands, ref):
        s.line(Xs(c), Ys(r1), Xs(c), Ys(r2), "#9e9e9e", 3)
        t, bt = Ys(r1) + 0.55 * Q, Ys(r2) - 0.55 * Q
        s.add(f'<rect x="{Xs(c) - 0.27 * Q:.1f}" y="{t:.1f}" width="{0.54 * Q:.1f}" height="{bt - t:.1f}" rx="7" '
              f'fill="#e9d3a4" stroke="#8d6e63" stroke-width="1.5"/>')
        for i, col in enumerate(bands):
            yy = t + (bt - t) * (0.15 + 0.2 * i + (0.08 if i == 3 else 0))
            s.add(f'<rect x="{Xs(c) - 0.27 * Q:.1f}" y="{yy:.1f}" width="{0.54 * Q:.1f}" height="4" fill="{col}"/>')
        s.text(Xs(c) - 0.42 * Q, (t + bt) / 2 + 4, ref, 12, "#ffffff", anchor="end", weight="bold")

    def note(Xs, Ys, Q, r, text, col=INK, dy=0):
        s.text(Xs(3) + 0.8 * Q, Ys(r) + 4 + dy, text, 12, col, anchor="start")

    # --- 2. вход: столбец 2 (рычажок A3, R1)
    sx, sy = 1000, 300
    Xs, Ys, Q = strip(sx, sy, 1, 12, "2. ВХОД: рычажок → резистор 10 кОм",
                      "Столбец 2 (бит A3), ряды A–L. Так же столбцы 3–9 (SW1) и 12 (SW2, Cin).")
    hrail(Xs, Ys, Q, 3, RED)
    hrail(Xs, Ys, Q, 12, GNDC)
    s.add(f'<rect x="{Xs(2) - 0.42 * Q:.1f}" y="{Ys(3) - 0.42 * Q:.1f}" width="{1.84 * Q:.1f}" height="{3.84 * Q:.1f}" '
          f'rx="4" fill="#1e64c8" fill-opacity=".9"/>')
    for c in (2, 3):
        s.add(f'<rect x="{Xs(c) - 7}" y="{Ys(4) - 6}" width="14" height="{1.6 * Q:.1f}" rx="2" fill="#ffffff"/>'
              f'<rect x="{Xs(c) - 7}" y="{Ys(4) - 6}" width="14" height="{0.7 * Q:.1f}" fill="#b0bec5"/>')
    s.text(Xs(2.5), Ys(6) - 8, "SW1", 11, "#ffffff", weight="bold")
    for p in ((2, 3), (2, 6), (3, 3), (3, 6)):
        leg(Xs, Ys, p)
    bridge(Xs, Ys, Q, (2, 6), (2, 7))
    bridge(Xs, Ys, Q, (2, 7), (2, 8))
    resistor(Xs, Ys, Q, 2, 8, 12, BANDS["10k"], "R1")
    leg(Xs, Ys, (2, 8))
    leg(Xs, Ys, (2, 12))
    a3 = net_color("A3")
    dst = next(q for p, q, n in b.wires if n == "A3")
    s.add(f'<circle cx="{Xs(2)}" cy="{Ys(7)}" r="8" fill="{a3}" stroke="#ffffff" stroke-width="2"/>')
    note(Xs, Ys, Q, 3, "C2: верх рычажка — шина +5V (ряд C)", RED)
    note(Xs, Ys, Q, 6, "F2: низ рычажка")
    note(Xs, Ys, Q, 7, f"G2: сюда провод A3 → к кабелю X3 ({hn(dst)})", a3)
    note(Xs, Ys, Q, 8, "H2: верхняя ножка R1")
    note(Xs, Ys, Q, 9, "F2–G2–H2 спаяны снизу в одну точку", MUTED, 8)
    note(Xs, Ys, Q, 12, "L2: нижняя ножка R1 — шина GND (ряд L)", GNDC)
    yy = Ys(12) + 48
    for i, t in enumerate(["Как работает: рычажок ON — G2 соединён с +5V, это 1.",
                           "Рычажок OFF — R1 тянет G2 к GND, это 0.",
                           "Без R1 в положении OFF вход «висел» бы в воздухе."]):
        s.text(sx - 20, yy + 18 * i, t, 12, INK if i < 2 else MUTED, anchor="start")

    # --- 3. выход: столбец 3 (Cout: R10, HL1, Q1)
    sy3 = sy + 12 * 38 + 190
    Xs, Ys, Q = strip(sx, sy3, 14, 24, "3. ВЫХОД: резистор 470 Ом → светодиод → транзистор",
                      "Столбец 3 (светодиод Cout), ряды N–X. Так же столбцы 7, 11, 15, 19 (S3, S2, S1, S0).")
    hrail(Xs, Ys, Q, 14, RED)
    hrail(Xs, Ys, Q, 24, GNDC)
    resistor(Xs, Ys, Q, 3, 14, 18, BANDS["470"], "R10")
    bridge(Xs, Ys, Q, (3, 18), (3, 19))
    s.add(f'<circle cx="{Xs(3)}" cy="{(Ys(19) + Ys(20)) / 2}" r="{0.62 * Q:.1f}" fill="#e53935" fill-opacity=".75" '
          f'stroke="#b71c1c" stroke-width="2"/>')
    s.text(Xs(3) - 0.7 * Q, (Ys(19) + Ys(20)) / 2 + 4, "HL1", 12, "#ffffff", anchor="end", weight="bold")
    bridge(Xs, Ys, Q, (3, 20), (3, 21))
    fx = Xs(3) + 0.42 * Q
    s.add(f'<path d="M{fx:.1f},{Ys(21) - 0.3 * Q:.1f} C{fx - 1.5 * Q:.1f},{Ys(21) - 0.3 * Q:.1f} {fx - 1.5 * Q:.1f},'
          f'{Ys(23) + 0.3 * Q:.1f} {fx:.1f},{Ys(23) + 0.3 * Q:.1f} Z" fill="#37474f" fill-opacity=".72" stroke="#101418"/>')
    s.line(fx, Ys(21) - 0.3 * Q, fx, Ys(23) + 0.3 * Q, "#eceff1", 3)
    s.text(Xs(1), Ys(23) + 4, "Q1", 11, "#ffffff", weight="bold")
    bridge(Xs, Ys, Q, (2, 22), (3, 22))
    bridge(Xs, Ys, Q, (3, 23), (3, 24))
    for r in (14, 18, 19, 20, 21, 22, 23):
        leg(Xs, Ys, (3, r))
    for r, n in ((21, "D"), (22, "G"), (23, "S")):
        s.text(Xs(3) - 0.42 * Q, Ys(r) - 6, n, 10, "#ffffff", weight="bold")
    co = net_color("Cout")
    src = next(p for p, q, n in b.wires if n == "Cout")
    s.add(f'<circle cx="{Xs(2)}" cy="{Ys(22)}" r="8" fill="{co}" stroke="#ffffff" stroke-width="2"/>')
    note(Xs, Ys, Q, 14, "N3: верхняя ножка R10 — шина +5V (ряд N)", RED)
    note(Xs, Ys, Q, 18, "R3–S3: низ R10 + длинная ножка (анод) HL1", dy=10)
    note(Xs, Ys, Q, 20, "T3–U3: короткая ножка (катод) HL1 + D транзистора", dy=10)
    note(Xs, Ys, Q, 22, f"V2–V3: сюда провод Cout (от {hn(src)}) + G транзистора", co)
    note(Xs, Ys, Q, 23, "W3: S транзистора Q1")
    note(Xs, Ys, Q, 24, "X3: шина GND (ряд X)", GNDC)
    yy = Ys(24) + 48
    for i, t in enumerate(["Как работает: на G пришла 1 (5 В) — Q1 открыт, ток идёт",
                           "+5V → R10 → HL1 → Q1 → GND, светодиод горит. Пришёл 0 — не горит.",
                           "Плоская сторона Q1 — вправо, как на плате разряда."]):
        s.text(sx - 20, yy + 18 * i, t, 12, INK if i < 2 else MUTED, anchor="start")
    s.save("13_io_board_explained.svg")


if __name__ == "__main__":
    closeup()
    wiring_map(bit_board(), "11_bit_board_wiring_map.svg", "Плата разряда: какой провод что с чем соединяет")
    wiring_map(io_board(), "12_io_board_wiring_map.svg", "Плата ввода-вывода: какой провод что с чем соединяет")
    io_explained()
    print("готово: 10_cell_closeup.svg, 11_bit_board_wiring_map.svg, 12_io_board_wiring_map.svg, 13_io_board_explained.svg")
