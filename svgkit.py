"""svgkit: tiny helper to hand-build animated SVGs (CSS keyframes, dark/light switching).
It can also draw rough PNG previews by evaluating the same keyframes."""
import math
from contextlib import contextmanager
from xml.sax.saxutils import escape

D = dict(bg="#1a1b26", bar="#13141c", box="#20222f", t="#c0caf5", p="#9ece6a", k="#7dcfff",
         s="#ff9e64", c="#565f89", m="#bb9af7", r="#f7768e", a="#7aa2f7")
L = dict(bg="#f5f5f9", bar="#d9dbe6", box="#ebecf3", t="#343b58", p="#33635c", k="#0f4b6e",
         s="#965027", c="#7c7f94", m="#5a3e8e", r="#a8334c", a="#34548a")

def _mix(h, tgt, f):
    a = [int(h[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(tgt[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * f) for x, y in zip(a, b))
for _P, (_lt, _dk) in ((D, (0.22, 0.38)), (L, (0.35, 0.22))):
    for _k in list(_P):
        _P[_k + "l"] = _mix(_P[_k], "#ffffff", _lt)    # lit top face
        _P[_k + "d"] = _mix(_P[_k], "#000000", _dk)    # shaded side face
FONT = '"JetBrains Mono","Fira Code",Consolas,"DejaVu Sans Mono",monospace'
DEF = dict(op=1.0, tx=0.0, ty=0.0, rot=0.0, sx=1.0, sy=1.0)
TF = {"tx", "ty", "rot", "sx", "sy"}


class Doc:
    def __init__(self, W, H, T, switch=2, title="animation"):
        self.W, self.H, self.T, self.title = W, H, T, title
        self.cyc = switch * 2
        assert T % self.cyc == 0, "T must be a multiple of 2*switch"
        self.body, self.css, self.reg = [], [], set()
        self.anims, self.chain, self.prims = {}, [], []

    # ---- theme classes (colors switch dark <-> light) ----
    def cls(self, fill=None, stroke=None):
        name = f"x{fill or ''}_{stroke or ''}"
        if name not in self.reg:
            self.reg.add(name)
            def decl(P):
                out = []
                if fill: out.append(f"fill:{P[fill]}")
                if stroke: out.append(f"stroke:{P[stroke]}")
                return ";".join(out)
            self.css.append(f"@keyframes {name}{{0%,45%{{{decl(D)}}}50%,95%{{{decl(L)}}}100%{{{decl(D)}}}}}"
                            f".{name}{{{decl(D)};animation:{name} {self.cyc}s infinite}}")
        return name

    # ---- keyframe animations ----
    def anim(self, name, pts, org=None, timing="linear"):
        cur, full = dict(DEF), []
        for t, dct in sorted(pts, key=lambda p: p[0]):
            cur = {**cur, **dct}
            full.append((t, dict(cur)))
        if full[0][0] > 0: full.insert(0, (0, dict(full[0][1])))
        if full[-1][0] < self.T: full.append((self.T, dict(full[-1][1])))
        used = set()
        for _, dct in pts: used |= set(dct)
        has_tf, has_op = bool(used & TF), "op" in used
        frames, last = [], -1.0
        for t, s in full:
            p = max(t / self.T * 100, last + 0.001); last = p
            decl = []
            if has_op: decl.append(f"opacity:{s['op']:g}")
            if has_tf: decl.append(f"transform:translate({s['tx']:g}px,{s['ty']:g}px) rotate({s['rot']:g}deg) scale({s['sx']:g},{s['sy']:g})")
            frames.append(f"{p:.3f}%{{{';'.join(decl)}}}")
        rule = f".{name}{{animation:{name} {self.T:g}s {timing} infinite"
        if has_tf and org: rule += f";transform-box:fill-box;transform-origin:{org[0]}"
        self.css.append(f"@keyframes {name}{{{''.join(frames)}}}{rule}}}")
        self.anims[name] = (full, org)
        return name

    def show(self, name, a, b, f=0.3):          # visible between a and b (with fades)
        P = [(0, dict(op=0.0))]
        if a > 0: P.append((a, dict(op=0.0)))
        P += [(a + f, dict(op=1.0)), (b - f, dict(op=1.0)), (b, dict(op=0.0))]
        if b < self.T: P.append((self.T, dict(op=0.0)))
        return self.anim(name, P)

    def appear(self, name, a, f=0.15):           # hidden until a, then visible until the loop ends
        return self.anim(name, [(0, dict(op=0.0)), (a, dict(op=0.0)), (a + f, dict(op=1.0))])

    # ---- groups ----
    @contextmanager
    def g(self, name=None):
        self.body.append(f'<g class="{name}">' if name else "<g>")
        self.chain.append(("anim", name))
        yield
        self.chain.pop(); self.body.append("</g>")

    @contextmanager
    def at(self, tx=0, ty=0):
        self.body.append(f'<g transform="translate({tx:g},{ty:g})">')
        self.chain.append(("static", (tx, ty)))
        yield
        self.chain.pop(); self.body.append("</g>")

    # ---- shapes ----
    def _st(self, fill, stroke, sw):
        s = f' class="{self.cls(fill, stroke)}"'
        if not fill: s += ' fill="none"'
        if stroke: s += f' stroke-width="{sw:g}" stroke-linecap="round" stroke-linejoin="round"'
        return s

    def _rec(self, k, a, fill, stroke, sw, **kw):
        self.prims.append(dict(k=k, a=a, fill=fill, stroke=stroke, sw=sw, chain=list(self.chain), **kw))

    def rect(self, x, y, w, h, fill=None, stroke=None, sw=1, rx=0):
        self.body.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}"{self._st(fill, stroke, sw)}/>')
        self._rec("rect", (x, y, w, h, rx), fill, stroke, sw)

    def circle(self, cx, cy, r, fill=None, stroke=None, sw=1):
        self.body.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}"{self._st(fill, stroke, sw)}/>')
        self._rec("circle", (cx, cy, r), fill, stroke, sw)

    def line(self, x1, y1, x2, y2, stroke="t", sw=2):
        self.body.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}"{self._st(None, stroke, sw)}/>')
        self._rec("line", (x1, y1, x2, y2), None, stroke, sw)

    def poly(self, pts, fill=None, stroke=None, sw=1):
        p = " ".join(f"{x:g},{y:g}" for x, y in pts)
        self.body.append(f'<polygon points="{p}"{self._st(fill, stroke, sw)}/>')
        self._rec("poly", tuple(pts), fill, stroke, sw)

    def cuboid(self, x, y, w, h, dep=10, fill="box", stroke=None, sw=1, rx=0):
        """3D box: front face at (x,y,w,h), extruded dep px up and to the right."""
        dx, dy = dep * 0.7, -dep * 0.55
        self.poly([(x, y), (x + dx, y + dy), (x + w + dx, y + dy), (x + w, y)], fill=fill + "l", stroke=stroke, sw=sw)
        self.poly([(x + w, y), (x + w + dx, y + dy), (x + w + dx, y + h + dy), (x + w, y + h)], fill=fill + "d", stroke=stroke, sw=sw)
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx)

    def text(self, x, y, s, fill="t", size=14, bold=False, anchor="start"):
        extra = (' font-weight="700"' if bold else "") + (f' text-anchor="{anchor}"' if anchor != "start" else "")
        self.body.append(f'<text x="{x:g}" y="{y:g}" class="{self.cls(fill)}" style="font-size:{size}px"{extra} xml:space="preserve">{escape(s)}</text>')
        self._rec("text", (x, y, s, size, bold, anchor), fill, None, 0)

    # ---- output ----
    def svg(self):
        bg = self.cls("bg")
        style = f"text{{font-family:{FONT};font-size:14px;white-space:pre}}" + "".join(self.css)
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" viewBox="0 0 {self.W} {self.H}" role="img">',
               f"<title>{escape(self.title)}</title>", f"<style>{style}</style>",
               f'<rect class="{bg}" width="{self.W}" height="{self.H}" rx="14"/>'] + self.body + ["</svg>"]
        s = "\n".join(out)
        # lint: every class used must have a css rule, every animation a keyframes block
        import re
        for tok in set(re.findall(r'class="([^"]+)"', "".join(self.body))):
            assert f".{tok}{{" in style, f"class without css rule: {tok}"
        for nm in set(re.findall(r"animation:(\w+) ", style)):
            assert f"@keyframes {nm}{{" in style, f"missing keyframes: {nm}"
        return s


