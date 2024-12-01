import numpy as np
class MongoUtil:
  def __init__(self):
    self.user_to_index = {}
    self.index_to_user = {}
    self.item_to_index = {}
    self.index_to_item = {}

  def convertUserId(self, user_id):
    if user_id in self.user_to_index:
      return self.user_to_index[user_id]
    return -1

  def convertIndexToUser(self, index):
    if index in self.index_to_user:
      return self.index_to_user[index]
    return ""

  def convertProductId(self, product_id):
    if product_id in self.item_to_index:
      return self.item_to_index[product_id]
    return -1
  
  def convertIndexToProduct(self, index):
    if index in self.index_to_item:
      return self.index_to_item[index]
    return ""
  
  def convertList(self, method, data):
    return [method(item) for item in data]

  def changeColumnNames(self, df, old_columns, new_columns):
    df.rename(columns={old_columns: new_columns}, inplace=True)

  def convertMongoData(self, data, columns=['userId', 'productId']):
    if 'userId' in columns:
      self.user_to_index = {user: index for index, user in enumerate(np.unique(data['userId']))}
      self.index_to_user = {index: user for index, user in enumerate(np.unique(data['userId']))}
      data['userId'] = data['userId'].map(self.user_to_index)
    if 'productId' in columns:
      self.item_to_index = {item: index for index, item in enumerate(np.unique(data['productId']))}
      self.index_to_item = {index: item for index, item in enumerate(np.unique(data['productId']))}
      data['productId'] = data['productId'].map(self.item_to_index)
    return data

  def convertMongoFrameToNumpy(self, data):
    return data.values
  