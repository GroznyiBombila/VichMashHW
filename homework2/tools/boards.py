"""Монтаж сумматора на макетных платах: раскладка, проверка, чертежи.

Запуск из папки homework2.0:  python tools/boards.py

1. Строит раскладку платы разряда и платы ввода-вывода: какая деталь в каком
   отверстии, где перемычки из припоя, шины и провода.
2. Извлекает из раскладки электрические цепи и прогоняет собранную систему
   (плата ввода-вывода + 4 платы разряда + 4 кабеля) по всем 512 положениям
   переключателей на уровне ключей. Если чертёж где-то ошибается, скрипт падает.
3. Рисует виды сверху и снизу в schematics/ и список монтажа в wiring.md.

Отверстие обозначается буквой ряда и номером столбца: F3 = ряд F, столбец 3.
Ряды A..X идут сверху вниз, столбцы 1..30 слева направо (вид сверху).
"""
import os
from itertools import product

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROWS = "ABCDEFGHIJKLMNOPQRSTUVWX"


def hn(p):
    return f"{ROWS[p[1] - 1]}{p[0]}"


# ---------------------------------------------------------------- раскладка

class Board:
    def __init__(self, key, title, cols=30, rows=24):
        self.key, self.title, self.cols, self.rows = key, title, cols, rows
        self.comps, self.rails, self.bridges, self.wires, self.notes = [], [], [], [], []
        self.holes = {}          # отверстие -> кто в нём (вывод детали или конец провода)

    def _take(self, p, who):
        c, r = p
        assert 1 <= c <= self.cols and 1 <= r <= self.rows, f"{self.key}: {who} вне платы: {p}"
        assert p not in self.holes, f"{self.key}: {hn(p)} уже занято ({self.holes[p]}), нужно для {who}"
        self.holes[p] = who

    def comp(self, ref, kind, value, pins, **kw):
        for n, p in pins.items():
            self._take(p, f"{ref}.{n}")
        d = dict(ref=ref, kind=kind, value=value, pins=pins, **kw)
        self.comps.append(d)
        return d

    def res(self, ref, value, c, r1, r2, **kw):
        return self.comp(ref, "R", value, {"1": (c, r1), "2": (c, r2)}, **kw)

    def fet(self, ref, c, r, **kw):
        """2N7000 стоя, выводы по столбцу: D сверху, G, S снизу.

        Цоколёвка: плоская сторона к себе, ножки вниз -> 1 S, 2 G, 3 D (слева направо).
        Чтобы D оказался сверху (ряд A), плоская сторона должна смотреть ВПРАВО,
        к столбцу 30. Если повернуть влево, сверху окажется S и схема не заработает.
        """
        return self.comp(ref, "Q", "2N7000", {"D": (c, r), "G": (c, r + 1), "S": (c, r + 2)}, **kw)

    def led(self, ref, c, r, **kw):
        return self.comp(ref, "LED", "LED", {"A": (c, r), "K": (c, r + 1)}, **kw)

    def cap(self, ref, value, plus, minus, **kw):
        return self.comp(ref, "C", value, {"+": plus, "-": minus}, **kw)

    def dip(self, ref, c0, r, labels, n=8):
        pins = {}
        for k in range(1, n + 1):
            pins[f"{k}"] = (c0 + k - 1, r)
            pins[f"{k}'"] = (c0 + k - 1, r + 3)
        return self.comp(ref, "SW", f"DIP-{n}", pins, labels=labels, n=n)

    def header(self, ref, pads, names, **kw):
        return self.comp(ref, "J", f"PLS-{len(pads)}",
                         {str(i + 1): p for i, p in enumerate(pads)}, names=names, **kw)

    def cable(self, ref, pads, names, **kw):
        return self.comp(ref, "X", "кабель", {str(i + 1): p for i, p in enumerate(pads)},
                         names=names, **kw)

    def rail(self, name, a, b):
        (c1, r1), (c2, r2) = a, b
        assert c1 == c2 or r1 == r2
        if r1 == r2:
            pads = [(c, r1) for c in range(min(c1, c2), max(c1, c2) + 1)]
        else:
            pads = [(c1, r) for r in range(min(r1, r2), max(r1, r2) + 1)]
        self.rails.append((name, pads))

    def bridge(self, p, q):
        assert abs(p[0] - q[0]) + abs(p[1] - q[1]) == 1, f"{self.key}: перемычка не между соседями {p} {q}"
        self.bridges.append((p, q))

    def wire(self, p, q, net):
        self._take(p, f"провод {net}")
        self._take(q, f"провод {net}")
        self.wires.append((p, q, net))

    def note(self, c, r, text, **kw):
        self.notes.append((c, r, text, kw))

    # ---- связность по меди
    def finder(self, wires=True):
        """Связность по меди; wires=False — без проводов сверху (только площадка с перемычками)."""
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            parent[find(a)] = find(b)

        for _, pads in self.rails:
            for a, b in zip(pads, pads[1:]):
                union(a, b)
        for p, q in self.bridges:
            union(p, q)
        if wires:
            for p, q, _ in self.wires:
                union(p, q)
        return find

    def pin(self, ref, name):
        return next(c for c in self.comps if c["ref"] == ref)["pins"][name]


