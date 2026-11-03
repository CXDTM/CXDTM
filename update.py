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
EMAIL      = "your-email@gmail.com"
LINKEDIN   = "your-linkedin-id"
FALLBACK   = dict(repos=2, stars=3, followers=0, commits=5)   # used if the GitHub API fails
# ===========================================

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
AGE = f"{plural(ay,'year')}, {plural(am,'month')}, {plural(ad,'day')}"
EXP = f"{plural(ey,'year')}, {plural(em,'month')}"

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

# ---------- layout ----------
RW = 60
def kv(key, val):
    ks = key + ": "
    return [("k", ". " + ks), ("d", "." * max(RW - len(ks) - len(val) - 2, 2) + " "), ("v", val)]
def header(t):
    t = f"- {t} "
    return [("d", t + "-" * (RW - len(t)))]

right = [
    header(HEADER),
    kv("OS", "Linux (Ubuntu, RHEL), Windows"),
    kv("Uptime", AGE),
    kv("Role", "DevOps Engineer"),
    kv("Experience", EXP),
    kv("Cloud", "AWS, Azure"),
    kv("CI/CD", "Jenkins, GitHub Actions, GitLab CI"),
    kv("Containers", "Docker, Kubernetes, Helm"),
    kv("IaC", "Terraform, Ansible"),
    kv("Monitoring", "Prometheus, Grafana, ELK"),
    [("d", ".")],
    kv("Languages.Programming", "Bash, Python, Groovy"),
    kv("Languages.Computer", "YAML, JSON, HCL, Dockerfile"),
    kv("Languages.Real", "English, Hindi"),
    [("d", ".")],
    kv("Hobbies.Software", "Automation, Open Source"),
    kv("Hobbies.Hardware", "Home Lab"),
    [],
    header("Contact"),
    kv("Email.Personal", EMAIL),
    kv("LinkedIn", LINKEDIN),
    kv("GitHub", USERNAME),
    [],
    header("GitHub Stats"),
    kv("Repos", f"{stats['repos']} | Stars: {stats['stars']}"),
    kv("Commits", f"{stats['commits']} | Followers: {stats['followers']}"),
]

art = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "art.txt")).read().rstrip("\n").split("\n")
COLS = max(len(l) for l in art)

themes = {
 "dark_mode":  dict(bg="#161b22", t="#c9d1d9", k="#ffa657", v="#a5d6ff", d="#6e7b8b"),
 "light_mode": dict(bg="#f6f8fa", t="#24292f", k="#953800", v="#0a3069", d="#a0aab5"),
}
LH, FS, CW = 20, 16, 9.6
RX = 15 + (COLS + 3) * CW
rows = max(len(art), len(right))
width, height = int(RX + (RW + 2) * CW + 15), rows * LH + 30
oa, orr = (rows - len(art)) // 2, (rows - len(right)) // 2
here = os.path.dirname(os.path.abspath(__file__))

for name, c in themes.items():
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         f'<style>text{{font-family:Consolas,"Courier New","DejaVu Sans Mono",monospace;font-size:{FS}px;white-space:pre;fill:{c["t"]}}}'
         f'.k{{fill:{c["k"]}}}.v{{fill:{c["v"]}}}.d{{fill:{c["d"]}}}</style>',
         f'<rect width="100%" height="100%" rx="12" fill="{c["bg"]}"/>']
    for i, ln in enumerate(art):
        if ln.strip():
            s.append(f'<text x="15" y="{28+(i+oa)*LH}" xml:space="preserve">{escape(ln)}</text>')
    for i, parts in enumerate(right):
        if parts:
            sp = "".join(f'<tspan class="{cl}">{escape(tx)}</tspan>' for cl, tx in parts)
            s.append(f'<text x="{RX:.1f}" y="{28+(i+orr)*LH}" xml:space="preserve">{sp}</text>')
    s.append("</svg>")
    open(os.path.join(here, f"{name}.svg"), "w").write("\n".join(s))

# ---------- animated card (dark <-> light every SWITCH_SECONDS) ----------
SWITCH_SECONDS = 2
D, L = themes["dark_mode"], themes["light_mode"]
cycle = SWITCH_SECONDS * 2
def kf(name, key):
    return (f"@keyframes {name}{{0%,45%{{fill:{D[key]}}}50%,95%{{fill:{L[key]}}}100%{{fill:{D[key]}}}}}"
            f".{name}{{fill:{D[key]};animation:{name} {cycle}s infinite}}")
a = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
     f'<style>text{{font-family:Consolas,"Courier New","DejaVu Sans Mono",monospace;font-size:{FS}px;white-space:pre}}'
     + kf("bg", "bg") + kf("t", "t") + kf("k", "k") + kf("v", "v") + kf("d", "d") + '</style>',
     '<rect class="bg" width="100%" height="100%" rx="12"/>']
for i, ln in enumerate(art):
    if ln.strip():
        a.append(f'<text class="t" x="15" y="{28+(i+oa)*LH}" xml:space="preserve">{escape(ln)}</text>')
for i, parts in enumerate(right):
    if parts:
        sp = "".join(f'<tspan class="{cl}">{escape(tx)}</tspan>' for cl, tx in parts)
        a.append(f'<text x="{RX:.1f}" y="{28+(i+orr)*LH}" xml:space="preserve">{sp}</text>')
a.append("</svg>")
open(os.path.join(here, "animated.svg"), "w").write("\n".join(a))

print("Updated:", AGE, "|", EXP, "|", stats)
