"""Полные схемы соединений «как есть», без меток-заменителей (schematics/14–15).

14 — вся система: MB102, плата ввода-вывода, 4 кабеля, 4 платы разряда.
15 — плата разряда изнутри: 9 ячеек И-НЕ и разъём J1.

Каждое соединение нарисовано линией. Детали нарисованы так, как выглядят
(резистор с полосками, транзистор TO-92 с ножками D G S, светодиод, рычажок).
Точка — соединение; дуга — провода пересекаются, но НЕ соединены.
Цепи берутся из tools/boards.py (GATES, LED_ORDER, SW1_LABELS), поэтому совпадают
с чертежами плат и проверкой на 512 комбинациях.

Запуск из папки homework2.0:  python tools/full_diagrams.py
"""
from boards import GATES, BANDS, LED_ORDER, SW1_LABELS, J_NAMES, net_color
from closeups import Svg, INK, MUTED

LEAD = "#78909c"
HALO = 'stroke="#ffffff" stroke-width="3" paint-order="stroke"'
HOP = 6


class Wires:
    """Линии схемы: сначала собираем, потом рисуем; вертикали перепрыгивают чужие горизонтали."""

    def __init__(self, s):
        self.s, self.h, self.v, self.dots = s, [], [], []

    def hline(self, y, x1, x2, net, w=2.6):
        self.h.append((y, min(x1, x2), max(x1, x2), net, w))

    def vline(self, x, y1, y2, net, w=2.6):
        self.v.append((x, min(y1, y2), max(y1, y2), net, w))

    def dot(self, x, y, net):
        self.dots.append((x, y, net))

    def channel(self, nets, y0, pitch, gap=16):
        """Горизонтальный канал. nets: имя -> [(x, y_конца)], от каждой точки идёт вертикаль к своей дорожке."""
        rows, ys = [], {}
        for name in sorted(nets, key=lambda n: min(x for x, _ in nets[n])):
            xs = [x for x, _ in nets[name]]
            lo, hi = min(xs), max(xs)
            for i, last in enumerate(rows):
                if last + gap < lo:
                    rows[i] = hi
                    break
            else:
                rows.append(hi)
                i = len(rows) - 1
            ys[name] = y0 + i * pitch
            y = ys[name]
            if hi > lo:
                self.hline(y, lo, hi, name)
            for x, ye in nets[name]:
                self.vline(x, ye, y, name)
                if lo < x < hi:
                    self.dot(x, y, name)
        allx = sorted(x for n in nets for x, _ in nets[n])
        assert all(b - a >= 8 for a, b in zip(allx, allx[1:])), "две вертикали канала слишком близко"
        return ys, len(rows)

    def render(self):
        s = self.s
        for y, x1, x2, net, w in self.h:
            s.line(x1, y, x2, y, net_color(net), w)
        for x, y1, y2, net, w in self.v:
            cross = sorted(y for y, a, b, n, _ in self.h
                           if n != net and y1 + HOP < y < y2 - HOP and a + 1 < x < b - 1)
            d = f"M{x:.1f},{y1:.1f}"
            for yc in cross:
                d += f" L{x:.1f},{yc - HOP:.1f} A{HOP},{HOP} 0 0 1 {x:.1f},{yc + HOP:.1f}"
            d += f" L{x:.1f},{y2:.1f}"
            s.add(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="{w + 3}"/>'
                  f'<path d="{d}" fill="none" stroke="{net_color(net)}" stroke-width="{w}" stroke-linecap="round"/>')
        for x, y, net in self.dots:
            s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{net_color(net)}" stroke="#ffffff" stroke-width="1.2"/>')


# ---------------------------------------------------------------- значки деталей

