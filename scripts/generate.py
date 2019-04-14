from glob import glob
from itertools import groupby
import logging
from time import sleep

from eth_utils import is_hex_address, to_checksum_address
import requests

from helpers import (DEFAULT_HEADERS, LiteralString, has_cached_coin_details,
                     fetch_coin_details, read_entry, write_token_entry)

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


def clean_links_value(value):
    if value is None:
        return None
    elif isinstance(value, str):
        return value if value else None
    elif isinstance(value, list):
        clean_list = list(filter(clean_links_value, value))
        uniq_list = list(sorted(list(set(clean_list))))
        return uniq_list if uniq_list else None
    elif isinstance(value, dict):
        clean_pairs = [(k, clean_links_value(v)) for (k, v) in value.items()]
        clean_dict = {k: v for (k, v) in clean_pairs if v is not None}
        return clean_dict if clean_dict else None
    else:
        return value


def clean_text(text):
    return text.strip().replace("\r\n", "\n").replace(" \n", "\n")


def extract_ticker(ticker):
    market = ticker["market"]
    return dict(
        market={
            k: v
            for (k, v) in market.items() if k in ["name", "identifier"]
        },
        **{k: v
           for (k, v) in ticker.items() if k in ["base", "target"]})


not_stale = lambda ticker: ticker["is_stale"]


def make_token_entry(coin_details):
    checksum_address = to_checksum_address(coin_details["contract_address"])
    description = coin_details.get("description", {}).get("en")
    if isinstance(description, str):
        description = clean_text(description)

    tickers = list(
        map(extract_ticker, filter(not_stale, coin_details["tickers"])))
    return dict(
        address=checksum_address,
        description=LiteralString(description),
        links=clean_links_value(coin_details["links"]),
        tickers=tickers,
        **{
            k: v
            for (k, v) in coin_details.items()
            if k in ["id", "symbol", "name"]
        })


def main(listings):
    for listing in listings:
        print("Fetching", listing["id"])

        if not has_cached_coin_details(listing["id"]):
            sleep(0.5)

        coin_details = fetch_coin_details(listing["id"])
        if is_hex_address(coin_details.get("contract_address")):
            # We've got a live one!
            token_entry = make_token_entry(coin_details)
            write_token_entry(token_entry["address"], token_entry)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    main(get_listings())
