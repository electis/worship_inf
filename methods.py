import random
from datetime import datetime

from tinytag import TinyTag
import os

def insert_line_breaks(text: str, max_length=64):
    result = ''
    length = 0
    for num, char in enumerate(text):
        if length > max_length - max_length * 0.2:
            if text[num] == ' ':
                result += '\n'
                length = 0
                char = ''
        elif length > max_length:
            result += '\n'
            length = 0
        if text[num:num + 1] == '\n':
            length = -1
        length += 1
        result += char
    return result


def get_playing_text(filepath):
    artist, title = '', ''
    try:
        artist, title = os.path.basename(filepath).split('-')
        title = title[:-4]
    except:
        pass
    playing = TinyTag.get(filepath)
    artist = getattr(playing, 'artist', '') or artist
    title = getattr(playing, 'title', '') or title
    duration = getattr(playing, 'duration', 0) or 0
    return f"{title} - {artist}", duration


def choice(items, last = None):
    item = random.choice(items)
    while item == last:
        item = random.choice(items)
    return item


def calc_font(text):
    if len(text) < 550:
        return  56, 58
    else:
        return 50, 64


def now():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')
