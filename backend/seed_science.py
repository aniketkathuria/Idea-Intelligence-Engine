# seed_science.py
# Resets the DB and seeds 5 Science hypotheses through the full pipeline.
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from core.db import SessionLocal
from core.models import Idea, Cluster
from core.storage import save_idea, update_idea_status
from core.pipeline import process_idea

SCIENCE_IDEAS = [
    # 1 — Gut microbiome circadian rhythm + metabolic syndrome
    "Hypothesis: disruption of the gut microbiome's endogenous circadian oscillation — driven by "
    "irregular meal timing that uncouples host clock genes from microbial metabolic cycles — "
    "causally contributes to insulin resistance by reducing secondary bile acid diversity in the "
    "ileum, specifically through suppression of Lactobacillus and Akkermansia species that "
    "modulate FXR signalling. The claim is that restoring regular feeding schedules in a "
    "germ-free mouse model colonised with a defined microbiome will rescue secondary bile acid "
    "production and reverse diet-induced insulin resistance, independent of caloric intake.",

    # 2 — Black carbon on Himalayan glaciers
    "Hypothesis: black carbon aerosols deposited on Zanskar and Gangotri glaciers from Indian "
    "coal combustion and crop-residue burning in Punjab and Haryana reduce surface albedo by "
    "3-5 percentage points, contributing more to accelerated summer melt than the equivalent "
    "temperature anomaly from regional warming alone. The testable prediction is that spatial "
    "variation in melt rate across glacier surfaces will correlate more strongly with black "
    "carbon deposition density (measured by ice core elemental carbon analysis) than with "
    "local air temperature records, after controlling for aspect and elevation.",

    # 3 — Fig-wasp mutualism breakdown under forest fragmentation (Western Ghats)
    "Hypothesis: endemic Ficus species in the Western Ghats maintain obligate one-to-one "
    "pollination mutualism with genus-specific agaonid fig wasps, and forest fragment size "
    "below approximately 5 hectares causes local extinction of the resident wasp population "
    "within two to three generations due to pollen carryover distance limitations, after which "
    "the host Ficus trees enter sustained reproductive failure — producing figs that are "
    "entered but not pollinated. The prediction is that wasp occupancy rate in figs collected "
    "from fragments under 5 ha will be statistically indistinguishable from zero, while "
    "fragments above 20 ha will show occupancy rates comparable to continuous forest controls.",

    # 4 — NLRP3 inflammasome in repeated mild TBI and tau aggregation
    "Hypothesis: repeated mild traumatic brain injury (three closed-head impacts at 24-hour "
    "intervals) accelerates phosphorylated tau accumulation specifically in hippocampal CA3 "
    "pyramidal neurons through an NLRP3 inflammasome-dependent mechanism — not through "
    "direct mechanical axonal injury — and that administering the selective NLRP3 inhibitor "
    "MCC950 within 72 hours of the final impact will reduce CA3 p-tau burden by at least 40% "
    "compared to vehicle controls in a C57BL/6 mouse model, as measured by AT8 "
    "immunohistochemistry at 30 days post-injury.",

    # 5 — Rice straw cellulose nanocrystals as proton exchange membrane
    "Hypothesis: cellulose nanocrystals (CNCs) extracted from rice straw — abundant agricultural "
    "waste in Punjab producing 20 million tonnes annually — can be processed into sulfonated "
    "composite films that achieve proton conductivity above 10^-2 S/cm at room temperature and "
    "80% relative humidity, making them viable solid electrolytes for low-temperature hydrogen "
    "fuel cells. The specific claim is that sulfonation density above 1.8 mmol/g, achieved "
    "through controlled H2SO4 hydrolysis conditions, is the threshold above which conductivity "
    "crosses the 10^-2 S/cm benchmark, and that this is reproducible across three independent "
    "batches of rice straw from different harvest seasons.",
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

    for i, idea_text in enumerate(SCIENCE_IDEAS, 1):
        print(f"{'='*60}")
        print(f"Submitting idea {i}/{len(SCIENCE_IDEAS)}:")
        print(f"  {idea_text[:80]}...")
        print(f"{'='*60}")

        idea_id = save_idea(idea_text, {"evaluation": {"category": "Science"}}, [])
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
