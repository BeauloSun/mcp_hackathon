import requests


def find_place_id(query):
    """
    Uses the Google Places API Find Place endpoint to find a Place ID based on a text query.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address,geometry", # Request the fields you need
        "key": gmap_api,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data.get("status") == "OK" and data.get("candidates"):
            # Return the first candidate's information
            place = data["candidates"][0]
            return {
                "place_id": place.get("place_id"),
                "name": place.get("name"),
                "formatted_address": place.get("formatted_address"),
                "geometry": place.get("geometry")
            }
        elif data.get("status") == "ZERO_RESULTS":
            print(f"No results found for '{query}'.")
            return None
        else:
            print(f"Error from Google Places API: {data.get('status')}")
            print(data.get("error_message", ""))
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    

def get_review_data(place_id):
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    # Check for available fields:
    # https://developers.google.com/maps/documentation/places/web-service/place-details
    # fields is for information of the place (NO SPACE AFTER COMMA)
    fields = "displayName,rating,userRatingCount"
    params = {
        "fields": fields,
        "key": gmap_api
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 

        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"



# if __name__ == '__main__':
#     response = find_place_id('Endsleigh Court')
#     place_id = response['place_id']
#     data = get_review_data(place_id)
#     print(data)