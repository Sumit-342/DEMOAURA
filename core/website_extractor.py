import asyncio
import uuid
import hashlib
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page, ElementHandle

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

EXTRACT_TAGS = {
    "h1": "h1",
    "h2": "h2",
    "h3": "h3",
    "button": "button, [role='button'], input[type='submit']",
    "link": "a[href]"
}

SKIP_LINKS = {"#", "", "javascript:void(0)", "javascript:"}

NOISE_KEYWORDS = {
    "cookie", "privacy", "terms", "footer", "menu",
    "navigation", "copyright", "subscribe", "newsletter",
    "back to top", "loading", "sign in", "log in"
}

# -------------------------------------------------------------------
# NOISE CHECK
# -------------------------------------------------------------------

def is_noise(text: str) -> bool:
    t = text.lower().strip()
    if len(t) < 2:   # ✅ allow short texts like "AI"
        return True
    return any(n in t for n in NOISE_KEYWORDS)

# -------------------------------------------------------------------
# SINGLE ELEMENT CLEANER
# -------------------------------------------------------------------

async def _extract_element(el: ElementHandle, tag: str, viewport: dict):
    try:
        text_raw = await el.inner_text()
        bbox = await el.bounding_box()

        if not bbox:
            return None

        text = " ".join(text_raw.split()).strip()
        if not text or len(text) < 2:
            return None
        if is_noise(text):
            return None

        href = None
        if tag == "link":
            href = await el.get_attribute("href")
            if not href or href in SKIP_LINKS or href.startswith("javascript:"):
                return None

        # Detect fixed/sticky elements
        is_fixed = await el.evaluate("""
            (node) => {
                let el = node;
                while (el && el !== document.body) {
                    const s = window.getComputedStyle(el);
                    if (s.position === "fixed" || s.position === "sticky") return true;
                    el = el.parentElement;
                }
                return false;
            }
        """)

        return {
            "id": f"el_{uuid.uuid4().hex[:8]}",
            "hash_id": hashlib.md5(text.encode()).hexdigest()[:8],
            "tag": tag,
            "text": text,
            "href": href,
            "isFixed": is_fixed,
            "bbox": {
                "x": round(bbox["x"]),
                "y": round(bbox["y"]),
                "width": round(bbox["width"]),
                "height": round(bbox["height"])
            },
            "viewport_coverage": round(
                (bbox["width"] * bbox["height"]) /
                (viewport["width"] * viewport["height"]),
                4
            ),
            "center": {
                "x": bbox["x"] + bbox["width"] / 2,
                "y": bbox["y"] + bbox["height"] / 2
            },
            "importance_score": None,
            "scene_id": None
        }

    except Exception:
        return None

# -------------------------------------------------------------------
# PAGE EXTRACTION ENGINE
# -------------------------------------------------------------------

async def _extract_page(page: Page, url: str):
    viewport = page.viewport_size or {"width": 1280, "height": 720}
    page_height = await page.evaluate("document.body.scrollHeight")

    elements = []
    seen = set()

    for tag, selector in EXTRACT_TAGS.items():
        handles = await page.query_selector_all(selector)
        for el in handles:
            extracted = await _extract_element(el, tag, viewport)
            if not extracted:
                continue

            # ✅ Deduplication key includes isFixed
            key = f"{extracted['tag']}::{extracted['text']}::{extracted['isFixed']}"
            if key in seen:
                continue

            seen.add(key)
            elements.append(extracted)

    elements.sort(key=lambda e: (e["bbox"]["y"], e["bbox"]["x"]))

    return {
        "meta": {
            "url": url,
            "viewport": viewport,
            "page_height": page_height,
            "total_elements": len(elements),
            "extracted_at": datetime.now(timezone.utc).isoformat()
        },
        "elements": elements
    }

# -------------------------------------------------------------------
# MAIN EXTRACTOR
# -------------------------------------------------------------------

async def extract_website(url: str, headless: bool = True):
    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.launch(headless=headless)
            page = await browser.new_page(viewport={"width": 1280, "height": 720})

            print(f"🚀 Navigating: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            await page.wait_for_timeout(1500)

            unified = await _extract_page(page, url)

            legacy = {
                "title": await page.title(),
                "heading": {"h1": [], "h2": [], "h3": []},
                "buttons": [],
                "links": []
            }

            for el in unified["elements"]:
                if el["tag"] in legacy["heading"]:
                    legacy["heading"][el["tag"]].append(el["text"])
                elif el["tag"] == "button":
                    legacy["buttons"].append(el["text"])
                elif el["tag"] == "link":
                    legacy["links"].append({"text": el["text"], "url": el.get("href")})

            await browser.close()
            return unified, legacy

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return None, None

# -------------------------------------------------------------------
# RUN
# -------------------------------------------------------------------

async def main():
    url = input("Enter URL: ").strip()
    unified, legacy = await extract_website(url, headless=False)

    if unified:
        print("\n✅ TOTAL ELEMENTS:", unified["meta"]["total_elements"])
        print("\nSAMPLE:")
        print(unified["elements"][:5])

if __name__ == "__main__":
    asyncio.run(main())
