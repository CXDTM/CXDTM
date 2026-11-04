"""Regenerates animated.svg: a neofetch-style profile card (info on the left, portrait on the right).
It switches between dark and light every SWITCH_SECONDS. Age and experience are calculated from the
dates below, and the portrait is built from your GitHub profile picture, so running this on a
schedule (see .github/workflows/update.yml) keeps everything current."""
import json, os, urllib.request
from datetime import date, timedelta
from io import BytesIO
from xml.sax.saxutils import escape

# ============ EDIT THIS SECTION ============
USERNAME     = "CXDTM"
HEADER       = "prabhakant@tiwari"
DOB          = date(1992, 4, 15)
DEVOPS_START = date(2023, 1, 15)      # DevOps experience is counted from here (about 3.8 years in Nov 2026)
MECH_YEARS   = 2.3                    # earlier work as Mechanical Engineer
JOB_START    = date(2016, 5, 16)      # current job
EMAIL        = "prabhakantshandilya@gmail.com"
LINKEDIN     = "https://www.linkedin.com/in/prabhakant-tiwari-86637476/"
SWITCH_SECONDS = 2                    # dark <-> light every N seconds
USE_AVATAR   = True                   # True: portrait follows your GitHub profile picture. False: keep art.txt as it is
AVATAR_CROP  = None                   # optional zoom, (left, top, right, bottom) as fractions, e.g. (0.2, 0.05, 0.8, 0.6)
FALLBACK     = dict(repos=2, stars=3, followers=0, commits=5)   # used only if the GitHub API fails
# ===========================================

HERE = os.path.dirname(os.path.abspath(__file__))

def diff(a, b):
    y, m, d = b.year - a.year, b.month - a.month, b.day - a.day
    if d < 0:
        m -= 1
        d += (b.replace(day=1) - timedelta(days=1)).day
    if m < 0:
        y -= 1
        m += 12
    return y, m, d

def plural(n, w): return f"{n} {w}{'' if n == 1 else 's'}"

today = date.today()
ay, am, ad = diff(DOB, today)
AGE = f"{plural(ay, 'year')}, {plural(am, 'month')}, {plural(ad, 'day')}"
dev_years = (today - DEVOPS_START).days / 365.25
DEVOPS, MECH, TOTAL = f"{dev_years:.1f} years", f"{MECH_YEARS:.1f} years", f"{MECH_YEARS + dev_years:.1f} years"
jy, jm, jd = diff(JOB_START, today)
job_len = plural(jy * 12 + jm, "month") if jy * 12 + jm else plural(jd, "day")
JOB = f"since {JOB_START.day} {JOB_START:%B %Y} ({job_len})"
LINKEDIN_SHORT = LINKEDIN.replace("https://www.linkedin.com/in/", "").replace("https://linkedin.com/in/", "").rstrip("/")

# ---------- GitHub stats ----------
def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-card"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok: req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

stats = dict(FALLBACK)
try:
    u = api(f"/users/{USERNAME}")
    repos = api(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    stats.update(repos=u["public_repos"], followers=u["followers"], stars=sum(r["stargazers_count"] for r in repos),
                 commits=api(f"/search/commits?q=author:{USERNAME}&per_page=1")["total_count"])
except Exception as e:
    print("GitHub API failed, using fallback stats:", e)

# ---------- portrait (ASCII art) ----------
ART_COLS = 56
ART_FILE = os.path.join(HERE, "art.txt")

def make_art(img, crop=None):
    from PIL import Image, ImageOps, ImageFilter
    img = img.convert("L")
    w, h = img.size
    round_mask = False
    if crop:
        img = img.crop((int(w*crop[0]), int(h*crop[1]), int(w*crop[2]), int(h*crop[3])))
    else:                                         # GitHub avatars are square pictures shown in a circle
        side = min(w, h)
        img = img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
        round_mask = True
    w, h = img.size
    rows = max(8, int(ART_COLS * h / w / 2))
    bg = img.point(lambda v: 255 if v > 238 else 0)
    img = ImageOps.equalize(img, mask=ImageOps.invert(bg))
    img = img.point(lambda v: int(255 * (v / 255) ** 1.8))      # darken mid-tones so eyes, brows and nose show
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))
    small, bgs = img.resize((ART_COLS, rows), Image.LANCZOS), bg.resize((ART_COLS, rows), Image.BOX)
    ramp, out = "@%#*+=-:. ", []
    for y in range(rows):
        line = ""
        for x in range(ART_COLS):
            dx, dy = (x + .5 - ART_COLS / 2) / (ART_COLS / 2), (y + .5 - rows / 2) / (rows / 2)
            if (round_mask and dx * dx + dy * dy > 1) or bgs.getpixel((x, y)) > 200:
                line += " "
            else:
                line += ramp[min(int(small.getpixel((x, y)) / 256 * len(ramp)), len(ramp) - 1)]
        out.append(line.rstrip())
    return out

