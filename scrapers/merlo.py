import requests
from bs4 import BeautifulSoup
import re
from .base import BaseScraper
from urllib.parse import quote

class MerloScraper(BaseScraper):
    URL = "https://www.merlo.gob.ar/project/farmaciasdeturno/"
    LOCALIDAD = "Merlo"
    CONFIANZA = 2

    def fetch(self):
        response = requests.get(self.URL)
        soup = BeautifulSoup(response.text, "html.parser")

        bloques = soup.select("div.et_pb_toggle_content")
        farmacias = []

        for bloque in bloques:
            fecha_actual = None
            for p in bloque.find_all("p"):
                texto = p.get_text(strip=True)

                # Detectar la fecha
                match_fecha = re.match(r"^(?:Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+(\d{1,2})$", texto)
                if match_fecha:
                    fecha_actual = match_fecha.group(1)
                    continue

                # Detectar farmacia
                match_farmacia = re.match(r"^(.*?)\s+–\s+(.*)$", texto)
                if fecha_actual and match_farmacia:
                    nombre = match_farmacia.group(1).strip()
                    direccion = f"{match_farmacia.group(2).strip()}, {self.LOCALIDAD}"

                    farmacias.append({
                        "fecha": fecha_actual,
                        "nombre": nombre,
                        "direccion": direccion,
                        "telefono": "",
                        "localidad": self.LOCALIDAD,
                        "fuente": self.URL,
                        "nivel_confianza": self.CONFIANZA,
                        "mapa": f"https://www.google.com/maps/search/{quote(direccion)}"
                    })

        print(f"Scraping finalizado. Farmacias encontradas: {len(farmacias)}")
        return farmacias
