import logging
import logging_loki
from queue import Queue
from app.core.config import settings

def setup_loki_logging():
    """Configura o logger para enviar logs ao Grafana Loki."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    # Adiciona StreamHandler para garantir que os logs apareçam no console também
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Evita adicionar múltiplos handlers de Loki
    if not any(isinstance(h, (logging_loki.LokiHandler, logging_loki.LokiQueueHandler)) for h in logger.handlers):
        auth = None
        if settings.LOKI_USER_ID and settings.LOKI_TOKEN:
            auth = (settings.LOKI_USER_ID, settings.LOKI_TOKEN)

        try:
            # Usando queue.Queue (Thread-safe) para o LokiQueueHandler
            # Isso evita problemas de compatibilidade de tipos entre multiprocessing e queue
            handler = logging_loki.LokiQueueHandler(
                Queue(-1),
                url=settings.LOKI_URL,
                tags={"application": settings.PROJECT_NAME, "env": "production"},
                auth=auth,
                version="1",
            )
            logger.addHandler(handler)
            logger.info("Loki logging configurado (Modo Queue).")
        except Exception as e:
            # Em caso de erro, o StreamHandler já adicionado cuidará dos logs
            logging.error(f"Erro ao configurar Loki logging: {e}")

    return logger

# Instância global do logger
logger = setup_loki_logging()
