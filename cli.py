#!/usr/bin/env python3
import sys
import os
import json
import tempfile
import time
from pathlib import Path
from collections import Counter

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from core import (
    build_deck, open_in_anki, validate_json, load_css, load,
    front_template, back_template, make_model, make_deck,
    WORKSPACE_DIR, TEMPLATES_DIR, OUTPUT_DIR, ASSETS, TEMPLATE_VERSION,
)

console = Console()

app = typer.Typer(
    name="anki-mcq-builder",
    help="a cli tool to generate Material 3 Anki MCQ decks from JSON.",
    add_completion=False,
)


def _ensure_workspace():
    if not WORKSPACE_DIR.exists():
        console.print("[bold yellow]⚠ Workspace not found![/bold yellow]")
        console.print("Run [bold cyan]anki-mcq-builder build --init[/bold cyan] first.")
        raise typer.Exit(code=4)


def _read_json(path: Path = None) -> list:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if not sys.stdin.isatty():
        return json.load(sys.stdin)
    console.print("[bold red]Error:[/bold red] No input file and no piped data.")
    raise typer.Exit(code=2)


def _load_config() -> dict:
    defaults = {
        "output_dir": str(OUTPUT_DIR),
        "auto_open": False,
        "template_version": TEMPLATE_VERSION,
    }
    search = [
        Path("anki-mcq-builder.toml"),
        Path.home() / ".config" / "anki-mcq-builder" / "config.toml",
    ]
    try:
        import tomllib
    except ModuleNotFoundError:
        return defaults

    for p in search:
        if p.exists():
            with open(p, "rb") as f:
                cfg = tomllib.load(f)
            return {**defaults, **cfg}
    return defaults


def _parse_questions(path: Path = None) -> list:
    data = _read_json(path)
    try:
        return validate_json(
            path if path else _write_temp_json(data)
        )
    except Exception as e:
        console.print(f"[bold red]Validation error:[/bold red] {e}")
        raise typer.Exit(code=1)


def _write_temp_json(data: list) -> Path:
    p = Path(tempfile.mktemp(suffix=".json"))
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


