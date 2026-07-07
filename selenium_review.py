#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import html
import os
import time
from datetime import datetime

import yaml
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait


def load_entries(yaml_path: str) -> list[dict]:
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"{yaml_path} doit contenir une liste d'entrées au format "
            "'- url: ...\\n  message: ...'"
        )

    entries = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict) or "url" not in item:
            raise ValueError(f"Entrée {i} invalide dans {yaml_path} : {item!r}")
        entries.append({"url": item["url"], "message": item.get("message", "")})
    return entries


def build_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def wait_page_loaded(driver, timeout: float = 30.0, extra_wait: float = 1.0) -> None:
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    if extra_wait > 0:
        time.sleep(extra_wait)


def capture_full_page_screenshot(driver) -> bytes:
    metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    content_size = metrics["contentSize"]
    clip = {
        "x": 0,
        "y": 0,
        "width": content_size["width"],
        "height": content_size["height"],
        "scale": 1,
    }
    result = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {"format": "png", "clip": clip, "captureBeyondViewport": True},
    )
    return base64.b64decode(result["data"])


def run_manual_review(driver, entries: list[dict], wait_seconds: float) -> None:
    total = len(entries)
    for i, entry in enumerate(entries, start=1):
        print(f"\n[{i}/{total}] {entry['url']}")
        try:
            driver.get(entry["url"])
            wait_page_loaded(driver, extra_wait=wait_seconds)
        except WebDriverException as exc:
            print(f"  Erreur de chargement : {exc.msg or exc}")
        if entry["message"]:
            print(f"  Consigne : {entry['message']}")
        input("  Appuie sur Entrée pour passer à la page suivante...")


def run_screenshot_mode(driver, entries: list[dict], wait_seconds: float) -> list[dict]:
    results = []
    total = len(entries)
    for i, entry in enumerate(entries, start=1):
        print(f"[{i}/{total}] Capture de {entry['url']}")
        result = {"index": i, "url": entry["url"], "message": entry["message"]}
        try:
            driver.get(entry["url"])
            wait_page_loaded(driver, extra_wait=wait_seconds)
            screenshot = capture_full_page_screenshot(driver)
            result["screenshot_b64"] = base64.b64encode(screenshot).decode("ascii")
        except WebDriverException as exc:
            message = exc.msg or str(exc)
            print(f"  Erreur : {message}")
            result["error"] = message
        results.append(result)
    return results


def build_html_report(results: list[dict]) -> str:
    sections = []
    for item in results:
        index = item["index"]
        url = html.escape(item["url"])
        message = html.escape(item["message"]).replace("\n", "<br>")
        if item.get("error"):
            body = f'<p class="error">Erreur de chargement : {html.escape(item["error"])}</p>'
        else:
            body = (
                f'<img src="data:image/png;base64,{item["screenshot_b64"]}" '
                f'alt="Screenshot {index}">'
            )
        sections.append(f"""
        <section class="entry">
          <h2>{index}. <a href="{url}" target="_blank" rel="noopener">{url}</a></h2>
          {body}
          <p class="message">{message}</p>
        </section>
        """)

    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport de revue visuelle</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; background: #fff; }}
  h1 {{ font-size: 1.4rem; }}
  .entry {{ border-bottom: 1px solid #ddd; padding: 1.5rem 0; }}
  .entry h2 {{ font-size: 1rem; word-break: break-all; }}
  .entry img {{ max-width: 100%; border: 1px solid #ddd; display: block; margin: 0.75rem 0; }}
  .message {{ background: #f5f5f5; padding: 0.75rem 1rem; border-left: 4px solid #4a90d9; white-space: pre-wrap; }}
  .error {{ background: #fdecea; color: #a12; padding: 0.75rem 1rem; border-left: 4px solid #c0392b; }}
</style>
</head>
<body>
<h1>Rapport de revue visuelle</h1>
<p>Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
{''.join(sections)}
</body>
</html>
"""


def default_output_path() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join("output", f"report_{timestamp}.html")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ouvre une page de login Selenium, attend un login manuel, puis "
            "capture un screenshot pleine page de chaque URL d'une liste "
            "(ou les visite une par une en mode revue manuelle)."
        )
    )
    parser.add_argument("login_url", help="URL sur laquelle se connecter manuellement")
    parser.add_argument("urls_yaml", help="Fichier YAML listant les entrées {url, message}")
    parser.add_argument(
        "--manual-review",
        action="store_true",
        help="Ne prend pas de screenshot : visite chaque URL et attend Entrée pour continuer",
    )
    parser.add_argument(
        "--output",
        help="Chemin du rapport HTML de sortie (défaut : output/report_<timestamp>.html)",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="Délai en secondes après chargement de page avant capture (défaut : 1.0)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    entries = load_entries(args.urls_yaml)

    driver = build_driver()
    try:
        driver.get(args.login_url)
        input("\nConnecte-toi puis appuie sur Entrée pour continuer...\n")

        if args.manual_review:
            run_manual_review(driver, entries, args.wait)
        else:
            results = run_screenshot_mode(driver, entries, args.wait)
            output_path = args.output or default_output_path()
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(build_html_report(results))
            print(f"\nRapport généré : {output_path}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
