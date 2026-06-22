import asyncio
import uuid
import os
from playwright.async_api import async_playwright

async def capture_screenshot(url: str) -> dict:
    async with async_playwright() as pw:

        browser = await pw.chromium.launch(headless=True)

        page = await browser.new_page(
            viewport={"width": 1280, "height": 720}
        )

        await page.goto(
            url,
            wait_until="networkidle"
        )

        os.makedirs("assets/screenshots", exist_ok=True)

        path = f"assets/screenshots/{uuid.uuid4().hex}.png"

        await page.screenshot(
            path=path,
            full_page=True
        )

        size = await page.evaluate("""
        () => ({
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight
        })
        """)

        await browser.close()

        return {
            "url": url,
            "path": path,
            "width": size["width"],
            "height": size["height"]
        }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    url = "https://example.com"
    result = asyncio.run(capture_screenshot(url))
    print(result)
