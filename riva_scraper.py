#!/usr/bin/env python3
import os
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("=== SCRIPT DÉMARRÉ ===", flush=True)

CHANTIER = os.getenv("CHANTIER", "Riva")
MIN_LENGTH_M = float(os.getenv("MIN_LENGTH_M", "20"))
ALLOWED_CURRENCIES = {"EUR", "USD", "GBP"}
ALLOWED_LOCATIONS = [
    "italy", "france", "spain", "monaco", "turkey", "greece", "croatia",
    "portugal", "netherlands", "germany", "uk", "united kingdom",
    "cannes", "antibes", "monaco", "la spezia", "genoa", "genova",
    "marmaris", "bodrum", "istanbul", "fethiye", "nice", "porto cervo"
]

SEARCH_URLS = [
    f"https://www.yachtworld.com/boats-for-sale/make-{CHANTIER.lower()}/length-65-ft/",
    f"https://www.rightboat.com/boats-for-sale/{CHANTIER.lower()}?length_min=65",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_price(text):
    if not text:
        return None, None
    text = text.upper().replace(" ", "").replace(",", "").replace(".", "")
    match = re.search(r'(€|EUR|\$|USD|£|GBP)\s*([\d]+)', text)
    if not match:
        match = re.search(r'([\d]+)\s*(€|EUR|\$|USD|£|GBP)', text)
    if match:
        g = match.groups()
        if g[0] in ["€", "EUR", "$", "USD", "£", "GBP"]:
            currency = {"€": "EUR", "EUR": "EUR", "$": "USD", "USD": "USD", "£": "GBP", "GBP": "GBP"}[g[0]]
            price = g[1]
        else:
            price = g[0]
            currency = {"€": "EUR", "EUR": "EUR", "$": "USD", "USD": "USD", "£": "GBP", "GBP": "GBP"}[g[1]]
        return price, currency
    return None, None

def is_europe_or_turkey(location):
    if not location:
        return False
    loc = location.lower()
    return any(kw in loc for kw in ALLOWED_LOCATIONS)

def extract_length(text):
    if not text:
        return None
    m = re.search(r'([\d\.]+)\s*m', text.lower())
    if m:
        return float(m.group(1))
    ft = re.search(r'([\d\.]+)\s*(ft|\'|feet)', text.lower())
    if ft:
        return float(ft.group(1)) * 0.3048
    return None

def scrape_with_playwright(url):
    print(f"Ouverture de {url}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers(HEADERS)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)
            html = page.content()
            browser.close()
            return html
        except Exception as e:
            print(f"Erreur sur {url}: {e}", flush=True)
            browser.close()
            return None

def parse_listing(html, source_name, base_url):
    soup = BeautifulSoup(html, "lxml")
    results = []
    cards = soup.select("div.listing, div.boat-card, article, .boat-item, .yw-card, [class*='card'], [class*='listing']")
    print(f"  {len(cards)} cartes trouvées", flush=True)

    for card in cards[:40]:
        try:
            title_el = card.select_one("h2, h3, .title, .boat-name, a")
            title = title_el.get_text(strip=True) if title_el else ""
            if CHANTIER.lower() not in title.lower():
                continue

            link_el = card.select_one("a[href]")
            url = urljoin(base_url, link_el["href"]) if link_el else ""

            price_el = card.select_one(".price, .boat-price, [class*=price]")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price, currency = clean_price(price_text)
            if not price or currency not in ALLOWED_CURRENCIES:
                continue

            year_match = re.search(r'(19|20)\d{2}', title + " " + card.get_text())
            year = year_match.group(0) if year_match else ""

            length = extract_length(card.get_text())
            if not length or length < MIN_LENGTH_M:
                continue

            loc_el = card.select_one(".location, .boat-location, [class*=location]")
            location = loc_el.get_text(strip=True) if loc_el else ""
            if not is_europe_or_turkey(location):
                continue

            tva = "-"
            text_lower = card.get_text().lower()
            if "vat paid" in text_lower or "tva payée" in text_lower or "iva pagata" in text_lower:
                tva = "VAT Paid"
            elif "vat unpaid" in text_lower or "ex vat" in text_lower or "tva non" in text_lower:
                tva = "VAT Unpaid / Ex VAT"

            results.append({
                "nom": title,
                "année": year,
                "prix": price,
                "devise": currency,
                "lieu": location,
                "TVA": tva,
                "source": source_name,
                "longueur": round(length, 1),
                "url": url,
                "remarque": ""
            })
        except Exception:
            continue
    return results

def main():
    print(f"=== Démarrage robot {CHANTIER} – {datetime.now()} ===", flush=True)
    all_listings = []
    seen = set()

    for search_url in SEARCH_URLS:
        print(f"Scan : {search_url}", flush=True)
        html = scrape_with_playwright(search_url)
        if not html:
            continue
        source = urlparse(search_url).netloc.replace("www.", "")
        listings = parse_listing(html, source, search_url)
        for item in listings:
            if item["url"] not in seen:
                seen.add(item["url"])
                all_listings.append(item)
                line = f"{item['nom']}|{item['année']}|{item['prix']}|{item['devise']}|{item['lieu']}|{item['TVA']}|{item['source']}|{item['longueur']}|{item['url']}|{item['remarque']}"
                print(line, flush=True)

    print(f"\n=== Terminé ===", flush=True)
    print(f"Annonces retenues : {len(all_listings)}", flush=True)
    print("Le script va rester actif 90 secondes pour que tu puisses lire les logs...", flush=True)
    time.sleep(90)

if __name__ == "__main__":
    main()
