"""Regenerates dark_mode.svg and light_mode.svg for the GitHub profile card.
Age ("Uptime") and experience are calculated from today's date, so running this
daily (see update.yml) keeps them correct automatically."""
import json, os, urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

# ============ EDIT THIS SECTION ============
USERNAME   = "CXDTM"
DOB        = date(1992, 4, 15)
EXP_START  = date(2023, 1, 15)   # DevOps career start (about 3.8 years as of Nov 2026)
HEADER     = "prabhakant@tiwari"
EMAIL      = "prabhakantshandilya@gmail.com"
LINKEDIN   = "https://www.linkedin.com/in/prabhakant-tiwari-86637476/"
USE_AVATAR = True    # True = ASCII art follows your GitHub profile picture; False = keep art.txt as it is
SWITCH_SECONDS = 2      # dark <-> light every N seconds
FALLBACK   = dict(repos=2, stars=3, followers=0, commits=5)   # used if the GitHub API fails
# ===========================================

LINKEDIN_SHORT = LINKEDIN.replace("https://www.linkedin.com/", "").replace("https://linkedin.com/", "").rstrip("/")

def diff(a, b):
    y, m, d = b.year - a.year, b.month - a.month, b.day - a.day
    if d < 0:
        m -= 1
        d += (b.replace(day=1) - timedelta(days=1)).day
    if m < 0:
        y -= 1
        m += 12
    return y, m, d

def plural(n, w):
    return f"{n} {w}{'' if n == 1 else 's'}"

today = date.today()
ay, am, ad = diff(DOB, today)
ey, em, _ = diff(EXP_START, today)
AGE = f"{ay}y {am}m {ad}d"
EXP = f"{ey}y {em}m"

# ---------- GitHub stats ----------
def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-card"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

stats = dict(FALLBACK)
try:
    u = api(f"/users/{USERNAME}")
    repos = api(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    stats["repos"] = u["public_repos"]
    stats["followers"] = u["followers"]
    stats["stars"] = sum(r["stargazers_count"] for r in repos)
    stats["commits"] = api(f"/search/commits?q=author:{USERNAME}&per_page=1")["total_count"]
except Exception as e:
    print("GitHub API failed, using fallback stats:", e)

# ---------- ASCII art from the GitHub profile picture ----------
ART_COLS = 46
ART_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art.txt")

def make_art(img):
    from PIL import Image, ImageOps, ImageFilter
    img = img.convert("L")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    rows = ART_COLS // 2
    bg = img.point(lambda v: 255 if v > 238 else 0)
    img = ImageOps.equalize(img, mask=ImageOps.invert(bg))
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))
    small = img.resize((ART_COLS, rows), Image.LANCZOS)
    bgs = bg.resize((ART_COLS, rows), Image.BOX)
    ramp = "@%#*+=-:. "
    out = []
    for y in range(rows):
        line = ""
        for x in range(ART_COLS):
            dx = (x + 0.5 - ART_COLS / 2) / (ART_COLS / 2)
            dy = (y + 0.5 - rows / 2) / (rows / 2)
            if dx * dx + dy * dy > 1 or bgs.getpixel((x, y)) > 200:
                line += " "
            else:
                line += ramp[min(int(small.getpixel((x, y)) / 256 * len(ramp)), len(ramp) - 1)]
        out.append(line.rstrip())
    return out

art = None
try:
    if not USE_AVATAR:
        raise RuntimeError("USE_AVATAR is off")
    from io import BytesIO
    from PIL import Image
    if os.environ.get("AVATAR_FILE"):                       # local testing
        im = Image.open(os.environ["AVATAR_FILE"])
    else:
        url = api(f"/users/{USERNAME}")["avatar_url"]
        url += ("&" if "?" in url else "?") + "s=460"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "profile-card"}), timeout=20) as r:
            im = Image.open(BytesIO(r.read()))
    art = make_art(im)
    open(ART_FILE, "w").write("\n".join(art) + "\n")
except Exception as e:
    print("Avatar -> ASCII failed, using saved art.txt:", e)
if art is None:
    art = open(ART_FILE).read().rstrip("\n").split("\n")

# ---------- design: terminal window ----------
FULL_NAME = "Prabhakant Tiwari"
ROLE      = "DevOps Engineer"
TITLE     = "cxdtm@devops: ~/profile"

def cmd(text):    return [(28, "p", "$"), (48, "t", text)]
def kv(k, v, vc="s"): return [(48, "k", k), (190, vc, v)]

