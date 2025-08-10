import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper
from urllib.parse import quote_plus
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class VarelaScraper(BaseScraper):
    URL = "https://www.varela.gov.ar/farmaciasdeturno/"
    LOCALIDAD = "Florencio Varela"
    CONFIANZA = 3  # Nivel de confianza del 1 al 3

    def fetch(self):
        session = requests.Session()
        retries = Retry(
            total=5,              # reintenta hasta 5 veces
            backoff_factor=1,     # espera exponencial: 1s, 2s, 4s, etc.
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            response = session.get(self.URL, timeout=15)  # timeout de 15 segundos
        except requests.exceptions.RequestException as e:
            print(f"Error al acceder a {self.URL}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("div.card")
        farmacias = []

        fecha = str(datetime.now().day)  # Día actual

        for card in cards:
            nombre_tag = card.select_one("h5.card-title")
            direccion_tag = card.select_one("div.card-footer small")
            iframe_tag = card.select_one("iframe")

            if not nombre_tag or not direccion_tag:
                continue

            nombre = nombre_tag.text.strip()
            direccion = direccion_tag.text.strip()
            telefono = ""  # No disponible

            if iframe_tag and "src" in iframe_tag.attrs:
                mapa = iframe_tag["src"]
            else:
                mapa = f"https://www.google.com/maps/search/{quote_plus(direccion)}+{quote_plus(self.LOCALIDAD)}"

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