art = None
try:
    if not USE_AVATAR: raise RuntimeError("USE_AVATAR is off")
    from PIL import Image
    if os.environ.get("AVATAR_FILE"):                         # local testing
        im = Image.open(os.environ["AVATAR_FILE"])
    else:
        url = api(f"/users/{USERNAME}")["avatar_url"]
        url += ("&" if "?" in url else "?") + "s=460"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "profile-card"}), timeout=20) as r:
            im = Image.open(BytesIO(r.read()))
    art = make_art(im, AVATAR_CROP)
    open(ART_FILE, "w").write("\n".join(art) + "\n")
except Exception as e:
    print("Avatar -> ASCII skipped, using saved art.txt:", e)
if art is None:
    art = open(ART_FILE).read().rstrip("\n").split("\n")

# ---------- info column (neofetch style: ". key: ........ value") ----------
RW = 62
def kv(key, val):
    pre = f". {key}: "
    return [("s", pre), ("c", "." * max(RW - len(pre) - 1 - len(val), 2) + " "), ("k", val)]
def head(t):
    s = f"- {t} "
    return [("c", s + "-" * (RW - len(s)))]

rows = [
    [("t", HEADER + " "), ("c", "-" * (RW - len(HEADER) - 1))],
    kv("OS", "Linux, Windows"),
    kv("Uptime", AGE),
    kv("Role", "DevOps Engineer"),
    kv("Current.Job", JOB),
    kv("Experience.Total", TOTAL),
    kv("Experience.Mechanical", MECH),
    kv("Experience.DevOps", DEVOPS),
    [("c", ".")],
    kv("Cloud", "Azure, AWS"),
    kv("CI/CD", "Jenkins, GitHub Actions, GitLab CI"),
    kv("Containers", "Docker, Kubernetes, Helm"),
    kv("IaC", "Terraform"),
    kv("Observability", "Prometheus, Grafana, ELK"),
    [("c", ".")],
    kv("Languages.Programming", "Bash, Python"),
    kv("Languages.Computer", "YAML, JSON, HCL"),
    kv("Languages.Real", "English, Hindi"),
    [],
    head("Contact"),
    kv("Email.Personal", EMAIL),
    kv("LinkedIn", LINKEDIN_SHORT),
    kv("GitHub", USERNAME),
    [],
    head("GitHub Stats"),
    kv("Repos", f"{stats['repos']} | Stars: {stats['stars']}"),
    kv("Commits", f"{stats['commits']} | Followers: {stats['followers']}"),
]

# ---------- svg ----------
D = dict(bg="#1a1b26", t="#c0caf5", k="#7dcfff", s="#ff9e64", c="#565f89", a="#7aa2f7")
L = dict(bg="#f5f5f9", t="#343b58", k="#0f4b6e", s="#965027", c="#7c7f94", a="#34548a")
CW, LH, TOP, LEFT = 9.0, 20, 46, 28
ART_CW, ART_LH, ART_FS = 7.8, 14, 13
ART_X = LEFT + RW * CW + 36
cols = max(len(l) for l in art)
WIDTH = int(ART_X + cols * ART_CW + 28)
HEIGHT = max(TOP + len(rows) * LH + 22, int(len(art) * ART_LH + 60))
art_top = (HEIGHT - len(art) * ART_LH) / 2 + 11
cyc = SWITCH_SECONDS * 2

css = ['text{font-family:"JetBrains Mono","Fira Code",Consolas,"DejaVu Sans Mono",monospace;font-size:15px;white-space:pre}.art{font-size:%dpx}' % ART_FS]
for k in D:
    css.append(f"@keyframes a_{k}{{0%,45%{{fill:{D[k]}}}50%,95%{{fill:{L[k]}}}100%{{fill:{D[k]}}}}}.{k}{{fill:{D[k]};animation:a_{k} {cyc}s infinite}}")

o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">',
     f"<title>{escape(HEADER)} profile card</title>", f"<style>{''.join(css)}</style>",
     f'<rect class="bg" width="{WIDTH}" height="{HEIGHT}" rx="14"/>']
for i, row in enumerate(rows):
    if not row: continue
    n = sum(len(tx) for _, tx in row)
    sp = "".join(f'<tspan class="{cl}">{escape(tx)}</tspan>' for cl, tx in row)
    o.append(f'<text x="{LEFT}" y="{TOP + i*LH}" textLength="{n*CW:g}" lengthAdjust="spacing" xml:space="preserve">{sp}</text>')
for i, ln in enumerate(art):
    if ln.strip():
        o.append(f'<text class="a art" x="{ART_X:g}" y="{art_top + i*ART_LH:.1f}" textLength="{len(ln)*ART_CW:.1f}" lengthAdjust="spacing" xml:space="preserve">{escape(ln)}</text>')
o.append("</svg>")
open(os.path.join(HERE, "animated.svg"), "w").write("\n".join(o))
print("Updated:", AGE, "|", TOTAL, "|", DEVOPS, "|", JOB, "|", stats)
