"""
Tests for MCP_Server/src/utilities/exceptions/http_status.py

Covers: HttpStatusCode integer constants.
"""
import sys
import os

SERVER_SRC = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "MCP_Server", "src"
)
if SERVER_SRC not in sys.path:
    sys.path.insert(0, SERVER_SRC)

from utilities.exceptions.http_status import HttpStatusCode


class TestHttpStatusCode:
    def test_ok_is_200(self):
        assert HttpStatusCode.OK == 200

    def test_created_is_201(self):
        assert HttpStatusCode.CREATED == 201

    def test_bad_request_is_400(self):
        assert HttpStatusCode.BAD_REQUEST == 400

    def test_unauthorized_is_401(self):
        assert HttpStatusCode.UNAUTHORIZED == 401

    def test_forbidden_is_403(self):
        assert HttpStatusCode.FORBIDDEN == 403

    def test_not_found_is_404(self):
        assert HttpStatusCode.NOT_FOUND == 404

    def test_conflict_is_409(self):
        assert HttpStatusCode.CONFLICT == 409

    def test_internal_server_error_is_500(self):
        assert HttpStatusCode.INTERNAL_SERVER_ERROR == 500

    def test_service_unavailable_is_503(self):
        assert HttpStatusCode.SERVICE_UNAVAILABLE == 503

    def test_all_constants_are_integers(self):
        for attr in vars(HttpStatusCode):
            if not attr.startswith("_"):
                assert isinstance(getattr(HttpStatusCode, attr), int), (
                    f"HttpStatusCode.{attr} is not an integer"
                )
