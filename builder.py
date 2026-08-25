import json
from pathlib import Path
import genanki

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
REVIEWERS_DIR = BASE_DIR / "reviewers"

SCHEMA_VERSION = 6
MODEL_ID = 1607392360 + SCHEMA_VERSION
DECK_ID = 2059392460


def load(name: str) -> str:
    return (STATIC_DIR / name).read_text(encoding="utf-8")


THEME_CSS = load("_theme.css")
COMPONENT_CSS = load("style.css")
SHADOW_MOUNT_JS = load("shadow-mount.js")
MCQ_FRONT_JS = load("_mcq-front.js")
MCQ_BACK_JS = load("_mcq-back.js")

# CSS is embedded inside <template> for Shadow DOM encapsulation.
# Anki's own CSS injection (css= param) is not used — it would leak outside shadow.
EMBEDDED_CSS = THEME_CSS + "\n" + COMPONENT_CSS

FRONT_TEMPLATE = f"""
{load('front.html').replace('/*INJECT_CSS*/', EMBEDDED_CSS)}
<script>
{SHADOW_MOUNT_JS}
{MCQ_FRONT_JS}
(function() {{
  var rawChoicesEl = document.getElementById("raw-choices");
  var rawAnswerEl = document.getElementById("raw-answer");
  if (!rawChoicesEl || !rawAnswerEl) return;

  var choices = rawChoicesEl.innerHTML
    .split(/<br\\s*[\\/]?>|\\n/gi)
    .map(function(c) {{
      var t = document.createElement("div");
      t.innerHTML = c;
      return t.textContent.trim();
    }})
    .filter(function(c) {{ return c !== ""; }});

  var shadow = window.__m3ShadowRoot;
  if (window.initM3Front) initM3Front(choices, rawAnswerEl.textContent.trim(), shadow);
}})();
</script>
"""

BACK_TEMPLATE = f"""
{load('back.html').replace('/*INJECT_CSS*/', EMBEDDED_CSS)}
<script>
{SHADOW_MOUNT_JS}
{MCQ_BACK_JS}
if (window.initM3Back) initM3Back(window.__m3ShadowRoot);
</script>
"""

mcq_model = genanki.Model(
    MODEL_ID,
    f"Material 3 Expressive MCQ v{SCHEMA_VERSION}",
    fields=[
        {"name": "Question"},
        {"name": "Choices"},
        {"name": "Answer"},
        {"name": "Extra"},
    ],
    templates=[
        {
            "name": "MCQ Card",
            "qfmt": FRONT_TEMPLATE,
            "afmt": BACK_TEMPLATE,
        },
    ],
)

deck = genanki.Deck(DECK_ID, "Programming Languages Prelims")

with open(REVIEWERS_DIR / "programming-languages-prelims.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

for item in questions:
    if item["answer"] not in item["choices"]:
        raise ValueError(f"id {item['id']}: answer {item['answer']!r} not found in choices")
    if not (4 <= len(item["choices"]) <= 6):
        print(f"WARN id {item['id']}: {len(item['choices'])} choices (recommended 4-6)")

    deck.add_note(genanki.Note(
        model=mcq_model,
        guid=genanki.guid_for(str(item["id"])),
        fields=[
            item["question"],
            "<br>".join(item["choices"]),
            item["answer"],
            item.get("extra", ""),
        ],
    ))

output_file = BASE_DIR / "programming-languages-prelims.apkg"
genanki.Package(deck).write_to_file(output_file)

print(f"OK built {output_file.name} ({len(questions)} notes, schema v{SCHEMA_VERSION})")