GATES = [  # (выход, вход a -> верхний транзистор, вход b -> нижний)
    ("N1", "A", "B"), ("N2", "A", "N1"), ("N3", "B", "N1"), ("N4", "N2", "N3"),
    ("N5", "N4", "Cin"), ("N6", "N4", "N5"), ("N7", "Cin", "N5"),
    ("S", "N6", "N7"), ("Cout", "N1", "N5"),
]
J_NAMES = ["+5V", "GND", "A", "B", "Cin", "S", "Cout"]


def bit_board():
    b = Board("bit", "Плата разряда (одинаковая для разрядов 0–3)")
    b.rail("+5V", (1, 1), (29, 1))
    b.rail("GND", (1, 12), (29, 12))
    col = {}
    for k, (out, ina, inb) in enumerate(GATES):
        c = 3 + 3 * k
        col[out] = c
        n = k + 1
        b.res(f"R{n}", "10k", c, 1, 5)
        b.fet(f"Q{2 * n - 1}", c, 6)
        b.fet(f"Q{2 * n}", c, 9)
        b.bridge((c, 5), (c, 6))            # R -> сток верхнего = выход
        b.bridge((c, 8), (c, 9))            # исток верхнего -> сток нижнего
        b.bridge((c, 11), (c, 12))          # исток нижнего -> GND
        b.bridge((c - 1, 7), (c, 7))        # площадка входа a -> затвор верхнего
        b.bridge((c - 1, 10), (c, 10))      # площадка входа b -> затвор нижнего
        b.bridge((c + 1, 6), (c, 6))        # площадка выхода
        b.note(c, 0.25, f"N{n}" if out.startswith("N") else f"N{n}={out}", bold=True)
    fan = {}
    for out, ina, inb in GATES:
        for net in (ina, inb):
            fan[net] = fan.get(net, 0) + 1
    # дополнительные площадки выхода для разветвлений (до трёх нагрузок)
    out_pads = {}
    for out, c in col.items():
        k = fan.get(out, 1) if out not in ("S", "Cout") else 1
        pads = [(c + 1, 6), (c + 1, 5), (c + 1, 4)][:k]
        for p, q in zip(pads, pads[1:]):
            b.bridge(p, q)
        out_pads[out] = pads
    # разъём J1
    jx = {name: 12 + i for i, name in enumerate(J_NAMES)}
    b.header("J1", [(jx[n], 15) for n in J_NAMES], J_NAMES)
    src = {}
    for name in J_NAMES:
        x = jx[name]
        b.bridge((x, 15), (x, 14))
        src[name] = [(x, 14)]
        if name in ("A", "B", "Cin"):
            b.bridge((x, 15), (x, 16))
            src[name].append((x, 16))
    b.wire(src["+5V"][0], (10, 1), "+5V")
    b.wire(src["GND"][0], (13, 12), "GND")
    for out, pads in out_pads.items():
        src[out] = list(pads)
    # провода: источник -> площадки входов, по порядку вентилей
    for out, ina, inb in GATES:
        c = col[out]
        for net, pad in ((ina, (c - 1, 7)), (inb, (c - 1, 10))):
            b.wire(src[net].pop(0), pad, net)
    b.wire(src["S"].pop(0), (jx["S"], 14), "S")
    b.wire(src["Cout"].pop(0), (jx["Cout"], 14), "Cout")
    assert all(not v for k, v in src.items() if k not in ("+5V", "GND")), src
    b.gate_out = {out: (c, 6) for out, c in col.items()}
    b.note(15, 18.6, "J1 — штыри PLS-7, сюда надевается кабель с платы ввода-вывода", small=True)
    return b


LED_ORDER = ["Cout", "S3", "S2", "S1", "S0"]
SW1_LABELS = ["A3", "A2", "A1", "A0", "B3", "B2", "B1", "B0"]
CABLE_ROW = {0: 11, 1: 14, 2: 17, 3: 20}


