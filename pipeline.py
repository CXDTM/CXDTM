"""Builds pipeline.svg: an animated CI/CD pipeline run (commit -> monitor).
Edit STAGES / BUILD_NO / TITLE below, then run:  python pipeline.py
(The data shown is an illustrative run, not live data.)"""
from xml.sax.saxutils import escape

SWITCH_SECONDS = 2          # dark <-> light, same as the profile card
BUILD_NO = 142
TITLE = f"pipeline #{BUILD_NO} · main → production"
# (label, log description, time shown in log)
STAGES = [
    ("COMMIT",  "git push origin main · webhook triggers the pipeline", "2s"),
    ("BUILD",   "docker build -t app:%d" % BUILD_NO,                   "41s"),
    ("TEST",    "unit + integration tests passed",                      "58s"),
    ("SCAN",    "image and dependency security checks, 0 critical",     "33s"),
    ("DEPLOY",  "kubectl rollout status deployment/app",                "27s"),
    ("MONITOR", "dashboards green · alerts quiet",                      "live"),
]

D = dict(bg="#1a1b26", bar="#13141c", box="#20222f", t="#c0caf5", p="#9ece6a", k="#7dcfff", c="#565f89", m="#bb9af7")
L = dict(bg="#f5f5f9", bar="#e4e5ee", box="#ebecf3", t="#343b58", p="#33635c", k="#0f4b6e", c="#7c7f94", m="#5a3e8e")

W, H, T = 1028, 412, 12.0          # T = length of one pipeline run in seconds (must be a multiple of 2*SWITCH_SECONDS)
N = len(STAGES)
BX, BW, BH, BY, GAP = 49, 130, 84, 62, 160
RAIL_Y, RAIL_X0 = 172, 49 + 65
RAIL_W = GAP * (N - 1)
LOG_Y, LOG_LH = 222, 24
FONT = '"JetBrains Mono","Fira Code",Consolas,"DejaVu Sans Mono",monospace'

def pct(t): return t / T * 100
starts = [0.8 + 1.6 * i for i in range(N)]
ends   = [s + 1.0 for s in starts]

# ---------- css ----------
css = [f'text{{font-family:{FONT};font-size:14px;white-space:pre}}.b{{font-weight:700}}']
cyc = SWITCH_SECONDS * 2
for k in D:
    css.append(f"@keyframes a_{k}{{0%,45%{{fill:{D[k]}}}50%,95%{{fill:{L[k]}}}100%{{fill:{D[k]}}}}}"
               f".{k}{{fill:{D[k]};animation:a_{k} {cyc}s infinite}}")
for k, name in (("c", "sc"), ("k", "sk"), ("p", "sp")):
    css.append(f"@keyframes a_{name}{{0%,45%{{stroke:{D[k]}}}50%,95%{{stroke:{L[k]}}}100%{{stroke:{D[k]}}}}}"
               f".{name}{{stroke:{D[k]};animation:a_{name} {cyc}s infinite}}")
for i in range(N):
    ps, pe = pct(starts[i]), pct(ends[i])
    css.append(f"@keyframes q{i}{{0%,{ps:.2f}%{{opacity:1}}{ps+.01:.2f}%,96%{{opacity:0}}100%{{opacity:1}}}}.q{i}{{animation:q{i} {T}s infinite}}")
    css.append(f"@keyframes r{i}{{0%,{ps:.2f}%{{opacity:0}}{ps+.01:.2f}%,{pe:.2f}%{{opacity:1}}{pe+.01:.2f}%,100%{{opacity:0}}}}.r{i}{{opacity:0;animation:r{i} {T}s infinite}}")
    css.append(f"@keyframes d{i}{{0%,{pe:.2f}%{{opacity:0}}{pe+.01:.2f}%,95%{{opacity:1}}100%{{opacity:0}}}}.d{i}{{opacity:0;animation:d{i} {T}s infinite}}")
pb = pct(ends[-1] + 0.4)
css.append(f"@keyframes bn{{0%,{pb:.2f}%{{opacity:0}}{pb+.01:.2f}%,95%{{opacity:1}}100%{{opacity:0}}}}.bn{{opacity:0;animation:bn {T}s infinite}}")

