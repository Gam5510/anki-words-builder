import requests
import json
import genanki
from bs4 import BeautifulSoup
from gtts import gTTS
import os
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional

# ====== Config ======
OUTPUT_APKG = "english_words1.apkg"  # change this to customize output filename

# ====== HTTP session with pooling and retries ======
_SESSION = None

def get_http_session():
    global _SESSION
    if _SESSION is not None:
        return _SESSION
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    _SESSION = session
    return _SESSION

# ====== Translation via Google Translate (public endpoint) ======
def google_translate(word, target="ru"):
    session = get_http_session()
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": target,
        "dt": "t",
        "q": word
    }
    r = session.get(url, params=params, timeout=10)
    if r.status_code == 200:
        result = r.json()
        return result[0][0][0]
    return "Translation not found"

# ====== Examples: multiple sources with resilient parsing ======

def _example_from_dictionaryapi(word: str) -> Optional[str]:
    try:
        session = get_http_session()
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if not isinstance(data, list) or not data:
            return None
        # Find first example in meanings -> definitions
        for entry in data:
            for meaning in entry.get("meanings", []):
                for definition in meaning.get("definitions", []):
                    ex = definition.get("example")
                    if ex:
                        return ex.strip()
        return None
    except Exception:
        return None


def _example_from_tatoeba(word: str) -> Optional[str]:
    try:
        session = get_http_session()
        api_url = "https://tatoeba.org/eng/api_v0/search"
        params = {
            "query": word,
            "from": "eng",
            "to": "rus",
            "orphans": "no",
            "unapproved": "no",
            "page": 1,
        }
        r = session.get(api_url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results", []) if isinstance(data, dict) else []
        for item in results:
            text_en = item.get("text")
            translations = item.get("translations") or []
            ru_text = None
            for tr in translations:
                if isinstance(tr, dict) and tr.get("language") in ("rus", "ru") and tr.get("text"):
                    ru_text = tr.get("text")
                    break
            if text_en and ru_text:
                return f"{text_en} — {ru_text}"
        if results:
            first = results[0]
            if first.get("text"):
                return first["text"]
        return None
    except Exception:
        return None


def _example_from_reverso(word: str) -> Optional[str]:
    try:
        session = get_http_session()
        url = f"https://context.reverso.net/translation/english-russian/{word}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
        r = session.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # Multiple selectors in case of layout changes
        candidates = soup.select(".example .text, .example .src, .example .trg, .example.single .example-text")
        for el in candidates:
            txt = el.get_text(strip=True)
            if txt:
                return txt
        return None
    except Exception:
        return None


def get_example(word):
    q = (word or "").strip()
    if not q:
        return "Example not found"
    q = q.lower()

    ex = _example_from_dictionaryapi(q)
    if ex:
        return ex

    ex = _example_from_tatoeba(q)
    if ex:
        return ex

    ex = _example_from_reverso(q)
    if ex:
        return ex

    return f"I often use the word '{word}' in daily conversation."

# ====== Audio via gTTS (cached in audio/ folder) ======
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def get_audio(word):
    safe_name = word.replace("/", "-")
    filename = f"{safe_name}.mp3"
    audio_path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(audio_path):
        tts = gTTS(word, lang="en")
        tts.save(audio_path)
    return audio_path

# ====== Note model ======
my_model = genanki.Model(
    20251001,
    "EN-RU Vocabulary",
    fields=[
        {"name": "Word"},
        {"name": "Translation"},
        {"name": "Example"},
        {"name": "Audio"},
    ],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Word}}",
        "afmt": "{{FrontSide}}<hr id='answer'>{{Translation}}<br><i>{{Example}}</i><br>{{Audio}}",
    }]
)

# ====== Deck ======
my_deck = genanki.Deck(2059400222, "English Vocabulary")
media_files = []

# ====== Local databases ======
WORDS_DB_PATH = "words_db.json"
CARDS_DB_PATH = "cards_db.json"  # full per-word data

