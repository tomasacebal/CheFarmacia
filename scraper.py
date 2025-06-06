import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pygit2 import Repository, Signature

load_dotenv()

GITHUB_REPO_PATH = os.getenv("GITHUB_REPO_PATH")
GITHUB_REMOTE = os.getenv("GITHUB_REMOTE")
JSON_PATH = os.getenv("JSON_PATH")

def scrape_farmacias():
    url = "https://colfarma.info/colfarmasanisidro/farmacias-de-turno/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    farmacias_por_dia = {}

    for dia_td in soup.select("td.simcal-day-has-events"):
        dia = dia_td.select_one(".simcal-day-number")
        if not dia:
            continue
        dia_num = dia.text.strip()
        eventos = dia_td.select("li.simcal-event")
        eventos_info = []

        for evento in eventos:
            nombre = evento.select_one("span.simcal-event-title")
            direccion = evento.select_one("span.simcal-event-address")
            telefono_tag = evento.select_one("div.simcal-event-description")
            telefono = None
            if telefono_tag:
                tel_line = telefono_tag.get_text(separator="\n").split("\n")
                for line in tel_line:
                    if "✆" in line:
                        telefono = line.replace("✆", "").strip()
                        break

            eventos_info.append({
                "nombre": nombre.text.strip() if nombre else None,
                "dirección": direccion.text.strip() if direccion else None,
                "teléfono": telefono
            })

        fecha = f"Junio {dia_num}"  # Podés modificar para usar datetime real
        farmacias_por_dia[fecha] = eventos_info

    return farmacias_por_dia

def save_to_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def push_to_git(repo_path, file_path, commit_msg="Actualización de farmacias de turno"):
    repo = Repository(repo_path)
    index = repo.index
    index.add(file_path)
    index.write()

    author = Signature("AutoScraper", "scraper@colfarma.bot")
    tree = index.write_tree()

    if repo.head_is_unborn:
        parents = []
    else:
        parents = [repo.head.target]

    commit = repo.create_commit(
        'refs/heads/main',
        author,
        author,
        commit_msg,
        tree,
        parents
    )

    remote = repo.remotes["origin"]
    callbacks = repo.remotes.create_anonymous(GITHUB_REMOTE).credentials
    remote.push(["refs/heads/main:refs/heads/main"])

if __name__ == "__main__":
    data = scrape_farmacias()
    save_to_json(data, JSON_PATH)
    push_to_git(GITHUB_REPO_PATH, JSON_PATH)
    print("Scraping y subida a GitHub completados.")