rows = [
    cmd("whoami"),
    [(48, "m", FULL_NAME.upper()), (270, "c", "//"), (295, "s", ROLE)],
    [],
    cmd("cat profile.yaml"),
    kv("age:", AGE),
    kv("experience:", EXP),
    kv("os:", "linux · windows"),
    kv("languages:", "english · hindi"),
    [],
    cmd("./stack --list"),
    kv("cloud", "Azure · AWS"),
    kv("ci/cd", "Jenkins · GitHub Actions · GitLab CI"),
    kv("containers", "Docker · Kubernetes · Helm"),
    kv("iac", "Terraform"),
    kv("observe", "Prometheus · Grafana · ELK"),
    kv("code", "Bash · Python · YAML · HCL"),
    [],
    cmd("./pipeline.sh"),
    [(48, "p", "● build"), (140, "c", "→"), (160, "p", "● test"), (245, "c", "→"), (265, "p", "● deploy")],
    [],
    cmd("./contact.sh"),
    kv("mail", EMAIL),
    kv("linkedin", LINKEDIN_SHORT),
    kv("github", "github.com/" + USERNAME),
    [],
    cmd("git shortlog --stats"),
    [(48, "k", "repos"), (108, "s", str(stats["repos"])), (150, "k", "stars"), (210, "s", str(stats["stars"])),
     (250, "k", "followers"), (340, "s", str(stats["followers"])), (385, "k", "commits"), (465, "s", str(stats["commits"]))],
    [],
    [(28, "p", "$")],
]
CURSOR_ROW = len(rows) - 1

themes = {
 "dark_mode":  dict(bg="#1a1b26", bar="#13141c", t="#c0caf5", p="#9ece6a", k="#7dcfff", s="#ff9e64", c="#565f89", m="#bb9af7", a="#7aa2f7"),
 "light_mode": dict(bg="#f5f5f9", bar="#e4e5ee", t="#343b58", p="#33635c", k="#0f4b6e", s="#965027", c="#7c7f94", m="#5a3e8e", a="#34548a"),
}
D, L = themes["dark_mode"], themes["light_mode"]

LH, TOP, LEFT_W = 20, 62, 610
ART_X, ART_CW, ART_LH, ART_FS = 640, 7.8, 14, 13
cols = max(len(l) for l in art)
WIDTH = int(ART_X + cols * ART_CW + 30)
HEIGHT = TOP + len(rows) * LH + 24
art_top = 36 + (HEIGHT - 36 - len(art) * ART_LH) / 2

FONT = '"JetBrains Mono","Fira Code",Consolas,"DejaVu Sans Mono",monospace'
KEYS = ["bg", "bar", "t", "p", "k", "s", "c", "m", "a"]

def css(mode, c=None):
    base = (f'text{{font-family:{FONT};font-size:15px;white-space:pre}}'
            '.m{font-weight:700}.art{font-size:%dpx}.ttl{font-size:13px}'
            '@keyframes blink{0%%,49%%{opacity:1}50%%,100%%{opacity:0}}.cur{animation:blink 1s step-end infinite}' % ART_FS)
    out = []
    for k in KEYS:
        if mode == "anim":
            out.append(f"@keyframes a_{k}{{0%,45%{{fill:{D[k]}}}50%,95%{{fill:{L[k]}}}100%{{fill:{D[k]}}}}}"
                       f".{k}{{fill:{D[k]};animation:a_{k} {SWITCH_SECONDS*2}s infinite}}")
        else:
            out.append(f".{k}{{fill:{c[k]}}}")
    return base + "".join(out)

def render(mode, c=None):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
         f"<style>{css(mode, c)}</style>",
         f'<rect class="bg" width="{WIDTH}" height="{HEIGHT}" rx="12"/>',
         f'<rect class="bar" width="{WIDTH}" height="36" rx="12"/>',
         f'<rect class="bar" y="24" width="{WIDTH}" height="12"/>',
         '<circle cx="22" cy="18" r="6" fill="#ff5f56"/><circle cx="42" cy="18" r="6" fill="#ffbd2e"/><circle cx="62" cy="18" r="6" fill="#27c93f"/>',
         f'<text class="c ttl" x="{WIDTH/2}" y="23" text-anchor="middle">{escape(TITLE)}</text>',
         f'<rect class="c" x="{LEFT_W}" y="56" width="1" height="{HEIGHT-56-20}" opacity="0.5"/>']
    for i, row in enumerate(rows):
        y = TOP + i * LH
        for x, cl, tx in row:
            o.append(f'<text class="{cl}" x="{x}" y="{y}" xml:space="preserve">{escape(tx)}</text>')
    cy = TOP + CURSOR_ROW * LH
    o.append(f'<rect class="p cur" x="48" y="{cy-13}" width="9" height="16"/>')
    for i, ln in enumerate(art):
        if ln.strip():
            o.append(f'<text class="a art" x="{ART_X}" y="{art_top + i*ART_LH:.1f}" xml:space="preserve" '
                     f'textLength="{len(ln)*ART_CW:.1f}" lengthAdjust="spacing">{escape(ln)}</text>')
    o.append("</svg>")
    return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
for name, c in themes.items():
    open(os.path.join(here, f"{name}.svg"), "w").write(render("static", c))
open(os.path.join(here, "animated.svg"), "w").write(render("anim"))
print("Updated:", AGE, "|", EXP, "|", stats)
