from typing import List, Dict

def plan_timeline(motion_plan: List[Dict], transition_plan: List[Dict]) -> List[Dict]:
    """
    Generate timeline with start and end times for scenes and transitions.
    """

    timeline = []
    current_time = 0.0

    # Build a lookup for transitions by (from_scene, to_scene)
    transition_lookup = {
        (t["from_scene"], t["to_scene"]): t for t in transition_plan
    }

    for i, scene in enumerate(motion_plan):
        duration = scene["motion"].get("duration", 3)

        # Scene entry
        scene_entry = {
            "scene_id": scene["scene_id"],
            "type": scene.get("type"),
            "start_time": round(current_time, 2),
            "end_time": round(current_time + duration, 2)
        }
        timeline.append(scene_entry)

        current_time += duration

        # Transition entry (if not last scene)
        if i < len(motion_plan) - 1:
            next_scene_id = motion_plan[i + 1]["scene_id"]
            transition = transition_lookup.get((scene["scene_id"], next_scene_id))

            if transition:
                t_duration = transition.get("duration", 0.5)
                transition_entry = {
                    "transition": transition["transition"],
                    "from_scene": scene["scene_id"],
                    "to_scene": next_scene_id,
                    "start_time": round(current_time, 2),
                    "end_time": round(current_time + t_duration, 2)
                }
                timeline.append(transition_entry)
                current_time += t_duration

    total_duration = round(current_time, 2)

    return {
    "timeline": timeline,
    "total_duration": total_duration
}




# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mock_motion_plan = [
        {"scene_id": 1, "motion": {"type": "zoom_in", "duration": 3}},
        {"scene_id": 2, "motion": {"type": "pan_down", "duration": 4}},
    ]

    mock_transition_plan = [
        {"from_scene": 1, "to_scene": 2, "transition": "smooth_scroll", "duration": 1.2}
    ]

    result = plan_timeline(mock_motion_plan, mock_transition_plan)
    import json
    print(json.dumps(result, indent=2))
