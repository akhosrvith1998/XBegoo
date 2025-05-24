import time
from collections import defaultdict

INLINE_QUERY_CACHE = defaultdict(dict)
CACHE_TTL = 10  # 10 ثانیه

def get_cached_inline_query(sender_id, query):
    if sender_id in INLINE_QUERY_CACHE and query in INLINE_QUERY_CACHE[sender_id]:
        cache_entry = INLINE_QUERY_CACHE[sender_id][query]
        if time.time() - cache_entry["timestamp"] < CACHE_TTL:
            return cache_entry["results"]
    return None

def set_cached_inline_query(sender_id, query, results):
    INLINE_QUERY_CACHE[sender_id][query] = {
        "results": results,
        "timestamp": time.time()
    }