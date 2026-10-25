API_KEY = "0cfd16273a174c60b80a4dcd9c8b4179"


import requests
import folium
import webbrowser
import os

GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
ROUTING_URL = "https://api.geoapify.com/v1/routing"


def geocode(location) -> dict:
    params = {
        "text": location,
        "format": "json",
        "limit": 1,
        "bias": "proximity:-86.9140,40.4237",
        "apiKey": API_KEY
    }

    response = requests.get(
        GEOCODING_URL, params=params, timeout=10
    )
    response.raise_for_status()

    results = response.json()["results"]

    if not results:
        raise ValueError(f"Location not found: {location}")

    place = results[0]
    print(f"Place found: {place['formatted']}")

    return {
        "name": place["formatted"],
        "lat": float(place["lat"]),
        "lon": float(place["lon"])
    }


def routePlaces(start, end):
    params = {
        "waypoints": (
            f"{start['lat']},{start['lon']}|"
            f"{end['lat']},{end['lon']}"
        ),
        "mode": "walk",
        "format": "geojson",
        "apiKey": API_KEY
    }

    response = requests.get(
        ROUTING_URL, params=params, timeout=20
    )
    response.raise_for_status()

    features = response.json().get("features", [])

    if not features:
        raise ValueError("Geoapify did not return a walking route.")

    route = features[0]

    # campus_map = folium.Map(
    #     location=[
    #         (start["lat"] + end["lat"]) / 2,
    #         (start["lon"] + end["lon"]) / 2
    #     ],
    #     zoom_start=15,
    #     tiles="OpenStreetMap"
    # )

    # folium.Marker(
    #     [start["lat"], start["lon"]],
    #     tooltip="Start",
    #     popup=start["name"]
    # ).add_to(campus_map)

    # folium.Marker(
    #     [end["lat"], end["lon"]],
    #     tooltip="Destination",
    #     popup=end["name"]
    # ).add_to(campus_map)

    # folium.GeoJson(
    #     route,
    #     style_function=lambda feature: {
    #         "color": "blue",
    #         "weight": 5
    #     }
    # ).add_to(campus_map)

    # Fit the map around the route
    # coordinates = route["geometry"]["coordinates"]

    # bounds = [
    #     [coordinate[1], coordinate[0]]
    #     for coordinate in coordinates
    # ]
    
    # campus_map.fit_bounds(bounds)

    # filename = os.path.abspath("walking_route.html")
    # campus_map.save(filename)
    # print(f"Map saved to: {filename}")

    # webbrowser.open("file://" + filename)


def main():
    try:
        location = input("Enter starting location: ")
        start = geocode(location)

        location2 = input("Enter destination: ")
        end = geocode(location2)

        routePlaces(start, end)

    except (requests.exceptions.RequestException, ValueError, KeyError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()


