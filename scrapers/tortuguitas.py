import json
import os
from datetime import datetime
from .base import BaseScraper
from urllib.parse import quote_plus

class TortuguitasScraper(BaseScraper):
    LOCALIDAD = "Malvinas Argentinas"
    CONFIANZA = 3
    FUENTE = "https://www.malvinasargentinas.gob.ar/farmaciasturno"
    FILE_PATH = r"sources\malvinas_argentinas\farmacias_turno_tortuguitas_junio.json"

    def fetch(self):
        if not os.path.exists(self.FILE_PATH):
            print(f"[ERROR] Archivo no encontrado: {self.FILE_PATH}")
            return []

        with open(self.FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        farmacias = []
        mes = "junio"

        if mes not in data:
            print(f"[ERROR] Mes '{mes}' no encontrado en el JSON")
            return []

        localidades = data[mes]

        for zona, contenido in localidades.items():
            for dia, lista in contenido.get("dias", {}).items():
                for f in lista:
                    direccion = f.get("direccion", "").strip()
                    telefono = f.get("telefono", "").strip()
                    nombre = f.get("nombre", "").strip()
                    direccion_completa = f"{direccion}, {zona}"
                    mapa = f"https://www.google.com/maps/search/{quote_plus(nombre + ' ' + direccion_completa)}"

                    farmacias.append({
                        "fecha": dia,
                        "nombre": nombre,
                        "direccion": direccion,
                        "telefono": telefono,
                        "localidad": self.LOCALIDAD,
                        "fuente": self.FUENTE,
                        "nivel_confianza": self.CONFIANZA,
                        "mapa": mapa
                    })

        print(f"[TORTUGUITAS] Farmacias cargadas desde archivo: {len(farmacias)}")
        return farmacias
