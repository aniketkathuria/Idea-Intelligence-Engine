import os
import math
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0

    return dot_product / (magnitude1 * magnitude2)

def find_similar_ideas(new_embedding, past_ideas, top_n=100):
    similarities = []

    for idea in past_ideas:
        if "embedding" in idea:
            score = cosine_similarity(new_embedding, idea["embedding"])
            similarities.append((idea["id"], idea["raw_idea"], score))
    #print("Total computed similarities:", len(similarities))

    similarities.sort(key=lambda x: x[2], reverse=True)

    return similarities[:top_n]