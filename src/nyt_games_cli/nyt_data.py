import asyncio
import time
import requests
import re
from pprint import pprint
from datetime import datetime
from pyppeteer import launch
from bs4 import BeautifulSoup
#import playwright
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


def current_event_loop_exists() -> bool:
    return asyncio.get_event_loop_policy()._local._loop is not None

def get_current_loop():
    if not current_event_loop_exists():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
    return asyncio.get_event_loop()

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


async def load_data(url, page_thing, func_to_call):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)

    await page.click('#portal-game-modals > div > div > div.xwd__modal--body.xwd__start-modal.mini > article > button')
    await page.click('#portal-game-toolbar > div > ul > div.xwd__toolbar--expandedMenu > li:nth-child(2) > button')
    await page.click('#portal-game-toolbar > div > ul > div.xwd__toolbar--expandedMenu > li:nth-child(2) > ul > li:nth-child(3) > button')
    asyncio.sleep(1)
    await page.click('#portal-game-modals > div > div > div.xwd__modal--body.xwd__confirmation-modal--wrapper.animate-opening > article > div > button:nth-child(2)')
    asyncio.sleep(0.5)
    return

    content = await page.content()

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
            letter = letter_soup.text

        cell_data = {
                'clue': clue_text,
                'empty': not has_text,
                'letter': letter,
                }
        print(clue_text, has_text, letter)
        boxes.append(cell_data)
        print(cell.prettify())

    mini_data = {
            'clues' : clue_data,
            'boxes' : boxes
            }
    global data
    data['mini'] = mini_data

    
def load_async_data(url, page_thing, func_to_call):
    loop = get_current_loop()
    task = loop.create_task(load_data(url, page_thing, func_to_call))
    return task

async def load_mini_data_new():
    def store_letterboxed(in_data):
        print(in_data)
        global data
        data['letterboxed'] = in_data
        #data['letterboxed'] = sides
    mini_url = 'https://www.nytimes.com/crosswords/game/mini'
    return await load_async_data(mini_url, 'window.gameData', store_letterboxed)

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

'''
def load_mini_data():
    url = 'https://www.nytimes.com/crosswords/game/mini'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    grid = soup.find('div', class_='crossword-grid')
    print(grid)


    titles = soup.find_all('div', class_='xwd__clue-list--wrapper')
    with open('results.txt', 'w+') as f:
        f.write(soup.prettify())

    print(titles)
'''


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

    return data


def main():
    #load_game_data()
    #load_mini_data()
    global data

    '''
    loop = get_current_loop()
    task = load_mini_data_new()
    loop.run_until_complete(task)
    '''
    load_mini_data()
    pprint(data)



if __name__ == '__main__':
    main()
