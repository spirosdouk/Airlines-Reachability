"""Download Open Flights dataset from Kaggle."""

import os
from kaggle.api.kaggle_api_extended import KaggleApi

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

if __name__ == "__main__":
    api = KaggleApi()
    api.authenticate()
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    api.dataset_download_files("open-flights/flight-route-database", path=DATA_DIR, unzip=True)
    print(f"Data downloaded to {DATA_DIR}/")
