"""Builds ../journey.svg: a day in the life of a DevOps engineer (plan -> code -> commit -> build+test -> deploy -> monitor), in 3D.
Everything is drawn as extruded boxes (svgkit's d.cuboid) on a floor, so it reads as a small 3D scene.
Edit the SCENES text below, then run:  python tools/journey.py   (illustrative, not live data)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import Doc

W, H, T = 1028, 450, 24
SEG = 4.0                                  # seconds per scene
SCENES = [  # (step label, thought line 1, thought line 2, laptop line 1, laptop line 2)
    ("PLAN",       "Pick a ticket",           "from the board",        "board",           "3 tickets"),
    ("CODE",       "Write the change",        "and a pipeline file",   "pipeline.yml",    "+ stage: test"),
    ("COMMIT",     "git commit",              "git push to GitHub",    "$ git push",      "origin feature"),
    ("BUILD+TEST", "Pipeline builds,",        "tests and scans",       "pipeline #142",   "running…"),
    ("DEPLOY",     "Roll out to",             "Kubernetes",            "kubectl apply", "rollout ok"),
    ("MONITOR",    "Watch dashboards",        "and handle alerts",     "grafana",         "all green"),
]
d = Doc(W, H, T, title="Animated 3D DevOps journey: plan, code, commit, build and test, deploy, monitor")
sc = [d.show(f"sc{i}", i * SEG, (i + 1) * SEG, 0.3) for i in range(6)]

d.text(24, 32, "a day in devops · 3D", fill="c", size=13)
d.text(24, H - 14, "illustrative", fill="c", size=11)

# ---------------- floor under the desk ----------------
d.poly([(44, 362), (366, 362), (398, 400), (10, 400)], fill="bar")

# ---------------- person + desk (left) ----------------
d.cuboid(36, 62, 300, 70, dep=8, fill="box", stroke="c", sw=1.5)                # thought bubble
d.circle(118, 144, 6, fill="box", stroke="c", sw=1.5); d.circle(108, 158, 4, fill="box", stroke="c", sw=1.5)
for i, s in enumerate(SCENES):
    with d.g(sc[i]):
        d.text(186, 94, s[1], fill="t", size=14, bold=True, anchor="middle")
        d.text(186, 116, s[2], fill="c", size=13, anchor="middle")
# chair + desk
d.line(80, 308, 80, 262, stroke="c", sw=4); d.cuboid(78, 306, 54, 6, dep=10, fill="c")
d.line(106, 312, 106, 356, stroke="c", sw=4); d.line(86, 358, 126, 358, stroke="c", sw=4)
d.line(182, 328, 182, 360, stroke="c", sw=4); d.line(334, 328, 334, 360, stroke="c", sw=4)
d.cuboid(172, 320, 172, 8, dep=22, fill="c")                                    # desk top
# person
d.circle(104, 224, 20, stroke="t", sw=3.5)
d.line(104, 244, 104, 304, stroke="t", sw=5)                                    # torso
d.line(104, 304, 152, 304, stroke="t", sw=5); d.line(152, 304, 152, 354, stroke="t", sw=5); d.line(152, 354, 170, 354, stroke="t", sw=5)
d.line(104, 254, 140, 284, stroke="t", sw=4.5)                                  # upper arm
tap = d.anim("tap", [(t, dict(ty=3.0 if int(t / 0.2) % 2 else 0.0)) for t in [SEG + 0.05 * k for k in range(0, 80)]] + [(2 * SEG, dict(ty=0.0))])
with d.g(tap): d.line(140, 284, 196, 306, stroke="t", sw=4.5)                  # forearm (types during CODE)
# laptop (screen slab + base slab)
d.cuboid(204, 232, 86, 80, dep=5, fill="bg", stroke="k", sw=2.5)
d.cuboid(190, 312, 112, 8, dep=14, fill="k")
for i, s in enumerate(SCENES):
    with d.g(sc[i]):
        d.text(247, 268, s[3], fill="k", size=10, anchor="middle")
        d.text(247, 286, s[4], fill="s", size=10, anchor="middle")

# ---------------- right panel (a thick slab) ----------------
d.cuboid(372, 56, 622, 292, dep=16, fill="box", stroke="c", sw=1.5)
for i, s in enumerate(SCENES):
    with d.g(sc[i]):
        d.text(392, 86, f"0{i + 1} · {s[0]}", fill="s", size=14, bold=True)

def step(i, k): return i * SEG + k       # absolute time inside scene i

# 1 PLAN: kanban, the card lifts, slides across and lands
with d.g(sc[0]):
    for j, name in enumerate(["TODO", "DOING", "DONE"]):
        x = 396 + j * 198
        d.cuboid(x, 104, 182, 226, dep=5, fill="bg", stroke="c", sw=1)
        d.text(x + 12, 124, name, fill="c", size=12, bold=True)
    d.cuboid(408, 190, 158, 34, dep=8, fill="m"); d.text(487, 212, "update docs", fill="bg", size=12, anchor="middle")
    d.cuboid(804, 138, 158, 34, dep=8, fill="p"); d.text(883, 160, "fix flaky test", fill="bg", size=12, anchor="middle")
    mv = d.anim("note", [(0, dict(tx=0, ty=0)), (step(0, 1.2), dict(tx=0, ty=0)), (step(0, 1.6), dict(ty=-12)),
                         (step(0, 2.1), dict(tx=198)), (step(0, 2.5), dict(ty=0)), (T, dict(tx=198, ty=0))])
    with d.g(mv):
        d.cuboid(408, 138, 158, 34, dep=8, fill="k"); d.text(487, 160, "add CI stage", fill="bg", size=12, anchor="middle")

# 2 CODE: editor with lines appearing
lines = [("k", "stages:"), ("t", "  - build"), ("t", "  - test"), ("t", "  - scan"), ("t", "  - deploy"),
         ("s", "trigger: push to main"), ("p", "✔ saved")]
with d.g(sc[1]):
    d.cuboid(396, 104, 572, 226, dep=6, fill="bg", stroke="c", sw=1)
    d.text(414, 126, "pipeline.yml", fill="c", size=12)
    for j, (col, txt) in enumerate(lines):
        with d.g(d.appear(f"ln{j}", step(1, 0.5 + 0.45 * j))):
            d.text(416, 160 + 24 * j, txt, fill=col, size=15)
    cur = d.anim("cur2", [(0, dict(op=0)), (step(1, 0.4), dict(op=0)), (step(1, 0.5), dict(op=1)), (step(1, 0.7), dict(op=0)),
                         (step(1, 0.9), dict(op=1)), (step(1, 1.1), dict(op=0)), (step(1, 1.3), dict(op=1)), (step(1, 1.5), dict(op=0)),
                         (step(1, 1.7), dict(op=1)), (step(1, 1.9), dict(op=0)), (step(1, 2.1), dict(op=1)), (step(1, 2.3), dict(op=0)),
                         (step(1, 2.5), dict(op=1)), (step(1, 3.1), dict(op=1)), (step(1, 3.3), dict(op=0))])
    with d.g(cur): d.rect(540, 148, 9, 16, fill="p")

# 3 COMMIT: local -> origin
with d.g(sc[2]):
    d.cuboid(412, 160, 152, 120, dep=14, fill="bg", stroke="k", sw=1.5); d.text(488, 184, "local", fill="c", size=12, anchor="middle")
    d.cuboid(790, 160, 152, 120, dep=14, fill="bg", stroke="m", sw=1.5); d.text(866, 184, "origin/main", fill="c", size=12, anchor="middle")
    d.line(488 - 50, 232, 488 + 50, 232, stroke="c", sw=2)
    for j, x in enumerate((438, 488, 538)):
        with d.g(d.appear(f"cm{j}", step(2, 0.4 + 0.35 * j))): d.cuboid(x - 8, 224, 16, 16, dep=8, fill="k")
    d.text(488, 268, "feature/ci", fill="s", size=12, anchor="middle")
    d.cuboid(570, 230, 214, 4, dep=4, fill="c")                                 # the rail
    d.text(677, 214, "git push", fill="c", size=12, anchor="middle")
    pk = d.anim("pk", [(0, dict(tx=0, op=0)), (step(2, 1.5), dict(tx=0, op=0)), (step(2, 1.6), dict(tx=0, op=1)), (step(2, 2.7), dict(tx=206, op=1)),
                       (step(2, 2.8), dict(tx=206, op=0)), (T, dict(tx=206, op=0))])
    with d.g(pk): d.cuboid(570, 224, 16, 16, dep=8, fill="m")
    with d.g(d.appear("arr", step(2, 2.8))):
        d.cuboid(858, 224, 16, 16, dep=8, fill="m"); d.text(866, 262, "✔ PR merged", fill="p", size=12, anchor="middle")

# 4 BUILD+TEST: three 3D progress bars
with d.g(sc[3]):
    d.text(396, 122, "pipeline #142", fill="c", size=12)
    for j, name in enumerate(["BUILD", "TEST", "SCAN"]):
        y = 168 + j * 62
        d.text(396, y + 6, name, fill="t", size=15, bold=True)
        d.cuboid(520, y - 12, 360, 20, dep=8, fill="bg", stroke="c", sw=1)
        a, b = step(3, 0.5 + 1.0 * j), step(3, 1.4 + 1.0 * j)
        bar = d.anim(f"bar{j}", [(0, dict(sx=0)), (a, dict(sx=0)), (b, dict(sx=1)), (T, dict(sx=1))], org=("left center", (520, y - 2)))
        with d.g(bar): d.cuboid(520, y - 12, 360, 20, dep=8, fill="k")
        with d.g(d.appear(f"ok{j}", b)): d.text(906, y + 6, "✔ passed", fill="p", size=13, bold=True)

# 5 DEPLOY: image box -> cluster box, pod cubes pop up
with d.g(sc[4]):
    d.cuboid(420, 170, 116, 90, dep=14, fill="bg", stroke="m", sw=2); d.text(478, 222, "app:142", fill="m", size=14, bold=True, anchor="middle")
    d.text(478, 192, "image", fill="c", size=12, anchor="middle")
    d.cuboid(640, 120, 318, 200, dep=16, fill="bg", stroke="k", sw=2); d.text(799, 146, "kubernetes cluster", fill="k", size=12, anchor="middle")
    mv5 = d.anim("img", [(0, dict(tx=0, op=1)), (step(4, 0.6), dict(tx=0, op=1)), (step(4, 1.6), dict(tx=170, op=1)), (step(4, 1.7), dict(tx=170, op=0)), (T, dict(tx=170, op=0))])
    with d.g(mv5): d.cuboid(420, 170, 116, 90, dep=14, fill="m"); d.text(478, 222, "app:142", fill="bg", size=14, bold=True, anchor="middle")
    for j in range(3):
        x = 676 + j * 92
        pod = d.anim(f"pod{j}", [(0, dict(sx=0, sy=0, op=0)), (step(4, 1.8 + 0.4 * j), dict(sx=0, sy=0, op=0)), (step(4, 2.1 + 0.4 * j), dict(sx=1, sy=1, op=1)), (T, dict(sx=1, sy=1, op=1))], org=("center", (x + 30, 214)))
        with d.g(pod): d.cuboid(x, 184, 60, 60, dep=12, fill="m"); d.text(x + 30, 220, "pod", fill="bg", size=13, bold=True, anchor="middle")
    d.text(799, 276, "replicas: 3", fill="c", size=12, anchor="middle")
    with d.g(d.appear("ro", step(4, 3.2))): d.text(799, 304, "✔ rollout complete", fill="p", size=13, bold=True, anchor="middle")

# 6 MONITOR: metric ribbon (with depth), alert, fix
with d.g(sc[5]):
    d.cuboid(396, 104, 572, 226, dep=6, fill="bg", stroke="c", sw=1)
    for gy in (170, 220, 270): d.line(412, gy, 952, gy, stroke="c", sw=0.7)
    d.text(414, 126, "response time", fill="c", size=12)
    ys = [262, 254, 264, 256, 260, 254, 214, 150, 226, 258, 252, 260, 254]
    xs = [416 + i * 44 for i in range(13)]
    for i in range(12):
        col = "r" if i in (5, 6, 7) else ("p" if i >= 8 else "k")
        with d.g(d.appear(f"sg{i}", step(5, 0.3 + 0.22 * i))):
            d.line(xs[i] + 3, ys[i] + 5, xs[i + 1] + 3, ys[i + 1] + 5, stroke=col + "d", sw=3)   # back edge of the ribbon
            d.line(xs[i], ys[i], xs[i + 1], ys[i + 1], stroke=col, sw=3)
    al = d.anim("alert", [(0, dict(op=0)), (step(5, 1.4), dict(op=0)), (step(5, 1.5), dict(op=1)), (step(5, 1.9), dict(op=0.3)), (step(5, 2.3), dict(op=1)),
                          (step(5, 2.7), dict(op=0.3)), (step(5, 3.0), dict(op=1)), (step(5, 3.1), dict(op=0)), (T, dict(op=0))])
    with d.g(al): d.cuboid(640, 112, 112, 26, dep=6, fill="r"); d.text(696, 130, "ALERT", fill="bg", size=13, bold=True, anchor="middle")
    with d.g(d.appear("fixd", step(5, 3.1))): d.cuboid(640, 112, 150, 26, dep=6, fill="p"); d.text(715, 130, "✔ fixed, redeployed", fill="bg", size=12, bold=True, anchor="middle")
    d.text(682, 316, "alert → fix → redeploy → plan the next one ↻", fill="c", size=12, anchor="middle")

# ---------------- stepper ----------------
X = [420 + i * 112 for i in range(6)]
d.line(X[0], 392, X[-1], 392, stroke="c", sw=2)
prog = d.anim("prog", [(0, dict(sx=0, op=1)), (5 * SEG, dict(sx=1)), (23.4, dict(sx=1, op=1)), (23.8, dict(sx=1, op=0)), (T, dict(sx=0, op=0))], org=("left center", (X[0], 392)))
with d.g(prog): d.line(X[0], 392, X[-1], 392, stroke="k", sw=3)
for i, s in enumerate(SCENES):
    d.circle(X[i] + 2, 396, 8, fill="bar")                                      # little drop shadow
    d.circle(X[i], 392, 8, fill="bg", stroke="c", sw=2)
    with d.g(d.show(f"done{i}", i * SEG + 0.6, T, 0.2)): d.circle(X[i], 392, 8, fill="p")
    with d.g(sc[i]): d.circle(X[i], 392, 13, stroke="k", sw=3)
    d.text(X[i], 424, s[0], fill="c", size=11, anchor="middle")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "journey.svg")
open(out, "w").write(d.svg())
if __name__ == "__main__":
    print("journey.svg written", len(d.svg()), "bytes")
    if "--preview" in sys.argv:
        from svgkit import montage
        montage(d, [2.0, 6.5, 10.5, 14.5, 19.0, 22.5], "/home/claude/journey_preview.png", cols=2)