@app.command(name="init")
def init_cmd():
    for d in [TEMPLATES_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    console.print("[bold green]✔ Workspace initialized![/bold green]")
    console.print(f"  • [cyan]Templates:[/cyan] {TEMPLATES_DIR}")
    console.print(f"  • [cyan]Decks:[/cyan] {OUTPUT_DIR}")


@app.command(name="build")
def build_cmd(
    json_path: Path = typer.Argument(..., exists=True, readable=True),
    deck_name: str = typer.Argument(...),
    output_dir: Path = typer.Option(None, "--output-to", "-o"),
    open_file: bool = typer.Option(False, "--open"),
):
    _ensure_workspace()
    with console.status(f"[bold cyan]Building deck '{deck_name}'...[/bold cyan]"):
        try:
            output_file = build_deck(json_path, deck_name, output_dir)
        except Exception as e:
            console.print(f"[bold red]Build error:[/bold red] {e}")
            raise typer.Exit(code=3)

    questions = validate_json(json_path)
    console.print(f"[bold green]✔ Built[/bold green] [yellow]{output_file.name}[/yellow]")
    console.print(f"  • Notes: {len(questions)} • Template: v{TEMPLATE_VERSION}")
    console.print(f"  • Saved to: {output_file.absolute()}")

    if open_file:
        open_in_anki(output_file)


@app.command()
def validate(
    json_path: Path = typer.Argument(None, exists=True, readable=True),
):
    questions = _parse_questions(json_path)
    total = len(questions)
    with_extra = sum(1 for q in questions if q.get("extra", "").strip())
    tags = Counter()
    for q in questions:
        for t in q.get("tags", []):
            tags[t] += 1

    console.print(f"[bold green]✔ Valid[/bold green] — {total} questions")
    console.print(f"  • Answers match: {total}/{total}")
    if with_extra:
        console.print(f"  • With explanations: {with_extra}/{total}")
    if tags:
        tag_str = ", ".join(f"{t}({c})" for t, c in tags.most_common(10))
        console.print(f"  • Tags: {tag_str}")


@app.command()
def preview(
    json_path: Path = typer.Argument(None, exists=True, readable=True),
):
    questions = _parse_questions(json_path)
    if not questions:
        console.print("[bold red]No questions to preview.[/bold red]")
        raise typer.Exit(code=1)

    q = questions[0]
    css = load_css()
    choices_html = "<br>".join(q["choices"])

    front_html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Preview — Front</title>
<link rel="stylesheet" href="{ASSETS / '_theme.css'}">
<link rel="stylesheet" href="{ASSETS / 'style.css'}">
<style>body {{ margin:0; background: var(--m3-surface); }}</style>
</head><body>
<div class="card"><div class="m3-mcq-wrapper">
  <div class="m3-question-card">
    <span class="m3-badge">Question</span>
    <h2 class="m3-question-text">{q['question']}</h2>
  </div>
  <div class="m3-options-group" id="m3-options-container" role="radiogroup"></div>
</div></div>
<div id="raw-choices" style="display:none">{choices_html}</div>
<script src="{ASSETS / '_mcq-front.js'}"></script>
<script>
  const choices = document.getElementById("raw-choices").innerHTML
    .split(/<br\\s*[\\/]?&gt;|\\n/gi).map(s=>s.trim()).filter(Boolean);
  initM3Front(choices);
</script>
</body></html>"""

    back_html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Preview — Back</title>
<link rel="stylesheet" href="{ASSETS / '_theme.css'}">
<link rel="stylesheet" href="{ASSETS / 'style.css'}">
<style>body {{ margin:0; background: var(--m3-surface); }}</style>
</head><body>
<div class="card"><div class="m3-mcq-wrapper">
  <div class="m3-check-banner" id="m3-check-banner"></div>
  <div class="m3-question-card">
    <span class="m3-badge">Question</span>
    <h2 class="m3-question-text">{q['question']}</h2>
  </div>
  <div class="m3-options-group" id="m3-options-back-container"></div>
  <div class="m3-explanation" id="m3-explanation">{q.get('extra', '')}</div>
</div></div>
<div id="raw-choices" style="display:none">{choices_html}</div>
<div id="raw-answer" style="display:none">{q['answer']}</div>
<script src="{ASSETS / '_mcq-back.js'}"></script>
<script>initM3Back();</script>
</body></html>"""

    tmp_dir = Path(tempfile.mkdtemp(prefix="anki_preview_"))
    front_path = tmp_dir / "preview-front.html"
    back_path = tmp_dir / "preview-back.html"
    front_path.write_text(front_html, encoding="utf-8")
    back_path.write_text(back_html, encoding="utf-8")

    import webbrowser
    webbrowser.open(str(front_path))
    webbrowser.open(str(back_path))

    console.print(f"[bold green]✔ Opening preview in browser...[/bold green]")
    console.print(f"  Front: {front_path}")
    console.print(f"  Back:  {back_path}")
    console.print("  [dim](Close browser tabs, temp files auto-cleaned on reboot)[/dim]")


@app.command()
def dry_run(
    json_path: Path = typer.Argument(None, exists=True, readable=True),
    deck_name: str = typer.Argument("Unnamed Deck"),
    output_dir: Path = typer.Option(None, "--output-to", "-o"),
):
    questions = _parse_questions(json_path)
    cfg = _load_config()
    out = output_dir or Path(cfg["output_dir"]).expanduser()
    out_file = out / f"{deck_name}.apkg"

    console.print(Panel(
        f"[bold]Deck:[/bold]       {deck_name}\n"
        f"[bold]Notes:[/bold]      {len(questions)}\n"
        f"[bold]Template:[/bold]   v{TEMPLATE_VERSION}\n"
        f"[bold]Output:[/bold]     {out_file}",
        title="Dry Run",
        border_style="cyan",
    ))


@app.command()
def watch(
    json_path: Path = typer.Argument(..., exists=True, readable=True),
    deck_name: str = typer.Argument(...),
    output_dir: Path = typer.Option(None, "--output-to", "-o"),
):
    _ensure_workspace()
    console.print(f"[bold cyan]Watching[/bold cyan] {json_path.name}... (Ctrl+C to stop)")

    last_mtime = os.path.getmtime(json_path)

    try:
        while True:
            time.sleep(2)
            current_mtime = os.path.getmtime(json_path)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                try:
                    output_file = build_deck(json_path, deck_name, output_dir)
                    questions = validate_json(json_path)
                    ts = time.strftime("%H:%M:%S")
                    console.print(f"[dim]{ts}[/dim] [green]Rebuilt[/green] — {len(questions)} notes → {output_file.name}")
                except Exception as e:
                    ts = time.strftime("%H:%M:%S")
                    console.print(f"[dim]{ts}[/dim] [red]Error:[/red] {e}")
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")


@app.command(name="list")
def list_decks():
    _ensure_workspace()
    if not OUTPUT_DIR.exists():
        console.print("[yellow]No decks directory. Run build --init first.[/yellow]")
        raise typer.Exit()

    files = sorted(OUTPUT_DIR.glob("*.apkg"), key=lambda f: f.stat().st_mtime, reverse=True)

    if not files:
        console.print("[dim]No decks found.[/dim]")
        raise typer.Exit()

    table = Table(title="Decks")
    table.add_column("Name", style="bold")
    table.add_column("Size", justify="right")
    table.add_column("Modified")

    for f in files:
        size = f.stat().st_size
        if size < 1024:
            size_str = f"{size} B"
        else:
            size_str = f"{size / 1024:.1f} KB"

        mtime = f.stat().st_mtime
        age = time.time() - mtime
        if age < 60:
            mod_str = "just now"
        elif age < 3600:
            mod_str = f"{int(age / 60)}m ago"
        elif age < 86400:
            mod_str = f"{int(age / 3600)}h ago"
        else:
            mod_str = f"{int(age / 86400)}d ago"

        table.add_row(f.stem, size_str, mod_str)

    console.print(table)


@app.command()
def inspect(
    json_path: Path = typer.Argument(None, exists=True, readable=True),
):
    questions = _parse_questions(json_path)
    total = len(questions)

    choices_counts = [len(q["choices"]) for q in questions]
    with_extra = sum(1 for q in questions if q.get("extra", "").strip())
    tags = Counter()
    for q in questions:
        for t in q.get("tags", []):
            tags[t] += 1

    console.print(Panel(
        f"[bold]Questions:[/bold]     {total}\n"
        f"[bold]Answers match:[/bold] {total}/{total} (100%)\n"
        f"[bold]With extras:[/bold]   {with_extra}/{total}\n"
        f"[bold]Choices:[/bold]       min={min(choices_counts)}, "
        f"max={max(choices_counts)}, avg={sum(choices_counts)/total:.1f}",
        title=f"Inspect: {json_path.name if json_path else 'stdin'}",
        border_style="cyan",
    ))

    if tags:
        tag_table = Table(title="Tags", show_header=True)
        tag_table.add_column("Tag", style="bold")
        tag_table.add_column("Count", justify="right")
        for tag, count in tags.most_common():
            tag_table.add_row(tag, str(count))
        console.print(tag_table)


@app.command()
def completions(
    shell: str = typer.Argument(..., help="shell: bash, zsh, or fish"),
):
    import shellingham
    try:
        detected = shellingham.detect_shell()[0]
    except Exception:
        detected = None

    if shell not in ("bash", "zsh", "fish"):
        console.print("[red]Supported shells: bash, zsh, fish[/red]")
        raise typer.Exit(code=1)

    if shell == "bash":
        console.print('eval "$(_ANKI_MCQ_BUILDER_COMPLETE=bash_source anki-mcq-builder)"')
    elif shell == "zsh":
        console.print('eval "$(_ANKI_MCQ_BUILDER_COMPLETE=zsh_source anki-mcq-builder)"')
    elif shell == "fish":
        console.print('anki-mcq-builder --completion-fish | source')

    console.print(f"\n[dim]Add the above to your ~/.{shell}rc[/dim]")


if __name__ == "__main__":
    app()
