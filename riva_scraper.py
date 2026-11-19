#!/usr/bin/env python3
import time
import re
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("=== SCRIPT DEMARRE ===", flush=True)

SEARCH_URL = "https://www.rightboat.com/boats-for-sale/riva?length_min=65"
MIN_LENGTH_M = 20.0

def clean_price(text):
    if not text or "POA" in text.upper() or "Request" in text:
        return None, None
    text = text.upper().replace(" ", "").replace(",", "").replace(".", "")
    match = re.search(r'(EUR|USD|GBP|€|\$|£)\s*(\d+)', text)
    if not match:
        match = re.search(r'(\d+)\s*(EUR|USD|GBP|€|\$|£)', text)
    if match:
        g = match.groups()
        mapping = {"€": "EUR", "EUR": "EUR", "$": "USD", "USD": "USD", "£": "GBP", "GBP": "GBP"}
        if g[0] in mapping:
            return g[1], mapping[g[0]]
        return g[0], mapping.get(g[1], g[1])
    return None, None

def extract_length(text):
    m = re.search(r'(\d+\.?\d*)\s*m', text.lower())
    if m:
        return float(m.group(1))
    ft = re.search(r'(\d+\.?\d*)\s*(ft|feet|\')', text.lower())
    if ft:
        return float(ft.group(1)) * 0.3048
    return None

def is_europe_or_turkey(location):
    if not location:
        return False
    keywords = ["italy", "france", "spain", "monaco", "turkey", "greece", "croatia", "portugal", "netherlands", "germany", "uk", "united kingdom", "giesbeek"]
    return any(k in location.lower() for k in keywords)

def main():
    print("Ouverture de Rightboat...", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "lxml")
    full_text = soup.get_text("\n", strip=True)
    print(f"Longueur du texte de la page: {len(full_text)} caracteres", flush=True)

    # Cherche les blocs qui contiennent "Riva" et un prix
    lines = full_text.split("\n")
    results = []
    current_block = []

    for line in lines:
        if "riva" in line.lower() or any(x in line for x in ["$", "€", "£", "USD", "EUR", "GBP"]):
            current_block.append(line)
        else:
            if current_block:
                block = " ".join(current_block)
                if "riva" in block.lower():
                    # Extraction
                    price_match = re.search(r'([$€£]|EUR|USD|GBP)\s*[\d,\.]+|[\d,\.]+\s*([$€£]|EUR|USD|GBP)', block)
                    price, currency = clean_price(price_match.group(0) if price_match else "")
                    if price and currency in ["EUR", "USD", "GBP"]:
                        year_match = re.search(r'(19|20)\d{2}', block)
                        year = year_match.group(0) if year_match else ""
                        length = extract_length(block)
                        if length and length >= MIN_LENGTH_M:
                            loc_match = re.search(r'(Italy|France|Spain|Monaco|Turkey|Greece|Croatia|Portugal|Netherlands|Germany|UK|United Kingdom|Giesbeek)', block, re.I)
                            location = loc_match.group(0) if loc_match else ""
                            if is_europe_or_turkey(location) and "sold" not in block.lower():
                                title = next((l for l in current_block if "riva" in l.lower()), "Riva")
                                line_out = f"{title}|{year}|{price}|{currency}|{location}|-|rightboat.com|{round(length,1)}|{SEARCH_URL}|"
                                print(line_out, flush=True)
                                results.append(line_out)
                current_block = []

    print(f"=== Termine - {len(results)} annonces ===", flush=True)
    time.sleep(60)

if __name__ == "__main__":
    main()
