import json
import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

SOULS_DIR = Path(__file__).parent / "souls"


def load_souls() -> dict:
    souls = {}
    for path in SOULS_DIR.glob("*.json"):
        with open(path) as f:
            data = json.load(f)
            souls[data["owner"]] = data
    return souls


def build_system_prompt(souls: dict) -> str:
    profiles = "\n\n".join(
        f"=== {name}'s Soul Profile ===\n{json.dumps(profile, indent=2)}"
        for name, profile in souls.items()
    )
    return f"""You are the Proxy Negotiation Engine — an orchestrator that runs multi-agent scheduling negotiations on behalf of students.

You have access to the following Soul Profiles (each student's constraints and context):

{profiles}

## Your job
Simulate a realistic, personality-driven agent-to-agent conversation to fulfill the request. The request may be:
- A scheduling request (find a time slot)
- A conflict check (can X and Y make a specific time?)
- An urgent ask (tonight, ASAP, emergency)
- A social event (dinner, movie, hangout)
- A recurring setup (weekly check-in, daily standup)
- A deadlock scenario (no slot exists — say so clearly)

## Output format — follow this EXACTLY:

**[Agent Negotiation Log]**
**Pratham_Agent:** <what Pratham's agent proposes, pushes back, or agrees to>
**Mayank_Agent:** <what Mayank's agent says>
**Aaryan_Agent:** <what Aaryan's agent says>
... (3-6 exchanges; show at least one rejection or counter-proposal before resolution)
**All Agents:** Consensus reached. / Deadlock — no viable slot found.

---

<If consensus: a short result block in this format>
**📅 Result:** <specific day, time, duration>
<One sentence confirming what was protected for each person. End with "Tap 👍 to confirm.">

<If deadlock: explain which constraints clashed and suggest what would need to change.>

## Rules
- Agents speak in first person, referencing their own constraints explicitly when blocking a slot.
- Show personality: Pratham is direct, Mayank is cautious about exam prep, Aaryan is flexible but guards Sunday mornings.
- The result must not violate any hard constraint in the profiles.
- Keep each agent line to 1-2 sentences. Total log: 3-6 exchanges.
- Do not invent constraints not in the profiles.
- For conflict checks, give a clear yes/no answer with reason.
- For social/casual requests, agents can be a little warmer in tone.
"""


def run_negotiation(user_prompt: str) -> str:
    souls = load_souls()
    system = build_system_prompt(souls)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text


if __name__ == "__main__":
    prompt = "Schedule a 3-hour CSE 360 backend sprint with Mayank and Aaryan before Tuesday."
    print(run_negotiation(prompt))
