import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Fallback: use open_flights_data if data/ doesn't exist (backward compatibility)
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.join(PROJECT_ROOT, "open_flights_data")

ROUTES_FILE = os.path.join(DATA_DIR, "routes.csv")
AIRLINES_FILE = os.path.join(DATA_DIR, "airlines.dat")
AIRPORTS_FILE = os.path.join(DATA_DIR, "airports.dat")

ROUTES_COLUMNS = [
    "Airline", "Airline_ID", "Source_airport", "Source_airport_ID",
    "Destination_airport", "Destination_airport_ID", "Codeshare",
    "Stops", "Equipment",
]

AIRLINES_COLUMNS = [
    "Airline_ID", "Name", "Alias", "IATA", "ICAO", "Callsign",
    "Country", "Active",
]

AIRPORTS_COLUMNS = [
    "Airport_ID", "Name", "City", "Country", "IATA", "ICAO",
    "Latitude", "Longitude", "Altitude", "Timezone", "DST",
    "Tz", "Type", "Source",
]
