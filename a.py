from kaggle.api.kaggle_api_extended import KaggleApi
import os

api = KaggleApi()
api.authenticate()

dataset = "open-flights/flight-route-database"
path = "open_flights_data"

if not os.path.exists(path):
    os.makedirs(path)

api.dataset_download_files(dataset, path=path, unzip=True)
