import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseScraper
import re

class SanBernardoScraper(BaseScraper):
    URL = "https://www.farmaciadeturnoahora.com.ar/directorio-de-farmacias/buenos-aires/la-costa/san-bernardo"
    LOCALIDAD = "San Bernardo"
    CONFIANZA = 1  # Nivel de confianza del 1 al 3

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

            from urllib.parse import unquote

            mapa_link_tag = bloque.select_one("a[href*='maps.apple.com']")
            coords_match = None

            if mapa_link_tag:
                href = mapa_link_tag.get("href", "")
                href_decoded = unquote(href)

                # Buscar formato ?q=lat,lon
                coords_match = re.search(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)", href_decoded)

                # Buscar formato ?coordinate=lat,lon
                if not coords_match:
                    coords_match = re.search(r"[?&]coordinate=(-?\d+\.\d+),(-?\d+\.\d+)", href_decoded)

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
