from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def fetch(self) -> list[dict]:
        """
        Debe retornar una lista de farmacias con:
        - nombre
        - dirección
        - teléfono
        - fecha
        - localidad
        - fuente
        - nivel_confianza (1-3)
        """
        pass
