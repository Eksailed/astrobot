from typing import Any
from services.astrology.constants import ASPECTS


def calculate_synastry(chart_a: dict[str, Any], chart_b: dict[str, Any]) -> dict[str, Any]:
    """
    Calculates inter-aspects between two charts (Synastry),
    domain compatibility scores, and overall compatibility percentage.
    """
    planets_a = chart_a.get("planets", {})
    planets_b = chart_b.get("planets", {})

    inter_aspects = []

    # Calculate all inter-planetary aspects
    for name_a, data_a in planets_a.items():
        lon_a = data_a.get("longitude", 0.0)
        ru_a = data_a.get("name_ru", name_a)

        for name_b, data_b in planets_b.items():
            lon_b = data_b.get("longitude", 0.0)
            ru_b = data_b.get("name_ru", name_b)

            diff = abs(lon_a - lon_b) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff

            for asp in ASPECTS:
                orb = abs(diff - asp["angle"])
                if orb <= asp["orb"]:
                    inter_aspects.append({
                        "planet_a": ru_a,
                        "planet_b": ru_b,
                        "name_a_en": name_a,
                        "name_b_en": name_b,
                        "aspect": asp["ru"],
                        "symbol": asp["symbol"],
                        "orb": round(orb, 2),
                        "nature": asp["nature"],
                    })

    # Domain Scores (Base 50%)
    love_score = 55
    emotional_score = 55
    intellect_score = 55
    stability_score = 50

    highlights = []
    challenges = []

    for asp in inter_aspects:
        p_a = asp["name_a_en"]
        p_b = asp["name_b_en"]
        nature = asp["nature"]
        text_rep = f"{asp['planet_a']} {asp['symbol']} {asp['planet_b']}"

        # 1. Love & Chemistry (Sun/Moon, Venus/Mars)
        if {p_a, p_b} in [{"Venus", "Mars"}, {"Sun", "Venus"}, {"Moon", "Venus"}]:
            if nature == "harmonious":
                love_score += 12
                highlights.append(f"Магнетическое влечение и гармония чувств ({text_rep})")
            elif nature == "neutral":  # Conjunction
                love_score += 15
                highlights.append(f"Мощное слияние энергий и страсть ({text_rep})")
            else:  # Tense
                love_score += 6
                challenges.append(f"Искры и бурные эмоции, требующие компромиссов ({text_rep})")

        # 2. Emotional Harmony (Moon/Moon, Sun/Moon)
        if {p_a, p_b} in [{"Moon", "Moon"}, {"Sun", "Moon"}]:
            if nature in ["harmonious", "neutral"]:
                emotional_score += 14
                highlights.append(f"Глубокое душевное родство и понимание без слов ({text_rep})")
            else:
                emotional_score -= 8
                challenges.append(f"Разные привычки и бытовые эмоциональные реакции ({text_rep})")

        # 3. Intellect & Communication (Mercury)
        if "Mercury" in [p_a, p_b] and ("Mercury" in [p_a, p_b] or "Sun" in [p_a, p_b] or "Jupiter" in [p_a, p_b]):
            if nature in ["harmonious", "neutral"]:
                intellect_score += 12
                highlights.append(f"Общий язык и интересные совместные беседы ({text_rep})")
            else:
                intellect_score -= 6
                challenges.append(f"Периодические споры из-за разного взгляда на факты ({text_rep})")

        # 4. Long-term Stability (Saturn/Jupiter)
        if "Saturn" in [p_a, p_b] and any(x in [p_a, p_b] for x in ["Sun", "Moon", "Venus"]):
            if nature in ["harmonious", "neutral"]:
                stability_score += 14
                highlights.append(f"Кармический цемент отношений: надежность и преданность ({text_rep})")
            else:
                stability_score -= 8
                challenges.append(f"Чувство взаимных обязательств или легкой критики ({text_rep})")

    # Normalize scores between 45 and 98
    love_score = min(max(love_score, 45), 98)
    emotional_score = min(max(emotional_score, 40), 98)
    intellect_score = min(max(intellect_score, 42), 97)
    stability_score = min(max(stability_score, 38), 96)

    overall_score = round(
        (love_score * 0.35) + (emotional_score * 0.30) + (intellect_score * 0.15) + (stability_score * 0.20)
    )

    if not highlights:
        highlights.append("Индивидуальная динамика: вы даете друг другу пространство для роста")
    if not challenges:
        challenges.append("Мягкая аспектарная связь, важно поддерживать совместные цели")

    return {
        "overall_percentage": overall_score,
        "love_score": love_score,
        "emotional_score": emotional_score,
        "intellect_score": intellect_score,
        "stability_score": stability_score,
        "highlights": highlights[:3],
        "challenges": challenges[:3],
        "inter_aspects_count": len(inter_aspects),
        "inter_aspects": inter_aspects,
    }
