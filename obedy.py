#!/bin/env python
from bs4 import BeautifulSoup
from datetime import date, datetime
import locale
import re
import requests
import sys
import pprint

NORMAL = '\u001b[0m'
BOLD = '\u001b[2m'
ITALIC = '\u001b[3m'
GREY = '\u001b[38;5;7m'
BLUE = '\u001b[34m'
DOUBLE_UNDERLINE = '\u001b[21m'

def blox():
    page = requests.get('http://www.blox-restaurant.cz/#!/page_obedy')
    soup = BeautifulSoup(page.content, 'html.parser')
    allTr = iter(soup.find(id='page_obedy').findAll('tr'))
    next(allTr) # Skip "Menu na týden..."

    res = {}

    for item in allTr:
        day_tag = item.find('strong')
        if day_tag is not None:
            current_day = re.sub(r'/.*$', '', day_tag.text)
            res[current_day] = []
            continue

        meals = item.find_all('td')
        if '\xa0' in meals[3].text: # Nonsense price -> we're already at the end
            break
        res[current_day].append({ 'name': meals[1].text, 'allergens': meals[2].text, 'price': meals[3].text })

    return res

def country_life():
    page = requests.get('https://www.countrylife.cz/mo-dejvice-restaurace')
    soup = BeautifulSoup(page.content, 'html.parser')
    menu = soup.find(text='Jídelní lístek na tento týden:').findNext('div').findAll('p')

    res = {}

    for item in menu:
        if item.text == '': # There are some bogus <p> elements
            continue
        day_tag = item.find('strong')
        current_day = re.sub(' .*$', '', day_tag.text) # Discard the date from the weekday
        res[current_day] = []
        meals = item.text.split('\n')[1:] # Discard the first element - it's the day
        for count, meal in enumerate(meals):
            meal = re.sub(' doporučujeme| NOVINKA', '', meal) # I don't care about this stuff
            match = re.match(r'([^\(]+)(\(.*\))*', meal)
            name = re.sub('\xa0', '', match.group(1))
            name = re.sub(' $', '', name)
            allergens = match.group(2)
            price = '39 Kč/porce' if count == 0 else '22 Kč/100 g' if datetime.now().hour > 16 else '27 Kč/100 g'
            res[current_day].append({ 'name': name, 'allergens': allergens if allergens is not None else '', 'price': price })

    return res

if 'blox' in sys.argv[0]:
    menu = blox()
elif 'country' in sys.argv[0]:
    menu = country_life()
else:
    print('Spusťte tento skript s jedním z těchto argv[0]: { blox }')
    exit(1)

if len(sys.argv) >= 2:
    day = str(sys.argv[1])
    if len(day) == 2:
        day = {'po': 'Pondělí', 'út': 'Úterý', 'st': 'Středa', 'čt': 'Čtvrtek', 'pá': 'Pátek',
                                'ut': 'Úterý',                 'ct': 'Čtvrtek', 'pa': 'Pátek', }[day]
else:
    locale.setlocale(locale.LC_TIME, 'cs_CZ.UTF-8')
    day = date.today().strftime('%A')

if day not in menu:
    print('Neznámý den: "' + day + '". Podporované formáty: Pátek|pá|pa')
    exit(1)

name_width = len(max(menu[day], key=lambda index: len(index['name']))['name'])
alergens_width = len(max(menu[day], key=lambda index: len(index['allergens']))['allergens'])
price_width = len(max(menu[day], key=lambda index: len(index['price']))['price'])
format_string = '{{}}  {{:{}}} {{:>{}}} {{:>{}}}'.format(name_width + 1, alergens_width + 1, price_width + 1)

print(BOLD + ITALIC + GREY + day + NORMAL)
print(DOUBLE_UNDERLINE + BLUE + BOLD + format_string.format('#', 'Název', 'Alergeny', 'Cena') + NORMAL)

for count, meal in enumerate(menu[day]):
    print(format_string.format(BLUE + BOLD + str(count + 1) + NORMAL, meal['name'], meal['allergens'], meal['price']))
