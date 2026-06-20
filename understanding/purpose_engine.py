import re
import json

VALID_TYPES = {
    "portfolio", "saas", "startup", "ai_tool", "ecommerce", "agency",
    "landing_page", "blog", "education", "documentation", "dashboard",
    "community", "unknown"
}
def _detect_website_type(clean_data: dict) -> tuple[str, float, str]:
    title = clean_data.get("title", "").lower()
    h1 = " ".join(clean_data.get("heading", {}).get("h1", [])).lower()
    h2 = " ".join(clean_data.get("heading", {}).get("h2", [])).lower()
    buttons = " ".join(clean_data.get("buttons", [])).lower()

    text_blob = " ".join([title, h1, h2, buttons])

    keyword_map = {
        "portfolio": ["projects", "skills", "hire me", "portfolio"],
        "saas": ["start free trial", "pricing", "subscription", "platform"],
        "ai_tool": ["ai", "generate", "assistant", "model", "automation"],
        "ecommerce": ["buy now", "cart", "₹", "price"],
        "blog": ["blog", "read more", "articles", "posts"],
        "education": ["course", "enroll", "syllabus", "learn"],
        "agency": ["services", "clients", "case studies", "our work"],
        "documentation": ["api", "docs", "guides", "reference"],
        "dashboard": ["analytics", "reports", "metrics", "dashboard"],
        "community": ["forum", "members", "join", "discussion"],
        "landing_page": ["sign up", "cta", "get started"],
        "startup": ["investors","vision","mission","funding","early access"],
    }

    scores = {k: 0 for k in keyword_map.keys()}

    for category, keywords in keyword_map.items():
        for kw in keywords:
            if kw in text_blob:
                scores[category] += 1

    website_type = max(scores, key=scores.get)
    score = scores[website_type]

    if score == 0:
        website_type = "unknown"
        confidence = 0.5
        reasoning = "No strong keyword matches found."
    else:
        confidence = min(0.95, 0.6 + score * 0.1)  # clamp confidence
        reasoning = f"Detected {website_type} because {score} keyword(s) matched."

    return website_type, confidence, reasoning




def _extract_primary_goal(website_type: str) -> str:
    goals = {
        "portfolio": "showcase skills and projects",
        "saas": "convert visitors into trial users",
        "ecommerce": "sell products online",
        "blog": "share knowledge and articles",
        "education": "teach and enroll students",
        "agency": "promote services and attract clients",
        "startup": "pitch vision and attract investors",
        "ai_tool": "offer AI-powered functionality",
        "landing_page": "drive sign-ups or conversions",
        "documentation": "provide technical reference",
        "dashboard": "display analytics and metrics",
        "community": "connect members and foster discussion",
        "unknown": "unknown"
    }
    return goals.get(website_type, "unknown")


def _extract_main_message(clean_data: dict) -> str:
    title = clean_data.get("title", "")
    h1 = clean_data.get("heading", {}).get("h1", [])
    if h1:
        return h1[0]
    elif title:
        return title
    return "unknown"



def _detect_target_audience(website_type: str) -> list[str]:
    audiences = {
        "portfolio": ["recruiters", "clients", "developers"],
        "saas": ["businesses", "startups", "tech users"],
        "ecommerce": ["consumers", "shoppers"],
        "blog": ["readers", "subscribers"],
        "education": ["students", "teachers"],
        "agency": ["clients", "businesses"],
        "startup": ["investors", "early adopters"],
        "ai_tool": ["developers", "creators", "tech enthusiasts"],
        "landing_page": ["potential customers"],
        "documentation": ["developers", "users"],
        "dashboard": ["analysts", "managers"],
        "community": ["members", "contributors"],
        "unknown": []
    }
    return audiences.get(website_type, [])



def detect_purpose(clean_data: dict) -> dict:
    website_type, confidence, reasoning = _detect_website_type(clean_data)
    if website_type not in VALID_TYPES:
        website_type = "unknown"

    return {
        "website_type": website_type,
        "confidence": confidence,
        "primary_goal": _extract_primary_goal(website_type),
        "main_message": _extract_main_message(clean_data),
        "target_audience": _detect_target_audience(website_type),
        "reasoning": reasoning
    }


if __name__ == "__main__":
    sample_clean_data = {
        "title": "Sumit | Full Stack Developer",
        "heading": {
            "h1": ["Hi, I'm Sumit", "I Build Things for the Web"],
            "h2": ["About Me", "Projects", "Skills", "Contact"],
            "h3": ["Resume Analyzer", "Portfolio Website", "AI Video Generator"],
        },
        "buttons": ["View Projects", "Download CV", "Hire Me"],
        "links": [
            {"text": "GitHub", "url": "https://github.com/sumit"},
            {"text": "LinkedIn", "url": "https://linkedin.com/in/sumit"},
        ],
    }

    result = detect_purpose(sample_clean_data)
    print(json.dumps(result, indent=2))
