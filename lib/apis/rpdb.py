import json
from copy import deepcopy

import httpx

from lib import log, utils
from typing import Optional


class RPDB:
    def __init__(self):
        self.__url = "https://api.ratingposterdb.com"

    def validate_api_key(self, api_key) -> bool:
        url = f"{self.__url}/{api_key}/isValid"
        if api_key is None:
            return False

        try:
            with httpx.Client() as client:
                response = client.get(url)
                return response.status_code == 200
        except Exception as e:
            log.info(e)
        return False

    def check_request_left(self, api_key: str) -> int:
        check_limit_url = f"{self.__url}/{api_key}/requests"
        try:
            with httpx.Client() as client:
                response = client.get(check_limit_url)
                if response.status_code == 200:
                    buffer = response.content
                    result: dict = json.loads(buffer)
                    req: int = result.get("req", None)
                    limit: int = result.get("limit", None)
                    return limit - req
        except Exception as e:
            log.info(e)
        return 0

    def get_poster(self, imdb_id: str, api_key: str, lang="en") -> Optional[str]:
        url = f"{self.__url}/{api_key}/imdb/poster-default/{imdb_id}.jpg?fallback=true"
        if not api_key.startswith("t1-"):
            url = f"{url}&lang={lang}"
        return url

    def replace_posters(self, metas: list[dict], api_key: str, lang="en") -> list[dict]:
        new_metas = deepcopy(metas)
        if self.check_request_left(api_key=api_key) < len(metas):
            return metas

        def __get_poster(item: dict, idx: int, worker_id: int, **kwargs) -> dict:
            if item is None:
                return None
            imdb_id = item.get("id", None)
            api_key = kwargs.get("api_key", None)
            lang = kwargs.get("lang", "en")
            item.update({"poster": self.get_poster(imdb_id=imdb_id, api_key=api_key, lang=lang)})
            return item

        return utils.parallel_for(__get_poster, items=new_metas, api_key=api_key, lang=lang)
