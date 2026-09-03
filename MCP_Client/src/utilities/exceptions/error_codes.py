# errors/error_codes.py

"""
Defines standardized error codes and their unique identifiers for consistent error handling.

This module centralizes:
- Human-readable error codes (`ErrorCode`) used throughout the application.
- Mapping from each error code to a unique `error_code_id` (`ErrorCodeStatus`) for logging, monitoring, documentation, and customer support.

Purpose:
- Ensure uniform error reporting across services and controllers.
- Enable precise tracking of errors via stable IDs (e.g., FINS_VAL_004).
- Support user-friendly messages while maintaining technical clarity.

Naming Convention:
    ErrorCode: <Domain>_<ErrorType> (e.g., USER_NOT_FOUND)
    ErrorCodeStatus ID: FINS_<DOMAIN>_<NNN> where:
        - FINS = "FINS Banking" or your system prefix
        - DOMAIN = e.g., SQL, VAL, HDR, AUTH
        - NNN = Sequential number

Used by:
    - CustomAppException
    - APIResponse
    - Middleware and validation layers
"""
class ErrorCode:
    # ==================== CONFIGURATION ERRORS ====================
    MISSING_ENV_VARS = "MissingEnvVarsErrorCode"
    
    # ==================== BUSINESS & APPLICATION ERRORS ====================
    USER_NOT_FOUND = "UserNotFoundErrorCode"
    WORK_ITEM_NOT_FOUND = "WorkItemNotFoundErrorCode"
    ESCALATE_TO_LANE = "EscalateToLaneErrorCode"
    NO_ROWS_AFFECTED = "NoRowsAffectedErrorCode"
    CONFLICT = "DataConflictErrorCode"
    
    # ==================== INPUT & VALIDATION ERRORS ====================
    INVALID_JSON_FORMAT = "InvalidJSONFormatErrorCode"
    VALIDATION_ERROR = "ValidationErrorCode"
    
    # Header-specific validation errors
    MISSING_HEADERS = "MissingHeadersErrorCode"
    MISSING_AUTHORIZATION_HEADER = "MissingAuthorizationHeaderErrorCode"
    INVALID_AUTHORIZATION_HEADER = "InvalidAuthorizationHeaderErrorCode"
    EMPTY_AUTHORIZATION_HEADER = "EmptyAuthorizationHeaderErrorCode"
    MISSING_REQUESTER_ID_HEADER = "MissingRequesterIdHeaderErrorCode"
    INVALID_REQUESTER_ID_HEADER = "InvalidRequesterIdHeaderErrorCode"
    EMPTY_REQUESTER_ID_HEADER = "EmptyRequesterIdHeaderErrorCode"
    
    # ==================== SYSTEM & INTERNAL ERRORS ====================
    INTERNAL_SERVER_ERROR = "InternalServerErrorCode"
    DATABASE_ERROR = "DatabaseErrorErrorCode"
    SERIALIZE_EVENT_DATA = "SerializeEventDataErrorCode"
    COMMIT_TRANSACTION = "CommitTransactionErrorCode"
    EXTERNAL_API_FAILED = "ExternalApiFailed"
    DB_CONNECTION_FAIL="DbFailed"
    
    # ==================== AUTHENTICATION & AUTHORIZATION ERRORS ====================
    UNAUTHORIZED = "UnauthorizedErrorCode"


# ==================== ERROR CODE TO STATUS MAPPING ====================
# Map ErrorCode to unique error ID (for logs/docs/tracing)
ErrorCodeStatus = {
    # Configuration Errors
    ErrorCode.MISSING_ENV_VARS: "TRAINING_ENV_001",
    
    # Business & Application Errors
    ErrorCode.USER_NOT_FOUND: "TRAINING_002",
    ErrorCode.WORK_ITEM_NOT_FOUND: "TRAINING_008",
    ErrorCode.ESCALATE_TO_LANE: "TRAINING_001",
    ErrorCode.NO_ROWS_AFFECTED: "TRAINING_009",
    ErrorCode.CONFLICT: "TRAINING_011",
    
    # Input & Validation Errors
    ErrorCode.INVALID_JSON_FORMAT: "TRAINING_ENV_003",
    ErrorCode.VALIDATION_ERROR: "TRAINING_VAL_004",
    
    # Header Validation Errors
    ErrorCode.MISSING_HEADERS: "TRAINING_HDR_001",
    ErrorCode.MISSING_AUTHORIZATION_HEADER: "TRAINING_HDR_002",
    ErrorCode.INVALID_AUTHORIZATION_HEADER: "TRAINING_HDR_003",
    ErrorCode.EMPTY_AUTHORIZATION_HEADER: "TRAINING_HDR_004",
    ErrorCode.MISSING_REQUESTER_ID_HEADER: "TRAINING_HDR_005",
    ErrorCode.INVALID_REQUESTER_ID_HEADER: "TRAINING_HDR_006",
    ErrorCode.EMPTY_REQUESTER_ID_HEADER: "TRAINING_HDR_007",
    
    # System & Internal Errors
    ErrorCode.INTERNAL_SERVER_ERROR: "TRAINING_005",
    ErrorCode.DATABASE_ERROR: "TRAINING_006",
    ErrorCode.SERIALIZE_EVENT_DATA: "TRAINING_001",
    ErrorCode.COMMIT_TRANSACTION: "TRAINING_010",
    ErrorCode.EXTERNAL_API_FAILED: "TRAINING_001",
    ErrorCode.DB_CONNECTION_FAIL: "TRAINING_001",
    # Authentication & Authorization Errors
    ErrorCode.UNAUTHORIZED: "TRAINING_AUTH_007",
}