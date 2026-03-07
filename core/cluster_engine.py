from config import CLUSTER_MATCH_MIN, MIN_MATCH_FOR_NEW_CLUSTER


def determine_cluster_action(new_idea_id, matched_ideas, clusters):
    """
    Decide whether to:
    - expand an existing cluster
    - create a new cluster
    - do nothing

    matched_ideas: list of full idea objects (already filtered by similarity threshold)
    clusters: list of existing cluster objects
    """

    matched_ids = [idea["id"] for idea in matched_ideas]

    # 1️⃣ Check if we should expand an existing cluster
    for cluster in clusters:
        cluster_ids = cluster["idea_ids"]
        overlap = set(cluster_ids).intersection(set(matched_ids))
        cluster_size = len(cluster_ids)

        if cluster_size <= CLUSTER_MATCH_MIN:
            # require full match
            if len(overlap) == cluster_size and cluster_size > 0:
                return {
                    "action": "expand",
                    "cluster_id": cluster["cluster_id"],
                    "cluster": cluster
                }
        else:
            # require minimum threshold match
            if len(overlap) >= CLUSTER_MATCH_MIN:
                return {
                    "action": "expand",
                    "cluster_id": cluster["cluster_id"],
                    "cluster": cluster
                }

    # 2️⃣ No expansion found — maybe create new cluster
    if len(matched_ids) >= MIN_MATCH_FOR_NEW_CLUSTER:
        return {
            "action": "create",
            "matched_ids": matched_ids
        }

    # 3️⃣ Otherwise do nothing
    return {"action": "none"}