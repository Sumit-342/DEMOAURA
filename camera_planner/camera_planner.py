from typing import List, Dict

def plan_camera(enriched_scenes: List[Dict]) -> List[Dict]:
    """
    Generate intelligent rule-based camera instructions for each scene.
    Adds focus_point, scene_bbox, and target_elements metadata.
    """

    output = []

    for scene in enriched_scenes:
        elements = scene.get("elements", [])

        # --- Focus Point (average of centers) ---
        if elements:
            focus_x = sum(el["center"]["x"] for el in elements) / len(elements)
            focus_y = sum(el["center"]["y"] for el in elements) / len(elements)
            focus_point = {"x": round(focus_x, 2), "y": round(focus_y, 2)}
        else:
            focus_point = None

        # --- Scene Bounding Box (union of all bboxes) ---
        if elements:
            left   = min(el["bbox"]["x"] for el in elements)
            top    = min(el["bbox"]["y"] for el in elements)
            right  = max(el["bbox"]["x"] + el["bbox"]["width"] for el in elements)
            bottom = max(el["bbox"]["y"] + el["bbox"]["height"] for el in elements)

            scene_bbox = {
                "x": left,
                "y": top,
                "width": round(right - left ,2),
                "height": round( bottom - top,2),
            }
        else:
            scene_bbox = None

        # --- Target Elements ---
        target_elements = [el["id"] for el in elements]

        # --- Rule-based shot selection ---
        shot = "static"
        duration = 3

        if scene["type"] == "hero":
            shot, duration = "zoom_in", 3

        elif scene["type"] == "skill":
            shot, duration = "pan_down", 4

        elif scene["type"] == "project":
            shot, duration = "focus", 4

        elif scene["type"] == "cta":
            shot, duration = "cta_zoom", 2

        elif scene["type"] == "contact":
            shot, duration = "static", 2

        scene_out = {
            "scene_id": scene["scene_id"],
            "type": scene["type"],
            "element_count": scene.get("element_count", 0),
            "camera": {
                "shot": shot,
                "duration": duration,
                "focus_point": focus_point,
                "scene_bbox": scene_bbox,
                "target_elements": target_elements
            }
        }

        output.append(scene_out)

    return output


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mock_scenes = [
        {
            "scene_id": 1,
            "type": "hero",
            "elements": [
                {"id": "el_1", "bbox": {"x": 484, "y": 164, "width": 667, "height": 56}, "center": {"x": 817.5, "y": 192}},
                {"id": "el_2", "bbox": {"x": 484, "y": 298, "width": 667, "height": 56}, "center": {"x": 817.5, "y": 326}},
            ]
        }
    ]

    result = plan_camera(mock_scenes)
    import json
    print(json.dumps(result, indent=2))
