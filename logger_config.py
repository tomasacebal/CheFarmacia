# --- START OF FILE logger_config.py ---

import logging
import sys
import os
from datetime import datetime

class StreamToLogger:
    """
    Clase para redirigir un stream (como sys.stdout o sys.stderr) a un logger.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        """
        Escribe el buffer en el logger. Cada línea se registra como una entrada separada.
        """
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        """
        Método flush requerido por la interfaz de stream.
        """
        pass

def setup_logging():
    """
    Configura el sistema de logging para que la salida se dirija tanto a la consola
    como a un archivo de log único con marca de tiempo.
    """
    # Crear el directorio de logs si no existe
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Crear un nombre de archivo único con la fecha y hora actual
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"run_{timestamp}.log")

    # Configurar el logger raíz
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'), # Handler para el archivo
            logging.StreamHandler(sys.__stdout__) # Handler para la consola original
        ]
    )

    # Redirigir stdout y stderr al sistema de logging
    # Esto captura todos los `print()` y los errores no controlados.
    stdout_logger = logging.getLogger('STDOUT')
    sys.stdout = StreamToLogger(stdout_logger, logging.INFO)

    stderr_logger = logging.getLogger('STDERR')
    sys.stderr = StreamToLogger(stderr_logger, logging.ERROR)

    # Informar que el logging ha sido configurado
    logging.info("Logging configurado. La salida se guardará en: %s", log_filename)

    return log_filename