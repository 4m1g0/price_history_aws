def save(catalog):
    with table.batch_writer() as batch:
        for key, item in catalog.items():
            print(key)
            hash = hashlib.sha256(('banggood' + item['id']).encode('utf-8')).hexdigest()
            batch.put_item(Item={'item_hash': hash, 'date': str(item['date']), 'price':str(item['price']), 'url':item['uri']})
