import pytesseract
from PIL import Image
import re
from urllib.parse import quote_plus
from .base import BaseScraper
import cv2
import numpy as np

class LomasDeZamoraScraper(BaseScraper):
    URL = "https://colegiodefarmaceuticoslz.com.ar/"
    LOCALIDAD = "Lomas de Zamora"
    CONFIANZA = 3

    def fetch(self):
        ruta_imagen = "./sources/imagenes_lomas_de_zamora/01.png"  # adaptalo a tu ruta real
        imagen = cv2.imread(ruta_imagen)
        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        _, umbral = cv2.threshold(gris, 200, 255, cv2.THRESH_BINARY_INV)

        # Buscar bloques de texto (cada tabla por día)
        contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        resultados = []

        for c in sorted(contornos, key=lambda x: cv2.boundingRect(x)[1]):
            x, y, w, h = cv2.boundingRect(c)
            if h < 50 or w < 300:
                continue  # descartar ruidos chicos

            recorte = imagen[y:y+h, x:x+w]
            pil_img = Image.fromarray(cv2.cvtColor(recorte, cv2.COLOR_BGR2RGB))
            texto = pytesseract.image_to_string(pil_img, lang="spa")

            resultado_bloque = self.procesar_bloque(texto)
            resultados.extend(resultado_bloque)

        print(f"Scraping finalizado. Farmacias encontradas: {len(resultados)}")
        return resultados

    def procesar_bloque(self, texto):
        farmacias = []

        # Buscar fecha en el bloque (ej. "LUNES 02/06")
        fecha_match = re.search(r"(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO|DOMINGO)\s+\d{2}/\d{2}", texto.upper())
        fecha = fecha_match.group(0).title() if fecha_match else "Sin fecha"

        # Dividir líneas y buscar patrones por farmacia
        lineas = [l.strip() for l in texto.split("\n") if l.strip()]
        for linea in lineas:
            # Nombre + Dirección (si está en una línea)
            if re.search(r"\d{3,4}", linea):  # contiene altura calle
                nombre_dir = linea
                direccion_match = re.search(r"[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+[\d]{2,5}", nombre_dir)
                direccion = direccion_match.group(0) if direccion_match else ""
                nombre = nombre_dir.replace(direccion, "").strip("- ").strip()
                if nombre and direccion:
                    maps_link = f"https://www.google.com/maps/search/{quote_plus(direccion + ', Lomas de Zamora')}"
                    farmacias.append({
                        "fecha": fecha,
                        "nombre": nombre,
                        "direccion": direccion + ", Lomas de Zamora",
                        "telefono": "No disponible",
                        "localidad": self.LOCALIDAD,
                        "fuente": self.URL,
                        "nivel_confianza": self.CONFIANZA,
                        "mapa": maps_link
                    })
        return farmacias
