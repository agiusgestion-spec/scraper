#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("=== SCRIPT DEMARRE ===", flush=True)

url = "https://www.rightboat.com/boats-for-sale/riva?length_min=65"

print("Ouverture de la page...", flush=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=60000)
    time.sleep(5)
    html = page.content()
    browser.close()

print("Page chargee, analyse en cours...", flush=True)
soup = BeautifulSoup(html, "lxml")
print(f"Titre de la page: {soup.title.string if soup.title else 'Aucun'}", flush=True)

# Affiche un extrait pour debug
text = soup.get_text()[:2000]
print("--- Extrait du texte ---", flush=True)
print(text, flush=True)
print("--- Fin extrait ---", flush=True)

print("Script termine. Attente 60s...", flush=True)
time.sleep(60)
