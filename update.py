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
DEVOPS_START = date(2022, 5, 16)      # DevOps experience is counted from here (4+ years, about 4.5 in Nov 2026) - set your exact date
MECH_YEARS   = 2.3                    # earlier work as Mechanical Engineer
JOB_START    = date(2016, 5, 16)      # job start: "Current.Job" and total experience count from here
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
total_years = (today - JOB_START).days / 365.25
DEVOPS, MECH, TOTAL = f"{dev_years:.1f} years", f"{MECH_YEARS:.1f} years", f"{total_years:.1f} years"
jy, jm, jd = diff(JOB_START, today)
if jy: job_len = plural(jy, "year") + (f", {plural(jm, 'month')}" if jm else "")
elif jm: job_len = plural(jm, "month")
else: job_len = plural(jd, "day")
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
D = dict(bg="#1a1b26", t="#c0caf5", k="#7dcfff", s="#ff9e64", c="#565f89", a="#7aa2f7", fs="#0d0e14", sh="#000000")
L = dict(bg="#f5f5f9", t="#343b58", k="#0f4b6e", s="#965027", c="#7c7f94", a="#34548a", fs="#c4c6d8", sh="#343b58")
CW, LH, TOP, LEFT = 9.0, 20, 46, 28
ART_CW, ART_LH, ART_FS = 7.8, 14, 13
INFO_END = LEFT + RW * CW
PAD_T, OVER_T, OVER_R = 58, 42, 30                 # empty canvas above the card; how far the face leaves the frame (top / right)
cols = max(len(l) for l in art)
lead = min(len(l) - len(l.lstrip()) for l in art if l.strip())
POP = max(1.0, min(1.4, 470 / ((cols - lead) * ART_CW)))           # the portrait is drawn bigger than the frame
ART_X = INFO_END + 14 - lead * ART_CW * POP                          # glyphs start right after the info column
ART_Y = PAD_T - OVER_T                                               # ...and the head sticks out above the card
CARD_W = int(ART_X + cols * ART_CW * POP - OVER_R)                   # ...and out of the right edge
CARD_H = max(TOP + len(rows) * LH + 22, int(len(art) * ART_LH * POP) + 40)
PAD_R = OVER_R + 16
WIDTH, HEIGHT = CARD_W + PAD_R, CARD_H + PAD_T
cyc = SWITCH_SECONDS * 2

def art_texts(cl):
    return "".join(f'<text class="{cl}" x="0" y="{i * ART_LH + 11}" textLength="{len(ln) * ART_CW:.1f}" lengthAdjust="spacing" xml:space="preserve">{escape(ln)}</text>'
                   for i, ln in enumerate(art) if ln.strip())

css = ['text{font-family:"JetBrains Mono","Fira Code",Consolas,"DejaVu Sans Mono",monospace;font-size:15px;white-space:pre}.art{font-size:%dpx}' % ART_FS]
for k in D:
    css.append(f"@keyframes a_{k}{{0%,45%{{fill:{D[k]}}}50%,95%{{fill:{L[k]}}}100%{{fill:{D[k]}}}}}.{k}{{fill:{D[k]};animation:a_{k} {cyc}s infinite}}")
css.append(f"@keyframes a_ln{{0%,45%{{stroke:{D['c']}}}50%,95%{{stroke:{L['c']}}}100%{{stroke:{D['c']}}}}}.ln{{fill:none;stroke:{D['c']};stroke-width:1.5;animation:a_ln {cyc}s infinite}}")
# pop-out: the face floats towards you (bigger, up and left) while its shadow slides away on the card (smaller, fainter) = depth
css.append("@keyframes pop{0%,100%{transform:translate(0px,0px) scale(1)}50%{transform:translate(-5px,-9px) scale(1.045)}}"
           ".pop{animation:pop 4s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 70%}")
css.append("@keyframes shd{0%,100%{transform:translate(10px,16px);opacity:.5}50%{transform:translate(22px,34px);opacity:.26}}"
           ".shd{animation:shd 4s ease-in-out infinite}")

o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">',
     f"<title>{escape(HEADER)} profile card</title>", f"<style>{''.join(css)}</style>",
     '<defs><filter id="blur" x="-15%" y="-15%" width="130%" height="130%"><feGaussianBlur stdDeviation="4"/></filter></defs>',
     f'<rect class="fs" x="9" y="{PAD_T + 9}" width="{CARD_W}" height="{CARD_H}" rx="14"/>',                     # card thickness
     f'<rect class="bg" x="0" y="{PAD_T}" width="{CARD_W}" height="{CARD_H}" rx="14"/>',
     f'<rect class="ln" x="0.75" y="{PAD_T + 0.75}" width="{CARD_W - 1.5}" height="{CARD_H - 1.5}" rx="14"/>']   # the frame the face steps out of
for i, row in enumerate(rows):
    if not row: continue
    n = sum(len(tx) for _, tx in row)
    sp = "".join(f'<tspan class="{cl}">{escape(tx)}</tspan>' for cl, tx in row)
    o.append(f'<text x="{LEFT}" y="{PAD_T + TOP + i*LH}" textLength="{n*CW:g}" lengthAdjust="spacing" xml:space="preserve">{sp}</text>')
o.append(f'<g transform="translate({ART_X:.1f},{ART_Y:.1f}) scale({POP:.3f})">')
o.append(f'<g class="shd" filter="url(#blur)">{art_texts("sh art")}</g>')                                      # soft shadow on the card
o.append(f'<g class="pop"><g transform="translate(-2.2,2.2)" opacity="0.55">{art_texts("k art")}</g>{art_texts("a art")}</g>')   # cyan edge + face
o.append("</g>")
o.append("</svg>")
open(os.path.join(HERE, "animated.svg"), "w").write("\n".join(o))
print("Updated:", AGE, "|", TOTAL, "|", DEVOPS, "|", JOB, "|", stats)
