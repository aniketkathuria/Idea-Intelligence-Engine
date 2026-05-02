# seed_other.py
# Resets the DB and seeds 5 Other-category ideas through the full pipeline.
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

OTHER_IDEAS = [
    # 1 — Cross-domain: Open satellite imagery archive for ground-truth agricultural data
    "Idea: create a publicly accessible, continuously updated archive that links Sentinel-2 and "
    "Landsat satellite imagery tiles to ground-truth agricultural outcome data collected by Krishi "
    "Vigyan Kendras (KVKs) and state agricultural universities across India — pairing each imagery "
    "tile with crop type, yield, input use, and soil health data from the corresponding field plots. "
    "The archive would be structured so that each record contains: (1) the raw spectral bands from "
    "the closest overpass within 5 days of harvest, (2) the ground-truth yield and crop type from "
    "the matched KVK plot, and (3) the input data (irrigation, fertiliser, pesticide) from the same "
    "plot. The primary use case is training machine learning models for crop yield prediction without "
    "requiring expensive private data licensing. The critical dependency is the willingness of ICAR "
    "(Indian Council of Agricultural Research) to mandate structured data collection and sharing "
    "from the KVK network, which currently produces ground-truth data in inconsistent formats "
    "with no central aggregation. The archive would be distinct from existing platforms (Bhuvan, "
    "ISRO's data portal) which provide imagery but not matched ground-truth agricultural outcomes.",

    # 2 — Cross-domain: Oral history archive for India's informal sector knowledge
    "Idea: build a structured, searchable oral history archive of craft, trade, and occupational "
    "knowledge held by practitioners in India's informal sector — specifically artisans, traditional "
    "builders, Ayurvedic practitioners, and small-scale farmers — using a standardised interview "
    "protocol that captures both the procedural knowledge (how to do X) and the contextual knowledge "
    "(when to do X, what signals indicate X is needed, what X was historically called in this "
    "community). The archive would be structured as a knowledge graph linking practices to "
    "practitioners, regions, communities, and material inputs, enabling researchers to identify "
    "patterns across traditions (e.g., convergent solutions to the same problem in different "
    "regions) and enabling practitioners to find related knowledge outside their own tradition. "
    "The critical dependency is a protocol for attribution and intellectual property that gives "
    "communities control over how their knowledge is accessed and cited — without this, communities "
    "will not participate. The minimum viable test is a single district (e.g., Kutch for craft "
    "traditions, or Vidarbha for traditional farming practices) with 50 structured interviews, "
    "a knowledge graph of 500 nodes, and a search interface tested with 10 researchers.",

    # 3 — Cross-domain: Night-school certification network for urban informal workers
    "Idea: create a network of employer-recognised, practically oriented certification programmes "
    "delivered in 2-hour evening modules, three evenings per week, specifically designed for "
    "urban informal workers in India (construction labour, domestic workers, street vendors, "
    "delivery workers) who have primary school education and limited time. Certifications would "
    "cover practical skills that directly increase earning power in their existing occupation "
    "(construction safety and quality inspection, food hygiene for vendors, basic electrical "
    "work, financial literacy for micro-business). The critical differentiator from existing "
    "vocational training is employer-recognition: certifications would only be worth building "
    "if a coalition of employers in each sector (construction contractors, food aggregators, "
    "housing societies) pre-commit to paying a wage premium for certified workers, which "
    "creates the incentive for workers to attend and for certification bodies to maintain "
    "standards. The critical dependency is assembling this employer coalition before launching "
    "the programme — worker participation is contingent on the wage premium being credible "
    "and verifiable, not promised. The minimum viable test is one skill (construction safety "
    "inspection), one city (Pune), 20 employers pre-committed to a 10% wage premium, and "
    "a cohort of 30 workers over 6 weeks.",

    # 4 — Cross-domain: Predictive maintenance cooperative for small manufacturing clusters
    "Idea: create a shared predictive maintenance service for small manufacturing clusters "
    "(auto components, textiles, ceramics, food processing) in India's industrial districts, "
    "structured as a cooperative where member firms share anonymised sensor data from their "
    "machines in exchange for access to a shared failure prediction model that is more accurate "
    "than any individual firm could build alone. The model improves with each firm's data, "
    "creating a network effect: more member firms produce a better model, which attracts more "
    "firms. Each firm retains ownership of its own raw data; only model gradients (not raw "
    "data) are shared, using federated learning to prevent leakage of proprietary production "
    "patterns to competitors in the same cluster. The critical dependency is trust: firms in "
    "Indian industrial clusters are often direct competitors and would not share data with "
    "a platform they believed was accessible to rivals — the federated architecture must be "
    "auditable and the governance structure must give member firms veto power over model "
    "access. The minimum viable test is a cluster of 10 firms in a single MSME cluster "
    "(e.g., Ludhiana bicycle parts or Rajkot engineering) with IoT sensors on one machine "
    "type per firm, a shared model updated weekly, and a 90-day comparison of unplanned "
    "downtime versus baseline.",

    # 5 — Cross-domain: Citizen science network for urban heat island mapping
    "Idea: build a citizen science network that uses low-cost temperature and humidity sensors "
    "(under Rs 500 per unit) attached to existing street infrastructure (lamp posts, bus stops, "
    "school gates) to produce a 100-metre resolution urban heat island map for Indian cities, "
    "updated every 15 minutes. The data would be used by municipal corporations for targeted "
    "heat action plans (identifying which wards need tree planting, cool roofs, or misting "
    "stations), by hospitals for heat-mortality correlation studies, and by researchers studying "
    "urban climate. The critical differentiator from existing weather station networks is spatial "
    "density: India's meteorological station network has coverage of approximately one station "
    "per 50 square kilometres in urban areas, which is insufficient to detect the intra-city "
    "variation that drives differential heat mortality between neighbourhoods. The critical "
    "dependency is a municipal corporation willing to give permission for sensor attachment "
    "to public infrastructure and to commit to using the data in their heat action plan — "
    "without institutional uptake of the data, the sensor network produces scientifically "
    "interesting but administratively unused information. The minimum viable test is a single "
    "ward (approximately 50,000 residents) in one city with extreme heat exposure (Nagpur, "
    "Ahmedabad, or Hyderabad), 200 sensors, 3 months of data, and a heat action plan "
    "recommendation delivered to the ward officer.",
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

    for i, idea_text in enumerate(OTHER_IDEAS, 1):
        print(f"{'='*60}")
        print(f"Submitting idea {i}/{len(OTHER_IDEAS)}:")
        print(f"  {idea_text[:80]}...")
        print(f"{'='*60}")

        idea_id = save_idea(idea_text, {"evaluation": {"category": "Other"}}, [])
        print(f"  [DB] Assigned idea ID: {idea_id}")

        try:
            result = process_idea(idea_text, idea_id=idea_id, category="Other")
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
