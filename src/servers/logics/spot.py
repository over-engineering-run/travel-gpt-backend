import os
import sys

import logging

from wrapt_timeout_decorator import timeout
from serpapi import GoogleSearch
import requests

_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root_dir)

from servers.models import spot as spot_models


_GLEN_TIMEOUT = 60.0
_GMAP_TIMEOUT = 10.0

_SPOT_SOURCE_WHITELIST_SET = {
    'agoda',
    'dreamstime',
    'expedia',
    'istockphoto',
    'kiwicollection',
    'kkday',
    'klook',
    'tripadvisor'
}

_SPOT_SOURCE_BLACKLIST_SET = {
    'skyscrapercity'
}


def _glen_match_to_spot_image(serpapi_match: str) -> spot_models.SpotImage:

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
    glen_visual_matches = serpapi_search_results["visual_matches"]

    logging.info("matching spots using serpapi...")

    # # by kayac crawler
    # glen_req_url = "https://visual-search-api-service.fly.dev/search/google-lens"
    # glen_req_params = {
    #     "url": pic_url
    # }

    # # matches
    # resp = requests.get(
    #     glen_req_url,
    #     params=glen_req_params,
    #     timeout=_GLEN_TIMEOUT
    # )
    # glen_visual_matches = resp.json().get('visual_matches')

    # filter match
    prioritized_matches = []
    other_matches = []
    for v_match in glen_visual_matches:

        pass_bool = False
        for v_src in _SPOT_SOURCE_WHITELIST_SET:
            if v_src in v_match['source'].lower():
                prioritized_matches.append(v_match)
                pass_bool = True
                print(v_match)
                break

        if not pass_bool:
            other_matches.append(v_match)

    filtered_matches = prioritized_matches

    # filtered_matches = prioritized_matches + other_matches
    # filtered_matches = filtered_matches[:10]

    # if len(prioritized_matches) > 0:
    #     filtered_matches = prioritized_matches
    # else:
    #     filtered_matches = other_matches[:10]

    # result
    spot_img_list = []
    for v_match in filtered_matches:
        spot_img_list.append(_glen_match_to_spot_image(v_match))

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
                rating=result.get('rating', 0),
                rating_n=result.get('user_ratings_total', 0),
                place_id=result['place_id'],
                reference=result['reference'],
                types=result['types'],
                geometry=result['geometry'],
            )
            result_list.append(spot)

    return result_list


def search_nearby_spots_by_spot(
        api_key: str,
        spot: spot_models.Spot,
        logger: logging.Logger
) -> list[spot_models.Spot]:

    # request for tourist_attraction
    gmap_req_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    gmap_req_params = {
        "location": f"{spot.geometry['location']['lat']},{spot.geometry['location']['lng']}",
        "radius":   "5000",
        "type":     "tourist_attraction",
        "key":      api_key
    }
    resp = requests.get(
        gmap_req_url,
        params=gmap_req_params,
        timeout=_GMAP_TIMEOUT
    )

    # check tourist_attraction response
    if len(resp.json().get('results')) == 0:

        # request without type
        gmap_req_params.pop('type', None)
        resp = requests.get(
            gmap_req_url,
            params=gmap_req_params,
            timeout=_GMAP_TIMEOUT
        )

    # parse response
    result_list = []

    raw_result_list = resp.json().get('results')
    if (raw_result_list is not None) and (len(raw_result_list) > 0):

        for result in raw_result_list:

            diff_set = {'vicinity', 'name', 'place_id', 'types', 'geometry'} - set(result.keys())

            if len(diff_set) > 0:
                logger.warning("result nearby spot missing %s", diff_set)
                continue

            spot = spot_models.Spot(
                address=result['vicinity'],
                name=result['name'],
                rating=result.get('rating', 0),
                rating_n=result.get('user_ratings_total', 0),
                place_id=result['place_id'],
                reference=spot.place_id,
                types=result['types'],
                geometry=result['geometry']
            )
            result_list.append(spot)

    return result_list