def track(kind):
    pts = [(0, 0)]
    for i in range(N):
        pts += [(starts[i], GAP * i), (ends[i], GAP * i)]
    pts += [(T * 0.95, RAIL_W)]
    def val(x, op):
        v = f"translateX({x}px)" if kind == "pkt" else f"scaleX({x / RAIL_W:.4f})"
        return f"transform:{v};opacity:{op}"
    out = [f"{pct(t):.2f}%{{{val(x, 1)}}}" for t, x in pts]
    out += [f"97%{{{val(RAIL_W, 0)}}}", f"99%{{{val(0, 0)}}}", f"100%{{{val(0, 1)}}}"]
    return f"@keyframes {kind}{{{''.join(out)}}}.{kind}{{animation:{kind} {T}s infinite}}"
css.append(track("pkt"))
css.append(f"{track('prg')}.prg{{transform-origin:{RAIL_X0}px {RAIL_Y}px}}")

# ---------- svg ----------
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     f"<style>{''.join(css)}</style>",
     f'<rect class="bg" width="{W}" height="{H}" rx="12"/>',
     f'<rect class="bar" width="{W}" height="36" rx="12"/><rect class="bar" y="24" width="{W}" height="12"/>',
     '<circle cx="22" cy="18" r="6" fill="#ff5f56"/><circle cx="42" cy="18" r="6" fill="#ffbd2e"/><circle cx="62" cy="18" r="6" fill="#27c93f"/>',
     f'<text class="c" x="{W/2}" y="23" text-anchor="middle" style="font-size:13px">{escape(TITLE)}</text>']

for i, (label, desc, secs) in enumerate(STAGES):
    x = BX + i * GAP; cx = x + BW / 2
    o.append(f'<rect class="box" x="{x}" y="{BY}" width="{BW}" height="{BH}" rx="10"/>')
    o.append(f'<rect class="sc" x="{x}" y="{BY}" width="{BW}" height="{BH}" rx="10" fill="none" stroke-width="1.5"/>')
    o.append(f'<g class="r{i}"><rect class="sk" x="{x}" y="{BY}" width="{BW}" height="{BH}" rx="10" fill="none" stroke-width="2.5"/></g>')
    o.append(f'<g class="d{i}"><rect class="sp" x="{x}" y="{BY}" width="{BW}" height="{BH}" rx="10" fill="none" stroke-width="2.5"/></g>')
    o.append(f'<text class="t b" x="{cx}" y="{BY+38}" text-anchor="middle" style="font-size:15px">{label}</text>')
    o.append(f'<g class="q{i}"><text class="c" x="{cx}" y="{BY+62}" text-anchor="middle" style="font-size:12px">queued</text></g>')
    o.append(f'<g class="r{i}"><text class="k" x="{cx}" y="{BY+62}" text-anchor="middle" style="font-size:12px">running…</text></g>')
    o.append(f'<g class="d{i}"><text class="p" x="{cx}" y="{BY+62}" text-anchor="middle" style="font-size:12px">✔ passed</text></g>')
    if i < N - 1:
        o.append(f'<text class="c" x="{x+BW+15}" y="{BY+47}" text-anchor="middle">→</text>')

o.append(f'<rect class="c" x="{RAIL_X0}" y="{RAIL_Y-1}" width="{RAIL_W}" height="2" rx="1" opacity="0.5"/>')
o.append(f'<g class="prg"><rect class="k" x="{RAIL_X0}" y="{RAIL_Y-2}" width="{RAIL_W}" height="4" rx="2"/></g>')
o.append(f'<g class="pkt"><circle class="m" cx="{RAIL_X0}" cy="{RAIL_Y}" r="7"/></g>')

for i, (label, desc, secs) in enumerate(STAGES):
    y = LOG_Y + i * LOG_LH
    o.append(f'<g class="d{i}"><text class="k" x="28" y="{y}">▸</text><text class="t" x="48" y="{y}">{label.lower()}</text>'
             f'<text class="c" x="140" y="{y}">{escape(desc)}</text><text class="p" x="860" y="{y}">✔ {secs}</text></g>')
by = LOG_Y + N * LOG_LH + 14
o.append(f'<g class="bn"><text class="p b" x="28" y="{by}">● pipeline #{BUILD_NO} succeeded · deployed to production</text></g>')
o.append(f'<text class="c" x="{W-20}" y="{H-12}" text-anchor="end" style="font-size:11px">illustrative run</text>')
o.append("</svg>")
open("pipeline.svg", "w").write("\n".join(o))
print("pipeline.svg written")
