# seed_engineering.py
# Resets the DB (clears all ideas + clusters) and seeds 5 Engineering ideas
# through the full pipeline (research → eval → embed → cluster).
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from core.db import SessionLocal
from core.models import Idea, Cluster, User
from core.storage import save_idea, update_idea_status
from core.pipeline import process_idea

ENGINEERING_IDEAS = [
    # 1 — Passive radiative cooling coating
    "A passive radiative cooling paint for rooftops that reflects over 95% of incident solar radiation "
    "and simultaneously emits heat in the 8–13 micron atmospheric window — the band where Earth's "
    "atmosphere is transparent — allowing surfaces to cool below ambient air temperature without any "
    "electricity. The paint would be formulated using calcium carbonate or barium sulfate microparticles "
    "in a polymer matrix and applied like standard exterior paint, targeting industrial warehouses and "
    "residential terraces in India's hot climates where cooling load accounts for 40–60% of electricity bills.",

    # 2 — Bamboo-reinforced concrete for rural construction
    "Treated bamboo culms used as a direct rebar replacement in reinforced concrete for low-rise rural "
    "construction in Northeast India and the Himalayan belt, where bamboo grows abundantly but steel "
    "rebar is expensive to transport. The bamboo is treated with borax-boric acid to resist rot and "
    "insects, then coated with epoxy to prevent water absorption that causes swelling and bond loss "
    "with concrete. Targeting single-storey homes, boundary walls, and agricultural sheds where design "
    "loads are within bamboo's tensile strength range of 100–200 MPa.",

    # 3 — Atmospheric water generator using desiccant and solar thermal
    "A solar-thermal atmospheric water generator that uses a solid desiccant — lithium chloride or "
    "silica gel — to adsorb water vapour from ambient air overnight, then regenerates the desiccant "
    "during the day using concentrated solar heat to release the captured moisture, which condenses "
    "on a cooled surface and is collected as drinking water. Unlike compressor-based AWGs that consume "
    "1–5 kWh per litre, this system is designed to operate with zero grid electricity, targeting "
    "water-scarce arid regions like Rajasthan and Gujarat where relative humidity drops to 15–25% "
    "at night but solar irradiance averages 5–6 kWh/m² per day.",

    # 4 — Embedded structural health monitoring for concrete bridges
    "A network of low-power wireless sensors — accelerometers, strain gauges, and corrosion probes — "
    "cast directly into bridge deck concrete during construction, powered by energy harvesting from "
    "vibration and thermal gradients, that continuously transmits structural health data to a cloud "
    "dashboard. The system flags anomalies like rebar corrosion current spikes, resonant frequency "
    "shifts indicating crack formation, or deflection exceeding design limits, giving bridge engineers "
    "a 6–18 month warning before failures become visible. Targeting India's NHAI and state PWD "
    "departments which manage 1.4 lakh bridges and conduct mostly reactive maintenance after visible "
    "damage.",

    # 5 — Modular anaerobic biogas digester from agricultural waste
    "A prefabricated, modular fixed-dome biogas digester made from glass-fibre reinforced plastic "
    "panels that can be assembled without skilled labour in 4–6 hours, designed for Indian farming "
    "households with 2–4 cattle. The digester processes cattle dung and crop residue into biogas for "
    "cooking and a nitrogen-rich slurry for fertiliser. Unlike traditional brick digesters that cost "
    "₹25,000–40,000 and require masons, this unit is designed to cost under ₹12,000, qualify for "
    "MNRE's biogas subsidy of ₹7,000–12,000 per unit, and ship as flat-pack components deliverable "
    "by a tempo to villages without paved roads.",
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

    for i, idea_text in enumerate(ENGINEERING_IDEAS, 1):
        print(f"{'='*60}")
        print(f"Submitting idea {i}/{len(ENGINEERING_IDEAS)}:")
        print(f"  {idea_text[:80]}...")
        print(f"{'='*60}")

        # Create a placeholder row to get a DB-assigned ID
        idea_id = save_idea(idea_text, {"evaluation": {"category": "Engineering"}}, [])
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
