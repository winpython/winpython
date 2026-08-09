# -*- coding: utf-8 -*-
"""Build-script options: --bytecode mode parsing.

The default must stay 'pip', because that is what release builds ship.
"""
import os

import pytest

from winpython.build_winpython import PARALLEL_DEFAULT_MAX, parse_bytecode_mode


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

    def test_parallel_is_capped(self):
        """Bare 'parallel' must not spawn a worker per logical CPU.

        Measured I/O-bound, so 8 workers on a 4-core/8-thread laptop only adds
        contention. cpu_count() is logical, hence the cap.
        """
        no_compile, jobs = parse_bytecode_mode("parallel")
        assert no_compile is True
        assert jobs == min(os.cpu_count() or 1, PARALLEL_DEFAULT_MAX)
        assert 1 <= jobs <= PARALLEL_DEFAULT_MAX

    def test_parallel_never_asks_for_zero_workers(self):
        """-j0 would hand the choice back to ProcessPoolExecutor, undoing the cap."""
        assert parse_bytecode_mode("parallel")[1] >= 1

    @pytest.mark.parametrize("value,jobs", [("parallel-1", 1), ("parallel-4", 4), ("parallel-16", 16)])
    def test_explicit_n_is_taken_literally_and_uncapped(self, value, jobs):
        """An explicit N is a deliberate choice, so the cap must not apply."""
        assert parse_bytecode_mode(value) == (True, jobs)

    @pytest.mark.parametrize("value", ["PIP", "  None  ", "Parallel-4"])
    def test_case_and_whitespace_tolerant(self, value):
        parse_bytecode_mode(value)  # must not raise

    @pytest.mark.parametrize("value", ["parallel-", "parallel-x", "quick", "no", "-j4",
                                       "parallel-4x", "parallel-0"])
    def test_rejects_nonsense_loudly(self, value):
        """A typo in the TOML must fail the build, not silently ship no .pyc."""
        with pytest.raises(ValueError, match="--bytecode"):
            parse_bytecode_mode(value)

    def test_only_pip_mode_lets_pip_compile(self):
        """Every non-default mode has to pass --no-compile, or work is done twice."""
        for mode in ("none", "parallel", "parallel-2"):
            assert parse_bytecode_mode(mode)[0] is True
