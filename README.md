# Campus Dots ✦

**The missing multiplayer layer for personal AI agents.**

Campus Dots lets personal AI agents negotiate on behalf of students — scheduling study sessions, resolving conflicts, and coordinating group plans through Discord. Each student has a *soul profile* that captures their hard constraints, and agents negotiate from that ground truth.

Built for **Cubbie Hackathon Track 2: Agent-to-Agent Coordination**.

> Track 1 is your agent. Track 2 is when your agents talk.

---

## How it works

1. **Create your soul** — connect to Cubbie or fill in your schedule manually. Your soul profile stores your classes, routines, clubs, and priorities.
2. **Agents negotiate** — mention `@ProxyAgent` in Discord with a request. The negotiation engine loads all soul profiles and runs a multi-agent conversation through Claude.
3. **Result confirmed** — agents surface a time that respects every hard constraint. No group chat needed.

---

## Demo prompts

Try these in Discord after inviting the bot:

```
@ProxyAgent schedule a 3-hour CSE 360 sprint with Mayank and Aaryan before Tuesday
@ProxyAgent we need to finish our CSE 360 presentation tonight — can everyone meet for 4 hours ASAP?
@ProxyAgent find a 2-hour movie night slot this weekend for all three of us
@ProxyAgent can Pratham and Mayank both make a 9 AM meeting this Monday?
@ProxyAgent find a time for all three of us to grab dinner this week, ideally 6–9 PM
@ProxyAgent set up a recurring weekly 30-minute check-in for the three of us
@ProxyAgent plan a 6-hour hackathon session before Friday without wrecking anyone's sleep
@ProxyAgent find a 4-hour slot on Sunday morning for everyone — no exceptions
```

---

## Stack

- **Discord bot** — `discord.py`, three webhook personas (Pratham_Agent, Mayank_Agent, Aaryan_Agent)
- **Negotiation engine** — Anthropic Claude (`claude-sonnet-4-5`) with soul profile context
- **Web app** — Flask, served at `localhost:3000`
- **Soul onboarding** — manual entry or AI extraction via `/api/parse-soul`

---

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```
ANTHROPIC_API_KEY=
DISCORD_TOKEN=
WEBHOOK_PRATHAM=
WEBHOOK_MAYANK=
WEBHOOK_AARYAN=
```

Run the web server:

```bash
python3 web.py
```

Run the Discord bot (separate terminal):

```bash
python3 bot.py
```

Visit `http://localhost:3000` to create soul profiles, then mention `@ProxyAgent` in your Discord server.

---

## Cubbie integration

[Cubbie](https://github.com/amahamu1-art/Better-call-cubbie) is a personal AI student assistant connected to Canvas and Google Calendar. Campus Dots extends Cubbie into the multi-agent layer — paste your Cubbie context during onboarding and your soul profile is built automatically from your real schedule data.

---

## Team

**Better Call Cubbie** — Aaryan Mahamuni, Pratham, Mayank
