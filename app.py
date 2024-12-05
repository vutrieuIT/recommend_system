from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin 
from connect_db import ConnectMongoDB
import pandas as pd
from waitress import serve
import os
import numpy as np

from collaborative_class import CollaborativeClass
from content_base_class import ContentBase
from mongo_util import MongoUtil

mongo_host = os.environ.get('MONGO_HOST', 'localhost')
mongo_port = os.environ.get('MONGO_PORT', 27017)
mongo_database = os.environ.get('MONGO_DATABASE', 'kltn')

# Câu truy vấn (tìm tất cả tài liệu trong collection 'rating')
query_mongo_rating = {}

# Projection (chỉ lấy 3 trường: userId, productId, rating)
projection_rating = {"userId": 1, "productId": 1, "rating": 1, "_id": 0}

pipeline_product = [
    {
        "$unwind": "$specifications"  # Unwind mảng specifications để xử lý từng phần tử trong đó
    },
    {
        "$unwind": "$specifications.colorVariant"  # Unwind mảng colorVariant để xử lý từng phần tử
    },
    {
        "$project": {
            "_id": {"$toString": "$_id"},  # Chuyển _id thành chuỗi
            "internalMemory": "$specifications.internalMemory",  # Lấy internalMemory từ specifications
            "price": "$specifications.price",  # Lấy price từ specifications
            "color": "$specifications.colorVariant.color",  # Lấy color từ colorVariant
            "ram": 1,  # Lấy ram từ document gốc
            "operatingSystem": 1,  # Lấy operatingSystem từ document gốc
            "mainCamera": 1,  # Lấy mainCamera từ document gốc
            "selfieCamera": 1,  # Lấy selfieCamera từ document gốc
            "batterySize": 1,  # Lấy batterySize từ document gốc
            "weight": 1  # Lấy weight từ document gốc
        }
    }
]

columns_products = ['internalMemory', 'price', 'color', 'ram', 'operatingSystem', 'mainCamera', 'selfieCamera', 'batterySize', 'weight']
columns_products_unused = ['_id']
class App:
    def __init__(self):
        self.conn = ConnectMongoDB(mongo_host, mongo_port)
        self.app = Flask(__name__)
        CORS(self.app)
        self.mongoUtil = MongoUtil()
        self.data = self.get_rating()
        self.products = self.get_product()
        self.model = CollaborativeClass(self.data.values, k=5, uuCF=1)
        self.model.fit()
        self.model_product = ContentBase(self.products, columns_products)
        self.model_product.fit()
        self.add_urls()
    
    def add_urls(self):
        self.app.add_url_rule('/recommend/user/<string:user_id>', 'recommend', self.recommend, methods=['GET'])
        self.app.add_url_rule('/recommend/product/<string:index>', 'recommend_product', self.recommend_product, methods=['GET'])
        self.app.add_url_rule('/recommend/refresh/ratings', 'refresh_ratings', self.refresh_ratings, methods=['GET'])
        self.app.add_url_rule('/recommend/refresh/products', 'refresh_products', self.refresh_products, methods=['GET'])
        
    def get_rating(self):
        self.conn.connect(database=mongo_database)
        data = self.conn.execute_query('rating', query_mongo_rating, projection_rating)
        data_frame = self.mongoUtil.convertMongoData(pd.DataFrame(data))
        self.conn.close()
        return data_frame

    def get_product(self):
        self.conn.connect(database=mongo_database)
        data = self.conn.execute_aggregation('product', pipeline_product)
        data_frame = pd.DataFrame(data).rename(columns={"_id": "productId"})
        self.conn.close()
        return data_frame

    def api(self):
        data = request.args.get('data')
        return jsonify({'data': data})

    def test(self):
        return jsonify(self.data.to_dict(orient='records'))
    
    def recommend(self, user_id):
        print("user_id: ", user_id)
        user_id = int(self.mongoUtil.convertUserId(user_id))
        spected_rating = request.args.get('spected_rating', default=3, type=float)
        if user_id not in self.data['userId'].values:
            user_ids = np.unique(self.data['userId'].values).tolist()
            user_ids = self.mongoUtil.convertList(self.mongoUtil.convertIndexToUser, user_ids)
            return jsonify({'message': 'User ID not found', 'user_ids': user_ids})
        result = self.model.recommend(user_id, spected_rating=spected_rating)
        result_converted = self.mongoUtil.convertList(self.mongoUtil.convertIndexToProduct, result)
        return result_converted

    def recommend_product(self, index):
        print("product_id: ", index)
        index = int(self.mongoUtil.convertProductId(index))
        limit = request.args.get('limit', default=5, type=int)
        result = self.model_product.recommend(index, limit=limit)
        result_converted = self.mongoUtil.convertList(self.mongoUtil.convertIndexToRealProductId, result)
        return result_converted

    def refresh_ratings(self):
        self.data = self.get_rating()
        self.model = CollaborativeClass(self.data.values, k=5, uuCF=1)
        self.model.fit()
        return jsonify({'message': 'Ratings has been refreshed'})
    
    def refresh_products(self):
        self.products = self.get_product()
        self.model_product = ContentBase(self.products, columns_products)
        self.model_product.fit()
        return jsonify({'message': 'Products has been refreshed'})
    

    def run(self, debug=False, host='0.0.0.0', port=5000):
        print('Server at http://{}:{}'.format(host, port))
        serve(self.app, host=host, port=port)