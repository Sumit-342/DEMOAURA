# importance_engine.py

def detect_category(element_text: str, tag: str, bbox: dict) -> str:
    text_lower = element_text.lower().strip()
    y = bbox.get("y", 9999)

    # --------------------------------------------------
    # Navigation Detection FIRST
    # --------------------------------------------------

    NAV_KEYWORDS = {
        "home",
        "about",
        "projects",
        "project",
        "skills",
        "services",
        "pricing",
        "contact",
        "blog",
        "features"
    }

    if tag == "link" and text_lower in NAV_KEYWORDS:
        return "navigation"

    # --------------------------------------------------
    # Hero Detection
    # --------------------------------------------------

    HERO_KEYWORDS = {
        "hello",
        "i'm",
        "i am",
        "developer",
        "engineer",
        "designer",
        "enthusiast",
        "full stack"
    }

    if tag == "h1" and y < 400:
        return "hero"

    if y < 800 and any(k in text_lower for k in HERO_KEYWORDS):
        return "hero"

    # --------------------------------------------------
    # Project Detection
    # (Skip navigation links)
    # --------------------------------------------------

    PROJECT_KEYWORDS = {
        "project",
        "portfolio",
        "generator",
        "analyzer",
        "dashboard",
        "tracker",
        "manager",
        "system",
        "github",
        "repository"
    }



    # Then project detection
    if tag in {"h1", "h2", "h3"} and any(
        k in text_lower for k in PROJECT_KEYWORDS
    ):
        return "project"
    
    if "github" in text_lower or "repository" in text_lower:
        return "project"

    if "live project" in text_lower:
        return "project"

    # --------------------------------------------------
    # Feature Detection
    # --------------------------------------------------

    if "feature" in text_lower or "benefit" in text_lower:
        return "feature"

    # --------------------------------------------------
    # CTA Detection
    # --------------------------------------------------

    CTA_KEYWORDS = {
        "get started",
        "try free",
        "hire me",
        "download",
        "contact me",
        "book call",
        "let's connect"
    }

    if tag in {"h1", "h2", "h3"} and any(
        k in text_lower for k in CTA_KEYWORDS
    ):
        return "cta"

    # --------------------------------------------------
    # Pricing Detection
    # --------------------------------------------------

    if "pricing" in text_lower or "$" in text_lower:
        return "pricing"

    # --------------------------------------------------
    # Testimonial Detection
    # --------------------------------------------------

    if "testimonial" in text_lower or "review" in text_lower:
        return "testimonial"

    # --------------------------------------------------
    # Skill Detection
    # --------------------------------------------------

    SKILL_KEYWORDS = {
        "skill",
        "skills",
        "expertise",
        "tech stack",
        "technology",
        "technical"
    }

    if any(k in text_lower for k in SKILL_KEYWORDS):
        return "skill"

    # --------------------------------------------------
    # Contact Detection
    # --------------------------------------------------

    CONTACT_KEYWORDS = {
        "contact",
        "email",
        "get in touch"
    }

    if any(k in text_lower for k in CONTACT_KEYWORDS):
        return "contact"

    # --------------------------------------------------
    # Noise Detection
    # --------------------------------------------------

    NOISE_KEYWORDS = {
        "cookie",
        "privacy",
        "terms",
        "footer",
        "copyright"
    }

    if any(k in text_lower for k in NOISE_KEYWORDS):
        return "noise"

    return "other"

def rank_importance(unified_data, purpose_data):
    seen_texts = set()
    important_elements = []
    ignored_count = 0

    for el in unified_data.get("elements", []):
        text = el.get("text", "")
        text_lower = text.lower()
        tag = el.get("tag", "")
        bbox = el.get("bbox", {})
        coverage = el.get("viewport_coverage", 0.0)
        element_id = el.get("id", "")

        # Deduplication
        if text_lower in seen_texts:
            continue
        seen_texts.add(text_lower)

        # Step 1: Category detection
        category = detect_category(text, tag, bbox)

        # Step 2: Base score
        weights = {"h1": 50, "h2": 35, "h3": 20, "button": 25, "link": 5}
        score = weights.get(tag, 10)
        reasons = [f"{tag} heading (+{score})"] if tag in weights else [f"default weight (+{score})"]

        # Navigation penalty
        if category == "navigation":
            score -= 40
            reasons.append("navigation penalty (-40)")

        # Step 3: Section-based boost
        if category == "hero":
            score += 30
            reasons.append("hero section boost (+30)")
        elif category == "project":
            score += 20
            reasons.append("project section boost (+20)")
        elif category == "cta":
            score += 15
            reasons.append("CTA section boost (+15)")
        elif category == "skill":
            score += 5
            reasons.append("skill section boost (+5)")

        # Step 4: Viewport coverage boost
        if coverage > 0.05:
            score += 15
            reasons.append("large viewport coverage (+15)")

        # Step 5: Purpose/category boost
        site_type = purpose_data.get("website_type", "")
        if site_type == "portfolio" and category == "project":
            score += 20
            reasons.append("portfolio project boost (+20)")
        if site_type == "portfolio" and category == "cta":
            score += 20
            reasons.append("portfolio CTA boost (+20)")

        AI_KEYWORDS = {"ai", "agent", "automation", "assistant", "generate", "model"}
        if site_type == "ai_tool" and any(k in text_lower for k in AI_KEYWORDS):
            score += 20
            reasons.append("AI tool keyword boost (+20)")

        if site_type == "saas" and category in ["pricing", "feature", "cta"]:
            score += 20
            reasons.append("SaaS boost (+20)")

        # Step 6: Noise penalty
        if category == "noise":
            score -= 100
            reasons.append("noise penalty (-100)")

        # Score cap
        score = min(score, 100)

        # Skip navigation and non-positive scores
        if category == "navigation" or score <= 0:
            ignored_count += 1
            continue

        # Final element object
        element_obj = {
            "id": element_id,
            "text": text,
            "tag": tag,
            "bbox": bbox,
            "viewport_coverage": coverage,
            "importance_score": score,
            "category": category,
            "reason": reasons
        }

        important_elements.append(element_obj)

    # Sort by score
    important_elements.sort(key=lambda x: x["importance_score"], reverse=True)

    # Limit top elements
    top_elements = important_elements[:25]

    return {
        "important_elements": top_elements,
        "ignored_elements": ignored_count
    }
