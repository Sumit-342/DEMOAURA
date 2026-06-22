from typing import List, Dict

def plan_transitions(camera_plan: List[Dict]) -> List[Dict]:
    """
    Generate transitions between consecutive scenes based on simple rules.
    """

    transitions = []

    for current, next_scene in zip(camera_plan, camera_plan[1:]):
        current_id = current["scene_id"]
        next_id = next_scene["scene_id"]

        current_camera = current.get("camera", {})
        next_camera = next_scene.get("camera", {})

        current_bbox = current_camera.get("scene_bbox", {})
        next_bbox = next_camera.get("scene_bbox", {})

        current_y = current_bbox.get("y", 0)
        next_y = next_bbox.get("y", 0)
        

        transition_type = "cut"
        duration = 0.3

        # Rule 1: next scene is below current → smooth scroll
        if next_y > current_y:
            transition_type = "smooth_scroll"
            duration = 1.2

        # Rule 2: CTA or Contact → fade
        if next_scene["type"] in ["cta", "contact"]:
            transition_type = "fade"
            duration = 0.8

        # Rule 3: default already set → cut

        transitions.append({
            "from_scene": current_id,
            "to_scene": next_id,
            "transition": transition_type,
            "duration": duration
        })

    return transitions


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mock_camera_plan = [
        {"scene_id": 1, "type": "hero", "camera": {"scene_bbox": {"y": 100}}},
        {"scene_id": 2, "type": "skill", "camera": {"scene_bbox": {"y": 800}}},
        {"scene_id": 3, "type": "project", "camera": {"scene_bbox": {"y": 1600}}},
        {"scene_id": 4, "type": "cta", "camera": {"scene_bbox": {"y": 2500}}},
        {"scene_id": 5, "type": "contact", "camera": {"scene_bbox": {"y": 3000}}},
    ]

    result = plan_transitions(mock_camera_plan)
    import json
    print(json.dumps(result, indent=2))
