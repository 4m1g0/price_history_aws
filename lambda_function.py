import boto3
import traceback
import json
import re
import requests
import hashlib
from boto3.dynamodb.conditions import Key, Attr
from shutil import copyfile
import os

URL = "https://api.telegram.org/bot506432655:AAFGQ8BSRhVKxc1tg8dMBmFP8grjVpmae38/"
dynamodb = boto3.resource('dynamodb')
history = dynamodb.Table('item_history')
copyfile("template.html", "/tmp/template.html")
copyfile("Chart.bundle.min.js", "/tmp/Chart.bundle.min.js")

def getIdFromUrl(url):
    match = re.match(r'.*-p-(\d*)\.html', str(url))
    if match:
        return match.group(1)

def lambda_handler(event, context):
    update = {}
    try:
        update = json.loads(event['body'])
    except:
        traceback.print_exc()
        return
        
    if update['message']['text'].startswith('/history '):
        url = update['message']['text'].split(' ')[1]
        id = getIdFromUrl(url)
        print(id)
        hash = hashlib.sha256(('banggood' + str(id)).encode('utf-8')).hexdigest()
        response = history.query(ProjectionExpression="price", KeyConditionExpression=Key('item_hash').eq(hash))
        if 'Items' in response and response['Items'] != []:
            print(response['Items'])
            items = [x['price'] for x in response['Items']]
            file = open('/tmp/data.js', 'w')
            file.write('data=%s' % (str(items)))
            file.close()
            os.system('./phantomjs phantomScript.js /tmp/template.html /tmp/image.png')
            s3 = boto3.client('s3')
            s3.upload_file('/tmp/image.png', 'crawler-graphs', str(hash) + '.png')
            r = requests.post(URL + "sendPhoto", data={"chat_id": -284240927, "photo": str("https://s3.us-east-2.amazonaws.com/crawler-graphs/" + hash + ".png")})
                
    return {"body": ""}

