API_KEY = "0cfd16273a174c60b80a4dcd9c8b4179"

import requests

url = "https://api.geoapify.com/v1/geocode/search"


def main():
    params = {
        "text": "Stewart Center, Purdue University, West Lafayette, Indiana",
        "format": "json",
        "limit": 5,
        "bias": "proximity:-86.9140,40.4237",
        "apiKey": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        for place in data.get("results", []):
            print("Place:", place.get("formatted"))
            print("Latitude:", place.get("lat"))
            print("Longitude:", place.get("lon"))
            print()

    except requests.exceptions.RequestException as error:
        print("API request failed:", error)


if __name__ == "__main__":
    main()

