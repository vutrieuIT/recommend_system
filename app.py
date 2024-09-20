from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin 
from connect_db import MySQLConnection
import pandas as pd
from waitress import serve
import os
import numpy as np

from collaborative_class import CollaborativeClass
from content_base_class import ContentBase

host = os.environ.get('MYSQL_HOST', 'localhost')
user = os.environ.get('MYSQL_USER', 'root')
password = os.environ.get('MYSQL_PASSWORD', '12345')
database = os.environ.get('MYSQL_DATABASE', 'tlcn')

sql_rating = "SELECT user_id, cellphone_id, rating FROM ratings"
sql_product = "SELECT * FROM specification"
columns_products = ["internal_memory","RAM","performance","main_camera","selfie_camera","battery_size","screen_size","weight","price"]
col_unused = ['cellphone_id',"brand_id", "model", "operating_system"]


class App:
    def __init__(self):
        self.conn = MySQLConnection(host=host, user=user, password=password, database=database)
        self.app = Flask(__name__)
        CORS(self.app)
        self.data = pd.DataFrame(self.get_data(sql_rating), columns=['user_id', 'cellphone_id', 'rating'])
        self.products = pd.DataFrame(self.get_product(sql_product), columns=col_unused + columns_products)
        self.model = CollaborativeClass(self.data.values, k=10, uuCF=1)
        self.model.fit()
        self.model_product = ContentBase(self.products, columns_products)
        self.model_product.fit()
        self.add_urls()
    
    def add_urls(self):
        self.app.add_url_rule('/recommend/user/<int:user_id>', 'recommend', self.recommend, methods=['GET'])
        self.app.add_url_rule('/recommend/product/<int:index>', 'recommend_product', self.recommend_product, methods=['GET'])
        self.app.add_url_rule('/recommend/refresh/ratings', 'refresh_ratings', self.refresh_ratings, methods=['GET'])
        self.app.add_url_rule('/recommend/refresh/products', 'refresh_products', self.refresh_products, methods=['GET'])
        
    def get_data(self, sql):
        self.conn.connect()
        data = self.conn.execute_query(sql)
        self.conn.close()
        return data
    
    def get_product(self, sql):
        self.conn.connect()
        data = self.conn.execute_query(sql)
        self.conn.close()
        return data

    def api(self):
        data = request.args.get('data')
        return jsonify({'data': data})

    def test(self):
        return jsonify(self.data.to_dict(orient='records'))
    
    def recommend(self, user_id):
        print("user_id: ", user_id)
        spected_rating = request.args.get('spected_rating', default=6, type=float)
        if user_id not in self.data['user_id'].values:
            user_ids = np.unique(self.data['user_id'].values).tolist()
            return jsonify({'message': 'User ID not found', 'user_ids': user_ids})
        return self.model.recommend(user_id, spected_rating=spected_rating)

    def recommend_product(self, index):
        print("product_id: ", index)
        limit = request.args.get('limit', default=5, type=int)
        return self.model_product.recommend(index, limit=limit)

    def refresh_ratings(self):
        self.data = pd.DataFrame(self.get_data(sql_rating), columns=['user_id', 'cellphone_id', 'rating'])
        self.model = CollaborativeClass(self.data.values, k=10, uuCF=1)
        self.model.fit()
        return jsonify({'message': 'Ratings has been refreshed'})
    
    def refresh_products(self):
        self.products = pd.DataFrame(self.get_product(sql_product), columns=col_unused + columns_products)
        self.model_product = ContentBase(self.products, columns_products)
        self.model_product.fit()
        return jsonify({'message': 'Products has been refreshed'})
    

    def run(self, debug=False, host='0.0.0.0', port=5000):
        print('Server at http://{}:{}'.format(host, port))
        serve(self.app, host=host, port=port)