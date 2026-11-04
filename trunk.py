"""Builds ../trunk.svg: trunk-based development in 3D. Short-lived branches fork off the main trunk, get merged back within hours,
every merge becomes a build that rides the trunk through the CI gate and into production; a feature flag finally switches the feature on.
Edit the values at the top, then run:  python tools/trunk.py   (illustrative run, not live data)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import Doc

W, H, T = 1028, 424, 24
TY = 250                    # top edge of the trunk's front face
BY = 178                    # height of the short-lived branches
GATE_X = 700                # CI gate position on the trunk
ALIVE = 4.5                 # seconds a branch lives before it merges
BRANCHES = [  # (name, colour, fork x, merge x, merge time, hours alive, build no)
    ("feat/login",   "m",  56, 226,  5.5, 3, 142),
    ("fix/cart-bug", "k", 246, 416, 10.5, 5, 143),
    ("feat/search",  "p", 436, 606, 15.5, 2, 144),
]
FLAG_T = 22.2               # when the feature flag flips on

d = Doc(W, H, T, title="Animated 3D trunk-based development pipeline: short-lived branches merge into main, a CI gate checks every merge, releases deploy to production")
d.text(24, 32, "trunk-based development · one main branch, short-lived feature branches", fill="c", size=13)
d.text(24, H - 12, "small commits → merge to main daily → CI on every merge → flags hide unfinished work", fill="c", size=11)
d.text(W - 20, H - 12, "illustrative run", fill="c", size=11, anchor="end")

# ---------------- floor (perspective grid) ----------------
FT, FB = 282, 398
d.poly([(70, FT), (W - 70, FT), (W, FB), (0, FB)], fill="box")
for i in range(11): d.line(70 + i * (W - 140) / 10, FT, i * W / 10, FB, stroke="c", sw=0.5)
for y in (294, 312, 336, 366):
    k = 70 * (1 - (y - FT) / (FB - FT)); d.line(k, y, W - k, y, stroke="c", sw=0.5)
d.poly([(60, 286), (850, 286), (884, 310), (86, 310)], fill="bar")           # shadow of the trunk

# ---------------- the trunk (a log) ----------------
d.cuboid(36, TY, 794, 26, dep=16, fill="s")
d.text(56, TY + 18, "main · trunk", fill="bg", size=13, bold=True)
for _, _, xf, _, _, _, _ in BRANCHES:                                         # base commits where branches fork
    d.cuboid(xf - 6, TY - 17, 12, 12, dep=5, fill="t")

# ---------------- CI gate ----------------
gx = GATE_X
d.cuboid(gx - 34, 164, 12, 86, dep=10, fill="c"); d.cuboid(gx + 22, 164, 12, 86, dep=10, fill="c")
d.cuboid(gx - 38, 146, 76, 20, dep=10, fill="c")
LX = [gx - 18, gx, gx + 18]
for x in LX: d.circle(x, 156, 5, fill="bg")
d.text(gx, 130, "CI GATE", fill="t", size=13, bold=True, anchor="middle")

# ---------------- production ----------------
d.cuboid(830, 150, 170, 126, dep=16, fill="bg", stroke="k", sw=2)
d.text(915, 174, "PRODUCTION", fill="t", size=13, bold=True, anchor="middle")
d.text(915, 189, "kubernetes", fill="c", size=11, anchor="middle")
marks = [0.0] + [b[4] + 6.0 for b in BRANCHES] + [float(T)]
labels = [("c", "waiting for a release")] + [("p", f"✔ #{b[6]} live") for b in BRANCHES]
for i, (col, txt) in enumerate(labels):
    with d.g(d.show(f"st{i}", marks[i], marks[i + 1], 0.12)): d.text(915, 262, txt, fill=col, size=12, anchor="middle")

# ---------------- branches, merges, builds ----------------
for k, (name, col, xf, xm, tm, hrs, bno) in enumerate(BRANCHES):
    ts = tm - ALIVE
    p0, p1, p2, p3 = (xf, TY - 8), (xf + 30, BY), (xm - 30, BY), (xm, TY - 8)
    with d.g(d.show(f"br{k}", ts, tm + 0.8, 0.2)):                            # the branch lives, then is deleted after the merge
        for nm, a_, b_, at in (("up", p0, p1, ts), ("flat", p1, p2, ts + 0.5), ("down", p2, p3, ts + 3.7)):
            with d.g(d.appear(f"{nm}{k}", at)):
                d.line(a_[0] + 3, a_[1] + 5, b_[0] + 3, b_[1] + 5, stroke=col + "d", sw=5)   # depth edge
                d.line(a_[0], a_[1], b_[0], b_[1], stroke=col, sw=5)
        cx = (xf + xm) / 2
        with d.g(d.appear(f"lb{k}", ts + 0.4)):
            d.text(cx, BY - 34, name, fill=col, size=12, bold=True, anchor="middle")
            d.text(cx, BY - 20, f"short-lived · {hrs}h", fill="c", size=11, anchor="middle")
        for j in range(3):
            with d.g(d.appear(f"cm{k}{j}", ts + 1.1 + 0.7 * j)): d.cuboid(xf + 48 + 37 * j - 7, BY - 14, 14, 14, dep=6, fill=col)
    # merge: ring flash + a permanent merge commit on the trunk
    ring = d.anim(f"ring{k}", [(0, dict(op=0, sx=0.4, sy=0.4)), (tm, dict(op=0)), (tm + 0.05, dict(op=1)), (tm + 0.9, dict(op=0, sx=2.6, sy=2.6)), (T, dict(op=0, sx=2.6, sy=2.6))],
                  org=("center", (xm, TY - 10)))
    with d.g(ring): d.circle(xm, TY - 10, 10, stroke=col, sw=3)
    with d.g(d.appear(f"mm{k}", tm)): d.cuboid(xm - 8, TY - 20, 16, 16, dep=6, fill=col)

    # gate lights: amber while checking, green when passed
    ta, td = tm + 3.0, tm + 4.3
    for j in range(3):
        sw_ = ta + 0.6 + 0.3 * j
        with d.g(d.show(f"am{k}{j}", ta, sw_, 0.1)): d.circle(LX[j], 156, 5, fill="s")
        with d.g(d.show(f"gr{k}{j}", sw_, td + 0.9, 0.1)): d.circle(LX[j], 156, 5, fill="p")
    with d.g(d.show(f"gc{k}", ta, ta + 1.2, 0.1)): d.text(gx, 114, "checking…", fill="s", size=11, anchor="middle")
    with d.g(d.show(f"gp{k}", ta + 1.2, td + 0.9, 0.1)): d.text(gx, 114, "✔ passed", fill="p", size=11, anchor="middle")

    # production pod for this build
    px, tp = 848 + 46 * k, tm + 6.0
    pod = d.anim(f"pod{k}", [(0, dict(sx=0, sy=0, op=0)), (tp, dict(sx=0, sy=0, op=0)), (tp + 0.35, dict(sx=1, sy=1, op=1)),
                             (T - 0.4, dict(sx=1, sy=1, op=1)), (T, dict(sx=0, sy=0, op=0))], org=("center", (px + 17, 215)))
    with d.g(pod):
        d.cuboid(px, 198, 34, 34, dep=10, fill=col); d.text(px + 17, 220, f"#{bno}", fill="bg", size=10, bold=True, anchor="middle")

    # the build rides the trunk: merge -> gate -> production
    px0 = xm - 17
    txg, txp = GATE_X - 17 - px0, 840 - 17 - px0
    cube = d.anim(f"cube{k}", [(0, dict(tx=0, op=0)), (tm + 0.2, dict(op=0)), (tm + 0.5, dict(op=1)), (tm + 1.3, dict(tx=0)),
                               (ta, dict(tx=txg)), (td, dict(tx=txg)), (tm + 6.0, dict(tx=txp)), (tm + 6.3, dict(op=0))], timing="ease-in-out")
    with d.g(cube):
        d.cuboid(px0, TY - 34, 34, 30, dep=12, fill=col)
        d.text(px0 + 17, TY - 14, f"#{bno}", fill="bg", size=11, bold=True, anchor="middle")

# ---------------- feature flag ----------------
d.text(848, 326, "feature flag: new-ui", fill="c", size=12)
d.cuboid(848, 336, 64, 26, dep=6, fill="bg", stroke="c", sw=1.5)
with d.g(d.appear("flagon", FLAG_T)): d.cuboid(848, 336, 64, 26, dep=6, fill="p")
knob = d.anim("knob", [(0, dict(tx=0)), (FLAG_T, dict(tx=0)), (FLAG_T + 0.4, dict(tx=40))], timing="ease-in-out")
with d.g(knob): d.cuboid(853, 341, 16, 16, dep=5, fill="t")
with d.g(d.show("flagoff", 0, FLAG_T, 0.12)): d.text(928, 354, "OFF", fill="c", size=12, bold=True)
with d.g(d.show("flagonT", FLAG_T, T, 0.12)): d.text(928, 354, "ON", fill="p", size=12, bold=True)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trunk.svg")
open(out, "w").write(d.svg())
if __name__ == "__main__":
    print("trunk.svg written", len(d.svg()), "bytes")
    if "--preview" in sys.argv:
        from svgkit import montage
        montage(d, [3.0, 5.8, 8.5, 12.0, 16.5, 19.0, 21.8, 23.0], "/home/claude/trunk_preview.png", cols=2)
