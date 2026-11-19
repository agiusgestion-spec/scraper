#!/usr/bin/env python3
import os
import time
import re
from datetime import datetime
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("=== SCRIPT DÉMARRÉ ===", flush=True)

CHANTIER = "Riva"
MIN_LENGTH_M = 20.0
ALLOWED_CURRENCIES = {"EUR", "USD", "GBP"}
ALLOWED_LOCATIONS = [
    "italy", "france", "spain", "monaco", "turkey", "greece", "croatia",
    "portugal", "netherlands", "germany", "uk", "united kingdom",
    "cannes", "antibes", "nice", "genoa", "genova", "marmaris", "bodrum",
    "istanbul", "fethiye", "balearic", "spain", "norway", "switzerland"
]

SEARCH_URL = "https://www.theyachtmarket.com/en/boats-for-sale/riva/"

def clean_price(text):
    if not text or "POA" in text.upper():
        return None, None
    text = text.upper().replace(" ", "").replace(",", "").replace(".", "")
    match = re.search(r'(€|EUR|\$|USD|£|GBP)\s*([\d]+)', text)
    if not match:
        match = re.search(r'([\d]+)\s*(€|EUR|\$|USD|£|GBP)', text)
    if match:
        g = match.groups()
        mapping = {"€": "EUR", "EUR": "EUR", "$": "USD", "USD": "USD", "£": "GBP", "GBP": "GBP"}
        if g[0] in mapping:
            return g[1], mapping[g[0]]
        else:
            return g[0], mapping[g[1]]
    return None, None

def extract_length(text):
    m = re.search(r'([\d\.]+)\s*m', text.lower())
    if m:
        return float(m.group(1))
    return None

def is_europe_or_turkey(location):
    if not location:
        return False
    loc = location.lower()
    return any(kw in loc for kw in ALLOWED_LOCATIONS)

def scrape_theyachtmarket():
    print(f"Ouverture de {SEARCH_URL}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        try:
            page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            html = page.content()
            browser.close()
            return html
        except Exception as e:
            print(f"Erreur : {e}", flush=True)
            browser.close()
            return None

def parse_theyachtmarket(html):
    soup = BeautifulSoup(html, "lxml")
    results = []

    # Cherche les blocs de listings (h3 avec liens)
    listings = soup.find_all("h3")
    print(f"  {len(listings)} titres h3 trouvés", flush=True)

    for h3 in listings:
        try:
            link = h3.find("a")
            if not link:
                continue
            title = link.get_text(strip=True)
            if "riva" not in title.lower():
                continue

            url = urljoin(SEARCH_URL, link.get("href", ""))

            # Le bloc parent contient le reste des infos
            parent = h3.find_parent()
            text = parent.get_text(" ", strip=True) if parent else ""

            # Prix
            price_match = re.search(r'([$€£]|EUR|USD|GBP)\s*[\d,\.]+|[\d,\.]+\s*([$€£]|EUR|USD|GBP)', text)
            price_text = price_match.group(0) if price_match else ""
            price, currency = clean_price(price_text)
            if not price or currency not in ALLOWED_CURRENCIES:
                continue

            # Année
            year_match = re.search(r'(19|20)\d{2}', text)
            year = year_match.group(0) if year_match else ""

            # Longueur
            length = extract_length(text)
            if not length or length < MIN_LENGTH_M:
                continue

            # Lieu (souvent juste avant le prix ou après le titre)
            loc_match = re.search(r'(Italy|France|Spain|Monaco|Turkey|Greece|Croatia|Portugal|Netherlands|Germany|United Kingdom|UK|Balearic|Norway|Switzerland)', text, re.I)
            location = loc_match.group(0) if loc_match else ""
            if not is_europe_or_turkey(location):
                continue

            # TVA
            tva = "-"
            if "tax paid" in text.lower() or "tva payée" in text.lower():
                tva = "VAT Paid"
            elif "tax not paid" in text.lower() or "excluded" in text.lower():
                tva = "VAT Unpaid / Ex VAT"

            # Ignore sold
            if "sold" in text.lower():
                continue

            results.append({
                "nom": title,
                "année": year,
                "prix": price,
                "devise": currency,
                "lieu": location,
                "TVA": tva,
                "source": "theyachtmarket.com",
                "longueur": round(length, 1),
                "url": url,
                "remarque": ""
            })
        except Exception as e:
            continue

    return results

def main():
    print(f"=== Démarrage robot {CHANTIER} – {datetime.now()} ===", flush=True)
    html = scrape_theyachtmarket()
    if not html:
        print("Impossible de charger la page", flush=True)
        time.sleep(30)
        return

    listings = parse_theyachtmarket(html)
    print(f"\n=== Résultats ({len(listings)}) ===", flush=True)
    for item in listings:
        line = f"{item['nom']}|{item['année']}|{item['prix']}|{item['devise']}|{item['lieu']}|{item['TVA']}|{item['source']}|{item['longueur']}|{item['url']}|{item['remarque']}"
        print(line, flush=True)

    print(f"\nAnnonces retenues : {len(listings)}", flush=True)
    print("Script actif 90 secondes...", flush=True)
    time.sleep(90)

if __name__ == "__main__":
    main()
