import os
from dotenv import load_dotenv
from tqdm import tqdm
from scrapers.san_isidro import SanIsidroScraper
from utils import save_to_json, commit_and_push, format_data_for_json

def main():
    load_dotenv()

    scraper = SanIsidroScraper()
    data = scraper.fetch()

    data_formateada = format_data_for_json(data)
    save_to_json(data_formateada)

    json_path = os.getenv("JSON_PATH")
    repo_path = os.getenv("GITHUB_REPO_PATH")
    commit_message = f"Actualización automática del archivo JSON (localidad: {scraper.LOCALIDAD})"
    
    if json_path and repo_path:
        commit_and_push(repo_path, json_path, commit_message)
    else:
        print("Faltan las variables JSON_PATH o GITHUB_REPO_PATH en el .env")

if __name__ == "__main__":
    main()
