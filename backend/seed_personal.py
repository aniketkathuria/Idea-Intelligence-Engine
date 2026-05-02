# seed_personal.py
# Resets the DB and seeds 5 Personal development ideas through the full pipeline.
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

PERSONAL_IDEAS = [
    # 1 — Cognitive offloading via daily brain dump
    "System: spend the first 10 minutes of every workday writing every open loop — unfinished tasks, "
    "unresolved worries, pending decisions, half-formed ideas — into a single plain-text list without "
    "organising or prioritising it. The list is not reviewed during this session. The mechanism is "
    "cognitive offloading: the brain's default mode network continuously allocates working memory to "
    "monitoring unfinished tasks (the Zeigarnik effect), and externalising them onto paper or a file "
    "signals to the monitoring system that the items are captured and no longer need active tracking. "
    "This should reduce the low-grade background anxiety and fragmented attention that most knowledge "
    "workers experience during focused work, not by resolving the open loops but by convincing the "
    "monitoring system that they are stored externally. The leading indicator is a subjective reduction "
    "in intrusive thoughts during the first focused work block of the day, measurable by counting "
    "interruption-to-task-switch events in the first 45 minutes. The minimum viable version is 10 "
    "minutes, one notebook, and no structure — no categories, no priorities, no review.",

    # 2 — Emotion labelling to reduce physiological stress response
    "Practice: when experiencing a strong negative emotion (anxiety before a presentation, frustration "
    "in a conflict, fear before a difficult conversation), spend 60-90 seconds writing or speaking "
    "aloud a precise label for the emotion — not 'I feel bad' but 'I feel a specific dread about "
    "being judged as incompetent by people whose opinion matters to me.' The mechanism is affect "
    "labelling: fMRI studies by Lieberman et al. (2007) show that naming an emotion reduces "
    "amygdala activation and increases prefrontal regulation — the mechanism is that symbolic "
    "representation of affect shifts processing from subcortical threat-detection circuits to "
    "prefrontal cortex, reducing the physiological stress response within 60-90 seconds. The key "
    "is precision: vague labels ('I feel stressed') produce smaller reductions than precise, "
    "differentiated labels ('I feel ashamed about my performance in that meeting'). Higher "
    "emotional granularity — the ability to distinguish between similar negative emotions — "
    "is associated with lower cortisol reactivity and better emotional regulation outcomes "
    "across multiple studies. The practice requires no tools, no time commitment beyond the "
    "moment, and produces a measurable physiological signal within the same episode.",

    # 3 — Temptation bundling for aversive but important tasks
    "System: identify one activity that produces strong immediate pleasure but you feel guilty "
    "consuming (a specific podcast, audiobook, TV series, or food treat), and make access to "
    "it strictly conditional on simultaneously performing an aversive but important task "
    "(exercise, administrative work, language study, deep reading). The mechanism is temptation "
    "bundling (Milkman et al., 2014): pairing an immediately rewarding activity with a delayed- "
    "reward activity transfers some of the immediate reward to the aversive task through classical "
    "conditioning, eventually making the aversive task a cue for the reward. The critical design "
    "constraint is strict exclusivity: the guilty pleasure must be unavailable in any other "
    "context, otherwise the bundle breaks because the reward is no longer contingent on the "
    "behaviour. A field experiment at a university gym found 51% higher gym attendance among "
    "participants who could only access audiobooks they wanted to hear during gym visits. The "
    "minimum viable version requires choosing one pleasure-task pair, deleting the app or "
    "removing access outside the bundle context, and holding the exclusivity rule for 30 days. "
    "The leading indicator is whether you begin looking forward to the aversive task within "
    "the first 10 days.",

    # 4 — Implementation intentions for reducing decision fatigue
    "System: for every recurring decision you make more than three times per week — what to eat "
    "for a specific meal, when to check email, how to respond to a common type of request — "
    "write an if-then implementation intention in the form 'When X happens, I will do Y' and "
    "commit to following it without deliberation for 30 days. The mechanism is implementation "
    "intention (Gollwitzer, 1999): pre-committing a specific response to a specific situational "
    "cue bypasses the deliberation phase entirely, reducing the cognitive load of the decision "
    "to near zero. The benefit is not the specific choice made but the elimination of the "
    "deliberation cost — each eliminated micro-decision preserves a small unit of the cognitive "
    "resource that is depleted by consecutive decisions (ego depletion, Baumeister et al.). "
    "Meta-analysis (Gollwitzer and Sheeran, 2006) across 94 studies found implementation "
    "intentions increase goal attainment rates with an effect size of d=0.65. The target "
    "population is anyone who routinely experiences decision fatigue by mid-afternoon — "
    "characterised by increased impulsivity, avoidance of decisions, and default to the "
    "easiest option regardless of preference.",

    # 5 — Strategic incompleteness to maintain motivation on long projects
    "System: when working on a long-horizon project (book, thesis, startup, course of study), "
    "deliberately stop each work session at a point of forward momentum — mid-sentence, mid-"
    "calculation, mid-argument — rather than at a natural stopping point or completion boundary. "
    "Leave a brief note (2-3 words) indicating the next immediate step. The mechanism operates "
    "through two channels: first, the Zeigarnik effect ensures the incomplete task remains "
    "active in working memory, reducing the activation energy required to restart; second, "
    "stopping at a point of momentum rather than at a satisfying completion prevents the "
    "psychological closure that makes restarting feel like beginning again from zero. Ernest "
    "Hemingway reported using this strategy explicitly ('Always stop when you know what is going "
    "to happen next'), and it is structurally equivalent to the 'cliffhanger' technique used "
    "in serial fiction to maintain reader engagement across episodes. The failure mode is "
    "stopping too early — before enough context is loaded into working memory to make the "
    "Zeigarnik activation meaningful — which produces anxiety about re-entry rather than "
    "anticipation. The leading indicator is whether re-entry to the project on the next "
    "session takes less than 3 minutes to full productive engagement.",
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

    for i, idea_text in enumerate(PERSONAL_IDEAS, 1):
        print(f"{'='*60}")
        print(f"Submitting idea {i}/{len(PERSONAL_IDEAS)}:")
        print(f"  {idea_text[:80]}...")
        print(f"{'='*60}")

        idea_id = save_idea(idea_text, {"evaluation": {"category": "Personal"}}, [])
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