def io_board():
    b = Board("io", "Плата ввода-вывода")
    # питание: вертикальные шины +5 В (столбец 22) и GND (столбец 24)
    b.header("J1", [(22, 1), (23, 1), (24, 1)], ["+5V", "—", "GND"])
    b.rail("+5V", (22, 1), (22, 20))
    b.rail("GND", (24, 1), (24, 24))
    b.cap("C1", "470 мкФ", (22, 7), (24, 7))
    # ввод: DIP -> узел -> 10 кОм на GND
    b.rail("+5V", (1, 3), (22, 3))
    b.rail("GND", (1, 12), (20, 12))
    b.dip("SW1", 2, 3, SW1_LABELS)
    b.dip("SW2", 12, 3, ["Cin"], n=1)
    in_cols = {name: 2 + i for i, name in enumerate(SW1_LABELS)}
    in_cols["Cin"] = 12
    for i, (name, c) in enumerate(in_cols.items()):
        b.bridge((c, 6), (c, 7))
        b.bridge((c, 7), (c, 8))
        b.res(f"R{i + 1}", "10k", c, 8, 12, label=False)
    b.wire((20, 12), (24, 12), "GND")
    # вывод: +5 В -> 470 Ом -> светодиод -> 2N7000 -> GND
    b.rail("+5V", (1, 14), (22, 14))
    b.rail("GND", (1, 24), (24, 24))
    led_gate = {}
    for i, name in enumerate(LED_ORDER):
        c = 3 + 4 * i
        b.res(f"R{10 + i}", "470", c, 14, 18)
        b.bridge((c, 18), (c, 19))
        b.led(f"HL{i + 1}", c, 19, net=name)
        b.bridge((c, 20), (c, 21))
        b.fet(f"Q{i + 1}", c, 21)
        b.bridge((c, 23), (c, 24))
        b.bridge((c - 1, 22), (c, 22))
        led_gate[name] = (c - 1, 22)
        b.note(c, 25.2, name, bold=True)
    # кабели к платам разрядов: 1 +5V, 2 GND, 3 A, 4 B, 5 Cin, 6 S, 7 Cout
    xs = [22, 24, 25, 26, 27, 28, 29]
    for i, r in CABLE_ROW.items():
        cin = "Cin" if i == 0 else f"C{i}"
        cout = "Cout" if i == 3 else f"C{i + 1}"
        b.cable(f"X{i}", [(x, r) for x in xs],
                ["+5V", "GND", f"A{i}", f"B{i}", cin, f"S{i}", cout], bit=i)
        for x in xs[2:]:            # в отверстии кабеля уже провод, рядом площадка
            b.bridge((x, r), (x, r + 1))
    pad = lambda i, k: (xs[k - 1], CABLE_ROW[i] + 1)
    for i in range(4):
        b.wire((in_cols[f"A{i}"], 7), pad(i, 3), f"A{i}")
        b.wire((in_cols[f"B{i}"], 7), pad(i, 4), f"B{i}")
        b.wire(pad(i, 6), led_gate[f"S{i}"], f"S{i}")
    b.wire((in_cols["Cin"], 7), pad(0, 5), "Cin")
    for i in range(3):
        b.wire(pad(i, 7), pad(i + 1, 5), f"C{i + 1}")
    b.wire(pad(3, 7), led_gate["Cout"], "Cout")
    b.note(6.5, 13.2, "R1–R9 = 10 кОм (стяжки входов)", small=True)
    return b


# ------------------------------------------------------------ проверка схемы

class System:
    """Плата ввода-вывода + 4 платы разряда, соединённые кабелями."""

    def __init__(self, io, bit):
        self.io, self.bit = io, bit
        self.insts = [("io", io)] + [(f"bit{i}", bit) for i in range(4)]
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        self.find = find
        finders = {name: brd.finder() for name, brd in self.insts}
        self.node = lambda inst, pad: find((inst, finders[inst](pad)))
        for i in range(4):   # кабель: X_i.k <-> J1.k платы разряда i
            for k in range(1, 8):
                a = self.node("io", io.pin(f"X{i}", str(k)))
                bb = self.node(f"bit{i}", bit.pin("J1", str(k)))
                parent[a] = bb
        self.VCC = self.node("io", io.pin("J1", "1"))
        self.GND = self.node("io", io.pin("J1", "3"))
        self.fets, self.res, self.sw, self.leds = [], [], [], []
        for inst, brd in self.insts:
            for c in brd.comps:
                P = {n: self.node(inst, p) for n, p in c["pins"].items()}
                if c["kind"] == "Q":
                    self.fets.append((f"{inst}.{c['ref']}", P["G"], P["D"], P["S"]))
                elif c["kind"] == "R":
                    self.res.append((P["1"], P["2"]))
                elif c["kind"] == "SW":
                    for k in range(1, c["n"] + 1):
                        lab = c["labels"][k - 1]
                        self.sw.append((lab, P[str(k)], P[f"{k}'"]))
                elif c["kind"] == "LED":
                    self.leds.append((c["net"], P["A"], P["K"]))

    def solve(self, on):
        g = {f[1]: 0 for f in self.fets}
        for _ in range(60):
            parent = {}

            def find(x):
                parent.setdefault(x, x)
                while parent[x] != x:
                    x = parent[x]
                return x

            for lab, a, b in self.sw:
                if lab and on.get(lab):
                    parent[find(a)] = find(b)
            for _, gate, d, s in self.fets:
                if g[gate]:
                    parent[find(d)] = find(s)
            vcc, gnd = find(self.VCC), find(self.GND)
            assert vcc != gnd, f"КЗ питания при {on}"

            def level(n):
                x = find(n)
                if x == vcc:
                    return 1
                if x == gnd:
                    return 0
                up = down = False
                for a, b in self.res:
                    for p, q in ((a, b), (b, a)):
                        if find(p) == x:
                            up |= find(q) == vcc
                            down |= find(q) == gnd
                assert not (up and down), f"резисторы тянут узел в обе стороны при {on}"
                return 1 if up else 0 if down else None

            new = {}
            for name, gate, d, s in self.fets:
                v = level(gate)
                assert v is not None, f"затвор {name} висит в воздухе при {on}"
                new[gate] = v
            if new == g:
                lit = {net: level(a) == 1 and find(k) == gnd for net, a, k in self.leds}
                return level, lit
            g = new
        raise AssertionError("схема не успокаивается")


