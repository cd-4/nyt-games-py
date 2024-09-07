import asyncio
import requests
import re
from datetime import datetime
from pyppeteer import launch

global data
data = {}

def get_date_str():
    now = datetime.now()
    day = str(now.day)
    month = str(now.month)
    year = str(now.year)
    if len(day) == 1:
        day = '0' + day
    if len(month) == 1:
        month = '0' + month
    return f'{year}-{month}-{day}'

# https://www.nytimes.com/svc/strands/v2/2024-09-01.json
# https://www.nytimes.com/svc/wordle/v2/2024-09-01.json

def load_strands_data():
    date = get_date_str()
    url = f'https://www.nytimes.com/svc/strands/v2/{date}.json'
    res = requests.get(url)
    jsondata = res.json()
    global data
    data['strands'] = jsondata


def load_wordle_data():
    date = get_date_str()
    url = f'https://www.nytimes.com/svc/wordle/v2/{date}.json'
    res = requests.get(url)
    jsondata = res.json()
    solution = jsondata['solution']
    global data
    data['wordle'] = solution

def load_letterboxed_data():
    url = 'https://nytimes.com/puzzles/letter-boxed'
    res = requests.get(url)
    nyt_groups = re.search(
        r'\"sides\":\[\"([A-Z]{3})\",\"([A-Z]{3})\",\"([A-Z]{3})\",\"([A-Z]{3})\"\]',
    res.text)
    sides = list(nyt_groups.groups())
    valid_words = re.search(
            r'\"dictionary\":\[([A-Z,"]*)\]', res.text
            )
    words_str = valid_words.groups()[0]
    words = [w.strip('"') for w in words_str.split(',')]
    par_group = re.search(
            r'\"par\":([0-9]+)', res.text
            )
    par_value = int(par_group.groups()[0])

    letterboxed_dict = {
            'par' : par_value,
            'dictionary' : words,
            'sides' : sides
            }
    global data
    data['letterboxed'] = letterboxed_dict

def load_game_data():
    global data
    load_wordle_data()
    load_letterboxed_data()
    load_strands_data()

    return data


def main():
    load_game_data()
    global data
    print(data)

if __name__ == '__main__':
    main()
