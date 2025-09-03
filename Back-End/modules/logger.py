import logging

def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    Configura um logger.
    :param name: Nome do logger
    :param log_file: Caminho do arquivo de log (opcional)
    :param level: Nível mínimo de log
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler opcional
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
