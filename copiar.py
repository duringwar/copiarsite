import requests, time, re
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as et

u = input("URL base: ").strip()
o = Path("copia_site")
s = requests.Session()
s.headers.update({"User-Agent": "sitecopy/1.0"})
d = 0.3
m = 500
bad = re.compile(r"(login|logout|signin|signup|register|admin|account|cart|checkout|private|wp-admin)", re.I)
h = urlparse(u).netloc
base = f"{urlparse(u).scheme}://{h}"
o.mkdir(exist_ok=True)

def a(x):
    x = urldefrag(urljoin(base, x))[0]
    p = urlparse(x)
    return p.scheme in ("http", "https") and p.netloc == h and not bad.search(x)

def b(x):
    return rp.can_fetch("*", x) and a(x)

def c(x):
    p = urlparse(x)
    q = p.path or "/"
    if q.endswith("/"):
        q += "index.html"
    elif "." not in Path(q).name:
        q += "/index.html"
    n = re.sub(r'[<>:"|?*]', "_", q.lstrip("/"))
    return o / n

def e(x, y):
    try:
        return Path(y).relative_to(Path(x).parent).as_posix()
    except Exception:
        return y.as_posix()

def f(x):
    time.sleep(d)
    try:
        r = s.get(x, timeout=15)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None

rp = RobotFileParser()
rp.set_url(urljoin(base, "/robots.txt"))
try:
    rp.read()
except Exception:
    rp.parse([])

sm = set()
r = f(urljoin(base, "/robots.txt"))
if r:
    for i in r.text.splitlines():
        if i.lower().startswith("sitemap:"):
            z = i.split(":", 1)[1].strip()
            if a(z):
                sm.add(z)
z = urljoin(base, "/sitemap.xml")
if a(z):
    sm.add(z)

seen_sm = set()
todo_sm = list(sm)
q = [u]
seen = set()

while todo_sm:
    x = todo_sm.pop()
    if x in seen_sm or not b(x):
        continue
    seen_sm.add(x)
    r = f(x)
    if not r:
        continue
    try:
        root = et.fromstring(r.content)
        for i in root.iter():
            if i.tag.endswith("loc") and i.text:
                z = i.text.strip()
                if z.endswith(".xml") and a(z):
                    todo_sm.append(z)
                elif b(z):
                    q.append(z)
    except Exception:
        pass

def g(x, cur):
    z = urljoin(cur, x or "")
    z = urldefrag(z)[0]
    return z if b(z) else ""

def j(x, cur):
    out = []
    for i in (x or "").split(","):
        p = i.strip().split()
        if not p:
            continue
        z = g(p[0], cur)
        if z:
            out.append(" ".join([e(c(cur), c(z))] + p[1:]))
    return ", ".join(out)

def k(t, cur):
    def r(mo):
        z = mo.group(1).strip("'\"")
        y = g(z, cur)
        if y:
            dl(y)
            return "url(" + e(c(cur), c(y)) + ")"
        return mo.group(0)
    return re.sub(r"url\(([^)]+)\)", r, t)

def l(x, cur):
    y = g(x, cur)
    if y:
        dl(y)
        return e(c(cur), c(y))
    return x

def dl(x):
    if x in got or not b(x):
        return
    got.add(x)
    r = f(x)
    if not r:
        return
    p = c(x)
    p.parent.mkdir(parents=True, exist_ok=True)
    ct = r.headers.get("content-type", "").lower()
    try:
        if "text/css" in ct or p.suffix.lower() == ".css":
            p.write_text(k(r.text, x), encoding=r.encoding or "utf-8", errors="ignore")
        else:
            p.write_bytes(r.content)
    except Exception:
        pass

got = set()

while q and len(seen) < m:
    x = q.pop(0)
    if x in seen or not b(x):
        continue
    seen.add(x)
    r = f(x)
    if not r:
        continue
    ct = r.headers.get("content-type", "").lower()
    p = c(x)
    p.parent.mkdir(parents=True, exist_ok=True)
    if "html" not in ct:
        try:
            p.write_bytes(r.content)
        except Exception:
            pass
        continue
    soup = BeautifulSoup(r.text, "html.parser")
    for tag, attr in [("a", "href"), ("link", "href"), ("script", "src"), ("img", "src"), ("source", "src"), ("video", "src"), ("audio", "src"), ("iframe", "src")]:
        for t in soup.find_all(tag):
            v = t.get(attr)
            if not v:
                continue
            y = g(v, x)
            if not y:
                continue
            if tag == "a":
                q.append(y)
            else:
                dl(y)
            t[attr] = e(p, c(y))
    for t in soup.find_all(srcset=True):
        t["srcset"] = j(t.get("srcset"), x)
    for t in soup.find_all(style=True):
        t["style"] = k(t.get("style"), x)
    try:
        p.write_text(str(soup), encoding="utf-8", errors="ignore")
    except Exception:
        pass
