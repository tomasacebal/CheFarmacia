import os
from dotenv import load_dotenv
from tqdm import tqdm

from scrapers.san_isidro import SanIsidroScraper
from scrapers.tigre import TigreScraper
from scrapers.lomas_de_zamora import LomasDeZamoraScraper

from utils import save_to_json, commit_and_push, format_data_for_json

def main():
    load_dotenv()

    # Lista de scrapers a ejecutar
    scrapers = [
        SanIsidroScraper(),
        TigreScraper(),
        # LomasDeZamoraScraper()
    ]

    from utils import merge_data  # Asegurate de tener esto arriba

    datos_combinados = {}

    for scraper in tqdm(scrapers, desc="Ejecutando scrapers"):
        print(f"\n[INFO] Ejecutando scraper para: {scraper.LOCALIDAD}")
        datos = scraper.fetch()
        datos_formateados = format_data_for_json(datos)
        datos_combinados = merge_data(datos_combinados, datos_formateados)


    # Guardar toda la info unificada
    FILENAME = "data/farmacias_turno.json"
    save_to_json(datos_combinados)

    # Hacer commit y push
    repo_path = os.getenv("GITHUB_REPO_PATH")
    json_path = FILENAME if repo_path else None
    commit_message = "Actualización automática del archivo JSON (todas las localidades)"

    if json_path and repo_path:
        commit_and_push(repo_path, json_path, commit_message)
    else:
        print("[ADVERTENCIA] Faltan las variables JSON_PATH o GITHUB_REPO_PATH en el .env")

if __name__ == "__main__":
    main()
