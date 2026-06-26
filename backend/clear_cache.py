"""
clear_cache.py — wipe the stale recommendation cache from Redis.

The topic recommender caches a pool per user for 1 hour. If that pool was
cached while the resource table was empty, it keeps serving empty results
until it expires. This deletes those cached pools so the next page load
rebuilds them from the (now populated) database.

Run from backend/ (reads REDIS_URL from your .env):

    python3 clear_cache.py
"""

import sys

url = None
for line in open(".env", encoding="utf-8", errors="replace"):
    if line.strip().startswith("REDIS_URL"):
        url = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

if not url:
    print("No REDIS_URL found in .env")
    sys.exit(1)

import redis

r = redis.from_url(url, decode_responses=True)

deleted_total = 0
for pattern in ("topics_pool:*", "recommendations:*", "recs:*"):
    keys = r.keys(pattern)
    if keys:
        r.delete(*keys)
        deleted_total += len(keys)
        print(f"deleted {len(keys)} key(s) matching '{pattern}'")

if deleted_total == 0:
    print("No matching cache keys found (nothing to clear).")
else:
    print(f"\n✅ Cleared {deleted_total} cached entr(ies). Reload the "
          f"Learning Materials page now.")
