#!/usr/bin/env python3
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
    "istanbul", "fethiye", "balearic", "spain", "norway", "switzerland",
    "giesbeek", "netherlands"
]

SEARCH_URL = "https://www.rightboat.com/boats-for-sale/riva?length_min=65"

def clean_price(text):
    if not text or "POA" in text.upper() or "Request" in text:
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
    # Cherche en mètres
    m = re.search(r'([\d\.]+)\s*m', text.lower())
    if m:
        return float(m.group(1))
    # Cherche en pieds
    ft = re.search(r'([\d\.]+)\s*(ft|feet|\')', text.lower())
    if ft:
        return float(ft.group(1)) * 0.3048
    return None

def is_europe_or_turkey(location):
    if not location:
        return False
    loc = location.lower()
    return any(kw in loc for kw in ALLOWED_LOCATIONS)

def scrape_rightboat():
    print(f"Ouverture de {SEARCH_URL}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = 
