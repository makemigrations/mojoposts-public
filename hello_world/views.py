# Copyright 2025 MakeMigrations
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
import binascii
import aiohttp
import asyncio
import json
import time
import re
from asgiref.sync import async_to_sync
from chia.types.blockchain_format.coin import Coin
from chia.util.ints import uint64
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Set up logging
import logging
logger = logging.getLogger(__name__)

# Ensure necessary settings are defined
if not hasattr(settings, "PUZZLE_HASH") or not settings.PUZZLE_HASH:
    raise ImproperlyConfigured("PUZZLE_HASH is missing. Please define it in your settings.")

if not hasattr(settings, "COINSET_API_BASE") or not settings.COINSET_API_BASE:
    raise ImproperlyConfigured("COINSET_API_BASE is missing. Please define it in your settings.")

# Configure requests session for retry
session = requests.Session()
retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

STREAM_DELAY = getattr(settings, "STREAM_DELAY", 1)  # Default to 1 second
if STREAM_DELAY == 1:
    logger.info("STREAM_DELAY not defined in settings. Using default value: 1 second")


def decode_memo(memo_hex):
    """
    Decodes a hexadecimal memo string, sanitizes it, and censors blocked content.

    Args:
        memo_hex (str): The hexadecimal memo string to decode.

    Returns:
        str: Decoded and censored memo string.
    """
    try:
        decoded_bytes = binascii.unhexlify(memo_hex[2:] if memo_hex.startswith("0x") else memo_hex)
        decoded_memo = decoded_bytes.decode("utf-8")
    except (UnicodeDecodeError, binascii.Error):
        return memo_hex[2:] if memo_hex.startswith("0x") else memo_hex

    # Censor blocked words
    for word in settings.BLOCKED_WORDS:
        decoded_memo = re.sub(rf"\b{word}\b", "-", decoded_memo, flags=re.IGNORECASE)

    # Censor blocked patterns
    for pattern in settings.BLOCKED_PATTERNS:
        decoded_memo = re.sub(pattern, "-", decoded_memo)

    # Catch generic URLs (even if not in BLOCKED_PATTERNS)
    url_pattern = r'\b((https?|ftp):\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/[^\s]*)?\b'
    decoded_memo = re.sub(url_pattern, "-", decoded_memo)

    return decoded_memo

def compute_coin_id(parent_coin_info, puzzle_hash, amount):
    """
    Computes the unique coin ID based on parent coin info, puzzle hash, and amount.

    Args:
        parent_coin_info (str): Parent coin information as a hexadecimal string.
        puzzle_hash (str): Puzzle hash as a hexadecimal string.
        amount (int): Amount associated with the coin.

    Returns:
        str: Computed coin ID as a hexadecimal string.
    """
    coin = Coin(bytes.fromhex(parent_coin_info[2:]), bytes.fromhex(puzzle_hash[2:]), uint64(amount))
    return coin.name().hex()

async def fetch_coin_records_by_puzzle_hash(puzzle_hash, page=1, page_size=50):
    """
    Fetches coin records associated with a given puzzle hash using pagination.

    Args:
        puzzle_hash (str): Puzzle hash as a hexadecimal string.
        page (int): Current page number for pagination.
        page_size (int): Number of records per page.

    Returns:
        list[dict]: List of coin records containing coin ID, block height, and amount.
    """
    url = f"{settings.COINSET_API_BASE}/get_coin_records_by_puzzle_hash"
    all_coin_data = []
    max_pages = settings.COINSET_SETTINGS.get("MAX_PAGES", 100)

    async with aiohttp.ClientSession() as session:
        while page <= max_pages:
            logger.info(f"Processing coin records for puzzle hash: {puzzle_hash}, page: {page}")
            try:
                async with session.post(url, json={
                    "puzzle_hash": puzzle_hash,
                    "include_spent_coins": True,
                    "page": page,
                    "page_size": page_size
                }) as response:
                    response.raise_for_status()
                    data = await response.json()

                if not data.get("success") or not data.get("coin_records"):
                    break

                all_coin_data.extend([
                    {
                        "coin_id": compute_coin_id(record["coin"]["parent_coin_info"], record["coin"]["puzzle_hash"], record["coin"]["amount"]),
                        "block_height": record["confirmed_block_index"],
                        "amount": record["coin"]["amount"]
                    }
                    for record in data["coin_records"]
                ])
                logger.info(f"Successfully fetched coin records for puzzle hash: {puzzle_hash}, page: {page}")

                if len(data["coin_records"]) < page_size:
                    break
                page += 1
            except aiohttp.ClientError as e:
                logger.error(f"Error fetching coin records: {e}")
                break

    return all_coin_data

def fetch_memos_for_coins(coin_data):
    """
    Fetches memos for a list of coins from the API.

    Args:
        coin_data (list[dict]): List of coin records containing coin IDs and other metadata.

    Returns:
        list[dict]: List of memos sorted by block height.
    """
    records = []
    for coin in coin_data:
        url = f"{settings.COINSET_API_BASE}/get_memos_by_coin_name"
        try:
            response = session.post(url, json={"name": coin["coin_id"]}, timeout=5)
            response.raise_for_status()

            memo_text = ""
            if response.status_code == 200:
                data = response.json()
                decoded_memos = [decode_memo(memo) for memo in data.get("memos", [])]
                memo_text = ", ".join(filter(None, decoded_memos))

            records.append({
                "coin_id": coin["coin_id"],
                "block_height": coin["block_height"],
                "amount": coin["amount"],
                "memo": memo_text
            })
        except requests.RequestException as e:
            logger.error(f"Error fetching memos for {coin['coin_id']}: {e}")
            records.append({
                "coin_id": coin["coin_id"],
                "block_height": coin["block_height"],
                "amount": coin["amount"],
                "memo": "[ERROR: Unable to fetch memo]"
            })

    return sorted(records, key=lambda x: x["block_height"], reverse=True)

