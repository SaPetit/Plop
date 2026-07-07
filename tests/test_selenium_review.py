import base64
import os
import re
import sys

import pytest
from selenium.common.exceptions import WebDriverException

import selenium_review as sr


class FakeDriver:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on or set()
        self.visited = []

    def get(self, url):
        self.visited.append(url)
        if url in self.fail_on:
            raise WebDriverException("boom")


# -- load_entries ------------------------------------------------------------

def test_load_entries_valid(tmp_path):
    f = tmp_path / "urls.yaml"
    f.write_text(
        "- url: https://example.com/a\n"
        "  message: \"check a\"\n"
        "- url: https://example.com/b\n",
        encoding="utf-8",
    )
    assert sr.load_entries(str(f)) == [
        {"url": "https://example.com/a", "message": "check a"},
        {"url": "https://example.com/b", "message": ""},
    ]


def test_load_entries_not_a_list(tmp_path):
    f = tmp_path / "urls.yaml"
    f.write_text("url: https://example.com\n", encoding="utf-8")
    with pytest.raises(ValueError):
        sr.load_entries(str(f))


def test_load_entries_missing_url(tmp_path):
    f = tmp_path / "urls.yaml"
    f.write_text("- message: oops\n", encoding="utf-8")
    with pytest.raises(ValueError):
        sr.load_entries(str(f))


# -- build_html_report --------------------------------------------------------

def test_build_html_report_escapes_html():
    results = [
        {
            "index": 1,
            "url": "https://example.com/<script>",
            "message": "<script>alert(1)</script>",
            "screenshot_b64": "AAAA",
        }
    ]
    html_out = sr.build_html_report(results)
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "AAAA" in html_out


def test_build_html_report_error_entry():
    results = [{"index": 1, "url": "https://example.com", "message": "", "error": "boom <b>"}]
    html_out = sr.build_html_report(results)
    assert "Erreur de chargement" in html_out
    assert "boom &lt;b&gt;" in html_out
    assert "<img" not in html_out


def test_build_html_report_preserves_order():
    results = [
        {"index": 1, "url": "https://a.example.com", "message": "m1", "screenshot_b64": "A"},
        {"index": 2, "url": "https://b.example.com", "message": "m2", "screenshot_b64": "B"},
    ]
    html_out = sr.build_html_report(results)
    assert html_out.index("https://a.example.com") < html_out.index("https://b.example.com")


# -- default_output_path ------------------------------------------------------

def test_default_output_path_format():
    path = sr.default_output_path()
    assert re.match(r"output[\\/]report_\d{8}_\d{6}\.html$", path)


# -- run_screenshot_mode -------------------------------------------------------

def test_run_screenshot_mode_success_and_error(monkeypatch):
    monkeypatch.setattr(sr, "wait_page_loaded", lambda d, extra_wait=1.0: None)
    monkeypatch.setattr(sr, "capture_full_page_screenshot", lambda d: b"PNGDATA")

    entries = [
        {"url": "https://good.example.com", "message": "m1"},
        {"url": "https://bad.example.com", "message": "m2"},
    ]
    driver = FakeDriver(fail_on={"https://bad.example.com"})

    results = sr.run_screenshot_mode(driver, entries, wait_seconds=0)

    assert driver.visited == ["https://good.example.com", "https://bad.example.com"]
    assert results[0]["screenshot_b64"] == base64.b64encode(b"PNGDATA").decode("ascii")
    assert "error" not in results[0]
    assert results[1]["error"] == "boom"
    assert "screenshot_b64" not in results[1]


# -- run_manual_review ---------------------------------------------------------

def test_run_manual_review_prints_message_and_waits_for_input(monkeypatch, capsys):
    monkeypatch.setattr(sr, "wait_page_loaded", lambda d, extra_wait=1.0: None)
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt="": prompts.append(prompt) or "")

    driver = FakeDriver()
    entries = [{"url": "https://a.example.com", "message": "check a"}]

    sr.run_manual_review(driver, entries, wait_seconds=0)

    assert driver.visited == ["https://a.example.com"]
    assert len(prompts) == 1
    captured = capsys.readouterr()
    assert "check a" in captured.out
    assert "https://a.example.com" in captured.out


def test_run_manual_review_continues_after_load_error(monkeypatch, capsys):
    monkeypatch.setattr(sr, "wait_page_loaded", lambda d, extra_wait=1.0: None)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    driver = FakeDriver(fail_on={"https://bad.example.com"})
    entries = [{"url": "https://bad.example.com", "message": "check b"}]

    sr.run_manual_review(driver, entries, wait_seconds=0)

    captured = capsys.readouterr()
    assert "Erreur de chargement" in captured.out
    assert "check b" in captured.out


# -- parse_args -----------------------------------------------------------------

def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["selenium_review.py", "https://login", "urls.yaml"])
    args = sr.parse_args()
    assert args.login_url == "https://login"
    assert args.urls_yaml == "urls.yaml"
    assert args.manual_review is False
    assert args.output is None
    assert args.wait == 1.0


def test_parse_args_manual_review_flag(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["selenium_review.py", "https://login", "urls.yaml", "--manual-review", "--wait", "2.5"],
    )
    args = sr.parse_args()
    assert args.manual_review is True
    assert args.wait == 2.5