def res_icon(s, x, y1, y2, ref, value, show_value=True):
    s.line(x, y1, x, y2, LEAD, 2.5)
    t, b = y1 + (y2 - y1) * 0.2, y2 - (y2 - y1) * 0.2
    s.add(f'<rect x="{x - 8}" y="{t:.1f}" width="16" height="{b - t:.1f}" rx="6" fill="#e9d3a4" stroke="#8d6e63" stroke-width="1.3"/>')
    for i, col in enumerate(BANDS["10k" if value.startswith("10") else "470"]):
        yy = t + (b - t) * (0.14 + 0.19 * i + (0.1 if i == 3 else 0))
        s.add(f'<rect x="{x - 8}" y="{yy:.1f}" width="16" height="3.5" fill="{col}"/>')
    s.text(x - 13, (t + b) / 2 - 2 + (0 if show_value else 6), ref, 11, INK, anchor="end", weight="bold", extra=HALO)
    if show_value:
        s.text(x - 13, (t + b) / 2 + 11, value, 10, MUTED, anchor="end", extra=HALO)


def fet_icon(s, x, yd, ref):
    """2N7000 как на плате: плоская сторона вправо, ножки D, G, S сверху вниз."""
    y1, y2 = yd - 9, yd + 59
    s.add(f'<path d="M{x + 5},{y1} C{x - 40},{y1} {x - 40},{y2} {x + 5},{y2} Z" fill="#37474f" stroke="#101418" stroke-width="1.2"/>')
    s.line(x + 5, y1, x + 5, y2, "#cfd8dc", 2)
    for i, n in enumerate("DGS"):
        y = yd + 25 * i
        s.add(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#cfd8dc"/>')
        s.text(x - 13, y + 4, n, 10, "#ffffff", weight="bold")
    s.text(x + 10, yd + 4, ref, 11, INK, anchor="start", weight="bold", extra=HALO)


def led_icon(s, x, ya, yk, ref, name):
    s.line(x, ya, x, yk, LEAD, 2.5)
    yc = (ya + yk) / 2
    s.add(f'<path d="M{x - 12},{yc + 10} L{x - 12},{yc - 2} A12,12 0 0 1 {x + 12},{yc - 2} L{x + 12},{yc + 10} Z" '
          f'fill="#ef5350" stroke="#b71c1c" stroke-width="1.5"/>'
          f'<rect x="{x - 15}" y="{yc + 9}" width="30" height="4" fill="#b71c1c"/>')
    s.text(x + 16, ya + 9, "+", 12, "#c62828", anchor="start", weight="bold")
    s.text(x - 17, yc + 2, ref, 11, INK, anchor="end", weight="bold")


def sw_icon(s, x, y1, y2, ref):
    s.line(x, y1, x, y2, LEAD, 2.5)
    yc = (y1 + y2) / 2
    s.add(f'<rect x="{x - 10}" y="{yc - 19}" width="20" height="38" rx="3" fill="#1e64c8"/>'
          f'<rect x="{x - 5}" y="{yc - 14}" width="10" height="28" rx="1.5" fill="#ffffff"/>'
          f'<rect x="{x - 5}" y="{yc - 14}" width="10" height="12" fill="#90a4ae"/>')
    s.text(x - 13, yc + 4, ref, 10, INK, anchor="end", weight="bold")


def cap_icon(s, x, y1, y2):
    s.line(x, y1, x, y2, LEAD, 2.5)
    yc = (y1 + y2) / 2
    s.add(f'<rect x="{x - 15}" y="{yc - 28}" width="30" height="56" rx="6" fill="#283593"/>'
          f'<rect x="{x - 15}" y="{yc + 12}" width="30" height="16" rx="3" fill="#c5cae9"/>')
    s.text(x, yc - 12, "+", 13, "#ffffff", weight="bold")
    s.text(x, yc + 25, "−", 13, "#283593", weight="bold")
    s.text(x + 20, yc - 4, "C1", 11, INK, anchor="start", weight="bold")
    s.text(x + 20, yc + 10, "470 мкФ", 10, MUTED, anchor="start")


def header_icon(s, xs, y, title=None):
    s.add(f'<rect x="{xs[0] - 13}" y="{y - 9}" width="{xs[-1] - xs[0] + 26}" height="18" rx="2" fill="#212121"/>')
    for i, x in enumerate(xs):
        s.add(f'<rect x="{x - 3.5}" y="{y - 3.5}" width="7" height="7" fill="#ffd54f"/>')
    if title:
        s.text(xs[0] - 18, y + 4, title, 11, INK, anchor="end", weight="bold")


def legend(s, x, y):
    s.text(x, y, "Как читать:", 13, anchor="start", weight="bold")
    y += 26
    res_icon(s, x + 30, y - 18, y + 30, "", "")
    s.text(x + 48, y + 9, "резистор (полоски: 10 кОм — коричн.-чёрн.-оранж.)", 12, anchor="start")
    fet_icon(s, x + 470, y - 8, "")
    s.text(x + 488, y + 9, "транзистор 2N7000: плоской стороной вправо, ножки D, G, S", 12, anchor="start")
    y += 60
    s.add(f'<circle cx="{x + 30}" cy="{y}" r="4.5" fill="{INK}"/>')
    s.line(x + 10, y, x + 50, y, INK, 2.6)
    s.line(x + 30, y, x + 30, y + 18, INK, 2.6)
    s.text(x + 60, y + 4, "точка — провода СОЕДИНЕНЫ (спаяны)", 12, anchor="start")
    s.line(x + 450, y, x + 510, y, INK, 2.6)
    s.add(f'<path d="M{x + 480},{y - 18} L{x + 480},{y - HOP} A{HOP},{HOP} 0 0 1 {x + 480},{y + HOP} L{x + 480},{y + 18}" '
          f'fill="none" stroke="#c62828" stroke-width="2.6"/>')
    s.text(x + 520, y + 4, "дуга — провода проходят друг над другом, НЕ соединены", 12, anchor="start")


# ---------------------------------------------------------------- 15: плата разряда изнутри

def bit_board_full():
    W, H = 1580, 1010
    s = Svg(W, H)
    w = Wires(s)
    s.text(24, 34, "Плата разряда изнутри: все 9 ячеек и все соединения линиями", 20, anchor="start", weight="bold")
    s.text(24, 58, "Каждая ячейка — вентиль И-НЕ: резистор сверху, под ним два транзистора друг под другом. "
           "Цветная линия — провод; одинаковый цвет = одна цепь.", 13, MUTED, anchor="start")
    Y5, YG = 150, 470
    xc = [180 + 150 * k for k in range(9)]
    terms = {}
    for k, (out, ina, inb) in enumerate(GATES):
        x, n = xc[k], k + 1
        s.text(x - 10, Y5 - 40, f"ячейка {n}", 12, MUTED, weight="bold")
        s.text(x - 10, Y5 - 22, f"{'N' + str(n) if out.startswith('N') else out} = И-НЕ({ina}, {inb})", 12, net_color(out), weight="bold")
        res_icon(s, x, Y5, 262, f"R{n}", "10 кОм")
        w.dot(x, Y5, "+5V")
        w.vline(x, 262, 296, out)
        w.dot(x, 272, out)
        w.hline(272, x - 52, x, out)
        terms.setdefault(out, []).append((x - 52, 272))
        fet_icon(s, x, 296, f"Q{2 * n - 1}")
        s.line(x, 346, x, 376, LEAD, 2.5)
        fet_icon(s, x, 376, f"Q{2 * n}")
        s.line(x, 426, x, YG, LEAD, 2.5)
        w.dot(x, YG, "GND")
        w.hline(321, x, x + 62, ina)
        terms.setdefault(ina, []).append((x + 62, 321))
        w.hline(401, x, x + 32, inb)
        terms.setdefault(inb, []).append((x + 32, 401))
    # J1 внизу; подбираем сдвиг, чтобы штырьки не совпали с вертикалями ячеек
    used = [x for t in terms.values() for x, _ in t]
    step = 46
    sx = max(range(560, 700), key=lambda a: min(abs(a + step * j - u) for j in range(1, 7) for u in used))
    jx = [sx + step * j for j in range(7)]
    for name, x in zip(J_NAMES[2:], jx[2:]):
        terms.setdefault(name, []).append((x, None))
    # высота канала нужна раньше J1: сначала считаем число дорожек
    tmp = Wires(s)
    _, nrows = tmp.channel({n: [(x, 0) for x, _ in t] for n, t in terms.items()}, 0, 20)
    y0 = YG + 40
    yj = y0 + nrows * 20 + 40
    nets = {n: [(x, yj if y is None else y) for x, y in t] for n, t in terms.items()}
    ys, _ = w.channel(nets, y0, 20)
    # питание J1: +5V налево и вверх к шине, GND прямо вверх к шине GND
    w.hline(yj, 40, jx[0], "+5V", 3.5)
    w.vline(40, Y5, yj, "+5V", 3.5)
    w.vline(jx[1], YG, yj, "GND", 3.5)
    w.dot(jx[1], YG, "GND")
    w.hline(Y5, 40, xc[-1] + 70, "+5V", 4)
    w.hline(YG, 60, xc[-1] + 70, "GND", 4)
    s.text(xc[-1] + 76, Y5 + 4, "+5V", 13, net_color("+5V"), anchor="start", weight="bold")
    s.text(xc[-1] + 76, YG + 4, "GND", 13, net_color("GND"), anchor="start", weight="bold")
    w.render()
    # подписи дорожек канала
    for name, y in ys.items():
        xs = [x for x, _ in nets[name]]
        s.text(min(xs) - 6, y + 4, name, 11, net_color(name), anchor="end", weight="bold", extra=HALO)
    header_icon(s, jx, yj)
    s.text(jx[0] - 14, yj - 16, "J1 (штыри PLS-7)", 12, INK, anchor="end", weight="bold", extra=HALO)
    for i, (name, x) in enumerate(zip(J_NAMES, jx)):
        s.text(x, yj + 26, str(i + 1), 11, MUTED, weight="bold")
        s.text(x, yj + 42, name, 11, net_color(name), weight="bold")
    s.text(jx[-1] + 30, yj - 2, "← сюда надевается гнездо PBS-7 кабеля", 12, anchor="start")
    s.text(jx[-1] + 30, yj + 14, "от платы ввода-вывода (схема 14)", 12, anchor="start")
    legend(s, 40, yj + 90)
    s.save("15_bit_board_full.svg")


# ---------------------------------------------------------------- 14: вся система

def system_full():
    W, H = 1580, 1290
    s = Svg(W, H)
    w = Wires(s)
    s.text(24, 34, "Вся схема целиком: питание, плата ввода-вывода, 4 кабеля, 4 платы разряда", 20, anchor="start", weight="bold")
    s.text(24, 58, "Сверху вниз: MB102 даёт 5 В → плата ввода-вывода (рычажки и светодиоды) → 4 кабеля по 7 проводов → "
           "4 одинаковые платы разряда. Что внутри платы разряда — схема 15.", 13, MUTED, anchor="start")
    Y5, YG = 230, 480
    # MB102
    mx, my = 40, 86
    s.add(f'<rect x="{mx}" y="{my}" width="190" height="78" rx="6" fill="#b71c1c" stroke="#7f0000" stroke-width="2"/>')
    s.text(mx + 12, my + 22, "MB102", 14, "#ffffff", anchor="start", weight="bold")
    s.text(mx + 12, my + 40, "перемычка на 5V", 11, "#ffffff", anchor="start", weight="bold")
    p5, pg = mx + 110, mx + 160
    for x, t in ((p5, "5V"), (pg, "GND")):
        s.add(f'<rect x="{x - 4}" y="{my + 70}" width="8" height="12" fill="#ffd54f"/>')
        s.text(x, my + 62, t, 11, "#ffffff", weight="bold")
    w.vline(p5, my + 82, Y5, "+5V", 4)
    w.vline(pg, my + 82, YG, "GND", 4)
    s.text(mx + 205, my + 50, "2 провода от штырьков 5V и GND модуля,", 12, INK, anchor="start")
    s.text(mx + 205, my + 66, "впаяны в A22 (+5V) и A24 (GND) платы ввода-вывода", 12, INK, anchor="start")
    # рамка платы ввода-вывода
    bx0, by0 = 90, 190
    xs_in = [360 + 62 * i for i in range(8)] + [360 + 62 * 8 + 18]
    names_in = SW1_LABELS + ["Cin"]
    xs_led = [965 + 100 * j for j in range(5)]
    cap_x = 120
    cap_icon(s, cap_x, Y5, YG)
    w.dot(cap_x, Y5, "+5V")
    w.dot(cap_x, YG, "GND")
    w.dot(p5, Y5, "+5V")
    w.dot(pg, YG, "GND")
    terms = {}
    for i, (x, name) in enumerate(zip(xs_in, names_in)):
        ref = f"SW1.{i + 1}" if i < 8 else "SW2.1"
        s.text(x, Y5 - 12, name, 12, net_color(name), weight="bold")
        sw_icon(s, x, Y5, 312, ref)
        w.dot(x, Y5, "+5V")
        w.vline(x, 312, 330, name)
        w.dot(x, 330, name)
        res_icon(s, x, 330, YG, f"R{i + 1}", "10 кОм", show_value=False)
        w.dot(x, YG, "GND")
        w.hline(330, x, x + 26, name)
        terms[name] = [(x + 26, 330)]
    for j, (x, name) in enumerate(zip(xs_led, LED_ORDER)):
        s.text(x, Y5 - 12, f"светодиод {name}", 12, net_color(name), weight="bold")
        res_icon(s, x, Y5, 300, f"R{10 + j}", "470 Ом")
        w.dot(x, Y5, "+5V")
        led_icon(s, x, 300, 362, f"HL{j + 1}", name)
        s.line(x, 362, x, 380, LEAD, 2.5)
        fet_icon(s, x, 380, f"Q{j + 1}")
        s.line(x, 430, x, YG, LEAD, 2.5)
        w.dot(x, YG, "GND")
        w.hline(405, x, x + 40, name)
        terms[name] = [(x + 40, 405)]
    w.hline(Y5, cap_x, xs_led[-1] + 60, "+5V", 4)
    w.hline(YG, cap_x, xs_led[-1] + 60, "GND", 4)
    s.text(276, YG - 34, "R1–R9 =", 11, MUTED, anchor="start", extra=HALO)
    s.text(276, YG - 20, "10 кОм", 11, MUTED, anchor="start", extra=HALO)
    s.text(xs_led[-1] + 66, Y5 + 4, "+5V", 13, net_color("+5V"), anchor="start", weight="bold")
    s.text(xs_led[-1] + 66, YG + 4, "GND", 13, net_color("GND"), anchor="start", weight="bold")
    # питание в кабели: отводы от шин
    terms["+5V"] = [(268, Y5)]
    terms["GND"] = [(284, YG)]
    w.dot(268, Y5, "+5V")
    w.dot(284, YG, "GND")
    # кабели: разряды слева направо 3, 2, 1, 0 (как светодиоды)
    used = [x for t in terms.values() for x, _ in t]
    step = 31
    cable = {}
    for m, bit in enumerate([3, 2, 1, 0]):
        base = 250 + 300 * m
        sx = max(range(base, base + 100), key=lambda a: min(abs(a + step * k - u) for k in range(7) for u in used))
        xs = [sx + step * k for k in range(7)]
        used += xs
        cable[bit] = xs
    def cnames(i):
        return ["+5V", "GND", f"A{i}", f"B{i}", "Cin" if i == 0 else f"C{i}", f"S{i}", "Cout" if i == 3 else f"C{i + 1}"]
    tmp = Wires(s)
    probe = {k: list(v) for k, v in terms.items()}
    for i, xs in cable.items():
        for x, n in zip(xs, cnames(i)):
            probe.setdefault(n, []).append((x, 0))
    _, nrows = tmp.channel({n: [(x, 0) for x, _ in t] for n, t in probe.items()}, 0, 18)
    y0 = YG + 40
    yx = y0 + nrows * 18 + 24          # точки пайки кабелей на плате ввода-вывода
    for i, xs in cable.items():
        for x, n in zip(xs, cnames(i)):
            terms.setdefault(n, []).append((x, yx))
    ys, _ = w.channel(terms, y0, 18)
    s.add(f'<rect x="{bx0}" y="{by0}" width="{xs_led[-1] + 110 - bx0}" height="{yx - by0 + 14}" rx="10" fill="none" '
          f'stroke="#43a047" stroke-width="2" stroke-dasharray="8 5"/>')
    s.text(xs_led[-1] + 110, by0 - 8, "ПЛАТА ВВОДА-ВЫВОДА", 13, "#2e7d32", anchor="end", weight="bold")
    # кабели вниз к платам разряда
    yb = yx + 170
    for i, xs in cable.items():
        for x, n in zip(xs, cnames(i)):
            w.vline(x, yx, yb, n, 2.2)
    w.render()
    for name, y in ys.items():
        xs = [x for x, _ in terms[name]]
        if max(xs) > min(xs):
            s.text(min(xs) - 5, y + 4, name, 10, net_color(name), anchor="end", weight="bold", extra=HALO)
    for i, xs in cable.items():
        for x in xs:
            s.add(f'<circle cx="{x}" cy="{yx}" r="3.5" fill="#ffd54f" stroke="#795548"/>')
        s.add(f'<rect x="{xs[0] - 12}" y="{yx + 30}" width="{xs[-1] - xs[0] + 24}" height="{yb - yx - 60}" rx="10" '
              f'fill="#90a4ae" fill-opacity=".25" stroke="#78909c"/>')
        s.text((xs[0] + xs[-1]) / 2, yx + 70, f"кабель X{i}", 13, INK, weight="bold", extra=HALO)
        s.text((xs[0] + xs[-1]) / 2, yx + 88, "7 проводов", 11, INK, extra=HALO)
        s.add(f'<rect x="{xs[0] - 13}" y="{yb - 30}" width="{xs[-1] - xs[0] + 26}" height="20" rx="2" fill="#424242"/>')
        s.text((xs[0] + xs[-1]) / 2, yb - 16, "гнездо PBS-7", 10, "#ffffff", weight="bold")
        bw = xs[-1] - xs[0] + 50
        bxx = (xs[0] + xs[-1]) / 2 - bw / 2
        s.add(f'<rect x="{bxx:.1f}" y="{yb - 6}" width="{bw:.1f}" height="150" rx="10" fill="#fff8e1" stroke="#f9a825" stroke-width="2"/>')
        header_icon(s, xs, yb + 6)
        for k, (x, n) in enumerate(zip(xs, cnames(i))):
            s.text(x, yb + 28, str(k + 1), 9, MUTED, weight="bold")
            s.text(x + 3, yb + 36, n, 9, net_color(n), anchor="start", weight="bold",
                   extra=f'transform="rotate(90 {x + 3} {yb + 36})"')
        s.text((xs[0] + xs[-1]) / 2, yb + 100, f"ПЛАТА РАЗРЯДА {i}", 13, "#e65100", weight="bold")
        s.text((xs[0] + xs[-1]) / 2, yb + 118, f"A{i} + B{i} + {cnames(i)[4]}", 11, INK)
        s.text((xs[0] + xs[-1]) / 2, yb + 134, f"→ S{i}, {cnames(i)[6]}  (схема 15)", 11, INK)
    for k, ln in enumerate(["жёлтые точки — сюда", "впаяны провода кабелей", "(X0…X3 на чертеже 07)"]):
        s.text(bx0 + 10, yx - 46 + 15 * k, ln, 11, INK, anchor="start", extra=HALO)
    s.text(24, yb + 175, "Перенос: провод C1 соединяет жилу 7 кабеля X0 (Cout разряда 0) с жилой 5 кабеля X1 (Cin разряда 1). "
           "Так же C2 и C3. Cout разряда 3 идёт на светодиод Cout.", 12, anchor="start")
    legend(s, 40, yb + 205)
    s.save("14_full_system.svg")


if __name__ == "__main__":
    system_full()
    bit_board_full()
    print("готово: 14_full_system.svg, 15_bit_board_full.svg")
