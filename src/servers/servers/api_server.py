import os
import sys
import json
import logging

import random

from flask.logging import create_logger
from flask import request, Response, abort

import openai

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from utils import json as js_utils
from init import openai as openai_init

from servers.models import mood as mood_models
from servers.models import picture as pic_models
from servers.logics import mood as mood_logics
from servers.logics import picture as pic_logics
from servers.logics import spot as spot_logics
from servers.utils import model as model_utils

from databases.models.mood import MoodMessage as DBMoodMessage
from databases.models.mood import MoodPicture as DBMoodPicture
from databases.models.picture import Picture as DBPicture
from databases.models.spot import SpotImage as DBSpotImage
from databases.models.spot import Spot as DBSpot


class EndpointAction:

    """init and add endpoint action with params"""

    def __init__(self, action, action_params):
        self.action = action
        self.__name__ = action.__name__
        self.__qualname__ = action.__name__
        self.action_params = action_params

    def __call__(self, *args, **kwargs):
        return self.action(self.action_params, *args, **kwargs)


class APIServer:

    """backend api server"""

    def __init__(self, app, params, db):

        self.app = app
        self.app_params = params
        self.app_resources = self.build_server_resources()
        self.db = db
        self.logger = create_logger(self.app)

        # debug
        self.logger.info("app params:\n%s", json.dumps(self.app_params, indent=4))

        # init openai
        self.logger.info("initializing openai api...")

        openai.organization = self.app_params['openai_api_org']
        openai.api_key = self.app_params['openai_api_key']
        try:
            openai_init.init_openai(
                self.app_params['openai_api_org'],
                self.app_params['openai_api_key'],
                1
            )
        except Exception as e:
            self.logger.error(e)
            abort(500)

        # init api endpoints
        self.logger.info("initializing api endpoints...")

        self.add_endpoint(
            endpoint="/healthz",
            endpoint_name="healthz",
            handler=self.healthz,
            handler_params={},
            req_methods=["GET"]
        )
        self.add_endpoint(
            endpoint="/v1/mood",
            endpoint_name="get-rand-mood-msg",
            handler=self.random_mood_message,
            handler_params={},
            req_methods=["GET"]
        )
        self.add_endpoint(
            endpoint="/v1/mood",
            endpoint_name="post-mood-msg",
            handler=self.create_mood_message,
            handler_params={},
            req_methods=["POST"]
        )
        self.add_endpoint(
            endpoint="/v1/mood/<string:mood_id>/picture",
            endpoint_name="post-mood-pic",
            handler=self.generate_mood_picture,
            handler_params={},
            req_methods=["POST"]
        )
        self.add_endpoint(
            endpoint="/v1/pictures",
            endpoint_name="post-picture",
            handler=self.save_picture_to_s3,
            handler_params={},
            req_methods=["POST"]
        )
        self.add_endpoint(
            endpoint="/v1/spots/search",
            endpoint_name="spot-search",
            handler=self.spot_search_by_picture,
            handler_params={},
            req_methods=["GET"]
        )

    def build_server_resources(self):

        # mood message
        with self.app.app_context():
            cached_msg_list = DBMoodMessage.query.filter_by(cached=True).all()

        cached_msg_id_list = []
        for msg in cached_msg_list:
            if (msg.content is None) or (len(msg.content.strip()) == 0):
                continue
            cached_msg_id_list.append(str(msg.id))

        return {
            'cached_mood_message_id_list': cached_msg_id_list
        }

    def run(self):

        """start running APIServer"""

        self.app.run(
            debug=self.app_params['app_debug'],
            port=self.app_params['app_port'],
            host=self.app_params['app_host']
        )

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None, handler_params=None, req_methods=["GET"]):

        """add new endpoint using EndpointAction"""

        self.app.add_url_rule(
            endpoint,
            endpoint_name,
            EndpointAction(handler, handler_params),
            methods=req_methods
        )

    def healthz(self, params: dict, *args: list, **kwargs: dict):

        """
        healthz: for endpoint heath checking
        curl -XGET 'http://0.0.0.0:5000/healthz'
        """

        return Response(
            response=json.dumps(
                {
                    "message":       "/healthz running",
                    "error_type":    None,
                    "error_message": None
                }
            ),
            status=200,
            headers={"Content-Type": "application/json"}
        )

    def random_mood_message(self, params: dict, *args: list, **kwargs: dict):

        """
        generate random mood description
        curl -XGET 'http://0.0.0.0:5000/v1/mood?cached=false'
        """

        self.logger.info(f"handling request for /v1/mood")

        # openai generate random mood description
        try:

            req_cache_bool_str = request.args.get('cached', default="true", type=str)
            req_cache_bool = req_cache_bool_str.lower() != 'false'

            random_mood_str = ""

            # try to get from cached
            if req_cache_bool:
                cached_mood_message_id_list = self.app_resources['cached_mood_message_id_list']
                cached_msg_n = len(cached_mood_message_id_list)
                if cached_msg_n > 0:
                    cached_i = random.randint(0, cached_msg_n-1)
                    cached_msg_id = cached_mood_message_id_list[cached_i]
                    db_mood_msg = DBMoodMessage.query.get(cached_msg_id)
                    random_mood_str = db_mood_msg.content

            # generate by openai
            if (random_mood_str is None) or (len(random_mood_str.strip()) == 0):
                random_mood_str = mood_logics.generate_random_mood_message(
                    model=self.app_params['mood_message_model'],
                )

        except Exception as e:
            err_msg = f"endpoint: /v1/mood, error: {repr(e)}"
            self.logger.error(err_msg)

            if type(e).__name__ == 'TimeoutError':
                status_code = 504
            else:
                status_code = 500

            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailedToProcessRequest",
                        "error_message": err_msg
                    }
                ),
                status=status_code,
                headers={"Content-Type": "application/json"}
            )

        self.logger.info("done request for /v1/mood")

        # response
        resp = {
            "message": random_mood_str,
        }

        return Response(
            response=json.dumps(
                resp,
                default=js_utils.json_serializer
            ),
            status=200,
            headers={"Content-Type": "application/json"}
        )

    def create_mood_message(self, params: dict, *args: list, **kwargs: dict):

        """
        generate random mood description
        curl -XPOST 'http://0.0.0.0:5000/v1/mood' -H 'Content-Type: application/json' -d '{"message":"quite happy and relaxing", "cache": true}'
        """

        # parse request
        req_data = request.get_json()
        req_msg = req_data.get('message')
        if req_msg is None:
            req_str = json.dumps(req_data, default=js_utils.json_serializer)
            err_msg = f"endpoint: /v1/mood, error: request missing message, request: {req_str}"
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "RequestMissingArguments",
                        "error_message": err_msg
                    }
                ),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        req_cache_bool = req_data.get('cache', False)

        # create new mood message instance
        mood_msg = mood_models.MoodMessage(content=req_msg)

        # create and save mood and mood message to db
        try:

            db_mood_message = DBMoodMessage(
                uuid_str=mood_msg.uuid,
                content=mood_msg.content,
                prompt=mood_msg.prompt,
                model=self.app_params['mood_message_model'],
                cached=req_cache_bool
            )
            self.db.session.add(db_mood_message)
            self.db.session.commit()

        except Exception as e:
            req_str = json.dumps(req_data, default=js_utils.json_serializer)
            err_msg = f"endpoint: /v1/mood, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailToAccessDB",
                        "error_message": err_msg
                    }
                ),
                status=500,
                headers={"Content-Type": "application/json"}
            )

        # response
        self.logger.info("saved mood message %s to database", mood_msg.uuid)
        resp = {
            "id": mood_msg.uuid
        }

        return Response(
            response=json.dumps(
                resp,
                default=js_utils.json_serializer
            ),
            status=200,
            headers={"Content-Type": "application/json"}
        )

    def generate_mood_picture(self, params: dict, *args: list, **kwargs: dict):

        """
        generate picture from mood description
        curl -XPOST 'http://0.0.0.0:5000/v1/mood/94a1a2d7-0303-47f8-9b1f-2c852413e1e1/picture'
        """

        # parse args
        try:

            # parse mood message id
            mood_msg_id = kwargs.get('mood_id')
            if mood_msg_id is None:
                raise Exception("failed to parse mood_id")

            # get mood from db
            db_mood_msg  = DBMoodMessage.query.get(mood_msg_id)
            svr_mood_msg = model_utils.db_mood_message_to_server_mood_message(db_mood_msg)

        except Exception as e:

            req_str = json.dumps(kwargs)
            err_msg = f"endpoint: /v1/mood/<mood_id>/picture, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "RequestMissingArguments",
                        "error_message": err_msg
                    }
                ),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # generate image
        try:

            image_size = self.app_params['mood_image_size']
            svr_mood_pic = mood_logics.generate_mood_image_by_description(
                mood_msg=svr_mood_msg,
                image_size=image_size,
            )

        except Exception as e:

            req_str = json.dumps({"mood_id": mood_msg_id})
            err_msg = f"endpoint: /v1/mood/{mood_msg_id}/picture, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)

            if type(e).__name__ == 'TimeoutError':
                status_code = 504
            else:
                status_code = 500

            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailedToProcessRequest",
                        "error_message": err_msg
                    }
                ),
                status=status_code,
                headers={"Content-Type": "application/json"}
            )

        # update mood and mood picture db
        try:

            db_mood_pic = DBMoodPicture(
                uuid_str=svr_mood_pic.uuid,
                url=svr_mood_pic.url,
                size=svr_mood_pic.size,
                prompt=svr_mood_pic.prompt,
                model=svr_mood_pic.model,
                mood_message_id=mood_msg_id
            )
            self.db.session.add(db_mood_pic)
            self.db.session.commit()

        except Exception as e:
            req_str = json.dumps({"mood_id": mood_msg_id})
            err_msg = f"endpoint: /v1/mood/{mood_msg_id}/picture, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailedToAccessDB",
                        "error_message": err_msg
                    }
                ),
                status=500,
                headers={"Content-Type": "application/json"}
            )

        # response
        resp = {
            'url':  svr_mood_pic.url,
            'size': svr_mood_pic.size,
        }

        # return
        return Response(
            response=json.dumps(
                resp,
                default=js_utils.json_serializer
            ),
            status=200,
            headers={"Content-Type": "application/json"}
        )

    def save_picture_to_s3(self, params: dict, *args: list, **kwargs: dict):

        """
        save picture to s3
        curl -XPOST 'http://0.0.0.0:5000/v1/pictures' -H 'Content-Type: application/json' -d '{"type":"mood_pic", "id": "94a1a2d7-0303-47f8-9b1f-2c852413e1e1"}'
        """

        # parse request
        try:

            # prase request params
            req_data = request.get_json()
            req_type = req_data.get('type')
            req_id   = req_data.get('id')
            if (req_type is None) or (req_id is None):
                raise Exception("request missing type or id")

            # get mood picture by mood id from db
            if req_type == 'mood_pic':

                db_mood_pic  = DBMoodPicture \
                    .query \
                    .filter_by(mood_message_id=req_id) \
                    .order_by(DBMoodPicture.created_at.desc()) \
                    .first()
                svr_mood_pic = model_utils.db_mood_picture_to_server_mood_picture(db_mood_pic)

                source_url  = svr_mood_pic.url
                source_size = svr_mood_pic.size

        except Exception as e:

            req_str = json.dumps(req_data, default=js_utils.json_serializer)
            err_msg = f"endpoint: /v1/pictures, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "RequestMissingArguments",
                        "error_message": err_msg
                    }
                ),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # upload pic to s3
        try:
            svr_picture = pic_logics.save_picture_to_s3_by_url(
                source_url=source_url,
                source_size=source_size,
                s3_region=self.app_params['aws_access_region'],
                s3_bucket_name=self.app_params['aws_s3_bucket_name'],
                s3_file_path=self.app_params['aws_s3_file_path'],
            )
        except Exception as e:

            req_str = json.dumps(req_data, default=js_utils.json_serializer)
            err_msg = f"endpoint: /v1/pictures, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)

            if type(e).__name__ == 'TimeoutError':
                status_code = 504
            else:
                status_code = 500

            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailedToProcessRequest",
                        "error_message": err_msg
                    }
                ),
                status=status_code,
                headers={"Content-Type": "application/json"}
            )

        # update mood and mood picture db
        try:

            db_picture = DBPicture(
                uuid_str=svr_picture.uuid,
                filename=svr_picture.filename,
                size=svr_picture.size,
                url=svr_picture.url,
                reference_type=req_type,
                reference_id=svr_mood_pic.uuid,
            )
            self.db.session.add(db_picture)
            self.db.session.commit()

        except Exception as e:
            req_str = json.dumps(req_data, default=js_utils.json_serializer)
            err_msg = f"endpoint: /v1/pictures, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailedToAccessDB",
                        "error_message": err_msg
                    }
                ),
                status=500,
                headers={"Content-Type": "application/json"}
            )

        # response
        resp = {
            'id':   svr_picture.uuid,
            'url':  svr_picture.url,
            'size': svr_picture.size,
        }

        # return
        return Response(
            response=json.dumps(
                resp,
                default=js_utils.json_serializer
            ),
            status=200,
            headers={"Content-Type": "application/json"}
        )

    def spot_search_by_picture(self, params: dict, *args: list, **kwargs: dict):

        """
        search spot by picture
        curl -XGET 'http://0.0.0.0:5000/v1/spots/search?pic_id=11ae17cf-b6a7-479a-943b-ec2e7e227d50'
        curl -XGET 'http://0.0.0.0:5000/v1/spots/search?pic_id=c62d633e-9c9c-4304-a37b-fd6e2171b57b'
        """

        # parse and check request
        try:

            # parse request args
            req_args_key_set = set(request.args.keys())
            req_must_key_set = {'pic_id'}

            if (req_must_key_set - req_args_key_set) != set():
                raise Exception("request missing arguments")

            # get picture by pic_id
            pic_id      = request.args.get('pic_id')
            db_picture  = DBPicture.query.get(pic_id)
            svr_picture = model_utils.db_picture_to_server_picture(db_picture)

        except Exception as e:
            err_msg = "endpoint: {}, error: {}, info: {}".format(
                "/v1/spots/search",
                repr(e),
                ", ".join(req_must_key_set - req_args_key_set),
            )
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "RequestMissingArguments",
                        "error_message": err_msg
                    }
                ),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # main
        spot_result = None

        try:

            # search: mood image -> spot image
            self.logger.info("searching spot image with picture %s", pic_id)
            spot_img_list = spot_logics.search_spot_image_by_pic_url(
                api_key=self.app_params['serpapi_api_key'],
                pic_url=svr_picture.url,
            )
            self.logger.info("found %d spot image for picture %s", len(spot_img_list), pic_id)

            # spot image -> spot
            spot_list = []
            for spot_img in spot_img_list:

                spot_list = spot_logics.search_spot_by_spot_image(
                    api_key=self.app_params['google_api_key'],
                    image=spot_img,
                )

                if len(spot_list) > 0:
                    spot_result = spot_list[0]
                    spot_result.image = spot_img
                    break

        except Exception as e:
            req_str = json.dumps(request.args, default=js_utils.json_serializer)
            err_msg = f"endpoint: /v1/spots/search, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)

            if type(e).__name__ == 'TimeoutError':
                status_code = 504
            else:
                status_code = 500

            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailedToProcessRequest",
                        "error_message": err_msg
                    }
                ),
                status=status_code,
                headers={"Content-Type": "application/json"}
            )

        # update spot image and spot to db
        try:

            db_spot_img = DBSpotImage(
                uuid_str=spot_result.image.uuid,
                thumbnail=spot_result.image.thumbnail,
                url=spot_result.image.url,
                title=spot_result.image.title,
                reference_id=db_picture.id,
                meta_data=spot_result.image.meta_data
            )
            db_spot = DBSpot(
                uuid_str=spot_result.uuid,
                address=spot_result.address,
                name=spot_result.name,
                rating=spot_result.rating,
                rating_n=spot_result.rating_n,
                place_id=spot_result.place_id,
                reference=spot_result.reference,
                types=spot_result.types,
                geometry=spot_result.geometry,
                spot_image_id=svr_picture.uuid
            )
            db_spot.spot_image = db_spot_img

            self.db.session.add(db_spot)
            self.db.session.commit()

        except Exception as e:

            req_str = json.dumps(request.args, default=js_utils.json_serializer)
            err_msg = f"endpoint: /v1/spots/search, error: {repr(e)}, request: {req_str}"
            self.logger.error(err_msg)
            return Response(
                response=json.dumps(
                    {
                        "error_type":    "FailedToAccessDB",
                        "error_message": err_msg
                    }
                ),
                status=500,
                headers={"Content-Type": "application/json"}
            )

        # response
        resp = {
            "uuid":       spot_result.uuid,
            "created_at": spot_result.created_at,
            "address":    spot_result.address,
            "name":       spot_result.name,
            "rating":     spot_result.rating,
            "rating_n":   spot_result.rating_n,
            "place_id":   spot_result.place_id,
            "reference":  spot_result.reference,
            "types":      spot_result.types,
            "geometry":   spot_result.geometry,
            "image": {
                "id":  spot_result.image.uuid,
                "url": spot_result.image.thumbnail,
            }
        }

        return Response(
            response=json.dumps(resp, default=js_utils.json_serializer),
            status=200,
            headers={"Content-Type": "application/json"}
        )
