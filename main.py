import os
import subprocess
import sys
from dotenv import load_dotenv
from datetime import datetime
import asyncio

from logger_config import setup_logging
from run_scrapers import run_all_scrapers
from utils import send_telegram_notification

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
    # 1. Configurar el logging y obtener el nombre del archivo de log
    log_filename = setup_logging()

    # 2. Preparar variables para el resumen final
    start_time = datetime.now()
    status = "✅ Éxito"
    error_details = ""

    try:
        # 3. Ejecutar la lógica principal
        main()

    except Exception as e:
        # 4. Si algo falla, capturar el error y cambiar el estado
        status = "❌ Falló"
        # Obtener el traceback para un error más detallado
        import traceback
        error_details = traceback.format_exc()
        # Loguear el error completo en el archivo
        print(f"[ERROR CRÍTICO] La ejecución falló: {e}\n{error_details}")

    finally:
        # 5. Este bloque se ejecuta SIEMPRE, haya habido error o no
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Formatear la duración para que sea más legible
        total_seconds = int(duration.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        duration_str = f"{minutes}m {seconds}s"

        # 6. Construir el mensaje de notificación
        # Los caracteres como '.' o '-' deben ser escapados en MarkdownV2
        log_filename_escaped = log_filename.replace('\\', '/').replace('.', '\\.').replace('-', '\\-')
        
        summary_message = f"""
*Resumen de Ejecución del Scraper*

*Estado:* {status}
*Duración:* {duration_str}
*Archivo de Log:* `{log_filename_escaped}`
"""
        if error_details:
            # Si hubo un error, añadir los detalles al mensaje
            summary_message += f"\n*Detalle del Error:*\n```\n{error_details[:3500]}\n```" # Telegram tiene un límite de 4096 caracteres

        # 7. Enviar la notificación
        asyncio.run(send_telegram_notification(summary_message))

        print(f"\n[INFO] Proceso completado en {duration_str}.")
        
        # 8. Si el script falló, salir con un código de error
        if status == "❌ Falló":
            sys.exit(1)