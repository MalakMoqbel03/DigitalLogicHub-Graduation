"""
seed_vark.py
────────────
Run once after migrations to populate vark_questions and vark_options.

Usage:
    cd backend
    python seed_vark.py

The script is idempotent: if questions already exist it exits without
inserting duplicates.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# ─────────────────────────────────────────────────────────────────────────────
# VARK questions for a Digital Systems / Computer Engineering context.
# Each question has exactly 4 options, one per VARK style.
# ─────────────────────────────────────────────────────────────────────────────
VARK_DATA = [
    {
        "question": "When you are trying to understand a new concept in Digital Systems (e.g. logic gates), you prefer to:",
        "options": [
            ("Look at circuit diagrams, truth tables, or visual schematics.", "visual"),
            ("Listen to a lecture or recorded explanation about the concept.", "auditory"),
            ("Read the textbook definition and take written notes.", "reading"),
            ("Build or simulate the circuit yourself to see how it behaves.", "kinesthetic"),
        ],
    },
    {
        "question": "You are revising Boolean Algebra. What do you find most helpful?",
        "options": [
            ("Colour-coded Karnaugh maps and visual simplification steps.", "visual"),
            ("Watching a video where someone talks through the simplification process.", "auditory"),
            ("Reading worked examples in a textbook and rewriting the steps.", "reading"),
            ("Practising simplification problems by hand until the pattern clicks.", "kinesthetic"),
        ],
    },
    {
        "question": "When you get a quiz result back, the first thing you do is:",
        "options": [
            ("Look at which questions you got wrong on the visual results chart.", "visual"),
            ("Ask a friend or tutor to explain what you misunderstood.", "auditory"),
            ("Read the written feedback and review your notes for those topics.", "reading"),
            ("Immediately redo the questions you missed to practise them.", "kinesthetic"),
        ],
    },
    {
        "question": "To remember the difference between combinational and sequential circuits, you would:",
        "options": [
            ("Draw a side-by-side comparison diagram with labelled boxes.", "visual"),
            ("Repeat the key differences out loud or explain them to someone.", "auditory"),
            ("Write a summary list of differences and review it later.", "reading"),
            ("Wire up examples of both and observe their different behaviours.", "kinesthetic"),
        ],
    },
    {
        "question": "A new topic (e.g. Flip-Flops) has just been introduced. How do you start learning it?",
        "options": [
            ("Find a diagram or animation that shows how a flip-flop stores state.", "visual"),
            ("Search for a YouTube video or podcast that explains flip-flops.", "auditory"),
            ("Read the lecture slides and Wikipedia article first.", "reading"),
            ("Open a simulator and experiment with a flip-flop circuit right away.", "kinesthetic"),
        ],
    },
    {
        "question": "You are studying for an exam on FSMs (Finite State Machines). You mainly use:",
        "options": [
            ("State transition diagrams drawn on paper or on screen.", "visual"),
            ("A recorded lecture playing in the background while you revise.", "auditory"),
            ("A written list of states, transitions, and conditions from your notes.", "reading"),
            ("Building and stepping through a small FSM in a simulator.", "kinesthetic"),
        ],
    },
    {
        "question": "During a lecture on Verilog HDL, you find it easiest to follow along by:",
        "options": [
            ("Looking at the waveform outputs projected on screen.", "visual"),
            ("Listening carefully to the instructor's verbal explanation of the syntax.", "auditory"),
            ("Following the printed code listing and annotating it with comments.", "reading"),
            ("Typing the code live in your editor and running it immediately.", "kinesthetic"),
        ],
    },
    {
        "question": "You want to explain how a multiplexer works to a classmate. You would:",
        "options": [
            ("Draw a schematic showing the data inputs, select lines, and output.", "visual"),
            ("Verbally walk them through the logic: 'When select is 0, input A passes through...'", "auditory"),
            ("Write out the truth table and Boolean expression on paper.", "reading"),
            ("Show them by wiring one up in a simulator and demonstrating each case.", "kinesthetic"),
        ],
    },
    {
        "question": "When reviewing your mistakes on a Digital Systems assignment, you prefer:",
        "options": [
            ("Circling errors on your diagram and drawing the corrected version.", "visual"),
            ("Talking through what went wrong with a lab partner or tutor.", "auditory"),
            ("Rewriting the solution step-by-step with annotations in your notes.", "reading"),
            ("Redoing the entire problem from scratch to rebuild the correct process.", "kinesthetic"),
        ],
    },
    {
        "question": "How do you best memorise the order of precedence for Boolean operators?",
        "options": [
            ("A visual hierarchy chart (NOT > AND > OR) pinned above your desk.", "visual"),
            ("Saying the rule out loud repeatedly: 'NOT first, then AND, then OR.'", "auditory"),
            ("Writing the rule in your own words and including it in your summary sheet.", "reading"),
            ("Solving many small Boolean expressions until the precedence feels automatic.", "kinesthetic"),
        ],
    },
    {
        "question": "When learning about Memory Systems (RAM, ROM, cache), you prefer to:",
        "options": [
            ("Study diagrams showing the memory hierarchy and address lines.", "visual"),
            ("Listen to a professor explain the access time differences.", "auditory"),
            ("Read a detailed article comparing the types and take notes.", "reading"),
            ("Run a benchmark or simulation that shows real access time differences.", "kinesthetic"),
        ],
    },
    {
        "question": "Before a lab session on combinational circuit design, you prepare by:",
        "options": [
            ("Studying the circuit schematic you will be building.", "visual"),
            ("Listening to the pre-lab video explanation the instructor posted.", "auditory"),
            ("Reading through the lab manual and writing out the steps.", "reading"),
            ("Trying to pre-build a simplified version of the circuit to get familiar.", "kinesthetic"),
        ],
    },
    {
        "question": "When a concept 'clicks' for you, it usually happens because:",
        "options": [
            ("You saw a clear diagram or visualisation that made the structure obvious.", "visual"),
            ("Someone explained it verbally in a way that finally made sense.", "auditory"),
            ("You read enough different written explanations that it became clear.", "reading"),
            ("You tried it enough times hands-on that the pattern became intuitive.", "kinesthetic"),
        ],
    },
    {
        "question": "You are choosing between two study resources on Timing & Performance. You pick the one that:",
        "options": [
            ("Has the most clear timing diagrams and annotated waveform figures.", "visual"),
            ("Is a recorded lecture where the speaker explains critical path analysis.", "auditory"),
            ("Provides thorough written explanations with worked numerical examples.", "reading"),
            ("Includes interactive exercises where you calculate slack and critical path.", "kinesthetic"),
        ],
    },
    {
        "question": "If you had to teach someone about Number Systems (binary, hex, BCD), you would:",
        "options": [
            ("Create a visual chart showing conversions and bit patterns.", "visual"),
            ("Explain it verbally, talking through the conversion process step by step.", "auditory"),
            ("Write up a clear written guide with conversion formulas.", "reading"),
            ("Give them conversion practice problems to work through immediately.", "kinesthetic"),
        ],
    },
    {
        "question": "Your preferred type of learning resource overall is:",
        "options": [
            ("Video lectures with clear slides, diagrams, and on-screen annotations.", "visual"),
            ("Audio explanations, podcasts, or verbal walkthroughs.", "auditory"),
            ("Written tutorials, textbooks, or detailed lecture notes.", "reading"),
            ("Interactive simulations, labs, or practice question sets.", "kinesthetic"),
        ],
    },
]


def seed():
    with Session() as session:
        # Idempotency check
        existing = session.execute(text("SELECT COUNT(*) FROM vark_questions")).scalar()
        if existing and existing > 0:
            print(f"VARK questions already seeded ({existing} found). Skipping.")
            return

        print("Seeding VARK questions...")
        for q_data in VARK_DATA:
            # Insert question
            result = session.execute(
                text("INSERT INTO vark_questions (question_text) VALUES (:q) RETURNING id"),
                {"q": q_data["question"]},
            )
            q_id = result.fetchone()[0]

            # Insert options
            for option_text, vark_type in q_data["options"]:
                session.execute(
                    text(
                        "INSERT INTO vark_options (question_id, option_text, vark_type) "
                        "VALUES (:qid, :opt, :vt)"
                    ),
                    {"qid": q_id, "opt": option_text, "vt": vark_type},
                )

        session.commit()
        print(f"Done. Inserted {len(VARK_DATA)} questions with 4 options each.")


if __name__ == "__main__":
    seed()