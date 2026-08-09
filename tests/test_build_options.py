# -*- coding: utf-8 -*-
"""Build-script options: --bytecode mode parsing.

The default must stay 'pip', because that is what release builds ship.
"""
import pytest

from winpython.build_winpython import parse_bytecode_mode


class TestBytecodeMode:
    def test_default_keeps_pip_behaviour(self):
        """No --no-compile, no extra pass: exactly what builds did before."""
        assert parse_bytecode_mode("pip") == (False, None)

    @pytest.mark.parametrize("empty", ["", None])
    def test_missing_value_defaults_to_pip(self, empty):
        assert parse_bytecode_mode(empty) == (False, None)

    def test_none_skips_compilation_entirely(self):
        no_compile, jobs = parse_bytecode_mode("none")
        assert no_compile is True
        assert jobs is None

    def test_parallel_uses_every_core(self):
        """compileall -j0 means one worker per core."""
        assert parse_bytecode_mode("parallel") == (True, 0)

    @pytest.mark.parametrize("value,jobs", [("parallel-1", 1), ("parallel-4", 4), ("parallel-16", 16)])
    def test_parallel_n_caps_the_workers(self, value, jobs):
        assert parse_bytecode_mode(value) == (True, jobs)

    @pytest.mark.parametrize("value", ["PIP", "  None  ", "Parallel-4"])
    def test_case_and_whitespace_tolerant(self, value):
        parse_bytecode_mode(value)  # must not raise

    @pytest.mark.parametrize("value", ["parallel-", "parallel-x", "quick", "no", "-j4", "parallel-4x"])
    def test_rejects_nonsense_loudly(self, value):
        """A typo in the TOML must fail the build, not silently ship no .pyc."""
        with pytest.raises(ValueError, match="--bytecode"):
            parse_bytecode_mode(value)

    def test_only_pip_mode_lets_pip_compile(self):
        """Every non-default mode has to pass --no-compile, or work is done twice."""
        for mode in ("none", "parallel", "parallel-2"):
            assert parse_bytecode_mode(mode)[0] is True
