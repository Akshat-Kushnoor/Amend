"""
Phase 1: CoreEngine Basic Tests
Verify that encode() produces correctly structured amend: keys
and that decode() round-trips them cleanly.
"""
import pytest
from amend.registry.core_engine import encode, decode, verify, CoreEngine


# ── Shared fixture params ─────────────────────────────────────────────
PARAMS = ("src/auth/handler.py", 12, "AuthHandler", "login", "user not found", "ScopeError")


class TestEncodeBasic:
    """Tests for encode() — key structure and format."""

    def test_encode_returns_string(self):
        assert isinstance(encode(*PARAMS), str)

    def test_encode_starts_with_amend_prefix(self):
        key = encode(*PARAMS)
        assert key.startswith("amend:"), f"Expected 'amend:' prefix, got: {key[:10]}"

    def test_encode_has_three_dot_segments(self):
        key = encode(*PARAMS)
        body = key[6:]  # strip "amend:"
        parts = body.split(".")
        assert len(parts) == 3, f"Expected 3 dot-segments, got {len(parts)}: {body}"

    def test_encode_class_code_sco(self):
        key = encode("f.py", 1, "", "fn", "msg", "ScopeError")
        code = key[6:].split(".")[0]
        assert code == "SCO"

    def test_encode_class_code_net(self):
        key = encode("f.py", 1, "", "fn", "msg", "NetworkError")
        code = key[6:].split(".")[0]
        assert code == "NET"

    def test_encode_class_code_val(self):
        key = encode("f.py", 1, "", "fn", "msg", "ValidationError")
        code = key[6:].split(".")[0]
        assert code == "VAL"

    def test_encode_unknown_class_falls_back_to_err(self):
        key = encode("f.py", 1, "", "fn", "msg", "CustomError")
        code = key[6:].split(".")[0]
        assert code == "ERR"

    def test_encode_minimal_params(self):
        key = encode("", 0, "", "", "", "")
        assert key.startswith("amend:")
        assert len(key[6:].split(".")) == 3


class TestDecodeBasic:
    """Tests for decode() — field extraction."""

    def test_decode_returns_dict(self):
        key = encode(*PARAMS)
        result = decode(key)
        assert isinstance(result, dict)

    def test_decode_contains_all_fields(self):
        key = encode(*PARAMS)
        result = decode(key)
        for field in ("key", "errorClass", "filePath", "line", "funcName", "message"):
            assert field in result, f"Missing field: {field}"

    def test_decode_key_field_matches_input(self):
        key = encode(*PARAMS)
        assert decode(key)["key"] == key

    def test_decode_error_class(self):
        key = encode(*PARAMS)
        assert decode(key)["errorClass"] == "ScopeError"

    def test_decode_message(self):
        key = encode(*PARAMS)
        assert decode(key)["message"] == "user not found"

    def test_decode_file_path(self):
        key = encode(*PARAMS)
        assert decode(key)["filePath"] == "src/auth/handler.py"

    def test_decode_line(self):
        key = encode(*PARAMS)
        assert decode(key)["line"] == 12

    def test_decode_func_name(self):
        key = encode(*PARAMS)
        assert decode(key)["funcName"] == "login"

    def test_decode_invalid_key_raises(self):
        with pytest.raises(ValueError):
            decode("not-a-valid-key")

    def test_decode_missing_prefix_raises(self):
        with pytest.raises(ValueError):
            decode("SCO.abc.def")


class TestVerify:
    """Tests for verify() — format validation."""

    def test_verify_valid_key(self):
        assert verify(encode(*PARAMS)) is True

    def test_verify_empty_string(self):
        assert verify("") is False

    def test_verify_garbage_string(self):
        assert verify("garb@ge!key") is False

    def test_verify_partial_key(self):
        assert verify("amend:SCO.abc") is False


class TestCoreEngineNamespace:
    """Tests for CoreEngine class-level shortcuts."""

    def test_error_class_helper(self):
        key = encode(*PARAMS)
        assert CoreEngine.error_class(key) == "ScopeError"

    def test_location_helper(self):
        key = encode(*PARAMS)
        loc = CoreEngine.location(key)
        assert loc["filePath"] == "src/auth/handler.py"
        assert loc["line"] == 12
        assert loc["funcName"] == "login"

    def test_message_helper(self):
        key = encode(*PARAMS)
        assert CoreEngine.message(key) == "user not found"