import os
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import asyncio
import re
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
from negotiation import run_negotiation

load_dotenv(Path(__file__).parent / ".env")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Map agent name keywords → env var → emoji
AGENT_CONFIG = {
    "pratham": {"env": "WEBHOOK_PRATHAM", "emoji": "🤖", "label": "Pratham_Agent"},
    "mayank":  {"env": "WEBHOOK_MAYANK",  "emoji": "🦁", "label": "Mayank_Agent"},
    "aaryan":  {"env": "WEBHOOK_AARYAN",  "emoji": "⚡", "label": "Aaryan_Agent"},
}


def get_webhooks() -> dict:
    """Return {agent_key: webhook_url} for configured agents."""
    hooks = {}
    for key, cfg in AGENT_CONFIG.items():
        url = os.environ.get(cfg["env"], "").strip()
        if url:
            hooks[key] = url
    return hooks


def match_agent(line: str) -> str | None:
    """Return agent key if the line starts with that agent's name."""
    clean = line.lower().lstrip("*").lstrip()
    for key in AGENT_CONFIG:
        if clean.startswith(key):
            return key
    return None


def strip_markdown(text: str) -> str:
    return text.replace("**", "").replace("*", "").strip()


async def post_webhook(session: discord.http.HTTPClient, url: str, username: str, content: str):
    """Post a message to a Discord webhook."""
    webhook = discord.Webhook.from_url(url, client=bot)
    await webhook.send(content=content, username=username)


@bot.event
async def on_ready():
    hooks = get_webhooks()
    print(f"ProxyAgent online as {bot.user}  |  {len(hooks)}/3 agent webhooks configured")
    for k, v in hooks.items():
        print(f"  {k}: {v[:40]}...")


@bot.event
async def on_message(message: discord.Message):
    print(f"[MSG] author={message.author} bot={message.author.bot} mentions={message.mentions} content={message.content[:60]!r}")
    if message.author.bot:
        return

    content = message.content
    is_mentioned = bot.user in message.mentions
    is_role_mention = any(r.name.lower() == "proxyagent" for r in message.role_mentions)
    is_text_mention = "proxyagent" in content.lower()

    if not is_mentioned and not is_role_mention and not is_text_mention:
        return

    print(f"[on_message] triggered by {message.author}: {content[:80]}")

    import re
    # Strip user mention, role mention, and plain text mention
    prompt = re.sub(r"<@[!&]?\d+>", "", content).replace("@ProxyAgent", "").replace("@proxyagent", "").strip()
    if not prompt:
        await message.reply(
            "Send me a scheduling request, e.g.\n"
            "> @ProxyAgent schedule a 3-hour CSE 360 sprint with Mayank and Aaryan before Tuesday"
        )
        return

    hooks = get_webhooks()
    thinking = await message.channel.send("⏳ Agents are negotiating…")

    try:
        result = run_negotiation(prompt)
    except Exception as e:
        await thinking.edit(content=f"⚠️ Negotiation failed: {e}")
        return

    await thinking.delete()

    # Split log from final answer
    if "---" in result:
        log_raw, answer_raw = result.split("---", 1)
    else:
        log_raw, answer_raw = result, ""

    # Parse log into lines
    lines = [
        strip_markdown(l)
        for l in log_raw.splitlines()
        if l.strip() and "[Agent Negotiation Log]" not in l
    ]

    # Stream each line — webhook if available, else plain channel message
    for line in lines:
        agent_key = match_agent(line)
        cfg = AGENT_CONFIG.get(agent_key) if agent_key else None
        hook_url = hooks.get(agent_key) if agent_key else None

        if hook_url and cfg:
            try:
                webhook = discord.Webhook.from_url(hook_url, client=bot)
                await webhook.send(
                    content=line,
                    username=cfg["label"],
                )
            except Exception:
                await message.channel.send(f"**{line}**")
        else:
            await message.channel.send(line)

        await asyncio.sleep(1.2)

    # Final result as an embed
    if answer_raw.strip():
        embed = discord.Embed(
            description=strip_markdown(answer_raw),
            color=0x111111,
        )
        embed.set_footer(text="Tap 👍 to confirm · Proxy Negotiation by Campus Dots")
        await message.channel.send(embed=embed)
        await message.channel.send("👍  **Confirm**  |  ❌  **Decline**")

    await bot.process_commands(message)


if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not set")
    bot.run(token)
