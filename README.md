![Anki Words Builder](https://i.postimg.cc/DwKn6SrD/2025-10-01-154521.png)

## Anki Words Builder — build smart vocabulary decks for Anki in minutes

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/github/license/Gam5510/anki-words-builder)
![Stars](https://img.shields.io/github/stars/Gam5510/anki-words-builder?style=social)

## Description
Anki Words Builder is a Python utility that turns a list of English words into a polished Anki deck. It automatically adds translations, example sentences, and audio, and keeps a local database so your cards are never lost between runs.

## Features
- 🌐 EN→RU translation (Google Translate public endpoint)
- 🧠 Contextual examples from multiple sources (dictionaryapi.dev → Tatoeba → Reverso)
- 🔊 Auto‑generated audio (gTTS), stored in `audio/`
- 🧰 Persistent local storage (`words_db.json` + `cards_db.json`) — no card loss
- ⚡ Parallel processing with shared HTTP pool for speed
- 🧾 Export to `.apkg` and terminal viewer for quick inspection

## Installation
- Option 1 (via git):
```bash
git clone https://github.com/Gam5510/anki-words-builder.git
cd anki-words-builder
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/activate
# Linux/macOS
# source .venv/bin/activate
pip install -r requirements.txt
```

## Usage examples
- Generate a deck from a list of words (newline or comma separated):
```bash
python anki_creator.py
```
Finish input: Windows — Ctrl+Z then Enter; Linux/macOS — Ctrl+D.

- Quick terminal view of the deck content:
```bash
python view_anki_words.py
```

- Minimal programmatic example:
```python
import subprocess
subprocess.run(["python", "anki_creator.py"], check=True)
```

## TODO / Roadmap\
- Add new languages
- Package and publish to PyPI (`pip install anki-words-builder`)
- CLI flags: `--workers`, `--no-audio`, example sources selection
- i18n for CLI (EN/RU)
- Cache translations/examples with versioning
- Integration tests and CI

## Author / Contact
- Author: Your Name (@your_handle)
- GitHub: https://github.com/Gam5510
- Email: you@example.com

> License: MIT. Feel free to use, fork, and open PRs — contributions welcome! 🎉 