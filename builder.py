from pathlib import Path
import json
import hashlib
import typer
from rich.console import Console
import genanki
import jsonschema

app = typer.Typer(
    name="anki-mcq-builder",
    help="a cli tool to generate Material 3 Anki MCQ decks from JSON.",
    add_completion=False,
)
console = Console()

SRC_DIR = Path(__file__).resolve().parent
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
    """Generates a fixed Anki ID based on a string."""
    return int(hashlib.sha256(name.encode('utf-8')).hexdigest()[:8], 16)

@app.command()
def build(
    json_path: Path = typer.Argument(
        ...,
        help="path to the JSON file containing questions",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    deck_name: str = typer.Argument(
        ...,
        help="title / name of the Anki deck to create"
    ),
):
    """
    Builds a custom Material Design 3 .apkg Anki deck from a formatted JSON file.
    """
    with console.status(f"[bold cyan]Building deck '{deck_name}'...[/bold cyan]"):

        MODEL_ID = generate_id(f"Material Design 3  MCQ v{TEMPLATE_VERSION}")
        DECK_ID = generate_id(deck_name)

        CSS = load("_theme.css") + "\n" + load("style.css")

        FRONT_TEMPLATE = f"""
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

        BACK_TEMPLATE = f"""
{load('back.html')}
<script>
{load('_mcq-back.js')}
if (window.initM3Back) initM3Back();
</script>
"""

        mcq_model = genanki.Model(
            MODEL_ID,
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
                    "qfmt": FRONT_TEMPLATE,
                    "afmt": BACK_TEMPLATE,
                },
            ],
            css=CSS,
        )

        deck = genanki.Deck(DECK_ID, deck_name)

        with open(json_path, "r", encoding="utf-8") as f:
            try:
                questions = json.load(f)
            except json.JSONDecodeError as e:
                console.print(f"[bold red]Error parsing JSON:[/bold red] {e}")
                raise typer.Exit(code=1)

        try:
            jsonschema.validate(instance=questions, schema=MCQ_SCHEMA)
        except jsonschema.ValidationError as e:
            console.print(f"[bold red]Schema Validation Error:[/bold red] {e.message}")
            raise typer.Exit(code=1)

        for item in questions:
            if item["answer"] not in item["choices"]:
                console.print(f"[bold red]Data Error in Question ID {item['id']}:[/bold red] Answer '{item['answer']}' does not exactly match any item in choices.")
                raise typer.Exit(code=1)

        for item in questions:
            stable_guid = genanki.guid_for(deck_name, item["id"])
            note = genanki.Note(
                model=mcq_model,
                fields=[
                    item["question"],
                    "<br>".join(item["choices"]),
                    item["answer"],
                    item.get("extra", ""),
                ],
                tags=item.get("tags", []),
                guid=stable_guid
            )
            deck.add_note(note)

        output_file = SRC_DIR / f"{json_path.stem}.apkg"
        genanki.Package(deck).write_to_file(output_file)

    console.print(f"[bold green]✔ Successfully built[/bold green] [bold yellow]{output_file.name}[/bold yellow]")
    console.print(f"  • Notes: {len(questions)}\n  • Template: v{TEMPLATE_VERSION}\n  • Deck: '{deck_name}'")

if __name__ == "__main__":
    app()
