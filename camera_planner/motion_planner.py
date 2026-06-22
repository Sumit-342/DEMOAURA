from typing import List, Dict

def plan_motion(camera_plan: List[Dict]) -> List[Dict]:
    """
    Convert camera plan (labels + metadata) into motion plan (actual movement instructions).
    """

    output = []

    for scene in camera_plan:
        cam = scene.get("camera", {})
        shot_type = cam.get("shot")
        duration = cam.get("duration", 3)

        motion = {"type": shot_type, "duration": duration, "easing": "ease_in_out"}

        if shot_type == "zoom_in":
            motion.update({
                "start_scale": 1.0,
                "end_scale": 1.25
            })

        elif shot_type == "pan_down":
            bbox = cam.get("scene_bbox", {})
            motion.update({
                "start_y": bbox.get("y", 0),
                "end_y": bbox.get("y", 0) + bbox.get("height", 0)
            })

        elif shot_type == "focus":
            motion.update({
                "target": cam.get("focus_point"),
                "target_elements": cam.get("target_elements", [])
            })

        elif shot_type == "cta_zoom":
            motion.update({
                "start_scale": 1.0,
                "end_scale": 1.35
            })

        elif shot_type == "static":
            # Static frame, no movement
            pass

        scene_out = {
            "scene_id": scene["scene_id"],
            "type": scene.get("type"),
            "motion": motion,
        }

        output.append(scene_out)

    return output


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mock_camera_plan = [
        {
            "scene_id": 1,
            "camera": {
                "shot": "zoom_in",
                "duration": 3,
                "focus_point": {"x": 817.5, "y": 259},
                "scene_bbox": {"x": 484, "y": 164, "width": 667, "height": 190},
                "target_elements": ["el_1", "el_2"]
            }
        },
        {
            "scene_id": 2,
            "camera": {
                "shot": "pan_down",
                "duration": 4,
                "scene_bbox": {"x": 0, "y": 1440, "width": 1265, "height": 1031}
            }
        }
    ]

    result = plan_motion(mock_camera_plan)
    import json
    print(json.dumps(result, indent=2))
