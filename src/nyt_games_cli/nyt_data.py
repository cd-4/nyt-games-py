import json
import re
from datetime import datetime

import requests


data = {}
REQUEST_TIMEOUT = 20
REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'
    )
}


def get_date_str():
    return datetime.now().strftime('%Y-%m-%d')


def get_json(url, headers=None):
    request_headers = {**REQUEST_HEADERS, **(headers or {})}
    response = requests.get(url, headers=request_headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_html(url):
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_mini_data(jsondata):
    puzzle = jsondata['body'][0]

    clues = {}
    for clue_list in puzzle['clueLists']:
        direction_clues = {}
        for clue_index in clue_list['clues']:
            clue = puzzle['clues'][clue_index]
            text = ''.join(part.get('plain', '') for part in clue['text'])
            direction_clues[clue['label']] = text
        clues[clue_list['name']] = direction_clues

    boxes = [
        {
            'clue': int(cell['label']) if cell.get('label') else None,
            'letter': cell.get('answer'),
        }
        for cell in puzzle['cells']
    ]
    return {'clues': clues, 'boxes': boxes}


def load_mini_data():
    """Load the Mini directly instead of driving the website with a browser."""
    jsondata = get_json(
        'https://www.nytimes.com/svc/crosswords/v6/puzzle/mini.json',
        headers={'X-Games-Auth-Bypass': 'true'},
    )
    data['mini'] = parse_mini_data(jsondata)


def load_connections_data():
    date = get_date_str()
    data['connections'] = get_json(
        f'https://www.nytimes.com/svc/connections/v2/{date}.json'
    )


def load_strands_data():
    date = get_date_str()
    data['strands'] = get_json(
        f'https://www.nytimes.com/svc/strands/v2/{date}.json'
    )


def load_wordle_data():
    date = get_date_str()
    jsondata = get_json(f'https://www.nytimes.com/svc/wordle/v2/{date}.json')
    data['wordle'] = jsondata['solution']


def load_spelling_bee_data():
    html = get_html('https://www.nytimes.com/puzzles/spelling-bee')
    content = re.search(r'gameData = ([^<]*)<', html)
    if content is None:
        raise ValueError('Could not find Spelling Bee game data')
    data['spelling-bee'] = json.loads(content.group(1))['today']


def load_letterboxed_data():
    html = get_html('https://www.nytimes.com/puzzles/letter-boxed')
    sides_match = re.search(
        r'"sides":\["([A-Z]{3})","([A-Z]{3})","([A-Z]{3})","([A-Z]{3})"\]',
        html,
    )
    words_match = re.search(r'"dictionary":\[([A-Z,"]*)\]', html)
    par_match = re.search(r'"par":([0-9]+)', html)
    if sides_match is None or words_match is None or par_match is None:
        raise ValueError('Could not find Letter Boxed game data')

    data['letterboxed'] = {
        'par': int(par_match.group(1)),
        'dictionary': [word.strip('"') for word in words_match.group(1).split(',')],
        'sides': list(sides_match.groups()),
    }


def load_game_data():
    data.clear()
    load_wordle_data()
    load_letterboxed_data()
    load_strands_data()
    load_mini_data()
    load_spelling_bee_data()
    load_connections_data()
    return data


def main():
    print(json.dumps(load_game_data(), indent=2))


if __name__ == '__main__':
    main()
