from utilities.logger import get_logger


def error_logger(file_name: str, function_name: str, error_message: str):
    logger = get_logger("coffee_bot_server")
    logger.error(
        "%s | %s | %s",
        file_name,
        function_name,
        error_message,
    )
    return True
