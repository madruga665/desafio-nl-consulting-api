import logging
import logging_loki
from app.core.config import settings

def setup_loki_logging():
    """Configura o logger para enviar logs ao Grafana Loki."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    # Evita adicionar múltiplos handlers se a função for chamada mais de uma vez
    if not any(isinstance(h, (logging_loki.LokiHandler, logging_loki.LokiQueueHandler)) for h in logger.handlers):
        auth = None
        if settings.LOKI_USER_ID and settings.LOKI_TOKEN:
            auth = (settings.LOKI_USER_ID, settings.LOKI_TOKEN)

        try:
            handler = logging_loki.LokiHandler(
                url=settings.LOKI_URL,
                tags={"app": settings.PROJECT_NAME, "env": "production"},
                auth=auth,
                version="1",
            )
            logger.addHandler(handler)
            logger.info("Loki logging configurado com sucesso.")
        except Exception as e:
            # Fallback para log padrão em caso de erro na configuração do Loki
            logging.error(f"Erro ao configurar Loki logging: {e}")

    return logger

# Instância global do logger
logger = setup_loki_logging()
