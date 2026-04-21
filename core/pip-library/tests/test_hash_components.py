"""
Phase 3: CoreEngine Component & Decode Tests
Verify that each segment of the key encodes its expected dimension,
and that the key is fully decodable to the original location + message.
"""
import pytest
from amend.registry.core_engine import encode, decode, CoreEngine


class TestSegmentIndependence:
    """Changing one input dimension must only change the corresponding segment."""

    def _segments(self, *args) -> tuple[str, str, str]:
        key  = encode(*args)
        body = key[6:]  # strip "amend:"
        parts = body.split(".")
        return parts[0], parts[1], parts[2]  # code, loc_b64, msg_b64

    def test_different_file_changes_loc_segment(self):
        _, loc1, msg1 = self._segments("src/a.py", 42, "C", "f", "err", "ScopeError")
        _, loc2, msg2 = self._segments("src/b.py", 42, "C", "f", "err", "ScopeError")
        assert loc1 != loc2, "loc segment must differ when filePath differs"
        assert msg1 == msg2, "msg segment must not change when only filePath differs"

    def test_different_line_changes_loc_segment(self):
        _, loc1, _ = self._segments("src/a.py", 1,   "C", "f", "err", "ScopeError")
        _, loc2, _ = self._segments("src/a.py", 999, "C", "f", "err", "ScopeError")
        assert loc1 != loc2

    def test_different_func_changes_loc_segment(self):
        _, loc1, _ = self._segments("src/a.py", 5, "C", "funcA", "err", "ScopeError")
        _, loc2, _ = self._segments("src/a.py", 5, "C", "funcB", "err", "ScopeError")
        assert loc1 != loc2

    def test_different_message_changes_msg_segment(self):
        code1, loc1, msg1 = self._segments("src/a.py", 5, "C", "f", "msg one", "ScopeError")
        code2, loc2, msg2 = self._segments("src/a.py", 5, "C", "f", "msg two", "ScopeError")
        assert msg1 != msg2
        assert loc1 == loc2,  "loc must not change when only message differs"
        assert code1 == code2, "code must not change when only message differs"

    def test_different_error_class_changes_code_segment(self):
        code1, loc1, msg1 = self._segments("src/a.py", 5, "C", "f", "msg", "ScopeError")
        code2, loc2, msg2 = self._segments("src/a.py", 5, "C", "f", "msg", "NetworkError")
        assert code1 != code2
        assert loc1 == loc2,  "loc must not change when only errorClass differs"
        assert msg1 == msg2, "msg must not change when only errorClass differs"

    def test_varying_only_class_name_does_not_change_loc(self):
        """className is NOT independently encoded in loc (only filePath|line|funcName are).
        Two errors with same file/line/func but different class are at identical call sites."""
        _, loc1, _ = self._segments("src/a.py", 5, "ClassA", "f", "msg", "ScopeError")
        _, loc2, _ = self._segments("src/a.py", 5, "ClassB", "f", "msg", "ScopeError")
        assert loc1 == loc2, "className alone should not change the loc segment"


class TestDecodeRecoversLocation:
    """The error location (filePath, line, funcName) must be recoverable from the key."""

    def test_file_path_decoded(self):
        key = encode("src/handlers/auth.py", 42, "Auth", "validate", "Invalid token", "ValidationError")
        assert decode(key)["filePath"] == "src/handlers/auth.py"

    def test_line_number_decoded(self):
        key = encode("src/db.py", 156, "DB", "connect", "refused", "NetworkError")
        assert decode(key)["line"] == 156

    def test_func_name_decoded(self):
        key = encode("src/api.py", 10, "", "get_user", "not found", "ScopeError")
        assert decode(key)["funcName"] == "get_user"

    def test_full_location_decoded(self):
        key = encode("src/api/routes.py", 45, "RouteHandler", "get_user", "User not found", "ScopeError")
        d   = decode(key)
        assert d["filePath"] == "src/api/routes.py"
        assert d["line"]     == 45
        assert d["funcName"] == "get_user"

    def test_location_from_helper(self):
        key = encode("src/api/routes.py", 45, "RouteHandler", "get_user", "User not found", "ScopeError")
        loc = CoreEngine.location(key)
        assert loc["filePath"] == "src/api/routes.py"
        assert loc["line"]     == 45
        assert loc["funcName"] == "get_user"


class TestDecodeRecoversMessage:
    """The error message must be recoverable from the key."""

    def test_simple_message(self):
        key = encode("src/db.py", 1, "", "query", "connection refused", "NetworkError")
        assert decode(key)["message"] == "connection refused"

    def test_message_with_special_chars(self):
        msg = "Failed: token=abc123 & user='admin'"
        key = encode("src/auth.py", 5, "", "check", msg, "ScopeError")
        assert decode(key)["message"] == msg

    def test_message_with_unicode(self):
        msg = "エラー: ユーザーが見つかりません"
        key = encode("src/i18n.py", 3, "", "lookup", msg, "ScopeError")
        assert decode(key)["message"] == msg

    def test_message_helper(self):
        key = encode("src/db.py", 1, "", "query", "connection refused", "NetworkError")
        assert CoreEngine.message(key) == "connection refused"


class TestUniqueness:
    """Different error sources must produce different keys."""

    def test_100_unique_errors_produce_100_unique_keys(self):
        params = [
            (f"src/file{i}.py", i, f"Class{i}", f"func{i}", f"error {i}", "ScopeError")
            for i in range(100)
        ]
        keys = [encode(*p) for p in params]
        assert len(set(keys)) == 100, "Every distinct error site must produce a unique key"

    def test_same_file_different_lines_are_unique(self):
        keys = [encode("src/a.py", i, "C", "f", "msg", "ScopeError") for i in range(1, 51)]
        assert len(set(keys)) == 50

    def test_same_location_different_messages_are_unique(self):
        keys = [encode("src/a.py", 1, "C", "f", f"error variant {i}", "ScopeError") for i in range(20)]
        assert len(set(keys)) == 20