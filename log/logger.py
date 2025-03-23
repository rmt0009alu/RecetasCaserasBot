import logging


def setup_logger():
    """Configuración de logging. 

    Parameters
    ----------

    Returns
    -------
        logger
            El logger ya configurado y listo para usar.
    """
    logger = logging.getLogger("TelegramBot")  # Usamos un nombre específico para el logger
    logger.setLevel(logging.INFO)  # Configuramos el nivel global

    # Manejador para los logs en archivo
    log_file = 'log/bot.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)  # Puedes personalizar el nivel para cada manejador

    # Manejador para mostrar logs en consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato de los logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Agregar los manejadores al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger