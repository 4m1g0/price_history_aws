import os
import base64
from shutil import copyfile
import boto3
from boto3.dynamodb.conditions import Key, Attr
from urllib.request import *
from bs4 import BeautifulSoup
import hashlib
import time
import re
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
frontier = dynamodb.Table('crawler_frontier')
history = dynamodb.Table('item_history')

def lambda_handler(event, context):
    response = frontier.query(KeyConditionExpression=Key('url').eq('banggood'), Limit=27)
    if 'Items' in response and response['Items'] != []:
        for item in response['Items']:
            consumeItem(item)
    else:
        initializeFrontier()


def initializeFrontier():
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
                frontier.put_item(Item={'url': 'banggood', 'page':subCatUri})
               
               
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
    
def addItems(items):
    for item in items:
        hash = hashlib.sha256(('banggood' + item['id']).encode('utf-8')).hexdigest()
        history.put_item(Item={'item_hash': hash, 'date': str(item['date']), 'price':str(item['price']), 'url':item['uri']})
    
def consumeItem(item):
    uri = item['page']
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
        print("Error page: " + uri + ". Trying later...")
        return # uri is not removed and will be tried again later
    
    frontier.delete_item(Key={'url':'banggood', 'page':uri})# remove uri from frontier
    soup = BeautifulSoup(html, 'html.parser')
    items = getItems(soup)
    addItems(items)
    link = soup.find('a', title='Next page')          
    if not link:
        return # no more pages here
        
    uri = link.get('href')
    frontier.put_item(Item={'url': 'banggood', 'page':link.get('href')})

    
    #response = table.delete_item(Key={'url':'banggood'}, ConditionExpression='page = :page', ExpressionAttributeValues={':page':'awd'})
