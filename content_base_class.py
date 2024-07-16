import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ContentBase:
    def __init__(self, df, columns):
        self.df = df
        self.columns = columns
        self.features = []
        self.cosine_sim = []
        self.indices = []

    def combine_features(self):
        for i in range(self.df.shape[0]):
            combined = ' '.join(self.df.loc[i, self.columns].values.astype(str))
            self.features.append(combined)

    def get_cosine_similarity(self):
        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform(self.features)
        self.cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    def fit(self):
        self.combine_features()
        self.get_cosine_similarity()
    
    def recommend(self, index, limit=5):
        sim_scores = list(enumerate(self.cosine_sim[index]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:limit+1]
        product_indices = [i[0] for i in sim_scores]
        return product_indices


    def get_recommendations(self, index, limit=5):
        self.indices = pd.Series(self.df.index, index=self.df.index)
        sim_scores = list(enumerate(self.cosine_sim[index]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:limit+1]
        product_indices = [i[0] for i in sim_scores]
        return self.df.iloc[product_indices]
