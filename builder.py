import json
import hashlib
from pathlib import Path
import typer
from rich.console import Console
import genanki

# Initialize Typer CLI and Rich Console for pretty printing
app = typer.Typer(
    name="anki-mcq-builder",
    help="A CLI tool to generate Material 3 Anki MCQ decks from JSON.",
    add_completion=False,
)
console = Console()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
SCHEMA_VERSION = 5

def load(name: str) -> str:
    return (STATIC_DIR / name).read_text(encoding="utf-8")

def generate_id(name: str) -> int:
    """Generates a stable, deterministic Anki ID based on a string."""
    return int(hashlib.sha256(name.encode('utf-8')).hexdigest()[:8], 16)

@app.command()
def build(
    json_path: Path = typer.Argument(
        ..., 
        help="Path to the JSON file containing questions",
        exists=True, 
        file_okay=True, 
        dir_okay=False, 
        readable=True
    ),
    deck_name: str = typer.Argument(
        ..., 
        help="Name of the Anki deck to create"
    ),
):
    """
    Builds a custom Material 3 .apkg Anki deck from a formatted JSON file.
    """
    with console.status(f"[bold cyan]Building deck '{deck_name}'...[/bold cyan]"):
        
        # Deterministic IDs
        MODEL_ID = generate_id(f"Material 3 Expressive MCQ v{SCHEMA_VERSION}")
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
            css=CSS,
        )

        deck = genanki.Deck(DECK_ID, deck_name)

        # Load JSON
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                questions = json.load(f)
            except json.JSONDecodeError as e:
                console.print(f"[bold red]Error parsing JSON:[/bold red] {e}")
                raise typer.Exit(code=1)

        # Build Notes
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
                guid=stable_guid
            )
            deck.add_note(note)

        # Export Package
        output_file = BASE_DIR / f"{json_path.stem}.apkg"
        genanki.Package(deck).write_to_file(output_file)

    console.print(f"[bold green]✔ Successfully built[/bold green] [bold yellow]{output_file.name}[/bold yellow]")
    console.print(f"  • Notes: {len(questions)}\n  • Schema: v{SCHEMA_VERSION}\n  • Deck: '{deck_name}'")

if __name__ == "__main__":
    app()
