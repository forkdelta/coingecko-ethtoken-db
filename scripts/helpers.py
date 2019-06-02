import json
import logging
from os.path import getmtime, isfile, join
import re
from time import time

import requests
import yaml

from yaml_helpers import (YAML_INDENT, YAML_WIDTH, LiteralString,
                          literal_presenter)

USER_AGENT = "CoinGecko Ethereum Tokens DB Builder (https://github.com/forkdelta/coingecko-ethtoken-db)"
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}

CACHE_PATH = ".cache"
CG_COIN_DETAILS_URL = "https://api.coingecko.com/api/v3/coins/{cid}/"
CG_COIN_DETAILS_MAXAGE = 86400

requests_session = requests.Session()


def has_cached_coin_details(cid, max_cache_age=CG_COIN_DETAILS_MAXAGE):
    assert re.match('^[a-zA-Z0-9 _-]+$', cid) is not None
    cache_file = join(CACHE_PATH, "{}.json".format(cid))
    return isfile(cache_file) and getmtime(cache_file) > time() - max_cache_age


def fetch_coin_details(cid,
                       cache=True,
                       cache_only=False,
                       max_cache_age=CG_COIN_DETAILS_MAXAGE):
    global requests_session
    assert re.match('^[a-zA-Z0-9 _-]+$', cid) is not None

    cache_file = join(CACHE_PATH, "{}.json".format(cid))
    if isfile(cache_file) and getmtime(cache_file) > time() - max_cache_age:
        logging.debug("Using cache for '%s'", cid)
        with open(cache_file) as f:
            return json.load(f)
    elif cache_only:
        raise Exception("cache_only and no cache file available")

    logging.debug("Fetching page for '%s'", cid)

    page_url = CG_COIN_DETAILS_URL.format(cid=cid)
    r = requests_session.get(page_url, headers=DEFAULT_HEADERS)
    r.raise_for_status()  # Raise error if status is not 200

    json_content = r.json()

    if cache:
        with open(cache_file, "w") as f:
            json.dump(json_content, f)
    return json_content


def read_entry(fn):
    with open(fn) as infile:
        return yaml.safe_load(infile)


def write_token_entry(address, listing):
    yaml.add_representer(LiteralString, literal_presenter)
    with open("tokens/{}.yaml".format(address), "w") as outfile:
        outfile.write(
            yaml.dump(
                listing,
                explicit_start=True,
                width=YAML_WIDTH,
                indent=YAML_INDENT,
                default_flow_style=False,
                allow_unicode=True))
