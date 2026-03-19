import csv
import os
import sys

import pandas as pd

from .config import (
    AIRLINES_COLUMNS,
    AIRLINES_FILE,
    AIRPORTS_COLUMNS,
    AIRPORTS_FILE,
    ROUTES_COLUMNS,
    ROUTES_FILE,
)


def read_data(file_path: str, columns: list[str], file_type: str = "csv") -> pd.DataFrame:
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        sys.exit(1)
    try:
        if file_type == "csv":
            df = pd.read_csv(file_path, header=0, names=columns, encoding="latin1")
        elif file_type == "dat":
            df = pd.read_csv(
                file_path,
                header=None,
                names=columns,
                encoding="latin1",
                delimiter=",",
                engine="python",
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"',
                na_values=["\\N"],
                keep_default_na=False,
                dtype=str,
            )
        else:
            raise ValueError("Unsupported file type.")
        print(f"Loaded {file_path} successfully.")
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)


def load_and_merge_data() -> pd.DataFrame:
    routes = read_data(ROUTES_FILE, ROUTES_COLUMNS, file_type="csv")
    airlines = read_data(AIRLINES_FILE, AIRLINES_COLUMNS, file_type="dat")
    airports = read_data(AIRPORTS_FILE, AIRPORTS_COLUMNS, file_type="dat")

    # Clean
    routes.replace("\\N", pd.NA, inplace=True)
    airlines.replace("\\N", pd.NA, inplace=True)
    airports.replace("\\N", pd.NA, inplace=True)

    routes["Stops"] = pd.to_numeric(routes["Stops"], errors="coerce")
    routes["Airline"] = routes["Airline"].astype(str)
    airlines["IATA"] = airlines["IATA"].astype(str)
    routes["Source_airport"] = routes["Source_airport"].astype(str)
    routes["Destination_airport"] = routes["Destination_airport"].astype(str)
    airports["Latitude"] = pd.to_numeric(airports["Latitude"], errors="coerce")
    airports["Longitude"] = pd.to_numeric(airports["Longitude"], errors="coerce")

    # Merge routes with airlines
    routes = routes.merge(
        airlines[["IATA", "Name", "Country"]],
        left_on="Airline",
        right_on="IATA",
        how="left",
        suffixes=("", "_airline"),
    )

    # Merge routes with airports (source)
    routes = routes.merge(
        airports[["IATA", "Country", "Latitude", "Longitude"]],
        left_on="Source_airport",
        right_on="IATA",
        how="left",
        suffixes=("", "_source"),
    )

    # Merge routes with airports (destination)
    routes = routes.merge(
        airports[["IATA", "Country", "Latitude", "Longitude"]],
        left_on="Destination_airport",
        right_on="IATA",
        how="left",
        suffixes=("", "_dest"),
    )

    return routes, airlines, airports
