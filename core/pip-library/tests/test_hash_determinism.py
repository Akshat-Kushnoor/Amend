"""
Phase 2: CoreEngine Determinism Tests
Verify that encode() always produces the same key for the same inputs,
regardless of how many times it is called.
"""
import pytest
from amend.registry.core_engine import encode, decode


PARAMS = ("src/main.py", 42, "MyClass", "run", "Error message", "ScopeError")


class TestEncodeDeterminism:
    """Same inputs must always produce the same key."""

    def test_same_params_10_runs(self):
        keys = [encode(*PARAMS) for _ in range(10)]
        assert len(set(keys)) == 1, f"Got different keys: {set(keys)}"

    def test_same_params_100_runs(self):
        keys = [encode(*PARAMS) for _ in range(100)]
        assert len(set(keys)) == 1

    def test_empty_params_deterministic(self):
        keys = [encode("", 0, "", "", "", "") for _ in range(50)]
        assert len(set(keys)) == 1

    def test_unicode_message_deterministic(self):
        keys = [encode("a.py", 1, "", "fn", "error: 世界🌍", "ScopeError") for _ in range(20)]
        assert len(set(keys)) == 1

    def test_special_chars_message_deterministic(self):
        keys = [encode("b.py", 2, "", "g", "err@#$%^&*()", "NetworkError") for _ in range(20)]
        assert len(set(keys)) == 1

    def test_different_params_produce_different_keys(self):
        param_list = [
            ("file1.py", 1, "C", "f",   "m", "ScopeError"),
            ("file2.py", 1, "C", "f",   "m", "ScopeError"),  # different file
            ("file1.py", 2, "C", "f",   "m", "ScopeError"),  # different line
            ("file1.py", 1, "C", "g",   "m", "ScopeError"),  # different func
            ("file1.py", 1, "C", "f",   "n", "ScopeError"),  # different message
            ("file1.py", 1, "C", "f",   "m", "NetworkError"),# different error class (code+msg seg)
            ("file1.py", 1, "C", "f",   "x", "ScopeError"),  # yet another message
        ]
        keys = [encode(*p) for p in param_list]
        assert len(set(keys)) == len(param_list), "All different params must produce unique keys"


    def test_100_unique_param_sets_produce_100_unique_keys(self):
        param_list = [
            (f"file{i}.py", i, f"Class{i}", f"func{i}", f"message {i}", "ScopeError")
            for i in range(100)
        ]
        keys = [encode(*p) for p in param_list]
        # Expect 100% uniqueness — Base64url encoding is lossless
        assert len(set(keys)) == 100


class TestRoundTripDeterminism:
    """decode(encode(...)) must return the exact original inputs."""

    def test_roundtrip_basic(self):
        key = encode(*PARAMS)
        d   = decode(key)
        assert d["filePath"]   == PARAMS[0]
        assert d["line"]       == PARAMS[1]
        assert d["funcName"]   == PARAMS[3]
        assert d["message"]    == PARAMS[4]
        assert d["errorClass"] == PARAMS[5]

    def test_roundtrip_empty_class_name(self):
        key = encode("script.py", 5, "", "main", "boom", "ValidationError")
        d   = decode(key)
        assert d["filePath"] == "script.py"
        assert d["line"]     == 5
        assert d["message"]  == "boom"

    def test_roundtrip_unicode_message(self):
        msg = "error: 世界🌍"
        key = encode("a.py", 1, "", "fn", msg, "ScopeError")
        assert decode(key)["message"] == msg

    def test_roundtrip_long_message(self):
        msg = "A" * 200
        key = encode("deep/path/to/module.py", 999, "BigClass", "bigFunc", msg, "NetworkError")
        d   = decode(key)
        assert d["message"]  == msg
        assert d["filePath"] == "deep/path/to/module.py"
        assert d["line"]     == 999

    def test_batch_roundtrip_consistency(self):
        base = "consistency-test"
        param_sets = [(f"file{i}.py", i, "C", f"fn{i}", f"msg {i}", "ScopeError") for i in range(10)]

        batch1 = [encode(*p) for p in param_sets]
        batch2 = [encode(*p) for p in param_sets]
        assert batch1 == batch2, "Keys must be identical across separate calls"