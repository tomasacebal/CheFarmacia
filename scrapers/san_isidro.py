import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper
from urllib.parse import quote_plus
import re

class SanIsidroScraper(BaseScraper):
    URL = "https://colfarma.info/colfarmasanisidro/farmacias-de-turno/"
    LOCALIDAD = "San Isidro"
    CONFIANZA = 3  # Nivel de confianza del 1 al 3

    def fetch(self):
        response = requests.get(self.URL)
        soup = BeautifulSoup(response.text, "html.parser")
        farmacias = []

        days = soup.select("td.simcal-day-has-events")

        for dia in days:
            fecha = dia.select_one("span.simcal-day-label").text.strip()
            eventos = dia.select("li.simcal-event")

            for evento in eventos:
                nombre = evento.select_one("span.simcal-event-title").text.strip()

                detalles = evento.select_one("div.simcal-event-details")
                
                # Dirección
                raw_direccion = detalles.select_one("span.simcal-event-address").text if detalles else ""
                direccion = raw_direccion.strip()
                direccion = re.sub(r"^[A-Z]{3},\s*", "", direccion)

                # Teléfono
                telefono = "No disponible"
                telefono_tag = evento.select_one("div.simcal-event-description")
                if telefono_tag:
                    for line in telefono_tag.get_text(separator="\n").split("\n"):
                        if "✆" in line or "Tel" in line:
                            telefono = re.sub(r"[^\d+]", "", line)  # Solo dejamos números y +
                            break


                # Google Maps link
                maps_link = f"https://www.google.com/maps/search/{quote_plus(direccion)}+{quote_plus(self.LOCALIDAD)}"

                farmacias.append({
                    "fecha": fecha,
                    "nombre": nombre,
                    "direccion": direccion,
                    "telefono": telefono,
                    "localidad": self.LOCALIDAD,
                    "fuente": self.URL,
                    "nivel_confianza": self.CONFIANZA,
                    "mapa": maps_link
                })

        print(f"Scraping finalizado. Farmacias encontradas: {len(farmacias)}")
        return farmacias