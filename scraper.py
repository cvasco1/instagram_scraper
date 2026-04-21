import asyncio
import json
from playwright.async_api import async_playwright

USERNAME = "nike"

# ⚙️ CONFIGURACIÓN
INCLUIR_FIJADOS = False
CANTIDAD_POSTS = 10

# 🔧 RESPALDO MANUAL
# None = usar automático
# 0,1,2,3 = fijados manuales
FIJADOS_MANUAL = 3


async def scrape_instagram():

    print("🚀 Iniciando scraper...")

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False,
            slow_mo=50
        )

        context = await browser.new_context()

        print("🍪 Cargando cookies...")

        with open("cookies.json", "r") as file:
            cookies = json.load(file)

        await context.add_cookies(cookies)

        page = await context.new_page()

        url = f"https://www.instagram.com/{USERNAME}/"

        print("📂 Abriendo perfil...")

        await page.goto(url)

        # ⏳ Esperar carga real
        await page.wait_for_timeout(6000)

        print("🔎 Esperando publicaciones...")

        try:

            await page.wait_for_selector(
                "a[href*='/p/']",
                timeout=60000
            )

        except:

            print("❌ No se detectaron publicaciones")
            await browser.close()
            return

        print("🔎 Detectando publicaciones...")

        posts = page.locator("a[href*='/p/']")

        total = await posts.count()

        print(f"📌 Posts visibles: {total}")

        links = []

        # =========================
        # EXTRAER LINKS
        # =========================

        for i in range(total):

            try:

                link = await posts.nth(i).get_attribute("href")

                if link:

                    full_link = (
                        "https://www.instagram.com"
                        + link
                    )

                    if full_link not in links:
                        links.append(full_link)

            except:
                pass

        print(f"📌 Links únicos: {len(links)}")

        # =========================
        # DETECTAR FIJADOS AUTOMÁTICO
        # =========================

        print("📌 Detectando posts fijados (auto)...")

        posts_fijados = 0

        try:

            for i in range(min(3, total)):

                elemento = posts.nth(i)

                # Buscar icono 📌 real
                pin = elemento.locator(
                    "svg[aria-label*='Pin'], svg[aria-label*='Fij']"
                )

                cantidad = await pin.count()

                if cantidad > 0:

                    posts_fijados += 1

        except:
            pass

        print(
            f"📌 Detectados automáticamente: {posts_fijados}"
        )

        # =========================
        # RESPALDO MANUAL
        # =========================

        if (
            FIJADOS_MANUAL is not None
            and posts_fijados == 0
        ):

            posts_fijados = FIJADOS_MANUAL

            print(
                f"🛠 Usando fijados manuales: {posts_fijados}"
            )

        # =========================
        # DEFINIR RANGO
        # =========================

        if INCLUIR_FIJADOS:

            inicio = 0

        else:

            inicio = posts_fijados

        fin = inicio + CANTIDAD_POSTS

        publicaciones = links[inicio:fin]

        print("\n🔥 POSTS ENCONTRADOS 🔥\n")

        for i, link in enumerate(publicaciones):

            print(f"{i+1}. {link}")

        if len(publicaciones) == 0:

            print(
                "⚠ No se encontraron publicaciones en ese rango"
            )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_instagram())