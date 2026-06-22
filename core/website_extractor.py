import asyncio
import uuid
import hashlib
import json
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page, ElementHandle
from understanding.purpose_engine import detect_purpose
from core.cleaner import clean_website_data
from importance.importance_engine import rank_importance
from scene_builder.coordinate_mapper import build_id_index , attach_coordinates
from scene_builder.scene_builder import build_scenes
from camera_planner.camera_planner import plan_camera 
from camera_planner.motion_planner import plan_motion
from camera_planner.transition_planner import plan_transitions
from camera_planner.timeline_planner import plan_timeline
from renderer.screenshot_engine import capture_screenshot

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

        page_y = await el.evaluate("""
        (node) => {
            const rect = node.getBoundingClientRect();
            return rect.top + window.scrollY;
        }
        """)

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
                "y": round(page_y),
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
                "y": page_y + bbox["height"] / 2
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
            await page.goto(
                url,
                wait_until="networkidle",   # ✅ better for modern JS frameworks
                timeout=15000
            )

            # ✅ Universal scroll to trigger lazy load
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = page.viewport_size["height"]

            for y in range(0, page_height, viewport_height):
                await page.evaluate(f"window.scrollTo(0,{y})")
                await page.wait_for_timeout(500)

            # ✅ Reset to top before extraction (for bbox consistency)
            await page.evaluate("window.scrollTo(0,0)")
            await page.wait_for_timeout(500)

            # ✅ Extract unified + legacy data
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

async def run_pipeline(url: str):
    # 1. Extract raw + legacy data
    unified, legacy = await extract_website(url, headless=False)

    if unified:
        print("\n✅ TOTAL ELEMENTS:", unified["meta"]["total_elements"])
        print("\nSAMPLE ELEMENTS:")
        for el in unified["elements"][:5]:
            print(el)
    
    if not legacy:
        print("❌ Extraction failed")
        return None

    # 2. Clean the legacy data
    cleaned = clean_website_data(legacy)

    # 3. Detect purpose
    purpose = detect_purpose(cleaned)
   

    # 4. Rank importance
    importance = rank_importance(unified, purpose)

    # Scene Builder
    scene_plan = build_scenes(importance)

    # Coordinate Mapper
    enriched_scenes = attach_coordinates(
        scene_plan,
        unified
    )

    # Camera Planner 
    camera_plan = plan_camera(enriched_scenes)

    # Motion Planner
    motion_plan = plan_motion(camera_plan)

    # Transition Planner
    transition_plan = plan_transitions(camera_plan)

    # Timeline Planner 
    timeline_plan = plan_timeline(
    motion_plan,
    transition_plan
    )

    # Taking Screenshot 
    screenshot_data = await capture_screenshot(url)
    
  
    result = {
        "purpose": purpose,
        "importance": importance,
        "scenes" : scene_plan,
        "enriched_scenes": enriched_scenes,
        "camera_plan" : camera_plan,
        "motion_plan" : motion_plan,
        "transition_plan": transition_plan,
        "timeline_plan" : timeline_plan,
        "screenshot" : screenshot_data,
    }

    # print("\n🎯 FULL PIPELINE OUTPUT:")
    # print(json.dumps(result, indent=4))

    print("\n🎥 CAMERA PLAN:")
    print(json.dumps(camera_plan, indent=4))

    print("\n🎞️ MOTION PLAN:")
    print(json.dumps(motion_plan, indent=4))

    print("\n🎞️ TRANSITION PLAN:")
    print(json.dumps(transition_plan, indent=4))

    print("\n⏱️ TIMELINE PLAN:")
    print(json.dumps(timeline_plan, indent=4))

    print("\n📸 SCREENSHOT:")
    print(json.dumps(screenshot_data, indent=4))
  

async def main():
    url = input("Enter URL: ").strip()
    result = await run_pipeline(url)

    if result:
        print("\n🎯 Pipeline Complete")
        print("Purpose:", result["purpose"]["website_type"])
        print("Top Important Elements:", len(result["importance"]["important_elements"]))

if __name__ == "__main__":
    asyncio.run(main())


