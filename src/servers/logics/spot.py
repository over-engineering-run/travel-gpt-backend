import os
import sys

from wrapt_timeout_decorator import timeout
from serpapi import GoogleSearch
import requests

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from servers.models import spot as spot_models


_SERPAPI_TIMEOUT = 15.0
_GMAP_TIMEOUT = 3.0

_SPOT_SOURCE_WHITELIST_SET = {
    'agoda.com',
    'dreamstime.com',
    'expedia.com',
    'istockphoto.com',
    'kiwicollection.comtrip.com',
    'kkday.com',
    'klook.com',
    'tripadvisor.com'
}

_SPOT_SOURCE_BLACKLIST_SET = {
    'skyscrapercity.com'
}


def _serpapi_match_to_spot_image(serpapi_match: str) -> spot_models.SpotImage:

    spot = spot_models.SpotImage(
        title=serpapi_match['title'],
        thumbnail=serpapi_match['thumbnail'],
    )

    spot.meta_data = {
        'position':   serpapi_match['position'],
        'src_domain': serpapi_match['source'],
        'src_url':    serpapi_match['link']
    }

    return spot


@timeout(_SERPAPI_TIMEOUT)
def search_spot_image_by_pic_url(api_key: str, pic_url: str) -> list[spot_models.SpotImage]:

    # serpapi request
    params = {
        "engine":   "google_lens",
        "url":      pic_url,
        "api_key":  api_key,
        "hl":       "en",
        "output":   "JSON",
        "no_cache": "true"
    }

    serpapi_search = GoogleSearch(params)
    serpapi_search_results = serpapi_search.get_dict()
    serpapi_search_visual_matches = serpapi_search_results["visual_matches"]

    # filter match
    filtered_matches = []
    for match in serpapi_search_visual_matches:
        if match['source'] in _SPOT_SOURCE_WHITELIST_SET:
            filtered_matches.append(match)

    # result
    spot_img_list = []
    for match in filtered_matches:
        spot_img_list.append(_serpapi_match_to_spot_image(match))

    return spot_img_list


def search_spot_by_spot_image(api_key: str, image: spot_models.SpotImage) -> list[spot_models.Spot]:

    # request
    gmap_req_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
    gmap_req_params = {
        'key':   api_key,
        'query': image.title
    }

    resp = requests.get(
        gmap_req_url,
        params=gmap_req_params,
        timeout=_GMAP_TIMEOUT
    )

    # result
    result_list = []

    raw_result_list = resp.json().get('results')
    if (raw_result_list is not None) and (len(raw_result_list) > 0):
        for result in raw_result_list:
            spot = spot_models.Spot(
                address=result['formatted_address'],
                name=result['name'],
                rating=result['rating'],
                rating_n=result['user_ratings_total'],
                place_id=result['place_id'],
                reference=result['reference'],
                types=result['types'],
                geometry=result['geometry'],
            )
            result_list.append(spot)

    return result_list
