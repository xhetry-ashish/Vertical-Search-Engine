"""Sample Task 2 document dataset for clustering."""

from __future__ import annotations


ECONOMICS_TOPICS = [
    ("inflation", "central banks", "interest rates"),
    ("household spending", "consumer confidence", "retail sales"),
    ("employment growth", "wage pressure", "labour markets"),
    ("currency depreciation", "exports", "trade balance"),
    ("public debt", "government borrowing", "bond yields"),
    ("energy prices", "manufacturing costs", "supply chains"),
    ("housing demand", "mortgage rates", "property prices"),
    ("tax policy", "business investment", "economic growth"),
    ("stock markets", "corporate earnings", "investor sentiment"),
    ("bank lending", "small businesses", "credit conditions"),
    ("global trade", "shipping costs", "import prices"),
    ("productivity", "technology adoption", "output per worker"),
    ("recession risk", "consumer demand", "forecast models"),
    ("foreign investment", "infrastructure projects", "regional development"),
    ("food prices", "agricultural output", "household budgets"),
]

ENTERTAINMENT_TOPICS = [
    ("film festival", "independent directors", "international awards"),
    ("streaming platform", "new drama series", "viewer ratings"),
    ("music tour", "stadium concerts", "ticket sales"),
    ("television comedy", "season finale", "audience reaction"),
    ("video game release", "online players", "review scores"),
    ("theatre production", "stage performers", "opening night"),
    ("celebrity interview", "fashion event", "social media"),
    ("animation studio", "family audience", "box office"),
    ("documentary film", "cultural history", "critics"),
    ("award ceremony", "red carpet", "nominations"),
    ("pop album", "music charts", "radio play"),
    ("reality show", "contestants", "public voting"),
    ("comedy special", "live audience", "stand-up performance"),
    ("art exhibition", "gallery visitors", "creative installations"),
    ("dance performance", "choreography", "festival programme"),
]

POLITICS_TOPICS = [
    ("parliament debate", "new legislation", "opposition parties"),
    ("election campaign", "voter turnout", "policy promises"),
    ("foreign minister", "diplomatic talks", "regional security"),
    ("public health policy", "government funding", "local councils"),
    ("climate bill", "energy targets", "parliament committee"),
    ("budget statement", "tax changes", "cabinet ministers"),
    ("constitutional reform", "legal experts", "public consultation"),
    ("immigration policy", "border rules", "human rights groups"),
    ("education reform", "school funding", "teacher unions"),
    ("defence strategy", "military spending", "international allies"),
    ("mayoral election", "city transport", "campaign pledges"),
    ("anti-corruption inquiry", "public officials", "ethics rules"),
    ("trade agreement", "negotiators", "national parliament"),
    ("judicial appointment", "senate hearing", "legal committee"),
    ("local government", "planning rules", "community services"),
]

TEMPLATES = {
    "Economics": [
        "Economics report: {a} influenced {b} as analysts watched {c} across markets.",
        "A business update explained how {b} responded to {a} while households adjusted to {c}.",
        "Financial researchers linked {a}, {b}, and {c} to changes in growth and investment.",
    ],
    "Entertainment": [
        "Entertainment report: the {a} highlighted {b} and generated attention from {c}.",
        "Reviewers discussed how {b} shaped the {a} while fans followed updates from {c}.",
        "Culture writers connected {a}, {b}, and {c} in coverage of the entertainment industry.",
    ],
    "Politics": [
        "Politics report: the {a} focused on {b} as {c} responded to the proposal.",
        "Government coverage explained how {b} affected the {a} while {c} prepared statements.",
        "Political analysts linked {a}, {b}, and {c} to wider public policy debates.",
    ],
}


def _build_category_documents(category: str, topics: list[tuple[str, str, str]]) -> list[dict]:
    documents = []
    templates = TEMPLATES[category]

    for topic in topics:
        for template in templates:
            documents.append(
                {
                    "category": category,
                    "text": template.format(a=topic[0], b=topic[1], c=topic[2]),
                }
            )

    return documents


def build_sample_dataset() -> list[dict]:
    """Return 135 short documents across Economics, Entertainment, and Politics."""
    return (
        _build_category_documents("Economics", ECONOMICS_TOPICS)
        + _build_category_documents("Entertainment", ENTERTAINMENT_TOPICS)
        + _build_category_documents("Politics", POLITICS_TOPICS)
    )
