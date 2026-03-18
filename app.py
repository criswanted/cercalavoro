from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import datetime

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9",
}

def parse_date(s):
    if not s:
        return ""
    s = s.strip().lower()
    now = datetime.datetime.now()
    if "oggi" in s or "just" in s or "ora" in s or "now" in s:
        return now.isoformat()
    if "ieri" in s:
        return (now - datetime.timedelta(days=1)).isoformat()
    for word, unit in [("ora","hours"),("giorno","days"),("settimana","weeks"),("mese","days")]:
        if word in s:
            try:
                n = int("".join(filter(str.isdigit, s)) or "1")
                if word == "mese": n *= 30
                return (now - datetime.timedelta(**{unit: n})).isoformat()
            except:
                pass
    return s

@app.route("/api/jobs")
def jobs():
    keyword = request.args.get("keyword", "")
    location = request.args.get("location", "Lanciano")
    results = []

    # Indeed
    try:
        url = f"https://it.indeed.com/jobs?q={requests.utils.quote(keyword)}&l={requests.utils.quote(location)}&sort=date"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        for card in soup.select("div.job_seen_beacon")[:15]:
            title = card.select_one("h2.jobTitle span")
            company = card.select_one("span.companyName")
            loc = card.select_one("div.companyLocation")
            date = card.select_one("span.date")
            link = card.select_one("a[id^=job_]")
            results.append({
                "fonte": "Indeed",
                "titolo": title.get_text(strip=True) if title else "—",
                "azienda": company.get_text(strip=True) if company else "—",
                "luogo": loc.get_text(strip=True) if loc else location,
                "data": parse_date(date.get_text(strip=True) if date else ""),
                "data_raw": date.get_text(strip=True) if date else "",
                "link": "https://it.indeed.com" + link["href"] if link else "#",
            })
    except Exception as e:
        print(f"Indeed error: {e}")

    # Subito
    try:
        url = f"https://www.subito.it/annunci-italia/offerte-lavoro/?q={requests.utils.quote(keyword)}&r={requests.utils.quote(location.lower())}&sort=datedesc"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        for card in soup.select("article.item-card")[:15]:
            title = card.select_one("h2,h3")
            date = card.select_one("time,[class*='date']")
            link = card.select_one("a[href]")
            loc = card.select_one("[class*='city'],[class*='location']")
            results.append({
                "fonte": "Subito.it",