def check(io, bit):
    for brd in (io, bit):
        # под лежачим резистором отверстия должны быть свободны
        for c in brd.comps:
            if c["kind"] == "R":
                (x, r1), (_, r2) = c["pins"]["1"], c["pins"]["2"]
                for r in range(r1 + 1, r2):
                    assert (x, r) not in brd.holes, f"{brd.key}: под {c['ref']} занято {hn((x, r))}"
        # каждый вывод должен быть с чем-то соединён
        find = brd.finder()
        count = {}
        for p in brd.holes:
            count[find(p)] = count.get(find(p), 0) + 1
        for c in brd.comps:
            for n, p in c["pins"].items():
                spare = c["kind"] == "SW" and not c["labels"][int(n.rstrip("'")) - 1]
                if not spare and c["kind"] != "X" and not (c["ref"] == "J1" and n == "2" and brd.key == "io"):
                    assert count[find(p)] > 1, f"{brd.key}: {c['ref']}.{n} ({hn(p)}) ни к чему не подключён"
    # исток каждого нижнего ключа на земле, сток верхнего на выходе вентиля
    fb = bit.finder()
    for k, (out, _, _) in enumerate(GATES):
        assert fb(bit.pin(f"Q{2 * k + 2}", "S")) == fb((1, 12))
        assert fb(bit.pin(f"Q{2 * k + 1}", "D")) == fb(bit.gate_out[out])
    sysm = System(io, bit)
    n = 0
    for a, bb, cin in product(range(16), range(16), range(2)):
        on = {f"A{i}": (a >> i) & 1 for i in range(4)}
        on.update({f"B{i}": (bb >> i) & 1 for i in range(4)})
        on["Cin"] = cin
        level, lit = sysm.solve(on)
        got = sum(lit[f"S{i}"] << i for i in range(4)) + (lit["Cout"] << 4)
        assert got == a + bb + cin, f"{a}+{bb}+{cin}: светодиоды показывают {got}"
        carry = cin
        for i in range(4):   # внутренние узлы каждого разряда против таблицы
            A, B, C = (a >> i) & 1, (bb >> i) & 1, carry
            n1 = 1 - (A & B); n2 = 1 - (A & n1); n3 = 1 - (B & n1); n4 = 1 - (n2 & n3)
            n5 = 1 - (n4 & C); n6 = 1 - (n4 & n5); n7 = 1 - (C & n5)
            want = [n1, n2, n3, n4, n5, n6, n7]
            got_n = [level(sysm.node(f"bit{i}", bit.gate_out[f"N{k}"])) for k in range(1, 8)]
            assert want == got_n, f"разряд {i}, A={A} B={B} C={C}: {got_n} вместо {want}"
            carry = (A + B + C) >> 1
        n += 1
    return n


# ---------------------------------------------------------------- рисование

NET_COLOR = {"+5V": "#d32f2f", "GND": "#263238", "A": "#1565c0", "B": "#2e7d32",
             "C": "#ef6c00", "Cin": "#ef6c00", "Cout": "#ef6c00", "S": "#8e24aa",
             "N1": "#00897b", "N2": "#6d4c41", "N3": "#c2185b", "N4": "#0288d1",
             "N5": "#9e9d24", "N6": "#5e35b1", "N7": "#546e7a"}
BANDS = {"10k": ["#6d4c41", "#212121", "#f57c00", "#c9a227"],
         "470": ["#fbc02d", "#7b1fa2", "#6d4c41", "#c9a227"]}


