from typing import List, Dict

def plan_camera(enriched_scenes: List[Dict]) -> List[Dict]:
    """
    Generate simple rule-based camera instructions for each scene.
    Args:
        enriched_scenes: List of enriched scene dicts (with bbox + center).
    Returns:
        List of scenes with camera instructions added.
    """

    output = []

    for scene in enriched_scenes:
        shot = None
        duration = None

        if scene["type"] == "hero":
            shot = "zoom_in"
            duration = 3

        elif scene["type"] == "skill":
            shot = "pan_down"
            duration = 4

        elif scene["type"] == "project":
            shot = "focus"
            duration = 4

        elif scene["type"] == "cta":
            shot = "cta_zoom"
            duration = 2

        elif scene["type"] == "contact":
            shot = "static"
            duration = 2

        scene_out = {
            "scene_id": scene["scene_id"],
            "type": scene["type"],
            "element_count": scene.get("element_count", 0),
            "camera": {
                "shot": shot,
                "duration": duration
            }
        }


        output.append(scene_out)

    return output


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mock_scenes = [
        {"scene_id": 1, "type": "hero", "elements": []},
        {"scene_id": 2, "type": "skill", "elements": []},
        {"scene_id": 3, "type": "project", "elements": []},
        {"scene_id": 4, "type": "cta", "elements": []},
        {"scene_id": 5, "type": "contact", "elements": []},
    ]

    result = plan_camera(mock_scenes)
    import json
    print(json.dumps(result, indent=2))
