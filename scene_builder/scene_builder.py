from typing import Dict, List

def build_scenes(importance: Dict) -> Dict:
    """
    Group important elements into scenes based on category.
    
    Args:
        importance: Output from importance_engine — {"important_elements": [...]}
    
    Returns:
        scene_plan: {"scenes": [...]}
    """
    scene_plan: Dict[str, List[Dict]] = {"scenes": []}
    categories = ["hero", "skill", "project", "cta", "contact"]

    scene_id = 1
    for cat in categories:
        element_ids = [
            el["id"] for el in importance.get("important_elements", [])
            if el.get("category") == cat
        ]
        if element_ids:
            scene_plan["scenes"].append({
                "scene_id": scene_id,
                "type": cat,
                "element_ids": element_ids
            })
            scene_id += 1

    return scene_plan

# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    mock_importance = {
        "important_elements": [
            {"id": "el_001", "text": "Sumit", "category": "hero"},
            {"id": "el_002", "text": "Hello I'm", "category": "hero"},
            {"id": "el_010", "text": "Resume Analyzer", "category": "skill"},
        ]
    }

    scene_plan = build_scenes(mock_importance)
    print(json.dumps(scene_plan, indent=2))