def net_color(net):
    if net in NET_COLOR:
        return NET_COLOR[net]
    return NET_COLOR.get(net.rstrip("0123456789"), "#455a64")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(b, side):
    P, ML, MT = 26, 56, 92
    W = 2 * ML + (b.cols + 1) * P + (70 if b.key == "io" else 0)
    H = MT + (b.rows + 1) * P + 60
    X = (lambda c: ML + c * P) if side == "top" else (lambda c: ML + (b.cols + 1 - c) * P + (70 if b.key == "io" else 0))
    Y = lambda r: MT + r * P
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="Segoe UI, Arial, sans-serif">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    t = lambda x, y, s, size=11, fill="#263238", anchor="middle", weight="normal", extra="": o.append(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
        f'font-weight="{weight}" {extra}>{esc(s)}</text>')
    head = "вид сверху, сторона деталей" if side == "top" else "вид снизу, сторона пайки (зеркально!)"
    t(ML, 30, f"{b.title}: {head}", 18, anchor="start", weight="bold")
    sub = ("Детали и изолированные провода ставятся сверху. Цвет провода нужен только чтобы различать цепи."
           if side == "top" else
           "Толстые линии — голый лужёный провод (шины). Короткие перемычки — ножка, загнутая на соседнюю площадку и пропаянная.")
    t(ML, 52, sub, 12, "#546e7a", anchor="start")
    x0, x1 = sorted((X(1), X(b.cols)))
    o.append(f'<rect x="{x0 - 0.75 * P}" y="{Y(1) - 0.75 * P}" width="{x1 - x0 + 1.5 * P}" '
             f'height="{(b.rows - 1 + 1.5) * P}" rx="8" fill="#2e7d4f" stroke="#1b5e20" stroke-width="2"/>')
    for c in range(1, b.cols + 1):
        t(X(c), Y(1) - 0.95 * P, str(c), 9, "#607d8b")
        t(X(c), Y(b.rows) + 1.3 * P, str(c), 9, "#607d8b")
    for r in range(1, b.rows + 1):
        t(x0 - 1.15 * P, Y(r) + 3.5, ROWS[r - 1], 10, "#607d8b", weight="bold")
        t(x1 + 1.15 * P, Y(r) + 3.5, ROWS[r - 1], 10, "#607d8b", weight="bold")
    for c in range(1, b.cols + 1):
        for r in range(1, b.rows + 1):
            o.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.31 * P:.1f}" fill="#d9a441" stroke="#9c6f1e" stroke-width="1"/>'
                     f'<circle cx="{X(c)}" cy="{Y(r)}" r="{0.11 * P:.1f}" fill="#123524"/>')
    if side == "bottom":
        render_bottom(b, o, X, Y, P, t)
    else:
        render_top(b, o, X, Y, P, t)
    for c, r, text, kw in b.notes:
        if side == "top" or kw.get("bold"):
            size = 10 if kw.get("small") else 12
            yy = Y(r) if r >= 1 else Y(1) - 1.75 * P + 4
            if r > b.rows:
                yy = Y(b.rows) + 2.2 * P
            t(X(c), yy, text, size, "#263238" if not kw.get("small") else "#e8f5e9" if 1 <= r <= b.rows else "#455a64",
              weight="bold" if kw.get("bold") else "normal")
    o.append("</svg>")
    return "\n".join(o)


def render_bottom(b, o, X, Y, P, t):
    for name, pads in b.rails:
        pts = " ".join(f"{X(c)},{Y(r)}" for c, r in (pads[0], pads[-1]))
        o.append(f'<polyline points="{pts}" fill="none" stroke="#5f6a73" stroke-width="{0.46 * P:.1f}" stroke-linecap="round"/>'
                 f'<polyline points="{pts}" fill="none" stroke="#cfd8dc" stroke-width="{0.3 * P:.1f}" stroke-linecap="round"/>')
    for p, q in b.bridges:
        o.append(f'<line x1="{X(p[0])}" y1="{Y(p[1])}" x2="{X(q[0])}" y2="{Y(q[1])}" stroke="#5f6a73" '
                 f'stroke-width="{0.5 * P:.1f}" stroke-linecap="round"/>'
                 f'<line x1="{X(p[0])}" y1="{Y(p[1])}" x2="{X(q[0])}" y2="{Y(q[1])}" stroke="#eceff1" '
                 f'stroke-width="{0.34 * P:.1f}" stroke-linecap="round"/>')
    for c in b.comps:
        for n, (x, y) in c["pins"].items():
            lab = {"Q": n, "LED": n, "C": "+" if n == "+" else "−"}.get(c["kind"], "")
            o.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{0.2 * P:.1f}" fill="#37474f"/>')
            if lab:
                t(X(x), Y(y) + 3.5, lab, 9, "#ffffff", weight="bold")
    for p, q, net in b.wires:
        for x, y in (p, q):
            o.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{0.26 * P:.1f}" fill="none" stroke="{net_color(net)}" stroke-width="3"/>')
    for name, pads in b.rails:
        c, r = pads[0]
        horiz = pads[0][1] == pads[-1][1]
        lx = X(c) + (-1.9 * P if horiz and X(pads[-1][0]) > X(c) else 1.9 * P if horiz else 0)
        ly = Y(r) + (4 if horiz else -0.9 * P)
        tag(o, lx, ly, name, net_color(name))
    # подписи деталей
    for c in b.comps:
        if c["kind"] in ("Q", "LED", "C"):
            xs = [X(p[0]) for p in c["pins"].values()]
            ys = [Y(p[1]) for p in c["pins"].values()]
            t(max(xs) + 0.55 * P if c["kind"] != "C" else sum(xs) / len(xs),
              sum(ys) / len(ys) + (4 if c["kind"] != "C" else 0.95 * P), c["ref"], 9, "#ffffff",
              anchor="start" if c["kind"] != "C" else "middle")


