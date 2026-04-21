import json

def convertir_cookies():

    cookies = []

    with open("cookies.txt", "r", encoding="utf-8") as f:

        for line in f:

            if line.startswith("#"):
                continue

            parts = line.strip().split("\t")

            if len(parts) >= 7:

                cookie = {
                    "domain": parts[0],
                    "path": parts[2],
                    "secure": parts[3] == "TRUE",
                    "name": parts[5],
                    "value": parts[6]
                }

                cookies.append(cookie)

    with open("cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)

    print("✅ Cookies convertidas correctamente")


convertir_cookies()