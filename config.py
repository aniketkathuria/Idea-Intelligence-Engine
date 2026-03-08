# config.py
DEFAULT_QUERY_COUNT = 5
SEARCH_DEPTH = {
    "fast": 5,
    "balanced": 10,
    "deep": 20
}

SIMILARITY_THRESHOLD = 0.55
TOP_K_SIMILAR = 5

CLUSTER_MATCH_MIN = 4          # for expanding large clusters
MIN_MATCH_FOR_NEW_CLUSTER = 1  # minimum matched ideas to form new cluster

