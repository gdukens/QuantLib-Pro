import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

class RegimeModel:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = None
        self.features = None
        self.pca_data = None
        self.labels = None
        self.regime_names = ['Bull', 'Bear', 'Sideways']

    def download_data(self):
        self.data = yf.download(self.ticker, period='5y', interval='1d')

    def compute_features(self):
        df = self.data.copy()
        price_col = 'Close'
        df['Return'] = df[price_col].pct_change()
        df['Volatility'] = df['Return'].rolling(window=21).std()
        df['Momentum'] = df[price_col].diff(21)
        df['MA50'] = df[price_col].rolling(window=50).mean()
        df['MA200'] = df[price_col].rolling(window=200).mean()
        df = df.dropna()
        self.features = df[['Return', 'Volatility', 'Momentum', 'MA50', 'MA200']]

    def reduce_dimensions(self):
        pca = PCA(n_components=3)
        self.pca_data = pca.fit_transform(self.features)

    def cluster_regimes(self):
        kmeans = KMeans(n_clusters=3, random_state=42)
        self.labels = kmeans.fit_predict(self.pca_data)

    def label_regimes(self):
        # Assign cluster labels to regimes based on mean returns
        means = [self.features['Return'][self.labels == i].mean() for i in range(3)]
        order = np.argsort(means)[::-1]
        mapping = {order[0]: 'Bull', order[1]: 'Sideways', order[2]: 'Bear'}
        self.labels = np.vectorize(mapping.get)(self.labels)

    def process(self):
        self.download_data()
        self.compute_features()
        self.reduce_dimensions()
        self.cluster_regimes()
        self.label_regimes()
