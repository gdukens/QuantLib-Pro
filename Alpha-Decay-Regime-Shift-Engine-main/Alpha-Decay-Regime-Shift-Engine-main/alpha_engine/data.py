import numpy as np
import pandas as pd

def generate_synthetic_data(n_assets=3, n_days=1000, seed=42):
    """
    Generate synthetic price data for multiple assets.
    Returns a DataFrame with columns: ['Asset', 'Date', 'Price']
    """
    np.random.seed(seed)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=n_days)
    data = []
    for asset in range(n_assets):
        price = 100 + np.cumsum(np.random.normal(0, 1, n_days))
        data.append(pd.DataFrame({
            'Asset': f'Asset_{asset+1}',
            'Date': dates,
            'Price': price
        }))
    return pd.concat(data, ignore_index=True)
