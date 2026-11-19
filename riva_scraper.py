#!/usr/bin/env python3
import time
import re
from datetime import datetime
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("=== SCRIPT DEMARRE ===", flush=True)

SEARCH_URL = "https://www.rightboat.com/boats-for-sale/riva?length_min=65"
MIN_LENGTH_M = 20.0

def clean_price(text):
    if not text or "POA" in text.upper():
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
    loc = location.lower()
    return any(k in loc for k in keywords)

def main():
    print("Ouverture de Rightboat...", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