def tag(o, x, y, text, color):
    w = 7 * len(text) + 8
    o.append(f'<rect x="{x - w / 2:.1f}" y="{y - 11:.1f}" width="{w}" height="15" rx="3" fill="{color}"/>'
             f'<text x="{x:.1f}" y="{y:.1f}" font-size="11" fill="#fff" text-anchor="middle" font-weight="bold">{esc(text)}</text>')


def render_top(b, o, X, Y, P, t):
    for c in b.comps:
        k = c["kind"]
        pins = c["pins"]
        if k == "R":
            (x, r1), (_, r2) = pins["1"], pins["2"]
            cx, ya, yb = X(x), Y(r1), Y(r2)
            o.append(f'<line x1="{cx}" y1="{ya}" x2="{cx}" y2="{yb}" stroke="#b0bec5" stroke-width="2.4"/>')
            bt, bb = ya + 0.55 * P, yb - 0.55 * P
            o.append(f'<rect x="{cx - 0.33 * P:.1f}" y="{bt:.1f}" width="{0.66 * P:.1f}" height="{bb - bt:.1f}" rx="6" '
                     f'fill="#e9d3a4" stroke="#8d6e63" stroke-width="1.2"/>')
            for i, col in enumerate(BANDS[c["value"]]):
                yy = bt + (bb - bt) * (0.18 + 0.19 * i + (0.08 if i == 3 else 0))
                o.append(f'<rect x="{cx - 0.33 * P:.1f}" y="{yy:.1f}" width="{0.66 * P:.1f}" height="4" fill="{col}"/>')
            if c.get("label", True):
                my = (ya + yb) / 2
                t(cx + 0.62 * P, my, f"{c['ref']} {c['value'].replace('k', 'к')}", 10, "#ffffff", anchor="middle",
                  extra=f'transform="rotate(-90 {cx + 0.62 * P:.1f} {my:.1f})"')
        elif k == "Q":
            cx = X(pins["G"][0])
            yg = Y(pins["G"][1])
            fx = cx + 0.42 * P          # плоская сторона справа, круглая спинка слева
            y1, y2 = yg - 1.02 * P, yg + 1.02 * P
            o.append(f'<path d="M{fx:.1f},{y1:.1f} C{fx - 1.75 * P:.1f},{y1:.1f} {fx - 1.75 * P:.1f},{y2:.1f} {fx:.1f},{y2:.1f} Z" '
                     f'fill="#37474f" fill-opacity=".8" stroke="#101418" stroke-width="1.2"/>'
                     f'<line x1="{fx:.1f}" y1="{y1:.1f}" x2="{fx:.1f}" y2="{y2:.1f}" stroke="#cfd8dc" stroke-width="2.5"/>')
            for n, (x, y) in pins.items():
                o.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="3" fill="#d9a441"/>')
                t(X(x) - 0.36 * P, Y(y) + 4, n, 9, "#ffffff", weight="bold")
            ys = Y(pins["S"][1])
            t(cx - 0.3 * P, ys + 0.66 * P, c["ref"], 9, "#ffffff", weight="bold")
        elif k == "LED":
            (x, ra), (_, rk) = pins["A"], pins["K"]
            cx, cy = X(x), (Y(ra) + Y(rk)) / 2
            o.append(f'<circle cx="{cx}" cy="{cy}" r="{1.12 * P:.1f}" fill="#ef5350" fill-opacity=".75" stroke="#b71c1c" stroke-width="1.5"/>'
                     f'<line x1="{cx - 0.9 * P:.1f}" y1="{cy + 0.72 * P:.1f}" x2="{cx + 0.9 * P:.1f}" y2="{cy + 0.72 * P:.1f}" stroke="#b71c1c" stroke-width="2"/>')
            for n, (px, py) in pins.items():
                o.append(f'<circle cx="{X(px)}" cy="{Y(py)}" r="3" fill="#d9a441"/>')
            t(cx - 0.62 * P, Y(ra) + 4, "+", 13, "#ffffff", weight="bold")
            t(cx + 1.3 * P, cy + 4, c["ref"], 10, "#ffffff", anchor="start", weight="bold")
        elif k == "C":
            (xp, yp), (xm, ym) = pins["+"], pins["-"]
            cx, cy = (X(xp) + X(xm)) / 2, (Y(yp) + Y(ym)) / 2
            R = 1.55 * P
            o.append(f'<circle cx="{cx}" cy="{cy}" r="{R:.1f}" fill="#1f3c88" stroke="#0d1b45" stroke-width="1.5"/>')
            sx = 1 if X(xm) > X(xp) else -1
            o.append(f'<path d="M{cx + sx * 0.55 * R:.1f},{cy - 0.83 * R:.1f} A{R:.1f},{R:.1f} 0 0 {1 if sx > 0 else 0} '
                     f'{cx + sx * 0.55 * R:.1f},{cy + 0.83 * R:.1f} Z" fill="#b0bec5"/>')
            t(cx + sx * 0.78 * R, cy + 5, "−", 16, "#0d1b45", weight="bold")
            t(cx - sx * 0.55 * R, cy - 0.3 * R, "+", 16, "#ffffff", weight="bold")
            for n, (px, py) in pins.items():
                o.append(f'<circle cx="{X(px)}" cy="{Y(py)}" r="3" fill="#d9a441"/>')
            t(cx, cy + R + 13, f"{c['ref']} {c['value']}", 10, "#ffffff", weight="bold")
        elif k == "SW":
            n = c["n"]
            c0, r = pins["1"]
            xa, xb = X(c0) - 0.62 * P, X(c0 + n - 1) + 0.62 * P
            o.append(f'<rect x="{xa:.1f}" y="{Y(r) - 0.5 * P:.1f}" width="{xb - xa:.1f}" height="{3.9 * P:.1f}" rx="3" '
                     f'fill="#1e63b5" stroke="#0d3c73" stroke-width="1.5"/>')
            for k2 in range(1, n + 1):
                x = X(c0 + k2 - 1)
                o.append(f'<rect x="{x - 0.26 * P:.1f}" y="{Y(r) + 0.55 * P:.1f}" width="{0.52 * P:.1f}" height="{1.9 * P:.1f}" fill="#f5f5f5"/>'
                         f'<rect x="{x - 0.22 * P:.1f}" y="{Y(r) + 1.5 * P:.1f}" width="{0.44 * P:.1f}" height="{0.9 * P:.1f}" fill="#9e9e9e"/>')
                t(x, Y(r) + 3.25 * P, str(k2), 9, "#ffffff")
                lab = c["labels"][k2 - 1]
                if lab:
                    tag(o, x, Y(r) - 0.95 * P, lab, net_color(lab))
            for (px, py) in pins.values():
                o.append(f'<circle cx="{X(px)}" cy="{Y(py)}" r="3" fill="#d9a441"/>')
            if n > 1:
                t(xb - 4, Y(r) + 0.35 * P, "ON = 1", 9, "#ffffff", anchor="end", weight="bold")
                t(xa + 4, Y(r) + 0.35 * P, c["ref"] + ": числа A и B", 9, "#ffffff", anchor="start", weight="bold")
            else:
                t(xb + 4, Y(r) + 1.2 * P, f"{c['ref']} (DIP-1)", 9, "#ffffff", anchor="start", weight="bold")
                t(xb + 4, Y(r) + 1.9 * P, "ON = 1", 9, "#ffffff", anchor="start", weight="bold")
        elif k == "J":
            pts = list(pins.values())
            xs = [X(p[0]) for p in pts]
            y = Y(pts[0][1])
            o.append(f'<rect x="{min(xs) - 0.5 * P:.1f}" y="{y - 0.5 * P:.1f}" width="{max(xs) - min(xs) + P:.1f}" '
                     f'height="{P}" fill="#212121" rx="2"/>')
            for i, (px, py) in enumerate(pts):
                o.append(f'<rect x="{X(px) - 4}" y="{Y(py) - 4}" width="8" height="8" fill="#ffd54f"/>')
            t(min(xs) - 0.7 * P, y + 4, c["ref"], 10, "#ffffff", anchor="end", weight="bold")
            for (px, py), name in zip(pts, c["names"]):
                ly = Y(py) + (2.35 * P if b.key == "bit" else -0.72 * P) if not (b.key == "io") else Y(py) + 1.15 * P
                if name != "—":
                    t(X(px), ly, name, 9, "#ffffff", weight="bold")
        elif k == "X":
            pts = list(pins.values())
            y = Y(pts[0][1])
            o.append(f'<path d="M{X(pts[-1][0]) + 0.3 * P:.1f},{y:.1f} L{X(b.cols) + 1.6 * P:.1f},{y:.1f}" '
                     f'stroke="#90a4ae" stroke-width="7" stroke-linecap="round"/>')
            t(X(b.cols) + 1.75 * P, y - 7, f"кабель", 9, "#455a64", anchor="start")
            t(X(b.cols) + 1.75 * P, y + 6, f"→ разряд {c['bit']}", 9, "#455a64", anchor="start", weight="bold")
            for (px, py), name in zip(pts, c["names"]):
                o.append(f'<circle cx="{X(px)}" cy="{Y(py)}" r="5.5" fill="#90a4ae" stroke="#37474f" stroke-width="1.5"/>')
                t(X(px), Y(py) - 0.55 * P, name, 8.5, "#ffffff", weight="bold")
    # провода поверх деталей
    for i, (p, q, net) in enumerate(b.wires):
        xa, ya, xb, yb = X(p[0]), Y(p[1]), X(q[0]), Y(q[1])
        dx, dy = xb - xa, yb - ya
        L = max((dx * dx + dy * dy) ** 0.5, 1)
        k = min(0.16 * L, 34) * (1 if i % 2 else -1)
        cx, cy = (xa + xb) / 2 - dy / L * k, (ya + yb) / 2 + dx / L * k
        col = net_color(net)
        d = f"M{xa:.1f},{ya:.1f} Q{cx:.1f},{cy:.1f} {xb:.1f},{yb:.1f}"
        o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="6.5" stroke-linecap="round"/>'
                 f'<path d="{d}" fill="none" stroke="{col}" stroke-width="4" stroke-linecap="round"/>')
        for x, y in ((xa, ya), (xb, yb)):
            o.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
        mx, my = (xa + 2 * cx + xb) / 4, (ya + 2 * cy + yb) / 4
        if L > 2.2 * P:
            tag(o, mx, my + 4, net, col)


