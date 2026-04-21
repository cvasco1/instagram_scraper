import asyncio
import json
import os
import requests
import re
import csv
from datetime import datetime

from playwright.async_api import async_playwright

# =========================
# CONFIG
# =========================

USERNAME = "latriecu"
CANTIDAD_POSTS = 5

COOKIES_FILE = "cookies.json"

DATA_DIR = "instagram_data"
IMG_DIR = f"{DATA_DIR}/media"

CSV_PATH = f"{DATA_DIR}/posts.csv"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# =========================
# DESCARGA
# =========================

def descargar_archivo(url, filename):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        if r.status_code == 200:

            with open(filename, "wb") as f:
                f.write(r.content)

            return True

    except Exception as e:

        print("⚠️ Error descarga:", e)

    return False


# =========================
# EXTRAER MEDIA
# =========================

async def obtener_media_real(page):

    media_urls = []

    await page.wait_for_timeout(3000)

    html = await page.content()

    try:

        # VIDEO

        videos = re.findall(
            r'"video_versions".*?"url":"(https:[^"]+)"',
            html,
            re.DOTALL
        )

        if videos:

            for v in videos:

                v = v.replace("\\/", "/")

                if v not in media_urls:
                    media_urls.append(v)

            return media_urls


        # CARRUSEL

        carousel = re.findall(
            r'"carousel_media":\[(.*?)\]',
            html,
            re.DOTALL
        )

        if carousel:

            urls = re.findall(
                r'"url":"(https:[^"]+)"',
                carousel[0]
            )

            for u in urls:

                u = u.replace("\\/", "/")

                if u not in media_urls:
                    media_urls.append(u)

            return media_urls


        # IMAGEN SIMPLE

        simple_imgs = re.findall(
            r'"image_versions2".*?"url":"(https:[^"]+)"',
            html,
            re.DOTALL
        )

        for url in simple_imgs:

            url = url.replace("\\/", "/")

            if url not in media_urls:

                media_urls.append(url)
                break

    except Exception as e:

        print("⚠️ Error media:", e)

    return media_urls


# =========================
# EXTRAER TEXTO BASICO
# =========================

def parsear_texto(html):

    caption = "NA"
    likes = 0
    comentarios = 0
    fecha = "NA"

    try:

        cap = re.search(
            r'"caption":\{"text":"(.*?)"',
            html,
            re.DOTALL
        )

        if cap:

            caption = cap.group(1)
            caption = caption.replace("\\n", " ")


        like = re.search(
            r'"like_count":(\d+)',
            html
        )

        if like:
            likes = int(like.group(1))


        com = re.search(
            r'"comment_count":(\d+)',
            html
        )

        if com:
            comentarios = int(com.group(1))


        date_match = re.search(
            r'"taken_at":(\d+)',
            html
        )

        if date_match:

            timestamp = int(date_match.group(1))

            fecha = datetime.fromtimestamp(
                timestamp
            ).strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:

        print("⚠️ Error parse texto:", e)

    return (
        caption,
        likes,
        comentarios,
        fecha
    )


# =========================
# EXTRAER COMENTARIOS REALES
# =========================

async def obtener_comentarios_reales(page, caption):

    comentarios = []

    try:

        await page.wait_for_timeout(3000)

        html = await page.content()

        # Buscar comentarios dentro del JSON interno

        textos = re.findall(
            r'"text":"(.*?)"',
            html
        )

        for texto in textos:

            texto = texto.replace("\\n", " ")
            texto = texto.replace("\\u00f3", "ó")

            texto = texto.strip()

            # Evitar caption
            if texto == caption:
                continue

            # Evitar textos muy cortos
            if len(texto) < 5:
                continue

            # Evitar duplicados
            if texto not in comentarios:

                comentarios.append(texto)

            if len(comentarios) >= 5:
                break

    except Exception as e:

        print("⚠️ Error comentarios:", e)

    return comentarios


# =========================
# SCROLL PERFIL
# =========================

async def scroll_profile(page):

    prev = 0

    while True:

        posts = page.locator("a[href*='/p/']")

        count = await posts.count()

        print("Posts visibles:", count)

        if count >= CANTIDAD_POSTS:
            break

        if count == prev:
            break

        prev = count

        await page.mouse.wheel(0, 8000)

        await page.wait_for_timeout(2500)


# =========================
# LINKS
# =========================

async def get_links(page):

    posts = page.locator("a[href*='/p/']")

    total = await posts.count()

    links = []

    for i in range(total):

        href = await posts.nth(i).get_attribute("href")

        if href:

            full = "https://www.instagram.com" + href

            if full not in links:
                links.append(full)

    return links[:CANTIDAD_POSTS]


# =========================
# SCRAP POST
# =========================

async def scrape_post(context, link, index):

    page = await context.new_page()

    print("\n📷 Abriendo:", link)

    await page.goto(link)

    await page.wait_for_timeout(5000)

    # 🔥 NUEVO — SCROLL PARA CARGAR COMENTARIOS

    for _ in range(6):

        await page.mouse.wheel(0, 4000)
        await page.wait_for_timeout(2000)

    html = await page.content()

    (
        caption,
        likes,
        comentarios,
        fecha
    ) = parsear_texto(html)

    # MEDIA

    media_urls = await obtener_media_real(page)

    # COMENTARIOS

    comentarios_texto = await obtener_comentarios_reales(
        page,
        caption
    )

    print(f"📅 Fecha: {fecha}")
    print(f"❤️ Likes: {likes}")
    print(f"💬 Comentarios: {comentarios}")
    print(f"🎞 Media detectada: {len(media_urls)}")
    print(f"📝 Comentarios capturados: {len(comentarios_texto)}")

    media_guardada = []

    for i, url in enumerate(media_urls):

        tipo = "video" if ".mp4" in url else "image"

        ext = ".mp4" if tipo == "video" else ".jpg"

        filename = f"{IMG_DIR}/post_{index}_{i}{ext}"

        if descargar_archivo(url, filename):

            media_guardada.append(filename)

    await page.close()

    return {
        "link": link,
        "fecha": fecha,
        "caption": caption,
        "likes": likes,
        "comentarios": comentarios,
        "media": media_guardada,
        "comentarios_texto": comentarios_texto
    }


# =========================
# EXPORT CSV
# =========================

def exportar_csv(dataset):

    with open(
        CSV_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "link",
            "fecha",
            "caption",
            "likes",
            "comentarios"
        ])

        for d in dataset:

            writer.writerow([
                d["link"],
                d["fecha"],
                d["caption"],
                d["likes"],
                d["comentarios"]
            ])


# =========================
# MAIN
# =========================

async def scrape_instagram():

    dataset = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False
        )

        context = await browser.new_context()

        print("🍪 Cargando cookies...")

        with open(COOKIES_FILE) as f:
            cookies = json.load(f)

        await context.add_cookies(cookies)

        page = await context.new_page()

        url = f"https://www.instagram.com/{USERNAME}/"

        await page.goto(url)

        await page.wait_for_timeout(4000)

        await scroll_profile(page)

        links = await get_links(page)

        print("Links:", len(links))

        for i, link in enumerate(links):

            data = await scrape_post(
                context,
                link,
                i+1
            )

            dataset.append(data)

        await browser.close()

    with open(
        f"{DATA_DIR}/posts.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            dataset,
            f,
            indent=4,
            ensure_ascii=False
        )

    exportar_csv(dataset)

    print("\n✅ SCRAPER COMPLETO FUNCIONANDO")


# =========================

if __name__ == "__main__":

    asyncio.run(scrape_instagram())