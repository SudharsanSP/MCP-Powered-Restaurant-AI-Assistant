# constants/http_Status.py

class HttpStatusCode:
    # ==================== SUCCESSFUL RESPONSES ====================
    OK = 200
    CREATED = 201
    NO_CONTENT = 204

    # ==================== CLIENT ERROR RESPONSES ====================
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422

    # ==================== SERVER ERROR RESPONSES ====================
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503