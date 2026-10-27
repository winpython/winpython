# -*- coding: utf-8 -*-
"""wppm -sa reads pins from files offline; only the osv.dev query needs network."""
from wppm import audit


def test_pins_from_requirements(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("# comment\nMako==1.3.12\nnbconvert[webpdf] == 7.17.1 ; python_version>'3'\nnumpy>=2\n", encoding="utf-8")
    assert audit.pins_from_file(req) == [("Mako", "1.3.12"), ("nbconvert", "7.17.1")]


def test_pins_from_pylock(tmp_path):
    lock = tmp_path / "pylock.toml"
    lock.write_text('lock-version = "1.0"\n[[packages]]\nname = "mako"\nversion = "1.3.12"\n'
                    '[[packages]]\nname = "local"\n', encoding="utf-8")
    assert audit.pins_from_file(lock) == [("mako", "1.3.12")]


def test_fixed_in_picks_lowest_fix_above_installed():
    vuln = {"affected": [{"package": {"ecosystem": "PyPI", "name": "Pydantic_AI-slim"},
                          "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "1.0"}]},
                                     {"type": "ECOSYSTEM", "events": [{"introduced": "1.100"}, {"fixed": "1.107.4"}]},
                                     {"type": "GIT", "events": [{"fixed": "01e0558825b8"}]}]}]}
    assert audit._fixed_in(vuln, "pydantic-ai-slim", "1.106.0") == "1.107.4"
    assert audit._fixed_in(vuln, "other", "1.106.0") == ""


def test_upgrades_flags_a_fix_with_advisories_of_its_own(monkeypatch):
    rows = [{"package": "a", "version": "1.0", "fixed": "1.2"}, {"package": "a", "version": "1.0", "fixed": "1.10"},
            {"package": "b", "version": "2.0", "fixed": "2.1"}, {"package": "c", "version": "3.0", "fixed": ""}]
    asked = []
    def fake_audit(pins):
        asked.extend(pins)
        return [{"package": "b"}]
    monkeypatch.setattr(audit, "audit", fake_audit)
    result = audit.upgrades(rows)
    assert sorted(asked) == [("a", "1.10"), ("b", "2.1")]
    assert result == {"a": {"version": "1.0", "to": "1.10", "clean": True},
                      "b": {"version": "2.0", "to": "2.1", "clean": False},
                      "c": {"version": "3.0", "to": "", "clean": None}}
