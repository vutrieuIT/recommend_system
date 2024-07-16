from flask import Flask, request, jsonify
from connect_db import MySQLConnection
import pandas as pd
import os

from collaborative_class import CollaborativeClass
from content_base_class import ContentBase

host = os.environ.get('MYSQL_HOST', 'localhost')
user = os.environ.get('MYSQL_USER', 'root')
password = os.environ.get('MYSQL_PASSWORD', '12345')
database = os.environ.get('MYSQL_DATABASE', 'recommend')

sql_rating = "SELECT * FROM ratings"
sql_product = "SELECT * FROM cellphones"
columns_products = ["internal_memory","RAM","performance","main_camera","selfie_camera","battery_size","screen_size","weight","price"]
col_unused = ['cellphone_id',"brand", "model", "operating_system"]


class App:
    def __init__(self):
        self.conn = MySQLConnection(host=host, user=user, password=password, database=database)
        self.app = Flask(__name__)
        self.data = pd.DataFrame(self.get_data(sql_rating), columns=['user_id', 'cellphone_id', 'rating'])
        self.products = pd.DataFrame(self.get_product(sql_product), columns=col_unused + columns_products)
        self.model = CollaborativeClass(self.data.values, k=10, uuCF=1)
        self.model.fit()
        self.model_product = ContentBase(self.products, columns_products)
        self.model_product.fit()
        self.add_urls()
    
    def add_urls(self):
        self.app.add_url_rule('/api/v2/recommend/<int:user_id>', 'recommend', self.recommend, methods=['GET'])
        self.app.add_url_rule('/api/v2/recommend_product/<int:index>', 'recommend_product', self.recommend_product, methods=['GET'])
        self.app.add_url_rule('/api/v2/refresh_ratings', 'refresh_ratings', self.refresh_ratings, methods=['GET'])
        self.app.add_url_rule('/api/v2/refresh_products', 'refresh_products', self.refresh_products, methods=['GET'])
        
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
        spected_rating = request.args.get('spected_rating', default=6, type=float)
        if user_id not in self.data['user_id'].values:
            user_ids = self.data['user_id'].values.distinct().tolist()
            return jsonify({'message': 'User ID not found', 'user_ids': user_ids})
        return self.model.recommend(user_id, spected_rating=spected_rating)

    def recommend_product(self, index):
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
    

    def run(self, debug=False, host='localhost', port=5000):
        self.app.run(debug=debug, host=host, port=port)