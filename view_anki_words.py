import zipfile, sqlite3, os, tempfile, json, sys, shutil

apkg_path = "english_words.apkg"

if not os.path.exists(apkg_path):
    print(f"Файл {apkg_path} не найден. Сначала сгенерируйте колоду.")
    sys.exit(1)

# распаковать во временную папку
tmpdir = tempfile.mkdtemp()
try:
    with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)

    db_path = os.path.join(tmpdir, "collection.anki2")
    if not os.path.exists(db_path):
        print("Внутри .apkg не найден файл базы данных collection.anki2")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # модели (структура карт) — можно раскомментировать для отладки
    # cursor.execute("SELECT models FROM col")
    # models = json.loads(cursor.fetchone()[0])
    # print(models)

    # все заметки (карточки)
    cursor.execute("SELECT id, flds FROM notes ORDER BY id")
    rows = cursor.fetchall()

    if not rows:
        print("В колоде нет карточек.")
        sys.exit(0)

    # Подготовим данные
    items = []
    for row in rows:
        fields = (row[1] or "").split("\x1f")  # разделитель полей
        # Ожидается порядок: Word, Translation, Example, Audio
        word = fields[0] if len(fields) > 0 else ""
        translation = fields[1] if len(fields) > 1 else ""
        example = fields[2] if len(fields) > 2 else ""
        items.append((word, translation, example))

    # Форматированный вывод
    def truncate(text: str, max_len: int) -> str:
        text = text.replace('\n', ' ').strip()
        return (text[: max_len - 1] + '…') if len(text) > max_len else text

    # Ограничим ширины для читаемости
    width_idx = max(len(str(len(items))), 2)
    width_word = min(max(max((len(i[0]) for i in items), default=4), len("Word")), 20)
    width_tran = min(max(max((len(i[1]) for i in items), default=11), len("Translation")), 25)
    width_ex = 60  # фиксированная ширина для примера

    header = f"{'#'.rjust(width_idx)}  { 'Word'.ljust(width_word) }  { 'Translation'.ljust(width_tran) }  { 'Example'.ljust(width_ex) }"
    sep = "-" * len(header)

    print(header)
    print(sep)

    for idx, (w, t, e) in enumerate(items, start=1):
        print(f"{str(idx).rjust(width_idx)}  { truncate(w, width_word).ljust(width_word) }  { truncate(t, width_tran).ljust(width_tran) }  { truncate(e, width_ex).ljust(width_ex) }")

    print(sep)
    print(f"Всего карточек: {len(items)}")

finally:
    # Чистим временную папку
    try:
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass
