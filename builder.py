from pathlib import Path
import typer
from rich.console import Console

from core import (
    build_deck, open_in_anki, WORKSPACE_DIR, TEMPLATES_DIR, OUTPUT_DIR,
    TEMPLATE_VERSION, validate_json,
)

app = typer.Typer(
    name="anki-mcq-builder",
    help="a cli tool to generate Material 3 Anki MCQ decks from JSON.",
    add_completion=False,
)
console = Console()


def init(value: bool):
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
        readable=True,
    ),
    deck_name: str = typer.Argument(
        ...,
        help="title / name of the Anki deck to create",
    ),
    init_flag: bool = typer.Option(
        False,
        "--init",
        help="initialize the AnkiBuilder workspace directories",
        callback=init,
        is_eager=True,
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-to", "-o",
        help="directory / path to save .apkg file",
    ),
    open_file: bool = typer.Option(
        False,
        "--open",
        help="open and import the .apkg file directly into Anki",
    ),
):
    if not WORKSPACE_DIR.exists():
        console.print("[bold yellow]⚠ Workspace not found![/bold yellow]")
        console.print("Please run [bold cyan]anki-mcq-builder init[/bold cyan] first to set up your directories.")
        raise typer.Exit(code=1)

    with console.status(f"[bold cyan]Building deck '{deck_name}'...[/bold cyan]"):
        try:
            output_file = build_deck(json_path, deck_name, output_dir)
        except Exception as e:
            console.print(f"[bold red]Build error:[/bold red] {e}")
            raise typer.Exit(code=3)

    questions = validate_json(json_path)

    console.print(f"[bold green]✔ Successfully built[/bold green] [bold yellow]{output_file.name}[/bold yellow]")
    console.print(f"  • Notes: {len(questions)}\n  • Template: v{TEMPLATE_VERSION}\n  • Deck: '{deck_name}'")
    console.print(f"  • Saved to: {output_file.absolute()}")

    if open_file:
        console.print("[bold cyan]Opening .apkg file for import...[/bold cyan]")
        try:
            open_in_anki(output_file)
        except Exception as e:
            console.print(f"[bold red]Failed to open:[/bold red] {e}")


if __name__ == "__main__":
    app()
