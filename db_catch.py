class DB:
  def __init__(self, client, db):
    self.client = client
    self.db = db
    self.dbs = self.client[self.db]
  def find_all(self, data):
    result = []
    if len(data['condition']) == 1:
      data['condition'].append({})
    temp = self.dbs[data['collect']].find(data['condition'][0], data['condition'][1])
    for doc in temp:
      doc['_id'] = str(doc['_id'])
      if data['collect'] == 'product':
        if doc['is_buy']:
          doc['is_buy'] = 1
        else:
          doc['is_buy'] = 0
      result.append(doc)
    return result
  
  def find_one(self, data):
    result = {}
    if len(data['condition']) == 1:
      data['condition'].append({})
    temp = self.dbs[data['collect']].find_one(data['condition'][0], data['condition'][1])
    result = temp
    if result != None:
      result["_id"] = str(result["_id"])
    return result
  
  def insert_one(self, data):
    self.dbs[data['collect']].insert_one(data['condition'][0])

  def delete_one(self, data):
    self.dbs[data['collect']].delete_one(data['condition'][0])

  def update_one(self, data):
    self.dbs[data['collect']].update_one(data['condition'][0], data['condition'][1])

  def aggregate(self, data):
    result = []
    temp = self.dbs[data['collect']].aggregate(data['condition'][0])
    for doc in temp:
      result.append(doc)
    return result