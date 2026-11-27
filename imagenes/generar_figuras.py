#!/usr/bin/env python3
"""Genera las figuras SVG del guion de competencia interespecífica.

Usa las mismas ecuaciones (Lotka-Volterra para la competencia), la misma paleta
y la misma tipografía que presentacion/simulador_isoclinas.html, para que las
figuras se parezcan a lo que los estudiantes ven en el simulador.

Uso:  python3 imagenes/generar_figuras.py
Escribe los SVG en la misma carpeta que este script. Solo usa la biblioteca estándar.
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent

# Paleta del simulador
C1 = "#a0522d"    # especie 1 · conejo marrón
C2 = "#2b6cb0"    # especie 2 · conejo blanco
INK = "#111827"
MUTED = "#4b5563"
PT = "#facc15"
Z1 = "rgba(160,82,45,.15)"
Z2 = "rgba(43,108,176,.15)"
SOFT1 = "160,82,45"
SOFT2 = "43,108,176"
FONT = 'system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'


def fmt(x, d=0):
    """Número con coma decimal, como el simulador (es-ES)."""
    s = f"{x:.{d}f}"
    if d:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


# ---------------------------------------------------------------- SVG mínimo
class SVG:
    def __init__(self, w, h):
        self.w, self.h, self.el = w, h, []

    def add(self, s):
        self.el.append(s)

    def line(self, x0, y0, x1, y1, col, lw=1, dash=None, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                 f'stroke="{col}" stroke-width="{lw}" stroke-linecap="{cap}"{d}/>')

    def path(self, pts, col, lw=1, dash=None, fill="none"):
        if len(pts) < 2:
            return
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{col}" stroke-width="{lw}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{da}/>')

    def poly(self, pts, fill):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polygon points="{d}" fill="{fill}"/>')

    def circle(self, x, y, r, fill, stroke=None, lw=0):
        s = f' stroke="{stroke}" stroke-width="{lw}"' if stroke else ""
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"{s}/>')

    def rect(self, x, y, w, h, fill):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"/>')

    def text(self, s, x, y, col=INK, size=13, weight=400, anchor="start", base="middle", rot=None, box=False):
        tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        if box:  # fondo blanco semitransparente, como textBox() del simulador
            tw = 0.56 * size * len(s)
            x0 = x if anchor == "start" else x - tw if anchor == "end" else x - tw / 2
            self.rect(x0 - 4, y - size * 0.78, tw + 8, size * 1.56, "rgba(255,255,255,.88)")
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" fill="{col}" font-size="{size}" font-weight="{weight}" '
                 f'text-anchor="{anchor}" dominant-baseline="{base}"{tr}>{escape(s)}</text>')

    def arrow(self, x0, y0, x1, y1, col, lw=1.2, hs=5):
        self.line(x0, y0, x1, y1, col, lw, cap="butt")
        a = math.atan2(y1 - y0, x1 - x0)
        p = [(x1, y1),
             (x1 - hs * math.cos(a - 0.45), y1 - hs * math.sin(a - 0.45)),
             (x1 - hs * math.cos(a + 0.45), y1 - hs * math.sin(a + 0.45))]
        self.poly(p, col)

    def save(self, name, title):
        body = "\n".join(self.el)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}" font-family=\'{FONT}\' role="img">\n'
               f'<title>{escape(title)}</title>\n'
               f'<rect width="100%" height="100%" fill="#ffffff"/>\n{body}\n</svg>\n')
        (OUT / name).write_text(svg, encoding="utf-8")
        print("escrito", name)


# ---------------------------------------------------------------- modelo
def f(n1, n2, P):
    d1 = P["r1"] * n1 * (P["K1"] - n1 - P["a"] * n2) / P["K1"]
    d2 = P["r2"] * n2 * (P["K2"] - n2 - P["b"] * n1) / P["K2"]
    return d1, d2


def simulate(n1, n2, P, t_max, h=0.02, every=5):
    traj, t, k = [(0.0, n1, n2)], 0.0, 0
    while t < t_max:
        a1, a2 = f(n1, n2, P)
        b1, b2 = f(n1 + h / 2 * a1, n2 + h / 2 * a2, P)
        c1, c2 = f(n1 + h / 2 * b1, n2 + h / 2 * b2, P)
        d1, d2 = f(n1 + h * c1, n2 + h * c2, P)
        n1 += h / 6 * (a1 + 2 * b1 + 2 * c1 + d1)
        n2 += h / 6 * (a2 + 2 * b2 + 2 * c2 + d2)
        t += h
        k += 1
        if k % every == 0:
            traj.append((t, n1, n2))
    return traj


def equilibria(P):
    K1, K2, a, b = P["K1"], P["K2"], P["a"], P["b"]
    E = [(0, 0, False), (K1, 0, b * K1 > K2), (0, K2, a * K2 > K1)]
    det = 1 - a * b
    if abs(det) > 1e-9:
        x, y = (K1 - a * K2) / det, (K2 - b * K1) / det
        if x > 0 and y > 0:
            E.append((x, y, det > 0))
    return E


# ---------------------------------------------------------------- plano N1–N2
class Plane:
    """Plano de fases con la geometría del simulador."""

    def __init__(self, svg, ox, oy, w, h, M, xlab, ylab, Mx=None):
        self.s, self.M, self.Mx = svg, M, Mx or M
        self.L, self.T = ox + 70, oy + 16
        self.pw, self.ph = w - 70 - 18, h - 16 - 62
        self.ox, self.oy, self.w, self.h = ox, oy, w, h
        self.xlab, self.ylab = xlab, ylab

    def X(self, v):
        return self.L + v / self.Mx * self.pw

    def Y(self, v):
        return self.T + self.ph - v / self.M * self.ph

    def iso(self, K, c, sp):
        """Extremos de la isoclina recortados al marco (sp=1: N1 = K − c·N2; sp=2: N2 = K − c·N1)."""
        M, Mx = self.M, self.Mx
        if sp == 1:
            return [(K, 0), (K - c * M, M) if c * M < K else (0, K / c)]
        return [(0, K), (Mx, K - c * Mx) if c * Mx < K else (K / c, 0)]

    def zone(self, K, c, sp, fill):
        p0, p1 = self.iso(K, c, sp)
        pts = [(0, 0), p0, p1, (0, p1[1])] if sp == 1 else [(0, 0), p0, p1, (p1[0], 0)]
        self.s.poly([(self.X(x), self.Y(y)) for x, y in pts], fill)

    def isoline(self, K, c, sp, col, lw=4, dash=None, opacity=1):
        p0, p1 = self.iso(K, c, sp)
        colr = col if opacity == 1 else col  # el color se pasa ya con alfa si hace falta
        self.s.line(self.X(p0[0]), self.Y(p0[1]), self.X(p1[0]), self.Y(p1[1]), colr, lw, dash)

    def field(self, P, n=13):
        """Campo de flechas gris, como el simulador."""
        cell = self.pw / n
        col = "rgba(55,65,81,.45)"
        for i in range(n):
            for j in range(n):
                n1, n2 = (i + .5) / n * self.M, (j + .5) / n * self.M
                d1, d2 = f(n1, n2, P)
                dx, dy = d1 / self.M * self.pw, -d2 / self.M * self.ph
                ln = math.hypot(dx, dy)
                if ln < 1e-9:
                    continue
                k = cell * .38 / ln
                cx, cy = self.X(n1), self.Y(n2)
                self.s.arrow(cx - dx * k, cy - dy * k, cx + dx * k, cy + dy * k, col, 1.2, 5)

    def traj(self, tr, col=INK, lw=2.5, start=True):
        self.s.path([(self.X(a), self.Y(b)) for _, a, b in tr], col, lw)
        if start:
            self.s.circle(self.X(tr[0][1]), self.Y(tr[0][2]), 6, PT, INK, 2)

    def eq(self, P):
        for x, y, st in equilibria(P):
            if x <= self.M and y <= self.M:
                self.s.circle(self.X(x), self.Y(y), 7, INK if st else "#fff", INK, 2.5)

    def axes(self, xt=(), yt=()):
        s, L, T, pw, ph = self.s, self.L, self.T, self.pw, self.ph
        s.path([(L, T), (L, T + ph), (L + pw, T + ph)], INK, 2)
        s.text(self.xlab, L + pw / 2, self.oy + self.h - 10, INK, 14, 600, "middle")
        s.text(self.ylab, self.ox + 16, T + ph / 2, INK, 14, 600, "middle", rot=-90)
        s.text("0", L - 6, T + ph + 9, MUTED, 13, 400, "end")
        xt = sorted(xt)
        for k, (v, lab, col) in enumerate(xt):
            dy = 17 if k and self.X(v) - self.X(xt[k - 1][0]) < 80 else 0
            s.rect(self.X(v) - 1, T + ph, 2, 6, col)
            s.text(lab, self.X(v), T + ph + 16 + dy, col, 13, 600, "middle")
        yt = sorted(yt)
        for k, (v, lab, col) in enumerate(yt):
            dy = -16 if k and self.Y(yt[k - 1][0]) - self.Y(v) < 30 else 0
            s.rect(L - 6, self.Y(v) - 1, 6, 2, col)
            top, bot = lab.split(" = ")
            s.text(top, L - 8, self.Y(v) - 7 + dy, col, 12, 600, "end")
            s.text(bot, L - 8, self.Y(v) + 8 + dy, col, 12, 600, "end")

    def label_iso(self, K, c, sp, col, text, off):
        p0, p1 = self.iso(K, c, sp)
        mx, my = (self.X(p0[0]) + self.X(p1[0])) / 2, (self.Y(p0[1]) + self.Y(p1[1])) / 2
        self.s.text(text, mx + off[0], my + off[1], col, 13, 700, box=True)


# ---------------------------------------------------------------- serie temporal
def time_series(svg, ox, oy, w, h, tr, P, names):
    L, Rm, T, B = ox + 52, 74, oy + 16, 44
    pw, ph = w - 52 - Rm, h - 16 - B
    t_max = tr[-1][0]
    n_max = 1.1 * max([P["K1"], P["K2"]] + [max(p[1], p[2]) for p in tr])
    X = lambda t: L + t / t_max * pw
    Y = lambda n: T + ph - n / n_max * ph
    svg.path([(L, T), (L, T + ph), (L + pw, T + ph)], INK, 1.5)
    step = 10 if t_max > 25 else 5
    t = 0
    while t <= t_max + 1e-9:
        svg.text(fmt(t), X(t), T + ph + 12, MUTED, 13, 400, "middle")
        t += step
    svg.text("tiempo", L + pw / 2, oy + h - 8, INK, 14, 600, "middle")
    svg.text("N (individuos)", ox + 16, T + ph / 2, INK, 14, 600, "middle", rot=-90)
    svg.text("0", L - 6, Y(0), MUTED, 13, 400, "end")
    close = abs(Y(P["K1"]) - Y(P["K2"])) < 14
    for K, col, lab, sh in [(P["K1"], C1, "K₁", 0), (P["K2"], C2, "K₂", 26 if close else 0)]:
        svg.line(L, Y(K), L + pw, Y(K), col, 1.3, "6 5", "butt")
        svg.text(lab, L + pw + 6 + sh, Y(K), col, 12, 600)
    svg.path([(X(p[0]), Y(p[1])) for p in tr], C1, 3)
    svg.path([(X(p[0]), Y(p[2])) for p in tr], C2, 3)
    # rótulos al final de cada curva
    e1, e2 = tr[-1][1], tr[-1][2]
    y1, y2 = Y(e1) - 14, Y(e2) - 14          # por defecto, encima de cada curva
    if abs(Y(e1) - Y(e2)) < 24:              # curvas juntas: la de abajo, rótulo debajo
        if e1 >= e2 and e2 > 0.05 * n_max:
            y2 = Y(e2) + 16
        elif e2 > e1 and e1 > 0.05 * n_max:
            y1 = Y(e1) + 16
    xr = X(t_max * 0.97)
    svg.text(names[0], xr, y1, C1, 13, 700, "end")
    svg.text(names[1], xr, y2, C2, 13, 700, "end")


def panel_title(svg, text, x, y):
    svg.text(text, x, y, MUTED, 13, 700)


# ================================================================ figuras
def fig1():
    """Crecimiento de la especie 1 sin y con 35 individuos de la especie 2 (K1 = 115, αN2 = 29,8)."""
    K1, N2, aN2 = 115, 35, 29.8
    a = aN2 / N2
    Ke = K1 - aN2
    W, H = 680, 380
    s = SVG(W, H)
    L, R, T, Bm = 60, 200, 22, 46
    pw, ph = W - L - R, H - T - Bm
    t_max, n_max = 12, 1.15 * K1
    X = lambda t: L + t / t_max * pw
    Y = lambda n: T + ph - n / n_max * ph
    logi = lambda K, N0: (lambda t: K / (1 + (K - N0) / N0 * math.exp(-t)))
    N0 = 0.03 * K1
    s.path([(L, T), (L, T + ph), (L + pw, T + ph)], INK, 2)
    s.text("tiempo", L + pw / 2, H - 14, INK, 14, 600, "middle")
    s.text("N₁ (individuos de la especie 1)", 18, T + ph / 2, INK, 14, 600, "middle", rot=-90)
    s.text("0", L - 6, Y(0), MUTED, 13, 400, "end")

    def curve(fn, col, lw, dash=None):
        s.path([(X(k / 200 * t_max), Y(fn(k / 200 * t_max))) for k in range(201)], col, lw, dash)

    def kline(v, col, lines):
        s.line(L, Y(v), L + pw, Y(v), col, 1.4, "6 5", "butt")
        for k, txt in enumerate(lines):
            s.text(txt, L + pw + 8, Y(v) + (k - (len(lines) - 1) / 2) * 16, col, 13, 600 if k == 0 else 400)

    curve(logi(K1, N0), f"rgba({SOFT1},.45)", 2.2, "7 5")
    curve(logi(Ke, N0), C1, 3.5)
    kline(K1, f"rgba({SOFT1},.75)", ["K₁ (sin especie 2)", f"= {fmt(K1)}"])
    kline(Ke, C1, ["K₁ − αN₂", f"= {fmt(K1)} − {fmt(a, 2)}·{N2}", f"= {fmt(Ke, 1)}"])
    s.text(f"con N₂ = {N2} individuos de la especie 2,", X(8.7), Y(Ke) + 46, C1, 14, 600, "middle")
    s.text(f"que pesan como αN₂ = {fmt(aN2, 1)} de la especie 1", X(8.7), Y(Ke) + 66, C1, 14, 600, "middle")
    s.save("fig1_crecimiento_con_competidor.svg",
           "Crecimiento logístico de la especie 1 sin la especie 2 y con 35 individuos de la especie 2")


def fig2():
    """Isoclina de crecimiento cero de la especie 1 (K1 = 45, α = 0,8)."""
    K1, a = 45, 0.8
    M = 1.12 * max(K1, K1 / a)
    s = SVG(560, 500)
    p = Plane(s, 0, 0, 560, 500, M, "N₁ (individuos de la especie 1)", "N₂ (individuos de la especie 2)")
    p.zone(K1, a, 1, Z1)
    n = 6
    cell, ln = min(p.pw, p.ph) / n, min(p.pw, p.ph) / n * .38
    for i in range(n):
        for j in range(n):
            n1, n2 = (i + .5) / n * M, (j + .5) / n * M
            F = K1 - n1 - a * n2
            if abs(F) / math.hypot(1, a) < .04 * M:
                continue
            sg = 1 if F > 0 else -1
            cx, cy = p.X(n1), p.Y(n2)
            s.arrow(cx - sg * ln / 2, cy, cx + sg * ln / 2, cy, C1, 2.2, 7)
    p.isoline(K1, a, 1, C1)
    p.axes(xt=[(K1, f"K₁ = {fmt(K1)}", C1)], yt=[(K1 / a, f"K₁/α = {fmt(K1 / a)}", C1)])
    p.label_iso(K1, a, 1, C1, "isoclina de la especie 1", (14, -14))
    s.text("N₁ + αN₂ < K₁: N₁ crece", p.X(4), p.Y(8), C1, 13, 700, box=True)
    s.text("N₁ + αN₂ > K₁: N₁ decrece", p.X(M * .52), p.Y(M * .88), C1, 13, 700, box=True)
    s.save("fig2_isoclina_especie1.svg", "Isoclina de crecimiento cero de la especie 1")


def fig3():
    """Efecto de α sobre la isoclina de la especie 1 (K1 = 45)."""
    K1, alphas = 45, [0.5, 1, 2]
    M = 1.12 * K1 / min(alphas)
    s = SVG(460, 500)
    p = Plane(s, 0, 0, 460, 500, M, "N₁ (individuos de la especie 1)", "N₂ (individuos de la especie 2)", Mx=1.6 * K1)
    p.zone(K1, 2, 1, Z1)
    styles = {0.5: (f"rgba({SOFT1},.45)", 3, "8 6"), 1: (f"rgba({SOFT1},.7)", 3, "3 5"), 2: (C1, 4, None)}
    for a in alphas:
        col, lw, dash = styles[a]
        p.isoline(K1, a, 1, col, lw, dash)
        s.text(f"α = {fmt(a, 1)}", p.X(2.5), p.Y(K1 / a) - 2, col if a != 2 else C1, 13, 700, box=True)
    p.axes(xt=[(K1, f"K₁ = {fmt(K1)}", C1)],
           yt=[(K1 / a, f"K₁/α = {fmt(K1 / a, 1)}", C1) for a in alphas])
    s.text("N₁ crece (α = 2)", p.X(K1 * .08), p.Y(K1 / 2 * .3), C1, 13, 700)
    s.save("fig3_efecto_alfa.svg", "Efecto del coeficiente de competencia alfa sobre la isoclina de la especie 1")


def fig4():
    """Las dos isoclinas juntas, con zonas y flechas sumadas (números de la pizarra del simulador)."""
    K1, a, K2, b = 100, 0.8, 80, 1.25
    M = 1.12 * max(K1, K2, K1 / a, K2 / b)
    s = SVG(600, 540)
    p = Plane(s, 0, 0, 600, 540, M, "N₁ (individuos de la especie 1)", "N₂ (individuos de la especie 2)")
    p.zone(K1, a, 1, Z1)
    p.zone(K2, b, 2, Z2)
    n = 6
    ln = min(p.pw, p.ph) / n * .38
    for i in range(n):
        for j in range(n):
            n1, n2 = (i + .5) / n * M, (j + .5) / n * M
            F1, F2 = K1 - n1 - a * n2, K2 - n2 - b * n1
            if abs(F1) / math.hypot(1, a) < .04 * M or abs(F2) / math.hypot(1, b) < .04 * M:
                continue
            s1, s2 = (1 if F1 > 0 else -1), (1 if F2 > 0 else -1)
            cx, cy = p.X(n1), p.Y(n2)
            s.arrow(cx, cy, cx + s1 * ln, cy, f"rgba({SOFT1},.32)", 2.2, 6)
            s.arrow(cx, cy, cx, cy - s2 * ln, f"rgba({SOFT2},.32)", 2.2, 6)
            s.arrow(cx, cy, cx + s1 * ln, cy - s2 * ln, INK, 2.8, 8)
    p.isoline(K1, a, 1, C1)
    p.isoline(K2, b, 2, C2)
    p.axes(xt=[(K1, f"K₁ = {fmt(K1)}", C1), (K2 / b, f"K₂/β = {fmt(K2 / b)}", C2)],
           yt=[(K2, f"K₂ = {fmt(K2)}", C2), (K1 / a, f"K₁/α = {fmt(K1 / a)}", C1)])
    p.label_iso(K1, a, 1, C1, "isoclina de la especie 1", (16, -16))
    s.text("isoclina de la especie 2", p.X(3), p.Y(47), C2, 13, 700, box=True)
    s.text("crecen las dos", p.X(6), p.Y(12), INK, 13, 700, box=True)
    s.text("crece la 1,", p.X(58), p.Y(15.5), INK, 13, 700, box=True)
    s.text("decrece la 2", p.X(58), p.Y(10.5), INK, 13, 700, box=True)
    s.text("decrecen las dos", p.X(92), p.Y(118), INK, 13, 700, box=True)
    s.save("fig4_dos_isoclinas.svg", "Las dos isoclinas de crecimiento cero superpuestas, con las regiones y los vectores de cambio")


def two_panel(P, starts, ts_start, t_max, name, title, iso_off):
    W, H = 1040, 470
    s = SVG(W, H)
    M = 1.12 * max(P["K1"], P["K2"], P["K1"] / P["a"], P["K2"] / P["b"])
    p = Plane(s, 0, 26, 520, H - 26, M, "N₁ (conejos marrones)", "N₂ (conejos blancos)")
    panel_title(s, "Plano de fases", p.L, 16)
    p.zone(P["K1"], P["a"], 1, Z1)
    p.zone(P["K2"], P["b"], 2, Z2)
    p.field(P)
    p.isoline(P["K1"], P["a"], 1, C1)
    p.isoline(P["K2"], P["b"], 2, C2)
    for st in starts:
        if st != ts_start:
            p.traj(simulate(*st, P, t_max), "rgba(17,24,39,.32)", 2, start=False)
            s.circle(p.X(st[0]), p.Y(st[1]), 3.5, "rgba(17,24,39,.4)")
    tr = simulate(*ts_start, P, t_max)
    p.traj(tr)
    p.eq(P)
    xt = [(P["K1"], f"K₁ = {fmt(P['K1'])}", C1)]
    yt = [(P["K2"], f"K₂ = {fmt(P['K2'])}", C2)]
    if abs(P["K2"] / P["b"] - P["K1"]) > 1:
        xt.append((P["K2"] / P["b"], f"K₂/β = {fmt(P['K2'] / P['b'])}", C2))
        yt.append((P["K1"] / P["a"], f"K₁/α = {fmt(P['K1'] / P['a'])}", C1))
    p.axes(xt, yt)
    p.label_iso(P["K1"], P["a"], 1, C1, "isoclina del conejo marrón", iso_off[0])
    p.label_iso(P["K2"], P["b"], 2, C2, "isoclina del conejo blanco", iso_off[1])
    panel_title(s, "Serie temporal", 560 + 52, 16)
    time_series(s, 560, 26, 480, H - 26 - 22, tr, P, ("conejo marrón", "conejo blanco"))
    s.save(name, title)


def fig5():
    """Nichos idénticos: exclusión competitiva (preajuste «gana el marrón» del simulador)."""
    P = dict(K1=60, K2=40, a=1, b=1, r1=1, r2=1)
    two_panel(P, [(12, 8)], (12, 8), 40, "fig5_exclusion_competitiva.svg",
              "Exclusión competitiva: isoclinas paralelas, trayectoria y serie temporal",
              ((10, -16), (14, -18)))


def fig6():
    """Nichos parcialmente solapados: coexistencia (preajuste «coexisten» del simulador)."""
    P = dict(K1=55, K2=55, a=0.55, b=0.55, r1=1, r2=1)
    starts = [(4, 60), (64, 4), (6, 6), (75, 70)]
    two_panel(P, starts, (64, 4), 30, "fig6_coexistencia.svg",
              "Coexistencia: isoclinas que se cruzan en un equilibrio estable, trayectorias y serie temporal",
              ((30, -40), (60, -30)))


if __name__ == "__main__":
    for fig in (fig1, fig2, fig3, fig4, fig5, fig6):
        fig()
