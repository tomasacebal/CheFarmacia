# --- START OF FILE scrapers/mar_del_plata.py ---

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseScraper
from utils import generar_link_mapa, limpiar_telefono

class MarDelPlataScraper(BaseScraper):
    URL = "http://www.colfarmamdp.com.ar/"
    LOCALIDAD = "Mar del Plata"
    CONFIANZA = 3

    def get_fecha_turno(self):
        """
        Determina el día del turno. El turno farmacéutico generalmente
        cambia por la mañana (ej. 8:30 AM).
        """
        ahora = datetime.now()
        # Asumimos que el turno cambia a las 8:30 AM
        hora_corte = ahora.replace(hour=8, minute=30, second=0, microsecond=0)
        
        if ahora < hora_corte:
            # Si es antes de las 8:30, el turno corresponde al día anterior
            turno_fecha = ahora - timedelta(days=1)
        else:
            # Si es después, corresponde al día actual
            turno_fecha = ahora
            
        # .day devuelve un entero, str() lo convierte sin ceros a la izquierda
        return str(turno_fecha.day)

    def fetch(self) -> list[dict]:
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener la página de Mar del Plata: {e}")
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        farmacias = []
        
        fecha_turno = self.get_fecha_turno()

        # Seleccionamos todas las filas con la clase 'trturnos'
        rows = soup.select("tr.trturnos")

        for row in rows:
            # Obtenemos todas las celdas (td) de la fila
            cells = row.find_all("td")
            
            # Verificamos que la fila tenga la estructura esperada (al menos 4 celdas)
            if len(cells) < 4:
                continue

            # Extraemos los datos basándonos en el índice de la celda
            # Celda 0: Letra (A, B, C...) - la ignoramos
            # Celda 1: Nombre de la farmacia
            # Celda 2: Dirección
            # Celda 3: Teléfono
            nombre = cells[1].text.strip()
            direccion_raw = cells[2].text.strip()
            telefono_raw = cells[3].text.strip()

            # Limpiamos y estandarizamos los datos
            telefono_limpio = limpiar_telefono(telefono_raw)
            
            # La dirección puede incluir "BATAN", que es una localidad dentro del partido.
            # Lo mantenemos, y agregamos Mar del Plata para el contexto general.
            if "BATAN" in direccion_raw.upper():
                 # Si la dirección ya especifica Batán, la respetamos.
                direccion_completa = f"{direccion_raw}, Provincia de Buenos Aires"
            else:
                direccion_completa = f"{direccion_raw}, {self.LOCALIDAD}, Provincia de Buenos Aires"

            farmacias.append({
                "fecha": fecha_turno,
                "nombre": nombre,
                "direccion": direccion_completa,
                "telefono": telefono_limpio,
                "localidad": self.LOCALIDAD,
                "fuente": self.URL,
                "nivel_confianza": self.CONFIANZA,
                "mapa": generar_link_mapa(direccion_completa)
            })

        print(f"Scraping de Mar del Plata finalizado. Farmacias encontradas: {len(farmacias)}")
        return farmacias