#! /usr/bin/python3
import sys
import pickle
import re
from urllib.request import *
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import random
import traceback

def isCategoryUrl(url):
    return bool(re.match(r'.*-c-\d*\.html', str(url)))
    
def getIdFromUrl(url):
    match = re.match(r'.*-p-(\d*)\.html', str(url))
    if match:
        return match.group(1)
    
def buildItem(li):
    item = {}
    item['uri'] = str(li.find('span', class_='title').a.get('href'))
    item['id'] = getIdFromUrl(item['uri'])
    try:
        item['price'] = float(li.find('span', class_='price').get('oriprice'))
    except:
        item['price'] = 0.0
    item['date'] = datetime.now()
    return item
    
def getItems(soup):
    lista = soup.find('ul', class_='goodlist_1') 
    if lista:
        return [buildItem(item) for item in lista.find_all('li')]
    return []
    
def addItems(catalog, items):
    for item in items:
        if item['id'] in catalog and item['date'] - catalog[item['id']]['date'] > timedelta(hours=48):
            print("DEBUG: Updated item")
            catalog[item['id']]['price'] = item['price']
            if abs(catalog[item['id']]['price'] - item['price']) > item['price']*0.20:
                print("HIGH diference: " + str(item))
            if catalog[item['id']]['uri'] != item['uri']:
                print("url changed: " + item)
                catalog[item['id']]['uri'] = item['uri']
        else:
            #print("DEBUG: Inserted item "+ str(item))
            catalog[item['id']] = item

def main(argv):
    if len(argv) < 1:
        print("Error. Usage: crowler <catalog file> [<saved frontier>]")
        sys.exit(2)

    try:
        catalog = pickle.load(open(argv[0], 'rb'))
    except:
        catalog = {}
        
    frontier = []
    try:
        if len(argv) > 1:
            frontier = pickle.load(open(argv[1], 'rb'))
    except:
        pass
    
    try:
        if not frontier:
            print("Initializing...")
            req = Request(
                'http://www.banggood.com/', 
                data=None, 
                headers={
                    'User-Agent': 'chrome'
                }
            )
            html = urlopen(req).read()
            soup = BeautifulSoup(html, 'html.parser')
            categories_bulk = soup.find_all('dl', class_='cate_list')
            # todas las categorias existentes
            for mainCategory in categories_bulk:
                subCategories = mainCategory.find('dd', class_='cate_sub').find_all('dt')
                for subCategory in subCategories:
                    if not subCategory:
                        continue
                    
                    subCatUri = subCategory.a.get('href')
                    if subCatUri:
                        frontier.append(str(subCatUri))
            
        while frontier:
            uri = random.choice(frontier)
            print("Trying uri: " + uri)
            
            req = Request(
                    uri, 
                    data=None, 
                    headers={
                        'User-Agent': 'chrome'
                    }
                )
                
            try:
                html = urlopen(req).read()
            except:
                time.sleep(50 + random.uniform(0,8)) # wait
                print("Error page: " + uri + ". Trying later...")
                continue # uri is not removed and will be tried again later
            
            frontier.remove(uri) # remove uri from frontier
            soup = BeautifulSoup(html, 'html.parser')
            items = getItems(soup)
            addItems(catalog, items)
            link = soup.find('a', title='Next page')          
            if not link:
                continue
                
            uri = link.get('href')
            frontier.append(str(uri))
            time.sleep(17 + random.uniform(0,8)) 
            print("Number of items in catalog: " + str(len(catalog)))
        
    except:
        print("Fatal Error: Saving progress...")
        pickle.dump(frontier, open('frontier_crash.bak', 'wb'))
        pickle.dump(catalog, open(argv[0], 'wb'))
        traceback.print_exc()
        sys.exit(0)
        
    pickle.dump(catalog, open(argv[0], 'wb'))

if __name__ == "__main__":
   main(sys.argv[1:])
