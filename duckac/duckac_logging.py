"""Local diagnostics for a windowed EXE, including native Python crashes."""
import faulthandler
import logging
from logging.handlers import RotatingFileHandler

_fault_file = None


def configure_logging(folder):
    global _fault_file
    try:
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / 'duckac.log', maxBytes=512_000,
                                      backupCount=2, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        native = folder / 'falha-nativa.log'
        if native.exists() and native.stat().st_size > 512_000:
            native.replace(folder / 'falha-nativa-anterior.log')
        _fault_file = native.open('a', encoding='utf-8')
        faulthandler.enable(_fault_file)
    except OSError:
        # A read-only profile must not prevent opening the app.
        pass
