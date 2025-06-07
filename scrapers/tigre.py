import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from .base import BaseScraper
from urllib.parse import quote_plus
import re

class TigreScraper(BaseScraper):
    URL = "https://www.tigre.gob.ar/salud/farmacias"
    LOCALIDAD = "Tigre"
    CONFIANZA = 3  # Nivel de confianza del 1 al 3

    def fetch(self):
        response = requests.get(self.URL, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        farmacias = []

        items = soup.select("li")

        for item in items:
            nombre_tag = item.find("p", class_="farm")
            direccion_tag = item.find("p", class_="dir")
            telefono_tag = item.find("p", class_="tel")
            mapa_tag = item.find("a", class_="text-rojo")

            if not (nombre_tag and direccion_tag and telefono_tag and mapa_tag):
                continue

            nombre = nombre_tag.get_text(strip=True)
            direccion = direccion_tag.get_text(strip=True)
            telefono = re.sub(r"[^\d+]", "", telefono_tag.get_text(strip=True))
            mapa = mapa_tag["href"]

            # La fecha corresponde al día actual, ya que es una lista que se actualiza diariamente
            fecha = str(date.today().day)

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

        print(f"Scraping finalizado. Farmacias encontradas: {len(farmacias)}")
        return farmacias
