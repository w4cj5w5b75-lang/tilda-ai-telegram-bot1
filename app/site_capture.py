import uuid
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


DATA_DIR = Path("/app/data")
SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def capture_site(url: str) -> dict:
    file_id = str(uuid.uuid4())

    viewport_path = SCREENSHOT_DIR / f"{file_id}_viewport.png"
    fullpage_path = SCREENSHOT_DIR / f"{file_id}_fullpage.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = await browser.new_page(
            viewport={"width": 1440, "height": 1200}
        )

        await page.goto(
            url,
            wait_until="networkidle",
            timeout=60000
        )

        await page.screenshot(
            path=str(viewport_path),
            full_page=False
        )

        await page.screenshot(
            path=str(fullpage_path),
            full_page=True
        )

        html = await page.content()

        await browser.close()

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")

    clean_text = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )

    return {
        "viewport_screenshot": str(viewport_path),
        "fullpage_screenshot": str(fullpage_path),
        "text": clean_text[:10000],
    }
