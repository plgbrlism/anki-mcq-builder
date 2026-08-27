<div align="center">
	<h1>
		Anki Builder
	</h1>
	<br>
		CLI tool that turns JSON files into Material Design 3 Anki multiple-choice decks.
	</br>
</div>

## Install

```bash
git clone https://github.com/plgbrlism/anki-mcq-builder.git && cd anki-mcq-builder
chmod +x install.sh && ./install.sh
```

On Windows:
```powershell
git clone https://github.com/plgbrlism/anki-mcq-builder.git
cd anki-mcq-builder
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\install.ps1
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate # On Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
```

Requires Python 3.11+.

## Quick Start

```bash
anki-mcq-builder init
anki-mcq-builder build questions.json "My Deck"
anki-mcq-builder build questions.json "My Deck" --open  # import into Anki directly
```

## Commands

| Command | What it does |
| --- | --- |
| `init` | Set up workspace folders |
| `build <json> <name>` | Build an `.apkg` deck from JSON |
| `validate <json>` | Check JSON for errors without building |
| `preview <json>` | Open first question in browser to preview card design |
| `dry-run <json> <name>` | Show what would be built (note count, output path) |
| `watch <json> <name>` | Rebuild automatically when JSON changes |
| `list` | List all decks in workspace with sizes |
| `inspect <json>` | Show question stats, tag distribution, choice counts |
| `completions <shell>` | Generate shell completions (bash/zsh/fish) |

### Build flags

| Flag | What it does |
| --- | --- |
| `--open` | Open the `.apkg` in Anki after building |
| `-o <dir>` | Save to a custom directory |

### Stdin support

```bash
cat questions.json | anki-mcq-builder validate
```

## Config

Copy `config.example.toml` to one of:

- `./anki-mcq-builder.toml` (project-level)
- `~/.config/anki-mcq-builder/config.toml` (user-level)

All options are commented out by default. See `config.example.toml` for available settings.

## JSON Format

```json
[
  {
    "id": 1,
    "question": "What is the primary function of a router?",
    "choices": [
      "Connect devices in one network",
      "Forward data between networks",
      "Convert signals",
      "Store data"
    ],
    "answer": "Forward data between networks",
    "extra": "Extra explanation for the back of the card (optional).",
    "tags": ["Networking", "Hardware"]
  }
]
```

The `"answer"` string must exactly match one of the `"choices"`.

Use `json-schema.md` as an LLM prompt to generate valid JSON from your sources.

Feel free to customize the questions to fit your needs.
