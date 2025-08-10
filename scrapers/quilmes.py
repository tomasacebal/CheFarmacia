import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseScraper
import re

class QuilmesScraper(BaseScraper):
    URL = "https://www.farmaciadeturnoahora.com.ar/de-turno/buenos-aires/quilmes"
    LOCALIDAD = "Quilmes"
    CONFIANZA = 3  # Nivel de confianza del 1 al 3

    def get_fecha_turno(self):
        ahora = datetime.now()
        hora_corte = ahora.replace(hour=8, minute=30, second=0, microsecond=0)
        if ahora < hora_corte:
            turno_fecha = ahora - timedelta(days=1)
        else:
            turno_fecha = ahora
        return turno_fecha.strftime("%d")

    def fetch(self):
        response = requests.get(self.URL)
        soup = BeautifulSoup(response.text, "html.parser")
        farmacias = []

        bloques = soup.select("div.farmacia-de-turno")
        fecha_turno = self.get_fecha_turno()

        for bloque in bloques:
            nombre = bloque.select_one("h3.titulo-farmacia-de-turno").text.strip()

            direccion_tag = bloque.select_one("span.direccion-farmacia-de-turno")
            direccion = direccion_tag.text.strip() if direccion_tag else "Dirección no disponible"

            telefono_tag = bloque.select_one("a[href^='tel:']")
            telefono = re.sub(r"[^\d+]", "", telefono_tag.text) if telefono_tag else "No disponible"

            # Coordenadas del link Apple Maps
            mapa_link_tag = bloque.select_one("a[href*='maps.apple.com']")
            coords_match = re.search(r"q=(-?\d+\.\d+),(-?\d+\.\d+)", mapa_link_tag["href"]) if mapa_link_tag else None
            if coords_match:
                lat, lon = coords_match.groups()
                maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            else:
                maps_link = f"https://www.google.com/maps/search/{direccion}+{self.LOCALIDAD}"

            farmacias.append({
                "fecha": fecha_turno,
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
