import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def _compute_center(bbox: Dict) -> Dict:
    return {
        "x": round(bbox["x"] + bbox["width"] / 2, 2),
        "y": round(bbox["y"] + bbox["height"] / 2, 2),
    }


def build_id_index(unified: Dict) -> Dict[str, Dict]:
    """id -> element lookup"""
    return {
        el["id"]: el
        for el in unified.get("elements", [])
        if "id" in el
    }


def attach_coordinates(scene_plan: Dict, unified: Dict) -> List[Dict]:
    """
    Enrich scene elements with bbox + center coordinates.

    Args:
        scene_plan:
        {
            "scenes": [...]
        }

        unified:
        {
            "meta": {...},
            "elements": [...]
        }

    Returns:
        [
            {
                "scene_id": ...,
                "type": ...,
                "element_count": ...,
                "elements": [...],
                "camera": None
            }
        ]
    """

    id_index = build_id_index(unified)
    enriched: List[Dict] = []

    for scene in scene_plan.get("scenes", []):

        matched: List[Dict] = []
        unmatched: List[str] = []

        for eid in scene.get("element_ids", []):

            el = id_index.get(eid)

            if not el:
                unmatched.append(eid)
                continue

            bbox = el.get("bbox")

            if not bbox:
                unmatched.append(eid)
                continue

            # Create safe copy (never mutate original extractor output)
            clean_bbox = {
                "x": max(0, bbox["x"]),
                "y": max(0, bbox["y"]),
                "width": bbox["width"],
                "height": bbox["height"],
            }

            matched.append({
                "id": el["id"],
                "text": el.get("text", ""),
                "tag": el.get("tag", ""),
                "bbox": clean_bbox,
                "center": _compute_center(clean_bbox),
            })

        if unmatched:
            logger.warning(
                f"Unmatched ids in scene {scene.get('scene_id')}: {unmatched}"
            )

        enriched.append({
            "scene_id": scene.get("scene_id"),
            "type": scene.get("type"),
            "element_count": len(matched),
            "elements": matched,
            "camera": None,   # Camera Planner will fill this later
        })

    enriched.sort(key=lambda s: s["scene_id"])

    return enriched