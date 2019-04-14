from glob import glob
from itertools import groupby
import logging
import requests

from helpers import (DEFAULT_HEADERS, has_cached_coin_details,
                     fetch_coin_details, read_entry)

CG_LISTINGS_API_URL = "https://api.coingecko.com/api/v3/coins/list"


def get_listings():
    """
    Returns a list of CoinMarketCap-listed currencies via /v2/listings/ API endpoint.

    Returns: a list of dicts like so:
        [{"id":"01coin","symbol":"zoc","name":"01coin"}, ...]
    """
    r = requests.get(CG_LISTINGS_API_URL, headers=DEFAULT_HEADERS)
    return r.json()


def map_existing_entries(files, exclude_deprecated=True):
    """
    Returns a hash keyed by CoinMarketCap asset ID with sets of Ethereum addresses
    known to be associated with that asset ID.
    """
    entries = ((entry["id"], entry["address"])
               for entry in (read_entry(fn) for fn in files)
               if not (exclude_deprecated and entry.get("_DEPRECATED", False)))

    return {
        e[0]: set(g[1] for g in e[1])
        for e in groupby(sorted(entries), key=lambda e: e[0])
    }


from contextlib import contextmanager
from time import sleep, time

#
# @contextmanager
# def rate_limit(rate, time_slice=60):
#     remaining = rate
#     while True:
#         batch_start = time()
#         while remaining > 0:
#             yield
#             if time() - batch_start > time_slice:
#                 batch_start = time()
#                 remaining = rate
#             else:
#                 remaining -= 1
#         if time_slice - (time() - batch_start) > 0:
#             sleep(time_slice - (time() - batch_start))


def main(listings):
    for listing in listings:
        print("Fetching", listing["id"])
        if not has_cached_coin_details(listing["id"]):
            sleep(0.5)

        asset_details = fetch_coin_details(listing["id"])


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    main(get_listings())
