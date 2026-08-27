from pathlib import Path
import json
import hashlib
import typer
from rich.console import Console
import genanki
import jsonschema
import os
import platform 
import subprocess
import shutil

app = typer.Typer(
    name="anki-mcq-builder",
    help="a cli tool to generate Material 3 Anki MCQ decks from JSON.",
    add_completion=False,
)
console = Console()

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
    """Generates a fixed Anki ID based on a string."""
    return int(hashlib.sha256(name.encode('utf-8')).hexdigest()[:8], 16)

def init(value: bool):
    """
    Initializes the AnkiBuilder workspace directories on your system.
    """
    if value:
        for directory in [TEMPLATES_DIR, OUTPUT_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            
        console.print("[bold green]✔ Workspace initialized successfully![/bold green]")
        console.print(f"  • [cyan]Templates (Put JSON here):[/cyan] {TEMPLATES_DIR}")
        console.print(f"  • [cyan]Decks (Output goes here):[/cyan] {OUTPUT_DIR}")
        raise typer.Exit()
    
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
    init: bool = typer.Option(
        False,
        "--init",
        help="initialize the AnkiBuilder workspace directories",
        callback=init,
        is_eager=True,
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-to", "-o",
        help="directory / path to save .apkg file"
    ),
    open_file: bool = typer.Option(
        False,
        "--open",
        help="open and import the .apkg file directly into Anki"
    ),
):
    if not WORKSPACE_DIR.exists():
        console.print("[bold yellow]⚠ Workspace not found![/bold yellow]")
        console.print("Please run [bold cyan]anki-mcq-builder init[/bold cyan] first to set up your directories.")
        raise typer.Exit(code=1)
        
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

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{deck_name}.apkg"
        else:
            output_file = OUTPUT_DIR / f"{deck_name}.apkg"
            
        genanki.Package(deck).write_to_file(output_file)

    console.print(f"[bold green]✔ Successfully built[/bold green] [bold yellow]{output_file.name}[/bold yellow]")
    console.print(f"  • Notes: {len(questions)}\n  • Template: v{TEMPLATE_VERSION}\n  • Deck: '{deck_name}'")
    console.print(f"  • Saved to: {output_file.absolute()}")

    if open_file:
        console.print("[bold cyan]Opening .apkg file for import...[/bold cyan]")
        try:
            ignore_logs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            
            match platform.system():
                case "Windows":
                    os.startfile(output_file)
                
                case "Darwin":
                    subprocess.Popen(["open", str(output_file)], **ignore_logs)

                case "Linux" if shutil.which("termux-open"):
                    subprocess.Popen(["termux-open", str(output_file)], **ignore_logs)
                    
                case "Linux":
                    if shutil.which("anki"):    
                        subprocess.Popen(["anki", str(output_file)], **ignore_logs)
                    elif shutil.which("gio"):
                        subprocess.Popen(["gio", "open", str(output_file)],  **ignore_logs)
                    else:
                        subprocess.Popen(["xdg-open", str(output_file)], **ignore_logs)
                
                case _:
                    subprocess.Popen(["xdg-open", str(output_file)], **ignore_logs)
                    
        except Exception as e:
            console.print(f"[bold red]Failed to open:[/bold red] {e}")

if __name__ == "__main__":
    app()
