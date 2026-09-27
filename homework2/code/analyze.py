"""
Разбор вывода bench.ino и графики для слайдов.
Вход:  Results/raw_exploreit.txt  (вывод монитора порта со всех трёх плат)
Выход: Results/summary.csv и три картинки Results/chart_*.png
"""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
RAW = HERE.parent / "Results" / "raw_exploreit.txt"
OUT = HERE.parent / "Results"

# цвета: фиксированный порядок категорий, проверен на различимость при дальтонизме
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e6e5e0", "#fcfcfb"

# ---------- разбор: каждый прогон начинается со строки "# плата" ----------
runs = []
for line in RAW.read_text(encoding="utf-8").splitlines():
    if line.startswith("# плата"):
        runs.append([])
    elif runs and line.count(";") == 4 and not line.startswith("плата"):
        board, test, ops, us, cyc = line.split(";")
        runs[-1].append((board, test, int(ops), int(us), float(cyc)))

# плата определяется по имени и наличию строк PSRAM
def board_of(run):
    if run[0][0] == "nano":
        return "nano"
    return "esp32cam" if any("psram" in r[1] for r in run) else "yotik"

# среднее по прогонам каждой платы: data[плата][тест] = (время_мкс, тактов)
acc = defaultdict(lambda: defaultdict(list))
for run in runs:
    b = board_of(run)
    for _, test, ops, us, cyc in run:
        acc[b][test].append((us, cyc))
data = {b: {t: (sum(v[0] for v in vals) / len(vals), sum(v[1] for v in vals) / len(vals))
            for t, vals in tests.items()} for b, tests in acc.items()}

print("прогонов:", {b: sum(1 for r in runs if board_of(r) == b) for b in data})

with open(OUT / "summary.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["тест", "nano_мкс", "nano_тактов", "yotik_мкс", "yotik_тактов",
                "esp32cam_мкс", "esp32cam_тактов"])
    all_tests = list(dict.fromkeys(t for b in ("nano", "yotik", "esp32cam") for t in data[b]))
    for t in all_tests:
        row = [t]
        for b in ("nano", "yotik", "esp32cam"):
            us, cyc = data[b].get(t, ("", ""))
            row += [round(us) if us != "" else "", round(cyc, 2) if cyc != "" else ""]
        w.writerow(row)


def style(ax, title):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=11)
    ax.set_title(title, loc="left", color=INK, fontsize=14, fontweight="bold", pad=14)


# ---------- график 1: во сколько раз ESP32 быстрее Nano ----------
labels = {
    "op_add8": "сложение 8 бит", "op_add32": "сложение 32 бита",
    "op_mul32": "умножение 32 бита", "op_divf": "деление float",
    "mandel_fixed": "Мандельброт, целые", "op_addf": "сложение float",
    "op_mulf": "умножение float", "mandel_float": "Мандельброт, float",
    "op_div32": "деление 32 бита",
}
ratios = sorted(((data["nano"][t][0] / data["esp32cam"][t][0], labels[t]) for t in labels))
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
y = range(len(ratios))
ax.barh(list(y), [r for r, _ in ratios], color=BLUE, height=0.62)
ax.set_xscale("log")
ax.set_yticks(list(y), [n for _, n in ratios])
ax.axvline(15, color=ORANGE, lw=2, ls="--")
ax.text(15 * 1.06, -0.95, "разница частот: 15 раз", color=INK2, fontsize=11, va="center")
ax.set_ylim(-1.4, len(ratios) - 0.5)
for i, (r, _) in enumerate(ratios):
    ax.text(r * 1.07, i, f"{r:.0f}×", va="center", color=INK, fontsize=11)
ax.set_xlim(8, 1500)
ax.set_xticks([10, 30, 100, 300, 1000], ["10", "30", "100", "300", "1000"])
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_xlabel("во сколько раз ESP32 быстрее Nano по времени", color=INK2, fontsize=11)
style(ax, "Одна и та же программа: ESP32 против Nano")
fig.tight_layout()
fig.savefig(OUT / "chart_ratio.png", facecolor=SURFACE)

