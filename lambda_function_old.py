import os
import base64
from shutil import copyfile
import boto3


def lambda_handler(event, context):
    # TODO implement
    copyfile("template.html", "/tmp/template.html")
    file = open('/tmp/data.js', 'w')
    file.write('word="%s"' % (event['queryStringParameters']['word']))
    file.close()
    
    os.system('./phantomjs phantomScript.js /tmp/template.html /tmp/test234.png')
    
    body = '<img src="data:image/png;base64, %s" />' % (base64.b64encode(open('/tmp/test234.png', 'rb').read()).decode('utf-8'))
    
    s3 = boto3.client('s3')
    s3.upload_file('/tmp/test234.png', 'crawler-graphs', 'imagen.png')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('crawler_frontier')
    table.put_item(Item={'url': str(event['queryStringParameters']['word'])})
    
    
    return {
        "statusCode": 200,
        "headers": { "Content-Type": "text/html"},
        "body":  body 
    }

