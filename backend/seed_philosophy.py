# seed_philosophy.py
# Resets the DB and seeds 5 Philosophy arguments through the full pipeline.
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

PHILOSOPHY_IDEAS = [
    # 1 — Philosophy of mind: functionalism and phenomenal consciousness
    "Argument: functional equivalence is sufficient for phenomenal consciousness — if two systems "
    "are functionally equivalent (same input-output behaviour, same causal-functional organisation "
    "across all internal states), then they are phenomenally equivalent. This entails that inverted "
    "qualia and absent qualia scenarios are incoherent: qualia are not additional non-functional "
    "properties layered over functional organisation, but are constituted by functional roles. The "
    "argument proceeds as a reductio of qualia-realism: if qualia were non-functional, they would "
    "be causally inert (epiphenomenal), but we have strong evidence that phenomenal states causally "
    "influence behaviour (we reach for things because they look red, avoid them because they hurt). "
    "Epiphenomenalism is self-refuting because the very act of asserting it relies on our phenomenal "
    "states playing a causal role in producing utterances. Therefore qualia cannot be non-functional, "
    "and functional equivalence is sufficient for phenomenal equivalence. This is a stronger claim "
    "than standard functionalism because it targets not just mental state identity but phenomenal "
    "character specifically.",

    # 2 — Ethics: moral uncertainty and parliamentary aggregation
    "Argument: under deep moral uncertainty — where a rational agent assigns non-trivial credence "
    "to multiple mutually incompatible ethical frameworks — the morally correct action is determined "
    "by a parliamentary procedure in which each framework holds voting power proportional to the "
    "agent's credence in it, and the action with plurality support is chosen. This is superior to "
    "both moral hedging (acting only on the lowest common denominator across frameworks, which "
    "produces paralysis) and credence-weighted expected moral value maximisation (which requires "
    "comparing utility across incommensurable theories — a procedure that itself presupposes a "
    "meta-theory). The parliamentary model treats ethical frameworks as having veto power only "
    "when credence is near-certain, allows trade-offs between frameworks at intermediate credence "
    "levels, and does not require inter-theoretic value comparisons beyond ordinal ranking within "
    "each framework. The key premise is that no single ethical framework has sufficient warrant "
    "for an agent to act on it exclusively when non-trivial alternatives exist — a premise "
    "supported by the persistent disagreement among competent moral philosophers.",

    # 3 — Epistemology: hermeneutical injustice in algorithmic systems
    "Argument: Miranda Fricker's concept of hermeneutical injustice — the wrong done when a "
    "gap in collective interpretive resources puts someone at an unfair disadvantage in making "
    "sense of their social experience — extends to algorithmic decision systems in a structurally "
    "non-trivial way. An algorithmic system perpetrates hermeneutical injustice when it is trained "
    "on a corpus that lacks the conceptual resources to accurately represent the experiences of a "
    "marginalized group, and this algorithmic hermeneutical injustice is categorically distinct "
    "from statistical bias. Statistical bias is a quantitative error in representation; "
    "hermeneutical injustice is a structural absence of interpretive concepts. The distinction "
    "matters because the corrective strategies differ: statistical bias is corrected by reweighting "
    "training data, while hermeneutical injustice requires introducing new conceptual categories "
    "that the affected group has developed to describe their own experience. The argument shows "
    "that the ethics of AI cannot be reduced to fairness metrics and requires a specifically "
    "epistemic analysis of what concepts a system can and cannot represent.",

    # 4 — Political philosophy: collective moral responsibility without shared intention
    "Argument: a group can bear genuine collective moral responsibility for a harmful outcome "
    "even when no individual member shared an intention to produce that outcome, provided three "
    "conditions hold: (1) each member performed an action they could foresee as contributing to "
    "the harmful outcome; (2) the members were jointly capable of preventing the outcome through "
    "coordinated action that was available to them; and (3) a social role structure assigned each "
    "member a specific duty relevant to prevention. This challenges the standard shared-intention "
    "view of collective agency (Bratman, Gilbert) which holds that collective intentionality is "
    "necessary for collective moral responsibility. The argument proceeds by analogy to structural "
    "racism: no individual racist intention is needed for a social structure to produce racially "
    "discriminatory outcomes, yet we correctly attribute responsibility to the group that "
    "maintains the structure. The implication is that responsibility can be distributed across "
    "a group through structural role-obligations without requiring any shared mental state, "
    "which has direct consequences for corporate liability, institutional responsibility, and "
    "the responsibility of democratic majorities for policy outcomes.",

    # 5 — Metaphysics / free will: compatibilism under algorithmic prediction
    "Argument: classical compatibilist accounts of free will — which ground freedom in the "
    "counterfactual 'the agent could have done otherwise if they had chosen differently' — are "
    "undermined by the possibility of accurate algorithmic behavioural prediction, not for the "
    "familiar reason that determinism threatens free will (the compatibilist already concedes "
    "this), but for a different reason: algorithmic prediction reveals that the counterfactual "
    "itself is predictable, which means the 'could have chosen otherwise' condition is not "
    "a genuine alternative possibility but a description of a counterfactual that the predictor "
    "already knows will not be actualised. This is a novel threat distinct from both hard "
    "determinism and manipulation arguments (Frankfurt, Fischer). Frankfurt cases show that "
    "alternative possibilities are not required for moral responsibility; manipulation arguments "
    "show that causal history matters. The algorithmic prediction argument shows that the "
    "specific counterfactual structure on which compatibilism relies is itself undermined by "
    "the predictor's knowledge — the agent 'could have done otherwise' only in a sense "
    "that the predictor has already ruled out, which is not the sense the compatibilist needs.",
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

    for i, idea_text in enumerate(PHILOSOPHY_IDEAS, 1):
        print(f"{'='*60}")
        print(f"Submitting idea {i}/{len(PHILOSOPHY_IDEAS)}:")
        print(f"  {idea_text[:80]}...")
        print(f"{'='*60}")

        idea_id = save_idea(idea_text, {"evaluation": {"category": "Philosophy"}}, [])
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
