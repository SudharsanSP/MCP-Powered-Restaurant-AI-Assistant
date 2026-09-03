from repositories.database import Database
from repositories.schema.coffee_shop_models import Error_Logger

class ErrorLog:
    def add_errorlog_repository(self, file_name, function_name, error_message):
        db_instance = Database()
        db_session = db_instance.SessionLocal()
        error = Error_Logger(
            file_name = file_name,
            function_name = function_name,
            error_message = error_message
        )
        db_session.add(error)
        db_session.commit()
        return True