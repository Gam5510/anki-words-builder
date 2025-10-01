import zipfile, sqlite3, os, tempfile, json, sys, shutil

apkg_path = "english_words.apkg"

if not os.path.exists(apkg_path):
    print(f"File {apkg_path} not found. Generate the deck first.")
    sys.exit(1)

# extract to a temporary directory
tmpdir = tempfile.mkdtemp()
try:
    with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)

    db_path = os.path.join(tmpdir, "collection.anki2")
    if not os.path.exists(db_path):
        print("Inside .apkg no collection.anki2 database was found")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # models (card structure) — uncomment for debugging
    # cursor.execute("SELECT models FROM col")
    # models = json.loads(cursor.fetchone()[0])
    # print(models)

    # all notes (cards)
    cursor.execute("SELECT id, flds FROM notes ORDER BY id")
    rows = cursor.fetchall()

    if not rows:
        print("No cards found in the deck.")
        sys.exit(0)

    # Prepare data
    items = []
    for row in rows:
        fields = (row[1] or "").split("\x1f")  # field separator
        # Expected order: Word, Translation, Example, Audio
        word = fields[0] if len(fields) > 0 else ""
        translation = fields[1] if len(fields) > 1 else ""
        example = fields[2] if len(fields) > 2 else ""
        items.append((word, translation, example))

    # Formatted output
    def truncate(text: str, max_len: int) -> str:
        text = text.replace('\n', ' ').strip()
        return (text[: max_len - 1] + '…') if len(text) > max_len else text

    # Column widths
    width_idx = max(len(str(len(items))), 2)
    width_word = min(max(max((len(i[0]) for i in items), default=4), len("Word")), 20)
    width_tran = min(max(max((len(i[1]) for i in items), default=11), len("Translation")), 25)
    width_ex = 60

    header = f"{'#'.rjust(width_idx)}  { 'Word'.ljust(width_word) }  { 'Translation'.ljust(width_tran) }  { 'Example'.ljust(width_ex) }"
    sep = "-" * len(header)

    print(header)
    print(sep)

    for idx, (w, t, e) in enumerate(items, start=1):
        print(f"{str(idx).rjust(width_idx)}  { truncate(w, width_word).ljust(width_word) }  { truncate(t, width_tran).ljust(width_tran) }  { truncate(e, width_ex).ljust(width_ex) }")

    print(sep)
    print(f"Total cards: {len(items)}")

finally:
    # Cleanup temp directory
    try:
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass
