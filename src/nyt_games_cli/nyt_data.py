import asyncio
import requests
from datetime import datetime
from pyppeteer import launch

global data
data = {}

def current_event_loop_exists() -> bool:
    return asyncio.get_event_loop_policy()._local._loop is not None

def get_current_loop():
    if not current_event_loop_exists():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
    return asyncio.get_event_loop()


def load_async_data(url, page_thing, func_to_call):
    loop = get_current_loop()
    task = loop.create_task(load_data(url, page_thing, func_to_call))
    return task

async def load_data(url, page_thing, func_to_call):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    content = await page.evaluate(page_thing, force_expr=True)
    func_to_call(content)
    await browser.close()


def load_wordle_data():
    now = datetime.now()
    day = str(now.day)
    month = str(now.month)
    year = str(now.year)
    if len(day) == 1:
        day = '0' + day
    if len(month) == 1:
        month = '0' + month
    url = f'https://www.nytimes.com/svc/wordle/v2/{year}-{month}-{day}.json'
    res = requests.get(url)
    jsondata = res.json()
    solution = jsondata['solution']
    global data
    data['wordle'] = solution

async def load_letterboxed_data():
    def store_letterboxed(in_data):
        global data
        data['letterboxed'] = in_data
        #data['letterboxed'] = sides
    return await load_async_data('https://www.nytimes.com/puzzles/letter-boxed', 'window.gameData', store_letterboxed)

def load_game_data():
    global data
    loop = get_current_loop()
    load_wordle_data()
    task = load_letterboxed_data()
    loop.run_until_complete(task)

    return data


def main():
    load_game_data()
    global data
    print(data)

if __name__ == '__main__':
    main()