def load_words_db():
    if os.path.exists(WORDS_DB_PATH):
        try:
            with open(WORDS_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                if isinstance(data, dict) and "words" in data:
                    return set(data["words"])
        except Exception:
            pass
    return set()

def save_words_db(words_set):
    with open(WORDS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(list(words_set)), f, ensure_ascii=False, indent=2)

def load_cards_db() -> Dict[str, Dict[str, str]]:
    if os.path.exists(CARDS_DB_PATH):
        try:
            with open(CARDS_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}

def save_cards_db(cards: Dict[str, Dict[str, str]]):
    with open(CARDS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

# ====== Progress helpers ======

def print_progress(phase: str, done: int, total: int):
    total = max(total, 1)
    percent = int(done * 100 / total)
    bar_len = 28
    filled = int(percent * bar_len / 100)
    bar = "█" * filled + "-" * (bar_len - filled)
    msg = f"\r{phase}: [{bar}] {percent}% ({done}/{total})"
    print(msg, end="", flush=True)

def finish_progress():
    print()

# ====== Fetch phases (only for new words) ======

def fetch_translations(words: List[str]) -> Dict[str, str]:
    print("Fetching translations…")
    results: Dict[str, str] = {}
    total = len(words)
    done = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(google_translate, w): w for w in words}
        for future in as_completed(futures):
            w = futures[future]
            try:
                results[w] = future.result()
            except Exception:
                results[w] = "Translation not found"
            done += 1
            print_progress("Translations", done, total)
    finish_progress()
    return results

def fetch_examples(words: List[str]) -> Dict[str, str]:
    print("Fetching examples…")
    results: Dict[str, str] = {}
    total = len(words)
    done = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(get_example, w): w for w in words}
        for future in as_completed(futures):
            w = futures[future]
            try:
                results[w] = future.result()
            except Exception:
                results[w] = "Example not found"
            done += 1
            print_progress("Examples", done, total)
    finish_progress()
    return results

def fetch_audios(words: List[str]) -> Dict[str, str]:
    print("Generating audio…")
    results: Dict[str, str] = {}
    total = len(words)
    done = 0
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(get_audio, w): w for w in words}
        for future in as_completed(futures):
            w = futures[future]
            try:
                audio_path = future.result()
            except Exception:
                audio_path = os.path.join(AUDIO_DIR, f"{w}.mp3")
            results[w] = audio_path
            done += 1
            print_progress("Audio", done, total)
    finish_progress()
    return results

# ====== Main ======
try:
    print("Paste words (comma- or newline-separated). Finish: Ctrl+Z then Enter (Windows) / Ctrl+D (Linux/macOS):")
    text = sys.stdin.read()
except KeyboardInterrupt:
    print("\nInput aborted. Exiting gracefully.")
    sys.exit(0)

if not text.strip():
    try:
        print("Enter words separated by comma or space:")
        text = input()
    except KeyboardInterrupt:
        print("\nInput aborted. Exiting gracefully.")
        sys.exit(0)

raw_items = re.split(r"[\n\r,;\t]+", text)
stdin_words = [item.strip() for item in raw_items if item.strip()]

known_words = load_words_db()
cards_db = load_cards_db()

new_words = []
for candidate in stdin_words:
    normalized = candidate.strip()
    if normalized and normalized not in known_words and normalized not in new_words:
        new_words.append(normalized)

apkg_path = OUTPUT_APKG

if not new_words and not os.path.exists(apkg_path):
    print("No new words, package missing — rebuilding from local DB…")
    words_to_build = sorted(known_words)
else:
    if new_words:
        for w in new_words:
            known_words.add(w)
        save_words_db(known_words)

        words_to_fetch = sorted(new_words)
        try:
            translations = fetch_translations(words_to_fetch)
            examples = fetch_examples(words_to_fetch)
            audios = fetch_audios(words_to_fetch)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user. Exiting gracefully.")
            sys.exit(0)
        for w in words_to_fetch:
            audio_path = audios.get(w, os.path.join(AUDIO_DIR, f"{w}.mp3"))
            cards_db[w] = {
                "translation": translations.get(w, "Translation not found"),
                "example": examples.get(w, "Example not found"),
                "audio_file": os.path.basename(audio_path),
            }
        save_cards_db(cards_db)
    words_to_build = sorted(known_words)

print("Assembling deck (all words from DB)…")
for w in words_to_build:
    entry = cards_db.get(w)
    if entry is None:
        try:
            translation = google_translate(w)
            example = get_example(w)
            audio_path = get_audio(w)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user. Exiting gracefully.")
            sys.exit(0)
        entry = {
            "translation": translation or "Translation not found",
            "example": example or "Example not found",
            "audio_file": os.path.basename(audio_path),
        }
        cards_db[w] = entry
    audio_path = os.path.join(AUDIO_DIR, entry["audio_file"]) if entry.get("audio_file") else get_audio(w)
    audio_tag = f"[sound:{os.path.basename(audio_path)}]"

    note = genanki.Note(
        model=my_model,
        fields=[w, entry.get("translation", "Translation not found"), entry.get("example", "Example not found"), audio_tag],
        guid=genanki.guid_for(w),
    )
    my_deck.add_note(note)
    if audio_path not in media_files:
        media_files.append(audio_path)

save_cards_db(cards_db)

try:
    package = genanki.Package(my_deck)
    package.media_files = media_files
    package.write_to_file(apkg_path)
except KeyboardInterrupt:
    print("\nSaving aborted. Exiting gracefully.")
    sys.exit(0)

print(f"✅ Done: {OUTPUT_APKG} created. Import into Anki!")

if new_words:
    print("New words added:", ", ".join(sorted(new_words)))
