import requests
import re
import json
from pprint import pprint
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import Playwright, sync_playwright

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

def get_mini_data_from_html(content):
    soup = BeautifulSoup(content, 'html.parser')

    clue_lists = soup.find_all('div', class_='xwd__clue-list--wrapper')
    clue_data = {}
    for cl in clue_lists:
        title_soup = cl.find('h3', class_='xwd__clue-list--title')
        direction = title_soup.text
        direction_data = {}

        clues = cl.find_all('li', class_='xwd__clue--li')
        for item in clues:
            number = item.find('span', class_='xwd__clue--label').text
            clue_text = item.find('span', class_="xwd__clue--text xwd__clue-format").text
            direction_data[number] = clue_text
        clue_data[direction] = direction_data

    cell_soup = soup.find('g', {'data-group': 'cells'})
    i = 0


    cells = cell_soup.find_all('g', class_='xwd__cell')

    index = 0
    boxes = []
    for cell in cells:
        clue_soup = cell.find('text', {'text-anchor' : 'start'})
        letter_soup = cell.find('text', {'text-anchor' : 'middle'})

        has_text = letter_soup != None
        has_clue = clue_soup != None

        clue_text = None
        if has_clue:
            clue_text = int(clue_soup.text)
        letter = None
        if has_text:
            letter = letter_soup.text[0]

        cell_data = {
                'clue': clue_text,
                'letter': letter,
                }
        boxes.append(cell_data)

    mini_data = {
            'clues' : clue_data,
            'boxes' : boxes
            }
    global data
    data['mini'] = mini_data

def load_mini_data():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        url = 'https://www.nytimes.com/crosswords/game/mini'
        page.goto(url)

        page.click('#portal-game-modals > div > div > div.xwd__modal--body.xwd__start-modal.mini > article > button')
        page.click('#portal-game-toolbar > div > ul > div.xwd__toolbar--expandedMenu > li:nth-child(2) > button')
        page.click('#portal-game-toolbar > div > ul > div.xwd__toolbar--expandedMenu > li:nth-child(2) > ul > li:nth-child(3) > button')
        page.click('#portal-game-modals > div > div > div.xwd__modal--body.xwd__confirmation-modal--wrapper.animate-opening > article > div > button:nth-child(2)')
        page.click('#portal-game-modals > div > div > div.xwd__modal--body.xwd__congrats-modal.mini__congrats-modal.animate-opening > div > i')
        content = page.content()

        get_mini_data_from_html(content)
        browser.close()

def load_connections_data():
    date = get_date_str()
    url = f'https://www.nytimes.com/svc/connections/v2/{date}.json'
    res = requests.get(url)
    jsondata = res.json()
    global data
    data['connections'] = jsondata

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

def load_spelling_bee_data():
    url = 'https://www.nytimes.com/puzzles/spelling-bee'
    res = requests.get(url)
    content = re.search(r'gameData = ([^<]*)<', res.text)
    found = content.groups()[0]
    jsondata = json.loads(found)['today']
    global data
    data['spelling-bee'] = jsondata

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
    load_mini_data()
    load_spelling_bee_data()
    load_connections_data()
    load_spelling_bee_data()
    return data


def main():
    #load_game_data()
    load_spelling_bee_data()
    #load_connections_data()
    global data
    pprint(data)

if __name__ == '__main__':
    main()