# ------------------------------------------------------------------ rough previewer
def _interp(full, t):
    if t <= full[0][0]: return full[0][1]
    for (t0, s0), (t1, s1) in zip(full, full[1:]):
        if t0 <= t <= t1:
            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return {key: s0[key] + (s1[key] - s0[key]) * k for key in s0}
    return full[-1][1]

def _mul(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1; a2, b2, c2, d2, e2, f2 = m2
    return (a1*a2 + c1*b2, b1*a2 + d1*b2, a1*c2 + c1*d2, b1*c2 + d1*d2, a1*e2 + c1*f2 + e1, b1*e2 + d1*f2 + f1)

def _state(chain, doc, t):
    M, op = (1, 0, 0, 1, 0, 0), 1.0
    for kind, val in chain:
        if kind == "static":
            M = _mul(M, (1, 0, 0, 1, val[0], val[1]))
        elif val in doc.anims:
            full, org = doc.anims[val]
            s = _interp(full, t); op *= s["op"]
            ox, oy = org[1] if org else (0, 0)
            a = math.radians(s["rot"]); ca, sa = math.cos(a), math.sin(a)
            A = (ca * s["sx"], sa * s["sx"], -sa * s["sy"], ca * s["sy"])
            e = ox + s["tx"] - (A[0] * ox + A[2] * oy); f = oy + s["ty"] - (A[1] * ox + A[3] * oy)
            M = _mul(M, (A[0], A[1], A[2], A[3], e, f))
    return M, op

def preview(doc, t, pal=D, S=2):
    from PIL import Image, ImageDraw, ImageFont
    FR = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    hx = lambda h: tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
    base = Image.new("RGBA", (doc.W * S, doc.H * S), (0, 0, 0, 0))
    ImageDraw.Draw(base).rounded_rectangle([0, 0, doc.W * S, doc.H * S], 14 * S, fill=hx(pal["bg"]) + (255,))
    for p in doc.prims:
        M, op = _state(p["chain"], doc, t)
        if op < 0.02: continue
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        al = int(255 * min(op, 1))
        fc = hx(pal[p["fill"]]) + (al,) if p["fill"] else None
        sc_ = hx(pal[p["stroke"]]) + (al,) if p["stroke"] else None
        T_ = lambda x, y: ((M[0]*x + M[2]*y + M[4]) * S, (M[1]*x + M[3]*y + M[5]) * S)
        k = math.sqrt(abs(M[0]*M[3] - M[1]*M[2])); sw = max(1, int(p["sw"] * k * S)) if p["stroke"] else 0
        a = p["a"]
        if p["k"] == "rect":
            x, y, w, h, rx = a
            pts = [T_(x, y), T_(x + w, y), T_(x + w, y + h), T_(x, y + h)]
            if abs(M[1]) < 1e-6 and abs(M[2]) < 1e-6:
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                d.rounded_rectangle([min(xs), min(ys), max(xs), max(ys)], rx * k * S, fill=fc, outline=sc_, width=sw)
            else:
                d.polygon(pts, fill=fc, outline=sc_)
        elif p["k"] == "circle":
            cx, cy, r = a; X, Y = T_(cx, cy); R = r * k * S
            d.ellipse([X - R, Y - R, X + R, Y + R], fill=fc, outline=sc_, width=sw)
        elif p["k"] == "line":
            d.line([T_(a[0], a[1]), T_(a[2], a[3])], fill=sc_, width=sw)
        elif p["k"] == "poly":
            pts = [T_(x, y) for x, y in a]
            d.polygon(pts, fill=fc, outline=sc_)
            if sc_: d.line(pts + [pts[0]], fill=sc_, width=sw)
        elif p["k"] == "text":
            x, y, s, size, bold, anchor = a
            font = ImageFont.truetype(FB if bold else FR, max(6, int(size * k * S)))
            d.text(T_(x, y), s, font=font, fill=fc, anchor={"start": "ls", "middle": "ms", "end": "rs"}[anchor])
        base = Image.alpha_composite(base, layer) if op < 0.999 or True else base
    out = Image.new("RGB", base.size, (13, 14, 20)); out.paste(base, mask=base.split()[3])
    return out.resize((doc.W, doc.H), Image.LANCZOS)

def montage(doc, times, path, pal=D, cols=1, label=True):
    from PIL import Image, ImageDraw
    ims = [preview(doc, t, pal) for t in times]
    gap = 12; rows = (len(ims) + cols - 1) // cols
    W = cols * doc.W + (cols - 1) * gap; H = rows * doc.H + (rows - 1) * gap
    out = Image.new("RGB", (W, H), (13, 14, 20))
    for i, im in enumerate(ims):
        x, y = (i % cols) * (doc.W + gap), (i // cols) * (doc.H + gap)
        out.paste(im, (x, y))
        if label: ImageDraw.Draw(out).text((x + 10, y + doc.H - 18), f"t = {times[i]:.1f}s", fill=(120, 125, 150))
    out.save(path)