def get_coin_memos_sync(puzzle_hash=None):
    """
    Fetches and processes memos for coins synchronously.

    Args:
        puzzle_hash (str, optional): Puzzle hash as a hexadecimal string.

    Returns:
        list[dict]: List of processed coin memos.
    """
    puzzle_hash = puzzle_hash or settings.PUZZLE_HASH
    return fetch_memos_for_coins(async_to_sync(fetch_coin_records_by_puzzle_hash)(puzzle_hash))

@csrf_exempt
@ratelimit(key="ip", rate="5/m", method=ratelimit.UNSAFE)
def coin_records_view(request):
    """
    Handles the coin records view. Fetches coin records based on user-provided puzzle hash.

    Args:
        request (HttpRequest): Django request object.

    Returns:
        HttpResponse: Rendered HTML response with coin records or JSON error response.
    """
    records = []
    searched = False

    if request.method == "POST":
        puzzle_hash = request.POST.get("puzzle_hash")
        if puzzle_hash:
            logger.info(f"Sending request to fetch coin records for puzzle hash: {puzzle_hash}")
            url = f"{settings.COINSET_API_BASE}/get_coin_records_by_puzzle_hash"
            json_data = {
                "puzzle_hash": puzzle_hash,
                "start_height": 0,
                "end_height": 0,
                "include_spent_coins": True
            }
            try:
                response = session.post(url, json=json_data, timeout=10)
                response.raise_for_status()

                data = response.json()
                records = [
                    {
                        "amount": record["coin"]["amount"],
                        "block_height": record["confirmed_block_index"]
                    }
                    for record in data.get("coin_records", [])
                ]
                logger.info(f"Successfully fetched coin records for puzzle hash: {puzzle_hash}")
                searched = True
            except requests.RequestException as e:
                logger.error(f"Error fetching coin records: {e}")
                return JsonResponse(
                    {"error": f"API connection failed: {str(e)}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON response from API.")
                return JsonResponse(
                    {"error": "Invalid API response format"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

    return render(request, "table.html", {"records": records, "searched": searched})

@csrf_exempt
@ratelimit(key="ip", rate="5/m", method=ratelimit.UNSAFE)
def coin_memos_view(request):
    """
    Handles the coin memos view. Fetches memos based on user-provided coin name.

    Args:
        request (HttpRequest): Django request object.

    Returns:
        HttpResponse: Rendered HTML response with memos or JSON error response.
    """
    records = []
    searched = False

    if request.method == "POST":
        coin_name = request.POST.get("coin_name")
        if coin_name:
            logger.info(f"Sending request to fetch memos for coin name: {coin_name}")
            url = f"{settings.COINSET_API_BASE}/get_memos_by_coin_name"
            try:
                response = session.post(url, json={"name": coin_name}, timeout=10)
                response.raise_for_status()

                data = response.json()
                if not isinstance(data, dict) or "memos" not in data:
                    logger.warning("Unexpected API response structure.")
                    return JsonResponse(
                        {"error": "Invalid API response"},
                        status=status.HTTP_502_BAD_GATEWAY
                    )

                records = [{"memo": memo} for memo in data.get("memos", [])]
                logger.info(f"Successfully fetched {len(records)} memos for coin name: {coin_name}")
                searched = True
            except requests.RequestException as e:
                logger.error(f"Error fetching memos: {e}")
                return JsonResponse(
                    {"error": f"API connection failed: {str(e)}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON response from API.")
                return JsonResponse(
                    {"error": "Invalid API response format"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

    return render(request, "get_memos_by_coin_name.html", {"records": records, "searched": searched})

def event_stream():
    """
    Generator function to simulate streaming of memos in real-time.

    Yields:
        str: JSON-formatted memo data for streaming.
    """
    logger.info("Starting streaming of memos in real-time")
    puzzle_hash = settings.PUZZLE_HASH
    memos = get_coin_memos_sync(puzzle_hash)

    for memo in memos:
        yield f"data: {json.dumps(memo)}\n\n"
        time.sleep(settings.STREAM_DELAY)  # Configurable delay

def stream_memos(request):
    """
    Django view to stream memos in real-time using Server-Sent Events (SSE).

    Args:
        request (HttpRequest): Django request object.

    Returns:
        StreamingHttpResponse: Streamed response containing memo data.
    """
    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    response["X-Frame-Options"] = "DENY"
    return response

def all_coin_memos_view(request):
    """
    Handles the view to display all coin memos.

    Args:
        request (HttpRequest): Django request object.

    Returns:
        HttpResponse: Rendered HTML response containing all coin memos.
    """
    memos = get_coin_memos_sync(settings.PUZZLE_HASH)
    return render(request, "memos.html", {"memos": memos})

def terms_of_use_view(request):
    """
    Render the Terms of Use page.
    """
    return render(request, "terms_of_use.html")

def privacy_policy_view(request):
    """
    Render the Privacy Policy page.
    """
    return render(request, "privacy_policy.html")

def post_view(request):
    """
    Render the How to Post page.
    """
    return render(request, "post.html")