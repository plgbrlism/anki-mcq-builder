from pathlib import Path
import json
import hashlib
import os
import platform
import subprocess
import shutil

import genanki
import jsonschema

SRC_DIR = Path(__file__).resolve().parent

current_os = platform.system()
if current_os == "Windows":
    base_dir = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
elif current_os == "Darwin":
    base_dir = Path.home() / "Library" / "Application Support"
else:
    base_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))

WORKSPACE_DIR = base_dir / "AnkiBuilder"
TEMPLATES_DIR = WORKSPACE_DIR / "templates"
OUTPUT_DIR = WORKSPACE_DIR / "decks"

ASSETS = SRC_DIR / "static"
TEMPLATE_VERSION = 5

MCQ_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": ["integer", "string"]},
            "question": {"type": "string"},
            "choices": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2
            },
            "answer": {"type": "string"},
            "extra": {"type": "string"},
            "tags": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["id", "question", "choices", "answer"]
    }
}


def load(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


def generate_id(name: str) -> int:
    return int(hashlib.sha256(name.encode('utf-8')).hexdigest()[:8], 16)


def load_css() -> str:
    return load("_theme.css") + "\n" + load("style.css")


def front_template() -> str:
    return f"""
{load('front.html')}
<script>
{load('_mcq-front.js')}
(function() {{
  const rawChoicesEl = document.getElementById("raw-choices");
  if (!rawChoicesEl) return;

  const choices = rawChoicesEl.innerHTML
    .split(/<br\\s*[\\/]?>|\\n/gi)
    .map(c => {{
      const t = document.createElement("div");
      t.innerHTML = c;
      return t.textContent.trim();
    }})
    .filter(Boolean);

  if (window.initM3Front) initM3Front(choices);
}})();
</script>
"""


def back_template() -> str:
    return f"""
{load('back.html')}
<script>
{load('_mcq-back.js')}
if (window.initM3Back) initM3Back();
</script>
"""


def make_model() -> genanki.Model:
    model_id = generate_id(f"Material Design 3  MCQ v{TEMPLATE_VERSION}")
    return genanki.Model(
        model_id,
        f"Material Design 3 MCQ v{TEMPLATE_VERSION}",
        fields=[
            {"name": "Question"},
            {"name": "Choices"},
            {"name": "Answer"},
            {"name": "Extra"},
        ],
        templates=[
            {
                "name": "MCQ Card",
                "qfmt": front_template(),
                "afmt": back_template(),
            },
        ],
        css=load_css(),
    )


def make_deck(deck_name: str) -> genanki.Deck:
    deck_id = generate_id(deck_name)
    return genanki.Deck(deck_id, deck_name)


def validate_json(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    jsonschema.validate(instance=questions, schema=MCQ_SCHEMA)

    for item in questions:
        if item["answer"] not in item["choices"]:
            raise ValueError(
                f"Question ID {item['id']}: answer '{item['answer']}' "
                f"not in choices"
            )

    return questions


def build_deck(json_path: Path, deck_name: str, output_dir: Path = None) -> Path:
    questions = validate_json(json_path)
    model = make_model()
    deck = make_deck(deck_name)

    for item in questions:
        stable_guid = genanki.guid_for(deck_name, item["id"])
        note = genanki.Note(
            model=model,
            fields=[
                item["question"],
                "<br>".join(item["choices"]),
                item["answer"],
                item.get("extra", ""),
            ],
            tags=item.get("tags", []),
            guid=stable_guid,
        )
        deck.add_note(note)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{deck_name}.apkg"
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / f"{deck_name}.apkg"

    genanki.Package(deck).write_to_file(output_file)
    return output_file


def open_in_anki(path: Path) -> None:
    ignore_logs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}

    match platform.system():
        case "Windows":
            os.startfile(path)

        case "Darwin":
            subprocess.Popen(["open", str(path)], **ignore_logs)

        case "Linux" if shutil.which("termux-open"):
            subprocess.Popen(["termux-open", str(path)], **ignore_logs)

        case "Linux":
            if shutil.which("anki"):
                subprocess.Popen(["anki", str(path)], **ignore_logs)
            elif shutil.which("gio"):
                subprocess.Popen(["gio", "open", str(path)], **ignore_logs)
            else:
                subprocess.Popen(["xdg-open", str(path)], **ignore_logs)

        case _:
            subprocess.Popen(["xdg-open", str(path)], **ignore_logs)
