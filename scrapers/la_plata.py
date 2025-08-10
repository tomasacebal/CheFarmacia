import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseScraper
import re

class LaPlataScraper(BaseScraper):
    URL = "https://www.colfarmalp.org.ar/turnos-la-plata/"
    LOCALIDAD = "La Plata"
    CONFIANZA = 3  # Nivel de confianza del 1 al 3

    def fetch(self):
        response = requests.get(self.URL)
        soup = BeautifulSoup(response.text, "html.parser")
        bloques = soup.select("div.td")

        farmacias = []
        i = 0
        while i + 4 < len(bloques):
            if "Farmacia" in bloques[i].text:
                nombre = bloques[i].get_text(strip=True).replace("Farmacia", "").strip()
                direccion = bloques[i + 1].get_text(strip=True).replace("Dirección", "").strip()
                zona = bloques[i + 2].get_text(strip=True).replace("Zona", "").strip()
                telefono = bloques[i + 3].get_text(strip=True).replace("Teléfono", "").strip()

                link_mapa_tag = bloques[i + 4].find("a")
                mapa = link_mapa_tag["href"] if link_mapa_tag else ""

                # Solo si nombre y dirección están presentes, agregamos
                if nombre and direccion:
                    ahora = datetime.now()
                    if ahora.hour < 8 or (ahora.hour == 8 and ahora.minute < 30):
                        fecha = (ahora - timedelta(days=1)).strftime("%d")
                    else:
                        fecha = ahora.strftime("%d")

                    farmacias.append({
                        "fecha": fecha,
                        "nombre": nombre,
                        "direccion": direccion,
                        "telefono": telefono,
                        "localidad": self.LOCALIDAD,
                        "fuente": self.URL,
                        "nivel_confianza": self.CONFIANZA,
                        "mapa": mapa
                    })
                else:
                    print(f"[SALTEADO] Bloque con datos incompletos en índice {i}: {nombre=} {direccion=}")

                i += 5
            else:
                i += 1

        print(f"Scraping finalizado. Farmacias encontradas: {len(farmacias)}")
        return farmacias
