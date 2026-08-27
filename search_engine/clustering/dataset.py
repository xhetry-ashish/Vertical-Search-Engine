""" Task 2 document dataset for clustering."""

from __future__ import annotations


DATASET_VERSION = "task2-topic-separated-v2"


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
        "Economics finance market {a}, {b}, and {c} inflation interest investment trade bank company price wage productivity growth.",
        "Business economy banking {a}, {b}, and {c} investor credit consumer export import revenue employment household retail.",
        "Financial monetary fiscal {a}, {b}, and {c} debt mortgage manufacturing supply chain output budget property market.",
    ],
    "Entertainment": [
        "Entertainment film music {a}, {b}, and {c} audience cinema actor performer festival award celebrity streaming theatre.",
        "Culture media television {a}, {b}, and {c} album concert comedy game gallery fans critics red carpet box office.",
        "Creative arts performance {a}, {b}, and {c} director musician choreography stage animation documentary reality show review.",
    ],
    "Politics": [
        "Politics government parliament {a}, {b}, and {c} legislation election minister party voter law senate cabinet policy campaign.",
        "Public policy state {a}, {b}, and {c} opposition diplomat council committee constitutional immigration defence judicial reform.",
        "Government political authority {a}, {b}, and {c} debate bill official mayoral anticorruption national local service rule.",
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