# ---------------------------------------------------------------- список монтажа

def wiring_md(boards):
    L = ["# Список монтажа", "",
         "Сгенерировано скриптом `tools/boards.py` из тех же данных, что и чертежи, и проверено",
         "моделированием всей собранной системы. Отверстие = буква ряда + номер столбца (вид сверху):",
         "`F3` — ряд F, столбец 3. Отмечайте галочками по ходу пайки.", ""]
    for b in boards:
        L += [f"## {b.title}", "", "### Детали", ""]
        for c in b.comps:
            if c["kind"] == "X":
                continue
            pins = ", ".join(f"{n}={hn(p)}" for n, p in c["pins"].items()
                             if c["kind"] != "SW" or "'" not in n and int(n) <= 1 or n in ("1", "1'", "8", "8'"))
            if c["kind"] == "SW":
                pins = f"выводы {hn(c['pins']['1'])} и {hn(c['pins'][chr(49) + chr(39)])}" if c["n"] == 1 else f"верхний ряд выводов {hn(c['pins']['1'])}…{hn(c['pins'][str(c['n'])])}, нижний {hn(c['pins'][chr(49) + chr(39)])}…{hn(c['pins'][str(c['n']) + chr(39)])}"
            extra = {"Q": " (плоская сторона ВПРАВО, к столбцу 30; D сверху)", "LED": " (длинная ножка, анод, в A)",
                     "C": " (полоса «−» на корпусе к GND)"}.get(c["kind"], "")
            L.append(f"- [ ] **{c['ref']}** {c['value']}: {pins}{extra}")
        L += ["", "### Шины (голый лужёный провод снизу; припаять к каждому выводу детали, который на него попадает, и по концам)", ""]
        for name, pads in b.rails:
            L.append(f"- [ ] {name}: {hn(pads[0])} → {hn(pads[-1])}")
        L += ["", f"### Соединения соседних отверстий снизу ({len(b.bridges)} шт.): загнуть ножку на соседнюю площадку и спаять", ""]
        line = []
        for p, q in b.bridges:
            line.append(f"{hn(p)}–{hn(q)}")
        for i in range(0, len(line), 8):
            L.append("- [ ] " + ", ".join(line[i:i + 8]))
        L += ["", f"### Провода сверху ({len(b.wires)} шт.)", "", "| # | цепь | откуда | куда |", "|---|---|---|---|"]
        for i, (p, q, net) in enumerate(b.wires, 1):
            L.append(f"| {i} | {net} | {hn(p)} | {hn(q)} |")
        cables = [c for c in b.comps if c["kind"] == "X"]
        if cables:
            L += ["", "### Кабели к платам разрядов", "",
                  "Каждый кабель — 7 проводов длиной 15–20 см. Один конец впаивается в плату ввода-вывода,",
                  "на другой напаивается гнездо PBS-7 (контакт 1 = +5V), которое надевается на J1 платы разряда.", "",
                  "| кабель | 1 | 2 | 3 | 4 | 5 | 6 | 7 |", "|---|---|---|---|---|---|---|---|"]
            for c in cables:
                cells = [f"{name} ({hn(p)})" for name, p in zip(c["names"], c["pins"].values())]
                L.append(f"| X{c['bit']} → разряд {c['bit']} | " + " | ".join(cells) + " |")
        L.append("")
    return "\n".join(L)


def main():
    io, bit = io_board(), bit_board()
    n = check(io, bit)
    out = os.path.join(ROOT, "schematics")
    for b, num in ((bit, 5), (io, 7)):
        for side, add in (("top", 0), ("bottom", 1)):
            name = f"{num + add:02d}_{b.key}_board_{side}.svg"
            with open(os.path.join(out, name), "w", encoding="utf-8") as f:
                f.write(render(b, side))
    with open(os.path.join(ROOT, "wiring.md"), "w", encoding="utf-8") as f:
        f.write(wiring_md([bit, io]))
    print(f"проверено комбинаций: {n}, все светодиоды и узлы N1–N7 совпали")
    for b in (bit, io):
        print(f"{b.key}: деталей {len([c for c in b.comps if c['kind'] != 'X'])}, "
              f"перемычек {len(b.bridges)}, проводов {len(b.wires)}")


if __name__ == "__main__":
    main()
