from pymongo import MongoClient
import pandas as pd
import os 

class ConnectMongoDB:

    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    def connect(self, database):
        self.client = MongoClient(self.host, self.port)
        self.db = self.client[database]

    def execute_query(self, collection, query, projection):
        return self.db[collection].find(query, projection)
    
    def execute_aggregation(self, collection, pipeline):
        return self.db[collection].aggregate(pipeline)

    def close(self):
        self.client.close()
