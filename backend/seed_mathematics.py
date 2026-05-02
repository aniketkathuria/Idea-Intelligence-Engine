# seed_mathematics.py
# Resets the DB and seeds 5 Mathematics conjectures through the full pipeline.
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

from core.db import SessionLocal
from core.models import Idea, Cluster
from core.storage import save_idea, update_idea_status
from core.pipeline import process_idea

MATHEMATICS_IDEAS = [
    # 1 — Number theory: Collatz stopping times
    "Conjecture: the number of positive integers n ≤ N that require exactly k steps to reach 1 "
    "under the Collatz map (n → n/2 if n even, n → 3n+1 if n odd) decays geometrically in k — "
    "specifically, that this count is asymptotically C · N · r^k for some universal constants "
    "C > 0 and 0 < r < 1 independent of N. If true, this would imply that the empirical "
    "distribution of Collatz stopping times converges to a geometric distribution as N → ∞, "
    "which is consistent with the heuristic that each odd step multiplies n by roughly 3/2 "
    "in expectation. The conjecture is testable computationally for all n ≤ 10^9 and the "
    "geometric decay rate r can be estimated from the data.",

    # 2 — Combinatorics: chromatic number of Kneser-like graphs
    "Conjecture: for the generalised Kneser graph K(n, k, t) — whose vertices are k-element "
    "subsets of {1, ..., n} and edges connect subsets whose intersection has size strictly "
    "less than t — the chromatic number equals n - 2k + 2t for all n ≥ 2k - t + 1, "
    "generalising the Lovász-Kneser theorem (the t=0 case). The proof strategy would use "
    "topological methods — specifically the Borsuk-Ulam theorem applied to a suitable "
    "simplicial complex built from the t-intersecting families — mirroring Lovász's 1978 "
    "proof. The conjecture has been verified computationally for all n ≤ 15 and the "
    "boundary cases n = 2k - t and n = 2k - t + 1 are the most dangerous for counterexamples.",

    # 3 — Number theory / partition theory: Ramanujan-type congruences mod 13
    "Conjecture: the partition function p(n) satisfies a congruence of the form "
    "p(13^a · n + d) ≡ 0 (mod 13^b) for all n ≥ 0, for specific values of a, b, d analogous "
    "to Ramanujan's congruences modulo 5, 7, and 11. Specifically, conjecture that "
    "p(13n + 6) ≡ 0 (mod 13) for all n ≥ 0, as a base case, and that this extends to higher "
    "powers of 13 via the same type of modular forms argument used by Watson and Atkin to "
    "prove the Ramanujan congruences. This is distinct from the known result that p(n) takes "
    "all residues mod 13 — the conjecture is specifically about the arithmetic progression "
    "n ≡ 6 (mod 13).",

    # 4 — Additive combinatorics: sumset structure
    "Conjecture: for any finite set A of positive integers with |A| = n and no three elements "
    "in arithmetic progression, the sumset A + A = {a + b : a, b ∈ A} has size at least "
    "n^(1 + c) for some absolute constant c > 0, improving the trivial lower bound of 2n - 1. "
    "This would mean that AP-free sets have expanding sumsets, connecting Szemerédi-type "
    "density results to additive structure. The conjecture is motivated by the fact that "
    "Salem-Spencer sets (the densest known AP-free sets) have sumsets of size roughly n^(4/3), "
    "and asks whether this expansion is universal among AP-free sets rather than specific to "
    "extremal constructions.",

    # 5 — Analytic number theory: prime gaps and quadratic residues
    "Conjecture: for any prime q and any non-zero quadratic residue r mod q, the number of "
    "prime gaps (p_{n+1} - p_n) in the range [1, X] that are congruent to r mod q is "
    "asymptotically equal to (1/(q-1)) · π(X) as X → ∞, where π(X) is the prime counting "
    "function — that is, prime gaps are equidistributed among quadratic residues mod q. "
    "This is a stronger regularity statement than what follows from the prime number theorem "
    "for arithmetic progressions, and would imply that the parity of prime gaps shows no "
    "bias modulo small primes. The conjecture can be checked computationally for all primes "
    "up to 10^12 and for q = 3, 5, 7.",
]


def reset_db():
    db = SessionLocal()
    print("Clearing all ideas and clusters...")
    db.query(Idea).update({"cluster_id": None, "synthesis_output": None})
    db.commit()
    db.query(Cluster).delete()
    db.commit()
    db.query(Idea).delete()
    db.commit()
    db.close()
    print("DB cleared.\n")


def seed():
    reset_db()

    for i, idea_text in enumerate(MATHEMATICS_IDEAS, 1):
        print(f"{'='*60}")
        print(f"Submitting idea {i}/{len(MATHEMATICS_IDEAS)}:")
        print(f"  {idea_text[:80]}...")
        print(f"{'='*60}")

        idea_id = save_idea(idea_text, {"evaluation": {"category": "Mathematics"}}, [])
        print(f"  [DB] Assigned idea ID: {idea_id}")

        try:
            result = process_idea(idea_text, idea_id=idea_id)
            update_idea_status(idea_id, "completed", result)
            cat = result["evaluation"].get("category", "?")
            cls = result["evaluation"].get("final_classification", "?")
            print(f"  [OK] category={cat}  classification={cls}\n")
        except Exception as e:
            update_idea_status(idea_id, "failed", {"error": str(e)})
            print(f"  [FAIL] {e}\n")

    print("All ideas submitted.")


if __name__ == "__main__":
    seed()
