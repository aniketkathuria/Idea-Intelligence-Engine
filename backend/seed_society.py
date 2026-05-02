# seed_society.py
# Resets the DB and seeds 5 Society hypotheses through the full pipeline.
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

SOCIETY_IDEAS = [
    # 1 — Digital penetration bypassing caste gatekeepers
    "Hypothesis: smartphone and 4G penetration in tier-2 and tier-3 Indian cities between 2016 and 2022 "
    "significantly accelerated occupational mobility for lower-caste individuals by bypassing traditional "
    "upper-caste gatekeepers in hiring and credit markets. The proposed mechanism is that digital job "
    "platforms (LinkedIn, Apna, Naukri) and digital lending (KreditBee, MoneyTap) reduced the role of "
    "personal referrals and social network capital — which historically correlated with caste — in "
    "accessing formal employment and small business finance. This predicts that districts with faster 4G "
    "rollout (Jio's phased expansion provides a natural experiment) should show larger reductions in the "
    "caste-wage gap than comparable districts with slower rollout, controlling for baseline education and "
    "urbanization. The effect should be stronger for SC/ST individuals than for OBC, and stronger in "
    "private-sector employment than in government jobs where caste-based reservation already operates.",

    # 2 — Joint family structure suppressing entrepreneurial risk
    "Hypothesis: Indian adults from joint family households (three or more generations co-residing) "
    "exhibit systematically lower entrepreneurial risk tolerance than adults from nuclear families, "
    "even after controlling for income, education, and caste. The proposed mechanism is dual: first, "
    "joint families pool income across earners, reducing individual income volatility and therefore "
    "reducing the perceived need for high-variance entrepreneurial income; second, joint family "
    "decision-making norms require consensus across elder family members who disproportionately prefer "
    "stable government or salaried employment over self-employment. This predicts that first-generation "
    "nuclear households — adults who themselves grew up in joint families but now live independently — "
    "should show intermediate risk tolerance between joint-family adults and multi-generation nuclear "
    "adults, reflecting a transitional norm state. The IHDS panel data (2004-05 and 2011-12) and "
    "NSSO employment surveys provide the household structure and self-employment data needed to test this.",

    # 3 — WhatsApp rumor propagation and religious identity
    "Hypothesis: the propagation velocity and geographic reach of false rumors on WhatsApp in India "
    "follows the structure of religiously homogeneous social clusters rather than geographic proximity "
    "or economic connectivity. Specifically, rumors targeting a specific religious community spread "
    "faster and wider within spatially dispersed networks of the opposing religious community than "
    "within geographically contiguous networks of mixed composition. The proposed mechanism is that "
    "WhatsApp group membership in India is heavily shaped by religious identity through pilgrimage "
    "networks, religious organization memberships, and kin networks that span geography but share "
    "religious identity. This predicts that the first outbreak districts for a given communal rumor "
    "should show lower geographic clustering and higher religious homogeneity than would be expected "
    "from a geographic diffusion model, and that inter-district propagation links should correlate "
    "with migration corridors from shared places of religious origin rather than physical adjacency.",

    # 4 — Female education and dowry inversion
    "Hypothesis: in Indian states with female labor force participation above 30 percent, the "
    "relationship between daughter's educational attainment and dowry amount inverts — higher education "
    "reduces dowry demanded rather than increasing it, as is observed in low-FLFP states. The proposed "
    "mechanism is that in high-FLFP states, educated women are net economic contributors to the "
    "husband's household from the first year of marriage, shifting the marriage market calculus from "
    "dowry-as-compensation-for-accepting-a-bride to dowry-as-competition-for-educated-matches. This "
    "predicts a state-level interaction effect: the coefficient on daughter's education in a dowry "
    "regression should be negative in high-FLFP states (Kerala, Himachal Pradesh, Sikkim) and "
    "positive in low-FLFP states (Bihar, Uttar Pradesh, Rajasthan), with the sign flip occurring "
    "around the 30 percent FLFP threshold. NFHS-4 and NFHS-5 both contain dowry amount and "
    "education data at individual level with state identifiers.",

    # 5 — Internal migrant workers forming neo-caste occupational clusters
    "Hypothesis: second-generation internal migrants in Indian tier-1 cities (Mumbai, Delhi, "
    "Bangalore, Chennai) are forming occupationally specialized clusters that replicate the "
    "functional structure of the jati system — hereditary occupational identity, endogamous "
    "marriage within the occupational cluster, and collective norm enforcement — but organized "
    "around regional-linguistic origin rather than traditional varna-jati categories. The proposed "
    "mechanism is that migrants use regional identity as a low-cost coordination device for trust, "
    "referral hiring, and social insurance in high-anonymity urban environments, and that over two "
    "generations this produces occupational concentration indistinguishable in structure from "
    "caste-based occupational clustering. This predicts that controlling for parental occupation "
    "and education, second-generation migrants should show stronger occupational inheritance "
    "within regional-origin groups than first-generation migrants, and that this effect should "
    "be stronger in occupations with high asymmetric information (domestic staffing, construction "
    "contracting, street vending) than in credentialed professions.",
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

    for i, idea_text in enumerate(SOCIETY_IDEAS, 1):
        print(f"{'='*60}")
        print(f"Submitting idea {i}/{len(SOCIETY_IDEAS)}:")
        print(f"  {idea_text[:80]}...")
        print(f"{'='*60}")

        idea_id = save_idea(idea_text, {"evaluation": {"category": "Society"}}, [])
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
