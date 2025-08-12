import os
import subprocess
import sys
from dotenv import load_dotenv

# Importamos la función principal del otro script
from run_scrapers import run_all_scrapers

def pull_latest_changes():
    """
    Ejecuta 'git pull' en el directorio del repositorio para obtener los últimos cambios.
    """
    load_dotenv()
    repo_path = os.getenv("GITHUB_REPO_PATH")

    if not repo_path:
        print("[ERROR] La variable de entorno GITHUB_REPO_PATH no está definida.")
        print("Asegúrate de que tu archivo .env contenga la ruta al repositorio.")
        sys.exit(1)

    if not os.path.isdir(os.path.join(repo_path, '.git')):
        print(f"[ERROR] La ruta '{repo_path}' no parece ser un repositorio de Git válido.")
        sys.exit(1)
        
    print(f"[INFO] Actualizando el repositorio en: {repo_path}")

    try:
        # Usamos subprocess.run para ejecutar el comando git pull
        # check=True lanzará una excepción si el comando falla (retorna un código != 0)
        # cwd especifica el directorio de trabajo donde se ejecutará el comando
        # capture_output=True para capturar stdout y stderr
        result = subprocess.run(
            ['git', 'pull'],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True # Decodifica stdout/stderr como texto
        )
        print("[INFO] Git pull exitoso.")
        print(result.stdout) # Muestra la salida del comando git pull

    except FileNotFoundError:
        print("[ERROR] El comando 'git' no se encontró. Asegúrate de que Git esté instalado y en el PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        # Esta excepción se lanza si git pull falla (ej. por conflictos de merge)
        print("[ERROR] Falló el comando 'git pull'.")
        print("--- STDOUT ---")
        print(e.stdout)
        print("--- STDERR ---")
        print(e.stderr)
        sys.exit(1)


def main():
    """
    Punto de entrada principal: actualiza el repo y luego ejecuta los scrapers.
    """
    # 1. Actualizar el código desde el repositorio de GitHub
    pull_latest_changes()

    # 2. Ejecutar el proceso de scraping y actualización de datos
    print("\n[INFO] Repositorio actualizado. Iniciando el proceso de scraping...")
    run_all_scrapers()
    print("\n[INFO] Proceso completado.")


if __name__ == "__main__":
    main()