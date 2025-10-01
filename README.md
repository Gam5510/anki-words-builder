![Anki Words Builder](https://i.postimg.cc/prg84W0F/2025-10-01-142107.png)

## Anki Words Builder — создавайте умные словарные колоды для Anki за минуты

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)]([https://www.python.org/](https://img.shields.io/badge/python-3.9%2B-blue)) [![License](https://img.shields.io/badge/License-MIT-green.svg)]([LICENSE](https://img.shields.io/github/license/Gam5510/anki-words-builder)) [![GitHub Stars](https://img.shields.io/badge/stars-★%20на%20GitHub-informational.svg)](https://github.com/Gam5510/anki-words-builder](https://img.shields.io/github/stars/Gam5510/anki-words-builder?style=social)

## Описание
Anki Words Builder — это утилита на Python для быстрого создания колод Anki из списка английских слов. Скрипт автоматически добавляет перевод, пример использования и озвучку, а также ведёт локальную базу, чтобы не терять карточки между запусками.

## Возможности
- 🌐 Перевод EN→RU (Google Translate, публичная конечная точка)
- 🧠 Контекстные примеры из нескольких источников (dictionaryapi.dev → Tatoeba → Reverso)
- 🔊 Автоматическая озвучка (gTTS), файлы в `audio/`
- 🧰 Стойкая локальная база (`words_db.json` + `cards_db.json`) — ничего не теряется
- ⚡ Параллельная обработка и общий HTTP‑пул для скорости
- 🧾 Экспорт в `.apkg` и просмотр содержимого в терминале

## Установка
- Вариант 1 (через git):
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

- Вариант 2 (как модуль pip — зарезервировано):
```bash
# Пока не опубликовано в PyPI — оставлено для будущего релиза
pip install anki-words-builder  # TODO
```

## Пример использования
- Сгенерировать колоду из списка слов (каждое с новой строки или через запятую):
```bash
python anki_creator.py
```
Завершите ввод: Windows — Ctrl+Z затем Enter; Linux/macOS — Ctrl+D.

- Программа создаст/обновит `english_words.apkg` и сохранит данные в локальную базу.

- Быстрый просмотр содержимого колоды в терминале:
```bash
python view_anki_words.py
```

- Мини‑пример кода (импорт из вашего проекта):
```python
# пример программного запуска генерации (упрощённый сценарий)
import subprocess
subprocess.run(["python", "anki_creator.py"], check=True)
```

## Демо
- GIF/скриншоты работы: добавьте сюда изображения вашего процесса генерации и результата в Anki
- Пример: ![Demo Placeholder](https://user-images.githubusercontent.com/0000000/placeholder-demo.gif)

## TODO / планы
- Пакетирование и публикация в PyPI (`pip install anki-words-builder`)
- Флаги CLI: `--workers`, `--no-audio`, выбор источников примеров
- Локализация интерфейса командной строки (RU/EN)
- Кэширование переводов/примеров в базе по версиям
- Интеграционные тесты и CI

## Контакты / автор
- Автор: Fazliddin (tg https://t.me/gam5510)
- GitHub: https://github.com/Gam5510
- Почта: ryvokteam@gmail.com


> Лицензия: MIT. Свободно используйте, форкайте и присылайте PR — буду рад вашему вкладу! 🎉 

