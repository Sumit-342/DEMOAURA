import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def _compute_center(bbox: Dict) -> Dict:
    return {
        "x": round(bbox["x"] + bbox["width"] / 2, 2),
        "y": round(bbox["y"] + bbox["height"] / 2, 2),
    }

def build_id_index(unified: Dict) -> Dict[str, Dict]:
    """id -> element, O(1) lookup."""
    return {el["id"]: el for el in unified.get("elements", [])}

def attach_coordinates(scene_plan: Dict, unified: Dict) -> List[Dict]:
    """
    Enrich rule-based scene elements with bbox + center from unified extractor output.

    Args:
        scene_plan: Output from Scene Builder v1 — {scenes: [...]}
                    Each scene contains element_ids list.
        unified: Output from extract_website() — {meta, elements}

    Returns:
        List of enriched scenes, sorted by scene_id, ready for camera planning.
    """
    id_index = build_id_index(unified)
    enriched: List[Dict] = []

    # ✅ safer loop
    for scene in scene_plan.get("scenes", []):
        matched: List[Dict] = []
        unmatched: List[str] = []

        for eid in scene.get("element_ids", []):
            el = id_index.get(eid)
            if el and el.get("bbox"):
                bbox = el["bbox"]
                matched.append({
                    "id":     el["id"],
                    "text":   el["text"],
                    "tag":    el["tag"],
                    "bbox":   bbox,
                    "center": el.get("center") or _compute_center(bbox),
                })
            else:
                unmatched.append(eid)

        if unmatched:
            logger.warning(f"Unmatched ids in scene {scene.get('scene_id')}: {unmatched}")

        enriched.append({
            "scene_id":      scene.get("scene_id"),
            "type":          scene.get("type"),
            "element_count": len(matched),   # ✅ new field
            "elements":      matched,
            "camera":        None,           # reserved for future camera planner
        })

    # ✅ always return scenes strictly ordered by scene_id
    enriched.sort(key=lambda s: s["scene_id"])
    return enriched

# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    mock_unified = {
        "elements": [
            {"id": "el_001", "tag": "h1", "text": "Sumit", "bbox": {"x": 483, "y": 219, "width": 667, "height": 78}},
            {"id": "el_002", "tag": "h3", "text": "Hello, I'm", "bbox": {"x": 483, "y": 163, "width": 667, "height": 56}},
            {"id": "el_003", "tag": "button", "text": "View Projects", "bbox": {"x": 695, "y": 595, "width": 146, "height": 40}},
        ]
    }

    mock_scene_plan = {
        "scenes": [
            {
                "scene_id": 1,
                "type": "hero",
                "element_ids": ["el_001", "el_002", "el_003"],
            }
        ]
    }

    result = attach_coordinates(mock_scene_plan, mock_unified)
    print(json.dumps(result, indent=2))