# ---------- график 2: чтение памяти с разным шагом ----------
steps = [1, 2, 4, 8, 16, 32, 64, 128]
series = [
    ("ESP32-CAM, PSRAM (DRAM)", "esp32cam", "psram", ORANGE),
    ("ESP32-CAM, флеш", "esp32cam", "flash", YELLOW),
    ("Nano, SRAM", "nano", "sram", AQUA),
    ("ЙоТик, SRAM", "yotik", "sram", BLUE),
]
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
for name, b, mem, color in series:
    vals = [data[b][f"mem_{mem}_step{s}"][1] for s in steps]
    ax.plot(steps, vals, color=color, lw=2.2, marker="o", ms=6,
            markeredgecolor=SURFACE, markeredgewidth=1.5, label=name)
    shift = {"flash": 1.12, "psram": 0.88}.get(mem, 1.0)  # две линии почти совпадают
    ax.text(128 * 1.12, vals[-1] * shift, name, color=INK, fontsize=10.5, va="center")
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xticks(steps, [str(s) for s in steps])
ax.set_yticks([10, 30, 100, 300], ["10", "30", "100", "300"])
ax.axvline(32, color=MUTED, lw=1.2, ls="--")
ax.text(32 * 1.08, 60, "строка кэша\n32 байта", color=INK2, fontsize=10.5, ha="left", va="center")
ax.set_xlim(0.8, 128 * 3.6)
ax.set_ylim(6, 450)
ax.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_xlabel("шаг чтения, байт", color=INK2, fontsize=11)
ax.set_ylabel("тактов на одно чтение", color=INK2, fontsize=11)
ax.legend(frameon=False, fontsize=10, loc="upper left", labelcolor=INK)
style(ax, "Чтение памяти: кэш виден как ступенька")
fig.tight_layout()
fig.savefig(OUT / "chart_memory.png", facecolor=SURFACE)

# ---------- график 3: частота 80 → 240 МГц ----------
freq = [
    ("арифметика", data["yotik"]["f80_add32"][0] / data["yotik"]["f240_add32"][0]),
    ("SRAM\n(ЙоТик)", data["yotik"]["f80_sram"][0] / data["yotik"]["f240_sram"][0]),
    ("PSRAM\n(ESP32-CAM)", data["esp32cam"]["f80_psram"][0] / data["esp32cam"]["f240_psram"][0]),
    ("флеш\n(ESP32-CAM)", data["esp32cam"]["f80_flash"][0] / data["esp32cam"]["f240_flash"][0]),
]
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
x = range(len(freq))
ax.bar(list(x), [v for _, v in freq], color=BLUE, width=0.56)
ax.axhline(3, color=ORANGE, lw=2, ls="--")
ax.text(3.45, 3.06, "частота выросла втрое", color=INK2, fontsize=11, ha="right", va="bottom")
for i, (_, v) in enumerate(freq):
    ax.text(i, v - 0.1, f"{v:.2f}×", ha="center", va="top", color="white", fontsize=13, fontweight="bold")
ax.set_xticks(list(x), [n for n, _ in freq])
ax.set_ylim(0, 3.6)
ax.set_yticks([0, 1, 2, 3], ["0", "1×", "2×", "3×"])
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_ylabel("ускорение при 80 → 240 МГц", color=INK2, fontsize=11)
style(ax, "Ядро разогнали втрое, а память — нет")
fig.tight_layout()
fig.savefig(OUT / "chart_freq.png", facecolor=SURFACE)

print("\n".join(f"{n:22s} {r:7.1f}x" for r, n in ratios))
print("freq:", [(n.replace(chr(10), ' '), round(v, 2)) for n, v in freq])
