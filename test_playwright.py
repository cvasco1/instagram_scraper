from playwright.sync_api import sync_playwright

print("Iniciando prueba...")

with sync_playwright() as p:
    print("Abriendo navegador...")

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    print("Abriendo Google...")

    page.goto("https://www.google.com")

    print("Playwright funciona correctamente ✅")

    browser.close()