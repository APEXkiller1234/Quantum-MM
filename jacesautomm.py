import asyncio
import io
import json
import logging
import math
import random
import re
import secrets
import time
import traceback
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from pathlib import Path
from urllib.parse import quote

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from colorama import Fore, Style, init as colorama_init


TOKEN = "" # Get from Discord Developer Portal
YOUR_USER = 1506688372045910227 # Your User ID
STAFF_COMMAND_ROLE = 1544772439014121572
TOS_CHANNEL = 1543637559463256214 # Middleman ToS Channel ID
MM_TOS_CHANNEL = 1543637636487450724 # Auto Middleman ToS Channel ID
AUTOMM_TRADE_CHANNEL = 1543637629243891764 # Channel linked in !autommtos ("start a trade here") 
TICKET_CATEGORY = 1543637510264061992 # Auto Middleman Tickets Category ID
TRANSCRIPT_CHANNEL = 1543639039868149910 # Auto Middleman Tickets Logging Channel ID
COMPLETED_TRANSACTION_CHANNEL = 1543637629243891764 # Completed Auto Middleman Embeds Channel ID
SETTLEMENT_CHANNEL = 1543639039868149910
DEMO_COMPLETED_TRANSACTION_CHANNEL = 1543637640459325551 # Must be different from COMPLETED_TRANSACTION_CHANNEL
DEMO_HALAL_COMPLETED_CHANNEL = 1546838969981993030 # Halal-format copy of the same demo post. 0 = off. Does not use extra APIs.
TUTORIAL_URL = "https://www.youtube.com/watch?v=XIkpcT2WNPI" # For Tutorial Button in Panel

LTC_DEPOSIT_ADDRESS = "LduBxCtH1jTrhmccGvZExDQHmhWB9r2d9D" # Your Litecoin Address
USDT_DEPOSIT_ADDRESS = "0x4675Bf0637fFd33A32419C0fDcD7b677A6ca146e" # Your USDT Address

# Demo completed-trade posts. Use one BlockCypher / Etherscan account here.
BLOCKCYPHER_TOKEN = "692da515d0ed4d4e9fd6352efcbe727b" # Get from https://www.blockcypher.com/apis.html
ETHERSCAN_API_KEY = "5M7Q4T5GX35IUUJ49HSC71JUUAD2F726E1" # Get from https://etherscan.io/api

# Live tickets. Use a second BlockCypher / Etherscan account here.
TICKET_BLOCKCYPHER_TOKEN = "fb1a4f21dc1f4f7ca2172e31091fd382" # Second BlockCypher token for tickets
TICKET_ETHERSCAN_API_KEY = "GU2JTN53158HUA6S9BA3D4HN6K9TY3TM6T" # Second Etherscan key for tickets

COINBASE_LTC_PRICE_URL = "https://api.coinbase.com/v2/prices/LTC-USD/spot"

USDT_BEP20_CONTRACT = "0x55d398326f99059ff775485246999027b3197955"
BSC_CHAIN_ID = "56"

SETTLEMENT_MODE = "manual"

AUTO_MONITOR_LTC = True
AUTO_MONITOR_USDT = True
AUTO_CLOSE_UNPAID = True

LTC_CONFIRMATIONS_REQUIRED = 1
USDT_CONFIRMATIONS_REQUIRED = 1

UNPAID_TIMEOUT_SECONDS = 1200
MONITOR_INTERVAL_SECONDS = 15

DEMO_ACTIVITY_ENABLED = True
DEMO_BASE_INTERVAL_SECONDS = 61
DEMO_JITTER_MIN_SECONDS = 35
DEMO_JITTER_MAX_SECONDS = 90
DEMO_MIN_CONFIRMATIONS = 6
DEMO_RECENT_BLOCK_WINDOW = 500

STARTING_TICKET_NUMBER = 12077

BIGGEST_TRADE_USD = 30006 # Biggest completed trade amount shown on the panel footer
BIGGEST_TRADE_MESSAGE_URL = "" # Message link to the biggest completed trade (e.g. https://discord.com/channels/guild/channel/message)

# ===== Jaces mode =====
# Put image files next to this script or inside jaces_assets/. Leave "" to skip that field.
# Example: JACES_SERVER_ICON = "jaces_server_icon.png"

JACES_SERVER_NAME = "Jace's MM Service"
JACES_SERVER_DESCRIPTION = "https://jaces.xyz/"
JACES_SERVER_ICON = "https://github.com/APEXkiller1234/Vaultix/blob/main/1788102354-icon%20(1).gif?raw=true"
JACES_SERVER_BANNER = "https://github.com/APEXkiller1234/Vaultix/blob/main/jacebanner.webp?raw=true"
JACES_BOT_NAME = "Auto Middleman"
JACES_BOT_AVATAR = "https://github.com/APEXkiller1234/Vaultix/blob/main/image_2026-08-30_225952052.png?raw=true"
JACES_BOT_BANNER = "https://github.com/APEXkiller1234/Vaultix/blob/main/image_2026-08-30_230056191.png?raw=true"
JACES_BOT_ROLE_NAME = "Auto Middleman"

NORMAL_SERVER_NAME = "Horizon Shop"
NORMAL_SERVER_DESCRIPTION = "Best shop in the world and cheapest"
NORMAL_SERVER_ICON = "https://github.com/APEXkiller1234/Vaultix/blob/main/image_2026-08-31_140013803.png?raw=true"
NORMAL_SERVER_BANNER = "https://github.com/APEXkiller1234/Vaultix/blob/main/image_2026-08-31_140022263.png?raw=true"
NORMAL_BOT_NAME = "Horizon Helper"
NORMAL_BOT_AVATAR = "https://github.com/APEXkiller1234/Vaultix/blob/main/image_2026-08-31_140013803.png?raw=true"
NORMAL_BOT_BANNER = "https://github.com/APEXkiller1234/Vaultix/blob/main/image_2026-08-31_140022263.png?raw=true"
NORMAL_BOT_ROLE_NAME = "Horizon the best"

# Applied by /jaces and /nonjaces. Leave "" to skip that field.
# Status: online, idle, dnd, invisible
# Activity type: playing, watching, listening, competing, custom
JACES_BOT_STATUS = "• 430,139 deals • https://jaces.xyz"
JACES_BOT_ACTIVITY_TYPE = ""
JACES_BOT_ACTIVITY = ""
JACES_BOT_BIO = """https://jaces.xyz/
https://kookie-py.github.io/bot-privacy-policy"""

NORMAL_BOT_STATUS = "Watching Everything"
NORMAL_BOT_ACTIVITY_TYPE = "Cooking Roblox"
NORMAL_BOT_ACTIVITY = ""
NORMAL_BOT_BIO = "HORIZONNNNNNNNNNNNNNN"

# ===== Halal mode =====
# Same switch as /jaces and /nonjaces. Fill these in; leave "" to skip that field.

HALAL_SERVER_NAME = "TheH Hub"
HALAL_SERVER_DESCRIPTION = ""
HALAL_SERVER_ICON = "https://github.com/APEXkiller1234/Vaultix/blob/main/image_2026-09-08_124839113.png?raw=true"
HALAL_SERVER_BANNER = ""
HALAL_BOT_NAME = "v3"
HALAL_BOT_AVATAR = "https://github.com/APEXkiller1234/Vaultix/blob/main/halal_v3.png?raw=true"
HALAL_BOT_BANNER = ""
HALAL_BOT_ROLE_NAME = "H Bot"
HALAL_BOT_STATUS = ""
HALAL_BOT_ACTIVITY_TYPE = ""
HALAL_BOT_ACTIVITY = ""
HALAL_BOT_BIO = ""

HALAL_WEBSITE_URL = "https://halalmm.com/" # Linked as "website" in Halal tickets
HALAL_TOS_URL = "https://www.halalmm.com/terms" # Linked as "Terms of Service" on the Halal panel
HALAL_KNOWN_SCAMS_URL = "https://www.halalmm.com/dashboard/creating-deals/known-scam" # Linked as "known scams" in the safety warning
HALAL_HOW_USERID_URL = "https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID"
HALAL_WELCOME_IMAGE = "https://github.com/APEXkiller1234/Vaultix/blob/main/Welcome_Prompt.gif?raw=true" # Deal Started thumbnail
HALAL_MASCOT_IMAGE = "https://github.com/APEXkiller1234/Vaultix/blob/main/Waiting_Anim.gif?raw=true" # Thumbnails on payment / detected / complete cards

HALAL_TICKET_CATEGORY = 0 # 0 = use TICKET_CATEGORY
HALAL_COMPLETED_CHANNEL = 0 # 0 = use COMPLETED_TRANSACTION_CHANNEL
HALAL_STARTING_TICKET_NUMBER = 2135780
HALAL_MIN_USD = "1.00"
HALAL_UNPAID_TIMEOUT_SECONDS = 1800
HALAL_AUTO_CLOSE_SECONDS = 300
HALAL_CONFIRMATIONS = 1
HALAL_SOLANA_RPC = "https://api.mainnet-beta.solana.com"

# Deposit addresses for Halal tickets. Leave "" until you set them.
HALAL_BTC_ADDRESS = "bc1q9za9stm00dx6qgcs08tsvrz6x75jctxfxsratv"
HALAL_ETH_ADDRESS = "0x4675Bf0637fFd33A32419C0fDcD7b677A6ca146e"
HALAL_LTC_ADDRESS = "LduBxCtH1jTrhmccGvZExDQHmhWB9r2d9D" # Blank uses LTC_DEPOSIT_ADDRESS
HALAL_SOL_ADDRESS = "Ewdis5EEXSf2FFnfg8fbnUqZuqvtZNPZULiJPwKnsvBq"
HALAL_USDT_ERC20_ADDRESS = "0x4675Bf0637fFd33A32419C0fDcD7b677A6ca146e"
HALAL_USDC_ERC20_ADDRESS = "0x4675Bf0637fFd33A32419C0fDcD7b677A6ca146e"
HALAL_USDT_BEP20_ADDRESS = "" # Blank uses USDT_DEPOSIT_ADDRESS
HALAL_USDT_SOL_ADDRESS = "Ewdis5EEXSf2FFnfg8fbnUqZuqvtZNPZULiJPwKnsvBq"
HALAL_USDC_SOL_ADDRESS = "Ewdis5EEXSf2FFnfg8fbnUqZuqvtZNPZULiJPwKnsvBq"

USDT_ERC20_CONTRACT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
USDC_ERC20_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT_SOL_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
USDC_SOL_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

HALAL_BTC_EMOJI = "<:halal_btc:1546837210022551612>"
HALAL_ETH_EMOJI = "<:halal_eth:1546837220416294952>"
HALAL_LTC_EMOJI = "<:halal_ltc:1546837239512834130>"
HALAL_SOL_EMOJI = "<:halal_sol:1546837202439503952>"
HALAL_USDT_EMOJI = "<:halal_usdteth:1546837193790717982>"
HALAL_USDC_EMOJI = "<:halal_usdceth:1546837185657962516>"
HALAL_USDT_ERC20_EMOJI = "<:halal_usdteth:1546837193790717982>"
HALAL_USDC_ERC20_EMOJI = "<:halal_usdceth:1546837185657962516>"
HALAL_USDT_BEP20_EMOJI = "<:halal_usdt_bsc:1546837178250698843>"
HALAL_USDT_SOL_EMOJI = "<:halal_usdtsol:1546837172341055529>"
HALAL_USDC_SOL_EMOJI = "<:halal_usdcsol:1546837162404880464>"


# ===== Emojis ========

LTC_EMOJI="<:ltc:1543646735761543279>"
USDT_EMOJI="<:usdt:1543646817391222915>"
ANIMATED_X_EMOJI="<a:x_:1543647917817069628>"
ANIMATED_WAVE_EMOJI="<a:wave:1543649366995238952>"
ROLE_SHIELD_EMOJI="<:role:1543649318492446751>"
BLUE_LOADING_EMOJI="<a:loading:1543649631697899590>"
GREEN_TICK_EMOJI="<a:correct:1543650468440571984>"
LOAD_EMOJI="<a:loading:1543649631697899590>"
MONEY_EMOJI = "💵" # Unicode in the real bot, don't edit.
SCROLL_EMOJI = "📜" # Unicode in the real bot, don't edit.
WARNING_EMOJI = "⚠️" # Unicode in the real bot, don't edit.
LOCK_EMOJI = "🔒" # Unicode in the real bot, don't edit.

COLOR_NEUTRAL = 0xBFBFBF
COLOR_SUCCESS = 0x86EF93
COLOR_ERROR = 0xDB504C
COLOR_WARNING = 0xF3AA3C
COLOR_BLURPLE = 0x5B65EA
COLOR_USDT = 0x509F7D
COLOR_HALAL_GREEN = 0x23A559
COLOR_HALAL_RED = 0xED4245
COLOR_HALAL_ORANGE = 0xF0B232
COLOR_HALAL_GRAY = 0x4E5058

DOT = "﹒"
H1 = chr(35)
H2 = chr(35) * 2
WORD_JOINER = chr(8288)
ZERO_WIDTH = chr(8203)

DATA_FILE = Path("middleman_data.json")

DATA_LOCK = asyncio.Lock()

JACES_ASSETS_DIR = Path("jaces_assets")
JACES_LOCK = asyncio.Lock()
JACES_PERM_CONCURRENCY = 8
JACES_RATE_RETRY_SECONDS = 15
JACES_REASON_ON = "Jaces mode"
JACES_REASON_OFF = "Jaces mode revert"
JACES_REASON_HALAL = "Halal mode"
JACES_RATE_WAIT_UNTIL = 0.0
HALAL_CLOSE_TASKS = {}

TICKET_LOCKS = {}
MONITOR_TASKS = {}
COUNTDOWN_TASKS = {}
BASELINE_TASKS = {}
BASELINE_IN_PROGRESS = 0
TICKET_CHAIN_CACHE = {}
TICKET_CHAIN_CACHE_LOCK = asyncio.Lock()

READY_RESUME_LOCK = asyncio.Lock()

READY_RESUMED = False
BANNER_PRINTED = False
DEMO_ACTIVITY_TASK = None


colorama_init(autoreset=True)


ASCII_WATERMARK = r"""
 _                            
| |__   ___  _ __   ___ _   _
| '_ \ / _ \| '_ \ / _ \ | | |
| | | | (_) | | | |  __/ |_| |
|_| |_|\___/|_| |_|\___|\__, |
                           |___/ 
                honey.py
"""




class ColorConsoleFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,
        logging.INFO: Fore.LIGHTCYAN_EX,
        logging.WARNING: Fore.LIGHTYELLOW_EX,
        logging.ERROR: Fore.LIGHTRED_EX,
        logging.CRITICAL: Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        timestamp = self.formatTime(
            record,
            "%H:%M:%S"
        )

        level_color = self.LEVEL_COLORS.get(
            record.levelno,
            Fore.WHITE
        )

        level = f"{record.levelname:<8}"

        message = record.getMessage()

        output = (
            f"{Fore.LIGHTBLACK_EX}[{timestamp}] "
            f"{level_color}{level}{Style.RESET_ALL} "
            f"{Fore.LIGHTMAGENTA_EX}{record.name}{Style.RESET_ALL} "
            f"{Fore.WHITE}{message}{Style.RESET_ALL}"
        )

        if record.exc_info:
            output += (
                "\n"
                + Fore.LIGHTRED_EX
                + self.formatException(record.exc_info)
                + Style.RESET_ALL
            )

        return output


root_logger = logging.getLogger()
root_logger.handlers.clear()

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    ColorConsoleFormatter()
)

root_logger.addHandler(
    console_handler
)

root_logger.setLevel(
    logging.INFO
)

logger = logging.getLogger(
    "honey.py"
)


def print_watermark():
    global BANNER_PRINTED

    if BANNER_PRINTED:
        return

    print(
        Fore.LIGHTMAGENTA_EX
        + Style.BRIGHT
        + ASCII_WATERMARK
        + Style.RESET_ALL
    )

    BANNER_PRINTED = True


def log_action(action, **details):
    detail_text = " | ".join(
        f"{key}={value}"
        for key, value
        in details.items()
    )

    if detail_text:
        logger.info(
            "%s | %s",
            action,
            detail_text
        )
    else:
        logger.info(
            "%s",
            action
        )


def log_security(action, **details):
    detail_text = " | ".join(
        f"{key}={value}"
        for key, value
        in details.items()
    )

    if detail_text:
        logger.warning(
            "%s | %s",
            action,
            detail_text
        )
    else:
        logger.warning(
            "%s",
            action
        )


def default_presence():
    return {
        "type": "playing",
        "text": "",
        "status": "online"
    }


def default_data():
    return {
        "next_ticket_number": STARTING_TICKET_NUMBER,
        "tickets": {},
        "stats": {},
        "privacy": {},
        "claimed_deposit_txids": {},
        "jaces": {
            "guilds": {}
        },
        "presence": default_presence(),
        "rank_roles": [],
        "next_halal_ticket_number": HALAL_STARTING_TICKET_NUMBER
    }


def load_data():
    if not DATA_FILE.exists():
        return default_data()

    try:
        with DATA_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(
            data,
            dict
        ):
            return default_data()

        data.setdefault(
            "next_ticket_number",
            STARTING_TICKET_NUMBER
        )

        data.setdefault(
            "tickets",
            {}
        )

        data.setdefault(
            "stats",
            {}
        )

        data.setdefault(
            "privacy",
            {}
        )

        data.setdefault(
            "claimed_deposit_txids",
            {}
        )

        data.setdefault(
            "jaces",
            {
                "guilds": {}
            }
        )

        data.setdefault(
            "presence",
            default_presence()
        )

        data.setdefault(
            "rank_roles",
            []
        )

        data.setdefault(
            "next_halal_ticket_number",
            HALAL_STARTING_TICKET_NUMBER
        )

        return data

    except Exception:
        logger.exception(
            "Failed to load middleman_data.json"
        )

        return default_data()


DATA = load_data()


def save_data_now():
    temporary = DATA_FILE.with_suffix(
        ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            DATA,
            file,
            indent=4,
            ensure_ascii=False
        )

    temporary.replace(
        DATA_FILE
    )


async def save_data():
    async with DATA_LOCK:
        save_data_now()


def get_ticket_lock(channel_id):
    key = str(
        channel_id
    )

    lock = TICKET_LOCKS.get(
        key
    )

    if lock is None:
        lock = asyncio.Lock()
        TICKET_LOCKS[key] = lock

    return lock


async def reserve_ticket_number():
    async with DATA_LOCK:
        number = int(
            DATA.get(
                "next_ticket_number",
                STARTING_TICKET_NUMBER
            )
        )

        if number < STARTING_TICKET_NUMBER:
            number = STARTING_TICKET_NUMBER

        DATA[
            "next_ticket_number"
        ] = number + 1

        save_data_now()

        return number


async def reserve_halal_ticket_number():
    async with DATA_LOCK:
        number = int(
            DATA.get(
                "next_halal_ticket_number",
                HALAL_STARTING_TICKET_NUMBER
            )
        )

        if number < HALAL_STARTING_TICKET_NUMBER:
            number = HALAL_STARTING_TICKET_NUMBER

        DATA[
            "next_halal_ticket_number"
        ] = number + 1

        save_data_now()

        return number


def get_ticket(channel_id):
    if channel_id is None:
        return None

    return DATA[
        "tickets"
    ].get(
        str(channel_id)
    )


def get_ticket_by_number(number):
    for ticket in DATA[
        "tickets"
    ].values():

        if int(
            ticket.get(
                "number",
                0
            )
        ) == int(number):
            return ticket

    return None


def custom_emoji(value):
    if not value:
        return None

    try:
        return discord.PartialEmoji.from_str(
            value
        )

    except Exception:
        return None


def emoji_text(value):
    return f"{value} " if value else ""


def clean_channel_name(value):
    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = value.encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value
    ).strip("-")

    return (
        value
        or "user"
    )[:45]


def safe_code_text(value):
    return str(
        value
    ).replace(
        "```",
        "~~~"
    ).strip()


def get_channel_mention(channel_id):
    if not channel_id:
        return "`CHANNEL NOT SET`"

    return (
        f"<{chr(35)}"
        f"{channel_id}>"
    )


def get_asset_name(ticket):
    if ticket.get("system") == "halal":
        coin = halal_coins().get(str(ticket.get("type") or ""), {})
        return coin.get("short") or "CRYPTO"

    return (
        "LTC"
        if ticket["type"] == "ltc"
        else "USDT"
    )


def get_asset_long_name(ticket):
    return (
        "Litecoin"
        if ticket["type"] == "ltc"
        else "USDT [BEP-20]"
    )


def get_asset_emoji(ticket):
    return (
        LTC_EMOJI
        if ticket["type"] == "ltc"
        else USDT_EMOJI
    )


def get_deposit_address(ticket):
    return (
        LTC_DEPOSIT_ADDRESS
        if ticket["type"] == "ltc"
        else USDT_DEPOSIT_ADDRESS
    )


def confirmations_required(ticket):
    if ticket.get("system") == "halal":
        try:
            coin = halal_coins().get(str(ticket.get("type") or ""), {})
            return int(coin.get("confirmations") or HALAL_CONFIRMATIONS)
        except Exception:
            return HALAL_CONFIRMATIONS

    return (
        LTC_CONFIRMATIONS_REQUIRED
        if ticket["type"] == "ltc"
        else USDT_CONFIRMATIONS_REQUIRED
    )


def money(value):
    amount = Decimal(
        str(value)
    ).quantize(
        Decimal("0.01")
    )

    return f"${amount:,.2f}"


def money_compact(value):
    amount = Decimal(
        str(value or "0")
    ).quantize(
        Decimal("0.01")
    )

    if amount == amount.to_integral_value():
        return f"${amount:,.0f}"

    return f"${amount:,.2f}"


def parse_money_amount(value, allow_zero=True):
    raw = (
        str(value)
        .replace("$", "")
        .replace(",", "")
        .strip()
    )

    try:
        amount = Decimal(raw)
    except InvalidOperation:
        return None

    if not amount.is_finite() or amount < 0:
        return None

    if amount == 0 and not allow_zero:
        return None

    return amount.quantize(Decimal("0.01"))


def parse_non_negative_int(value):
    raw = (
        str(value)
        .replace(",", "")
        .strip()
    )

    try:
        number = int(raw)
    except (TypeError, ValueError):
        return None

    if number < 0:
        return None

    return number


def default_user_stats():
    return {
        "deals_completed": 0,
        "deals_started": 0,
        "total_usd_value": "0.00",
        "biggest_deal": "0.00"
    }


def get_user_stats(user_id):
    stats = DATA.setdefault("stats", {}).get(str(user_id))

    if not isinstance(stats, dict):
        stats = default_user_stats()
        DATA["stats"][str(user_id)] = stats
        return stats

    stats.setdefault("deals_completed", 0)
    stats.setdefault("deals_started", 0)
    stats.setdefault("total_usd_value", "0.00")
    stats.setdefault("biggest_deal", "0.00")
    return stats


def rank_roles():
    items = DATA.setdefault("rank_roles", [])
    cleaned = []
    seen = set()

    if not isinstance(items, list):
        items = []

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            role_id = int(item.get("role_id"))
            amount = Decimal(
                str(
                    item.get("amount")
                    or item.get("threshold")
                    or "0"
                )
            )
        except (TypeError, ValueError, InvalidOperation):
            continue

        if role_id <= 0 or not amount.is_finite() or amount < 0:
            continue

        if role_id in seen:
            cleaned = [
                entry for entry in cleaned
                if int(entry["role_id"]) != role_id
            ]
        else:
            seen.add(role_id)

        cleaned.append({
            "role_id": str(role_id),
            "amount": str(amount.quantize(Decimal("0.01")))
        })

    cleaned.sort(key=lambda entry: Decimal(entry["amount"]))
    DATA["rank_roles"] = cleaned
    return cleaned


def rank_progress(total):
    total = Decimal(str(total or "0"))
    current = None
    nxt = None

    for item in rank_roles():
        amount = Decimal(item["amount"])
        if total >= amount:
            current = item
        elif nxt is None:
            nxt = item
            break

    return current, nxt


def rank_line(label, item):
    if item is None:
        return f"**{label}:** None"

    return (
        f"**{label}:** <@&{item['role_id']}> "
        f"({money_compact(item['amount'])})"
    )


def stats_embed(user, guild=None):
    if guild is not None:
        try:
            if guild_mode(jaces_guild_state(guild.id)) == "halal":
                return halal_stats_embed(user)
        except Exception:
            pass

    data = get_user_stats(user.id)
    current, nxt = rank_progress(data.get("total_usd_value", "0"))

    embed = discord.Embed(
        title=user.name,
        description=(
            f"{rank_line('Current Rank', current)}\n"
            f"{rank_line('Next Rank', nxt)}"
        ),
        colour=COLOR_NEUTRAL
    )

    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(
        name="Deals Completed",
        value=str(int(data.get("deals_completed", 0))),
        inline=False
    )
    embed.add_field(
        name="Total USD Value",
        value=money(data.get("total_usd_value", "0")),
        inline=True
    )
    embed.add_field(
        name="Biggest Deal",
        value=money(data.get("biggest_deal", "0")),
        inline=True
    )

    return embed


async def sync_rank_roles(guild, user_id):
    if guild is None or user_id is None:
        return []

    try:
        member_id = int(user_id)
    except (TypeError, ValueError):
        return []

    member = guild.get_member(member_id)
    if member is None:
        try:
            member = await guild.fetch_member(member_id)
        except discord.HTTPException:
            return []

    stats = get_user_stats(member_id)
    total = Decimal(str(stats.get("total_usd_value", "0") or "0"))
    configured = rank_roles()
    earned_ids = {
        int(item["role_id"])
        for item in configured
        if total >= Decimal(item["amount"])
    }
    configured_ids = {int(item["role_id"]) for item in configured}
    me = guild.me
    notes = []

    for role_id in configured_ids:
        role = guild.get_role(role_id)
        if role is None or role.is_default() or role.managed:
            continue

        if me is not None and role >= me.top_role:
            notes.append(f"{role.name} is above the bot")
            continue

        should_have = role_id in earned_ids
        has_role = role in member.roles

        try:
            if should_have and not has_role:
                await member.add_roles(role, reason="Reached rank")
                notes.append(f"gave {role.name}")
            elif has_role and not should_have:
                await member.remove_roles(role, reason="Below rank")
                notes.append(f"removed {role.name}")
        except discord.HTTPException as error:
            notes.append(f"{role.name} failed: {error}")

    return notes


async def sync_all_rank_roles(guild):
    notes = []
    for user_id in list(DATA.get("stats", {})):
        notes.extend(await sync_rank_roles(guild, user_id))
    return notes


def crypto_amount_text(
    ticket,
    value=None
):
    if ticket.get("system") == "halal":
        return halal_amount_text(ticket, value)

    if value is None:
        value = ticket.get(
            "crypto_amount",
            "0"
        )

    amount = Decimal(
        str(value)
    )

    if ticket["type"] == "ltc":
        return (
            f"{amount.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN):f}"
            .rstrip("0")
            .rstrip(".")
        )

    return (
        f"{amount.quantize(Decimal('0.01')):f}"
    )


def required_crypto_display(ticket):
    amount = Decimal(
        str(
            ticket.get(
                "crypto_amount",
                "0"
            )
        )
    )

    if ticket[
        "type"
    ] == "ltc":
        return (
            f"{amount.quantize(Decimal('0.00001'), rounding=ROUND_DOWN):f}"
        )

    return (
        f"{amount.quantize(Decimal('0.01')):f}"
    )


def required_crypto_decimal(ticket):
    return Decimal(
        str(
            ticket.get(
                "crypto_amount",
                "0"
            )
        )
    )


def parse_positive_decimal(value):
    raw = (
        str(value)
        .replace(
            "$",
            ""
        )
        .replace(
            ",",
            ""
        )
        .strip()
    )

    try:
        amount = Decimal(
            raw
        )

    except InvalidOperation:
        return None

    if (
        not amount.is_finite()
        or amount <= 0
    ):
        return None

    return amount


def normalize_txid(txid):
    return (
        str(txid)
        .strip()
        .lower()
    )


def parse_chain_timestamp(value):
    if value is None or value == "":
        return 0

    if isinstance(value, bool):
        return 0

    if isinstance(value, (int, float)):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return 0

        if number > 10_000_000_000:
            number //= 1000

        return number

    text = str(value).strip()
    if not text:
        return 0

    if text.isdigit():
        return parse_chain_timestamp(int(text))

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        return int(
            datetime.fromisoformat(text).timestamp()
        )
    except (TypeError, ValueError):
        return 0


def payment_started_unix(ticket):
    try:
        return int(
            ticket.get(
                "payment_started_at"
            ) or 0
        )
    except (TypeError, ValueError):
        return 0


def chain_event_is_before_payment(ticket, *values):
    started = payment_started_unix(ticket)
    if started <= 0:
        return False

    for value in values:
        timestamp = parse_chain_timestamp(value)
        if timestamp > 0:
            return timestamp < started

    return False


def is_manual_reference(txid):
    return (
        bool(txid)
        and str(txid)
        .upper()
        .startswith(
            "MANUAL-"
        )
    )


def is_simulation_reference(txid):
    return (
        bool(txid)
        and str(txid)
        .upper()
        .startswith(
            "SIMULATION-"
        )
    )


def tx_link(
    txid,
    asset
):
    asset = str(asset or "").lower()

    if asset in {"ltc", "btc"}:
        return (
            "https://live.blockcypher.com/"
            f"{asset}/tx/{txid}/"
        )

    if asset in {"eth", "usdt_erc20", "usdc_erc20"}:
        return (
            "https://etherscan.io/"
            f"tx/{txid}"
        )

    if asset in {"sol", "usdt_sol", "usdc_sol"}:
        return (
            "https://solscan.io/"
            f"tx/{txid}"
        )

    return (
        "https://bscscan.com/"
        f"tx/{txid}"
    )


def short_txid(txid):
    txid = str(
        txid
    )

    if len(txid) <= 23:
        return txid

    return (
        f"{txid[:10]}..."
        f"{txid[-10:]}"
    )


def tx_display(
    ticket,
    txid
):
    if not txid:
        return "`N/A`"

    if (
        ticket.get(
            "manual_deposit_override"
        )
        and txid
        == ticket.get(
            "deposit_txid"
        )
    ):
        return f"`{txid}`"

    if (
        is_manual_reference(txid)
        or is_simulation_reference(txid)
    ):
        return f"`{txid}`"

    return (
        f"[`{short_txid(txid)}`]"
        f"({tx_link(txid, ticket['type'])})"
    )


def is_admin(member):
    return (
        isinstance(
            member,
            discord.Member
        )
        and member.guild_permissions.administrator
    )


def is_ticket_party(
    interaction,
    ticket
):
    return interaction.user.id in {
        int(
            ticket[
                "opener_id"
            ]
        ),
        int(
            ticket[
                "trader_id"
            ]
        )
    }


def is_sender(
    interaction,
    ticket
):
    sender_id = ticket.get(
        "sender_id"
    )

    return (
        sender_id is not None
        and interaction.user.id
        == int(sender_id)
    )


def is_receiver(
    interaction,
    ticket
):
    receiver_id = ticket.get(
        "receiver_id"
    )

    return (
        receiver_id is not None
        and interaction.user.id
        == int(receiver_id)
    )


async def claim_deposit_txid(
    ticket,
    txid
):
    if (
        not txid
        or is_manual_reference(
            txid
        )
    ):
        return True

    normalized = normalize_txid(
        txid
    )

    async with DATA_LOCK:
        existing = DATA[
            "claimed_deposit_txids"
        ].get(
            normalized
        )

        if (
            existing is not None
            and int(existing)
            != int(
                ticket[
                    "number"
                ]
            )
        ):
            return False

        DATA[
            "claimed_deposit_txids"
        ][
            normalized
        ] = int(
            ticket[
                "number"
            ]
        )

        save_data_now()

    return True


def cleaned_secret(value):
    return str(value or "").strip()


def demo_blockcypher_token():
    return cleaned_secret(BLOCKCYPHER_TOKEN)


def ticket_blockcypher_token():
    return (
        cleaned_secret(TICKET_BLOCKCYPHER_TOKEN)
        or demo_blockcypher_token()
    )


def demo_etherscan_key():
    return cleaned_secret(ETHERSCAN_API_KEY)


def ticket_etherscan_key():
    return (
        cleaned_secret(TICKET_ETHERSCAN_API_KEY)
        or demo_etherscan_key()
    )


def chain_keys_shared():
    return not cleaned_secret(TICKET_BLOCKCYPHER_TOKEN)


def tickets_need_ltc_chain():
    if BASELINE_IN_PROGRESS > 0:
        return True

    for ticket in DATA.get("tickets", {}).values():
        if not isinstance(ticket, dict):
            continue

        if ticket.get("type") != "ltc":
            continue

        if ticket.get("status") in {
            "waiting_deposit",
            "deposit_unconfirmed"
        }:
            return True

    return False


def http_retry_after(response):
    headers = getattr(response, "headers", None) or {}
    raw = None
    if hasattr(headers, "get"):
        raw = headers.get("Retry-After") or headers.get("retry-after")

    try:
        return max(15.0, float(raw))
    except (TypeError, ValueError):
        return 60.0


def is_rate_limit_error(status, error_text):
    if status == 429:
        return True

    text = str(error_text or "").lower()
    return (
        "rate limit" in text
        or "limit exceeded" in text
        or "too many requests" in text
    )


async def cached_ticket_chain_get(key, fetcher, ttl=12):
    async with TICKET_CHAIN_CACHE_LOCK:
        now = time.monotonic()
        entry = TICKET_CHAIN_CACHE.get(key)
        if (
            entry is not None
            and now - entry[0] < entry[2]
        ):
            return entry[1]

        data = await fetcher()
        TICKET_CHAIN_CACHE[key] = (
            now,
            data,
            float(ttl) if data is not None else 5.0
        )
        return data


async def http_get_json(
    url,
    params=None,
    headers=None,
    attempts=3,
    timeout=15,
    wait_on_rate_limit=False
):
    last_error = None
    attempt = 0

    while attempt < attempts:
        try:
            async with bot.session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(
                    total=timeout
                )
            ) as response:
                status = response.status
                if status == 200:
                    data = await response.json()
                    error_text = ""
                    if isinstance(data, dict):
                        error_text = str(data.get("error") or "")

                    if error_text:
                        last_error = RuntimeError(error_text[:300])
                        if (
                            wait_on_rate_limit
                            and is_rate_limit_error(status, error_text)
                        ):
                            wait = http_retry_after(response)
                            log_action(
                                "chain_rate_limited",
                                url=url,
                                retry_in=int(wait)
                            )
                            await asyncio.sleep(wait)
                            continue
                    else:
                        return data
                else:
                    body = await response.text()
                    last_error = RuntimeError(
                        f"HTTP {status}: {body[:300]}"
                    )
                    if (
                        wait_on_rate_limit
                        and is_rate_limit_error(status, body)
                    ):
                        wait = http_retry_after(response)
                        log_action(
                            "chain_rate_limited",
                            url=url,
                            retry_in=int(wait)
                        )
                        await asyncio.sleep(wait)
                        continue

        except Exception as error:
            last_error = error

        attempt += 1

        if attempt < attempts:
            await asyncio.sleep(
                1.5 * attempt
            )

    if last_error:
        logger.warning(
            "HTTP request failed for %s: %s",
            url,
            last_error
        )

    return None


async def http_post_json(url, payload, timeout=20, wait_on_rate_limit=True):
    last_error = None
    attempt = 0
    attempts = 3

    while attempt < attempts:
        try:
            async with bot.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                status = response.status
                if status == 200:
                    return await response.json()

                body = await response.text()
                last_error = RuntimeError(f"HTTP {status}: {body[:300]}")
                if wait_on_rate_limit and is_rate_limit_error(status, body):
                    wait = http_retry_after(response)
                    log_action("chain_rate_limited", url=url, retry_in=int(wait))
                    await asyncio.sleep(wait)
                    continue
        except Exception as error:
            last_error = error

        attempt += 1
        if attempt < attempts:
            await asyncio.sleep(1.5 * attempt)

    if last_error:
        logger.warning("HTTP POST failed for %s: %s", url, last_error)
    return None


async def fetch_ltc_chain_overview():
    url = (
        "https://api.blockcypher.com/"
        "v1/ltc/main"
    )

    params = {}

    token = demo_blockcypher_token()
    if token:
        params[
            "token"
        ] = token

    data = await http_get_json(
        url,
        params=params
    )

    if not isinstance(
        data,
        dict
    ):
        return None

    try:
        height = int(
            data.get(
                "height",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):
        return None

    if height <= 0:
        return None

    return data


async def fetch_ltc_block(
    height,
    limit=500
):
    url = (
        "https://api.blockcypher.com/"
        f"v1/ltc/main/blocks/{int(height)}"
    )

    params = {
        "txstart": 0,
        "limit": min(
            max(
                int(limit),
                1
            ),
            500
        )
    }

    token = demo_blockcypher_token()
    if token:
        params[
            "token"
        ] = token

    data = await http_get_json(
        url,
        params=params
    )

    if not isinstance(
        data,
        dict
    ):
        return None

    return data


async def fetch_random_confirmed_ltc_sample():
    overview = await fetch_ltc_chain_overview()

    if overview is None:
        return None

    tip_height = int(
        overview[
            "height"
        ]
    )

    highest = (
        tip_height
        - max(
            DEMO_MIN_CONFIRMATIONS + 2,
            8
        )
    )

    lowest = max(
        1,
        highest
        - max(
            DEMO_RECENT_BLOCK_WINDOW,
            50
        )
    )

    if highest <= lowest:
        return None

    for _ in range(8):
        block_height = random.randint(
            lowest,
            highest
        )

        block = await fetch_ltc_block(
            block_height,
            limit=500
        )

        if block is None:
            continue

        txids = [
            str(value)
            for value
            in block.get(
                "txids",
                []
            )
            if value
        ]

        if len(txids) > 1:
            txids = txids[1:]

        if not txids:
            continue

        random.shuffle(
            txids
        )

        for txid in txids[:20]:
            tx = await fetch_ltc_transaction(
                txid,
                token=demo_blockcypher_token()
            )

            if not isinstance(
                tx,
                dict
            ):
                continue

            try:
                confirmations = int(
                    tx.get(
                        "confirmations",
                        0
                    )
                )

                total_satoshi = int(
                    tx.get(
                        "total",
                        0
                    )
                )

            except (
                TypeError,
                ValueError
            ):
                continue

            if (
                confirmations
                < DEMO_MIN_CONFIRMATIONS
                or total_satoshi <= 0
            ):
                continue

            return {
                "txid": txid,
                "confirmations": confirmations,
                "amount_ltc": (
                    Decimal(
                        total_satoshi
                    )
                    / Decimal(
                        "100000000"
                    )
                ),
                "block_height": block_height
            }

    return None


def demo_completed_embed(
    sample,
    ltc_price
):
    amount = Decimal(
        str(
            sample[
                "amount_ltc"
            ]
        )
    )

    amount_text = (
        f"{amount.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN):f}"
        .rstrip("0")
        .rstrip(".")
    )

    if not amount_text:
        amount_text = "0"

    usd_value = (
        (
            amount
            * ltc_price
        ).quantize(
            Decimal(
                "0.01"
            )
        )
        if ltc_price
        and ltc_price > 0
        else Decimal(
            "0.00"
        )
    )

    txid = str(
        sample[
            "txid"
        ]
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(LTC_EMOJI)}"
            "• **Trade Completed**\n\n"
            f"`{amount_text}` LTC "
            f"({money(usd_value)} USD)"
        ),
        colour=COLOR_NEUTRAL,
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="Sender",
        value="`Anonymous`",
        inline=True
    )

    embed.add_field(
        name="Receiver",
        value="`Anonymous`",
        inline=True
    )

    embed.add_field(
        name="Transaction ID",
        value=(
            f"[`{short_txid(txid)}`]"
            f"({tx_link(txid, 'ltc')})"
        ),
        inline=False
    )

    return embed


def demo_halal_completed_layout(sample, ltc_price):
    amount = Decimal(str(sample["amount_ltc"]))
    amount_text = (
        f"{amount.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN):f}"
        .rstrip("0")
        .rstrip(".")
    )
    if not amount_text:
        amount_text = "0"

    usd_value = (
        (amount * ltc_price).quantize(Decimal("0.01"))
        if ltc_price and ltc_price > 0
        else Decimal("0.00")
    )
    return build_halal_complete_layout(
        title="Litecoin Deal Complete",
        amount=amount_text,
        short="LTC",
        usd=usd_value,
        sender="`Anonymous`",
        receiver="`Anonymous`",
        txid=str(sample["txid"]),
        asset="ltc",
        explorer="BlockCypher",
        emoji=halal_emoji_or(HALAL_LTC_EMOJI, LTC_EMOJI or "Ł")
    )


async def resolve_demo_channel(channel_id):
    if not channel_id:
        return None
    try:
        channel_id = int(channel_id)
    except (TypeError, ValueError):
        return None
    if channel_id <= 0:
        return None
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.HTTPException:
            return None
    if not hasattr(channel, "send"):
        return None
    return channel


async def send_demo_completed_activity():
    if not DEMO_ACTIVITY_ENABLED:
        return False

    if chain_keys_shared() and tickets_need_ltc_chain():
        log_action(
            "demo_activity_skipped_for_tickets"
        )
        return False

    channel = await resolve_demo_channel(
        DEMO_COMPLETED_TRANSACTION_CHANNEL
    )
    halal_channel = await resolve_demo_channel(
        DEMO_HALAL_COMPLETED_CHANNEL
    )
    if halal_channel is None:
        halal_channel = channel

    if channel is None and halal_channel is None:
        logger.error(
            "Demo activity channel lookup failed | "
            "channel_id=%s | halal_channel_id=%s",
            DEMO_COMPLETED_TRANSACTION_CHANNEL,
            DEMO_HALAL_COMPLETED_CHANNEL
        )
        return False

    sample = await fetch_random_confirmed_ltc_sample()

    if sample is None:
        logger.warning(
            "Demo activity skipped because a confirmed "
            "BlockCypher LTC sample could not be found"
        )

        return False

    ltc_price = await get_ltc_price()

    if ltc_price is None:
        ltc_price = Decimal(
            "0"
        )

    sent = False

    if channel is not None:
        try:
            await channel.send(
                embed=demo_completed_embed(
                    sample,
                    ltc_price
                )
            )
            sent = True
        except discord.HTTPException as exc:
            logger.error(
                "Demo activity send failed | "
                "channel_id=%s | error=%s",
                DEMO_COMPLETED_TRANSACTION_CHANNEL,
                exc
            )

    if halal_channel is not None:
        try:
            await halal_channel.send(
                view=demo_halal_completed_layout(
                    sample,
                    ltc_price
                )
            )
            sent = True
        except discord.HTTPException as exc:
            logger.error(
                "Demo Halal activity send failed | "
                "channel_id=%s | error=%s",
                DEMO_HALAL_COMPLETED_CHANNEL,
                exc
            )

    if not sent:
        return False

    log_action(
        "demo_completed_activity_sent",
        channel_id=DEMO_COMPLETED_TRANSACTION_CHANNEL,
        halal_channel_id=DEMO_HALAL_COMPLETED_CHANNEL,
        txid=short_txid(
            sample[
                "txid"
            ]
        ),
        confirmations=sample[
            "confirmations"
        ],
        amount_ltc=sample[
            "amount_ltc"
        ],
        block_height=sample[
            "block_height"
        ]
    )

    return True


async def demo_activity_loop():
    try:
        await bot.wait_until_ready()

        while (
            not bot.is_closed()
            and DEMO_ACTIVITY_ENABLED
        ):
            jitter = random.randint(
                DEMO_JITTER_MIN_SECONDS,
                DEMO_JITTER_MAX_SECONDS
            )

            delay = (
                DEMO_BASE_INTERVAL_SECONDS
                + jitter
            )

            log_action(
                "demo_activity_scheduled",
                base_seconds=DEMO_BASE_INTERVAL_SECONDS,
                jitter_seconds=jitter,
                next_run_seconds=delay
            )

            await asyncio.sleep(
                delay
            )

            if (
                bot.is_closed()
                or not DEMO_ACTIVITY_ENABLED
            ):
                return

            try:
                await send_demo_completed_activity()

            except asyncio.CancelledError:
                raise

            except Exception:
                logger.exception(
                    "Unhandled demo activity error"
                )

    except asyncio.CancelledError:
        log_action(
            "demo_activity_stopped"
        )

        return


def ensure_demo_activity_task():
    global DEMO_ACTIVITY_TASK

    if not DEMO_ACTIVITY_ENABLED:
        return

    if (
        DEMO_ACTIVITY_TASK is not None
        and not DEMO_ACTIVITY_TASK.done()
    ):
        return

    DEMO_ACTIVITY_TASK = asyncio.create_task(
        demo_activity_loop()
    )

    log_action(
        "demo_activity_started",
        channel_id=DEMO_COMPLETED_TRANSACTION_CHANNEL,
        base_seconds=DEMO_BASE_INTERVAL_SECONDS,
        jitter_min_seconds=DEMO_JITTER_MIN_SECONDS,
        jitter_max_seconds=DEMO_JITTER_MAX_SECONDS
    )


async def get_ltc_price():
    data = await http_get_json(
        COINBASE_LTC_PRICE_URL,
        headers={
            "Accept": "application/json"
        },
        attempts=3,
        timeout=10
    )

    if not isinstance(
        data,
        dict
    ):
        logger.warning(
            "Coinbase LTC price response was not a JSON object"
        )

        return None

    try:
        price_data = data[
            "data"
        ]

        price = Decimal(
            str(
                price_data[
                    "amount"
                ]
            )
        )

        currency = str(
            price_data.get(
                "currency",
                "USD"
            )
        ).upper()

        if currency != "USD":
            logger.warning(
                "Coinbase LTC price returned unexpected "
                "currency | currency=%s",
                currency
            )

            return None

        if (
            not price.is_finite()
            or price <= 0
        ):
            logger.warning(
                "Coinbase LTC price returned invalid "
                "amount | amount=%s",
                price
            )

            return None

        log_action(
            "ltc_price_fetched",
            provider="coinbase",
            pair="LTC-USD",
            price=price
        )

        return price

    except (
        KeyError,
        TypeError,
        ValueError,
        InvalidOperation
    ):
        logger.exception(
            "Failed to parse Coinbase LTC price response"
        )

        return None


async def fetch_ltc_transactions(address, token=None):
    url = (
        "https://api.blockcypher.com/"
        f"v1/ltc/main/addrs/{address}/full"
    )

    params = {
        "limit": 50
    }

    if token is None:
        token = ticket_blockcypher_token()

    if token:
        params[
            "token"
        ] = token

    data = await http_get_json(
        url,
        params=params,
        timeout=30,
        wait_on_rate_limit=True
    )

    if data is None:
        return None

    txs = data.get(
        "txs",
        []
    )

    return (
        txs
        if isinstance(
            txs,
            list
        )
        else None
    )


async def fetch_ltc_transaction(txid, token=None):
    if token is None:
        token = ticket_blockcypher_token()

    async def load():
        url = (
            "https://api.blockcypher.com/"
            f"v1/ltc/main/txs/{txid}"
        )
        params = {}
        if token:
            params["token"] = token
        return await http_get_json(
            url,
            params=params,
            wait_on_rate_limit=True
        )

    return await cached_ticket_chain_get(
        f"tx:{txid}:{token}",
        load,
        ttl=12
    )


def ltc_received_by_tx(
    tx,
    address
):
    total = 0

    for output in tx.get(
        "outputs",
        []
    ):
        addresses = (
            output.get(
                "addresses"
            )
            or []
        )

        if address in addresses:
            total += int(
                output.get(
                    "value",
                    0
                )
            )

    return total


async def fetch_usdt_transfers(address, api_key=None):
    if api_key is None:
        api_key = ticket_etherscan_key()

    if not api_key:
        return None

    url = (
        "https://api.etherscan.io/"
        "v2/api"
    )

    params = {
        "chainid": BSC_CHAIN_ID,
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDT_BEP20_CONTRACT,
        "address": address,
        "page": 1,
        "offset": 1000,
        "sort": "desc",
        "apikey": api_key
    }

    data = await http_get_json(
        url,
        params=params,
        wait_on_rate_limit=True
    )

    if data is None:
        return None

    status = str(
        data.get(
            "status",
            ""
        )
    )

    message = str(
        data.get(
            "message",
            ""
        )
    ).lower()

    result = data.get(
        "result"
    )

    if (
        status == "0"
        and (
            "no transactions"
            in message
            or (
                isinstance(
                    result,
                    str
                )
                and "no transactions"
                in result.lower()
            )
        )
    ):
        return []

    if status != "1":
        logger.warning(
            "Etherscan error: %s",
            data
        )

        return None

    return (
        result
        if isinstance(
            result,
            list
        )
        else None
    )


def valid_usdt_transfer(
    transfer,
    destination
):
    recipient = str(
        transfer.get(
            "to",
            ""
        )
    ).lower()

    contract = str(
        transfer.get(
            "contractAddress",
            ""
        )
    ).lower()

    return (
        recipient
        == destination.lower()
        and contract
        == USDT_BEP20_CONTRACT.lower()
    )


def parse_usdt_transfer(transfer):
    try:
        decimals = int(
            transfer.get(
                "tokenDecimal",
                "18"
            )
        )

        raw_value = Decimal(
            str(
                transfer.get(
                    "value",
                    "0"
                )
            )
        )

        amount = (
            raw_value
            / (
                Decimal(10)
                ** decimals
            )
        )

        confirmations = int(
            transfer.get(
                "confirmations",
                "0"
            )
        )

        return (
            amount,
            confirmations
        )

    except Exception:
        return (
            Decimal("0"),
            0
        )


async def fetch_ltc_address_data(address, token=None):
    url = (
        "https://api.blockcypher.com/"
        f"v1/ltc/main/addrs/{address}"
    )

    params = {
        "limit": 50
    }

    if token is None:
        token = ticket_blockcypher_token()

    if token:
        params[
            "token"
        ] = token

    async def load():
        return await http_get_json(
            url,
            params=params,
            timeout=20,
            wait_on_rate_limit=True
        )

    data = await cached_ticket_chain_get(
        f"addr:{address}:{token}",
        load,
        ttl=12
    )

    if not isinstance(data, dict):
        return None

    return data


async def fetch_ltc_address_txids(address, token=None):
    data = await fetch_ltc_address_data(
        address,
        token=token
    )

    if not isinstance(data, dict):
        return None

    hashes = []
    for key in ("txrefs", "unconfirmed_txrefs"):
        items = data.get(key) or []
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            txid = item.get("tx_hash") or item.get("hash")
            if txid:
                hashes.append(txid)

    try:
        known = int(data.get("n_tx") or 0) + int(
            data.get("unconfirmed_n_tx") or 0
        )
    except (TypeError, ValueError):
        known = 0

    if not hashes and known > 0:
        return None

    return hashes


def ltc_txids_before_payment(ticket, txs=None, address_data=None):
    started = payment_started_unix(ticket)
    collected = []
    seen = set()

    def add_txid(txid, *times):
        if not txid:
            return

        normalized = normalize_txid(txid)
        if normalized in seen:
            return

        if started:
            timestamps = [
                parse_chain_timestamp(value)
                for value in times
                if value is not None and value != ""
            ]
            timestamps = [
                value for value in timestamps
                if value > 0
            ]
            if not timestamps or min(timestamps) >= started:
                return

        seen.add(normalized)
        collected.append(normalized)

    if isinstance(address_data, dict):
        for item in address_data.get("txrefs") or []:
            if not isinstance(item, dict):
                continue

            add_txid(
                item.get("tx_hash") or item.get("hash"),
                item.get("confirmed"),
                item.get("received")
            )

    if isinstance(txs, list):
        for tx in txs:
            if not isinstance(tx, dict):
                continue

            add_txid(
                tx.get("hash"),
                tx.get("confirmed"),
                tx.get("received")
            )

    return collected


async def create_baseline_once(ticket):
    if is_halal_ticket(ticket):
        return await create_halal_baseline_once(ticket)

    if ticket[
        "type"
    ] == "ltc":

        if not AUTO_MONITOR_LTC:
            ticket[
                "baseline_txids"
            ] = []

            return True

        address = ticket[
            "deposit_address"
        ]
        address_data = await fetch_ltc_address_data(
            address
        )

        if address_data is None:
            txs = await fetch_ltc_transactions(
                address
            )

            if txs is None:
                return False

            ticket[
                "baseline_txids"
            ] = ltc_txids_before_payment(
                ticket,
                txs=txs
            )

            return True

        ticket[
            "baseline_txids"
        ] = ltc_txids_before_payment(
            ticket,
            address_data=address_data
        )

        return True

    if not AUTO_MONITOR_USDT:
        ticket[
            "baseline_txids"
        ] = []

        return True

    transfers = await fetch_usdt_transfers(
        ticket[
            "deposit_address"
        ]
    )

    if transfers is None:
        return False

    started = payment_started_unix(ticket)
    baseline = []
    for item in transfers:
        txid = item.get(
            "hash"
        )
        if not txid:
            continue

        if started:
            timestamp = parse_chain_timestamp(
                item.get("timeStamp")
            )
            if timestamp >= started:
                continue

        baseline.append(
            normalize_txid(txid)
        )

    ticket[
        "baseline_txids"
    ] = baseline

    return True


async def create_baseline(ticket):
    global BASELINE_IN_PROGRESS

    BASELINE_IN_PROGRESS += 1
    try:
        while True:
            if get_ticket(ticket.get("channel_id")) is None:
                return False

            if await create_baseline_once(ticket):
                return True

            log_action(
                "baseline_retry",
                ticket=ticket.get("number"),
                asset=get_asset_name(ticket),
                retry_in=15
            )
            await asyncio.sleep(15)
    finally:
        BASELINE_IN_PROGRESS = max(0, BASELINE_IN_PROGRESS - 1)


async def run_baseline_task(ticket):
    key = str(
        ticket.get("channel_id")
    )

    try:
        ok = await create_baseline(ticket)
        current = get_ticket(
            ticket.get("channel_id")
        )

        if ok and current is not None:
            current["baseline_ready"] = True
            await save_data()
            log_action(
                "baseline_ready",
                ticket=current.get("number"),
                asset=get_asset_name(current),
                known=len(current.get("baseline_txids") or [])
            )
    except asyncio.CancelledError:
        return
    except Exception:
        logger.exception(
            "Baseline task failed for ticket %s",
            ticket.get("number")
        )
    finally:
        running = BASELINE_TASKS.get(key)
        if running is asyncio.current_task():
            BASELINE_TASKS.pop(key, None)


def start_baseline(ticket):
    channel_id = ticket.get("channel_id")
    if channel_id is None:
        return

    key = str(channel_id)
    existing = BASELINE_TASKS.get(key)
    if existing is not None and not existing.done():
        return

    BASELINE_TASKS[key] = asyncio.create_task(
        run_baseline_task(ticket)
    )


async def resolve_guild_member(guild, user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    if user_id <= 0 or guild is None:
        return None

    member = guild.get_member(user_id)
    if member is not None:
        return member

    try:
        return await guild.fetch_member(user_id)
    except discord.NotFound:
        return None
    except discord.HTTPException:
        pass

    try:
        found = await guild.query_members(user_ids=[user_id], limit=1)
        if found:
            return found[0]
    except (TypeError, ValueError, discord.HTTPException):
        pass

    return None


async def resolve_trader(
    guild,
    value
):
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = re.sub(r"[\u200b-\u200d\ufeff]", "", value).strip()
    if not value or guild is None:
        return None

    mention = re.fullmatch(r"<@!?(\d{17,20})>", value)
    if mention:
        return await resolve_guild_member(guild, mention.group(1))

    digits = re.fullmatch(r"\d{17,20}", value)
    if digits:
        return await resolve_guild_member(guild, digits.group(0))

    lowered = value.lower().lstrip("@")
    names = lambda member: {
        member.name.lower(),
        member.display_name.lower(),
        str(member).lower(),
        str(getattr(member, "global_name", "") or "").lower()
    }
    for member in guild.members:
        if lowered in names(member):
            return member

    if len(lowered) >= 2:
        try:
            found = await guild.query_members(query=lowered[:32], limit=5)
        except (TypeError, discord.HTTPException):
            found = []
        for member in found or []:
            if lowered in names(member):
                return member

    return None

def extract_user_ids(text):
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)
    found = []
    seen = set()
    for group in re.findall(r"<@!?(\d{17,20})>", text):
        uid = int(group)
        if uid not in seen:
            seen.add(uid)
            found.append(uid)
    raw = re.findall(r"\d{17,20}", text)
    raw.sort(key=len, reverse=True)
    for group in raw:
        uid = int(group)
        if uid not in seen:
            seen.add(uid)
            found.append(uid)
    return found


async def fetch_message(
    channel,
    message_id
):
    if not message_id:
        return None

    try:
        return await channel.fetch_message(
            int(
                message_id
            )
        )

    except discord.HTTPException:
        return None


async def get_configured_channel(
    guild,
    channel_id
):
    channel = guild.get_channel(
        channel_id
    )

    if channel is not None:
        return channel

    try:
        return await bot.fetch_channel(
            channel_id
        )

    except discord.HTTPException:
        return None


def cached_ticket_channel(
    guild,
    channel_id
):
    if channel_id is None:
        return None

    channel_id = int(
        channel_id
    )

    channel = bot.get_channel(
        channel_id
    )

    if channel is not None:
        return channel

    if guild is None:
        return None

    channel = guild.get_channel(
        channel_id
    )

    if channel is not None:
        return channel

    return guild.get_thread(
        channel_id
    )


async def resolve_ticket_channel(
    ticket
):
    channel_id = int(
        ticket[
            "channel_id"
        ]
    )

    guild = bot.get_guild(
        int(
            ticket[
                "guild_id"
            ]
        )
    )

    channel = cached_ticket_channel(
        guild,
        channel_id
    )

    if channel is None:
        try:
            channel = await bot.fetch_channel(
                channel_id
            )

        except discord.HTTPException:
            return None

    return channel


async def get_ticket_category(
    guild
):
    if guild is None:
        return None

    configured = guild.get_channel(
        TICKET_CATEGORY
    )

    if configured is None:
        try:
            configured = await bot.fetch_channel(
                TICKET_CATEGORY
            )

        except discord.HTTPException:
            return None

    if isinstance(
        configured,
        discord.CategoryChannel
    ):
        return configured

    category = getattr(
        configured,
        "category",
        None
    )

    if isinstance(
        category,
        discord.CategoryChannel
    ):
        return category

    return None


def ticket_member_overwrite(
    can_chat
):
    return discord.PermissionOverwrite(
        view_channel=True,
        read_message_history=True,
        send_messages=can_chat,
        add_reactions=can_chat,
        attach_files=can_chat,
        embed_links=can_chat,
        send_messages_in_threads=can_chat,
        create_public_threads=False,
        create_private_threads=False
    )


def ticket_channel_overwrites(
    guild,
    opener,
    trader,
    can_chat=False
):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            send_messages=False
        )
    }

    me = guild.me
    if me is not None:
        overwrites[me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True
        )

    if opener is not None:
        overwrites[opener] = ticket_member_overwrite(
            can_chat
        )

    if (
        trader is not None
        and (
            opener is None
            or trader.id != opener.id
        )
    ):
        overwrites[trader] = ticket_member_overwrite(
            can_chat
        )

    return overwrites


async def create_ticket_channel(
    guild,
    name,
    opener,
    trader,
    reason
):
    category = await get_ticket_category(
        guild
    )

    if category is None:
        raise RuntimeError(
            "ticket category missing"
        )

    return await guild.create_text_channel(
        name=name,
        category=category,
        overwrites=ticket_channel_overwrites(
            guild,
            opener,
            trader,
            can_chat=False
        ),
        reason=reason
    )


async def set_ticket_chat_enabled(
    channel,
    ticket,
    enabled
):
    if channel is None or ticket is None:
        return

    guild = channel.guild
    if guild is None:
        return

    for user_id in (
        ticket.get("opener_id"),
        ticket.get("trader_id")
    ):
        if not user_id:
            continue

        member = guild.get_member(
            int(user_id)
        )

        if member is None:
            try:
                member = await guild.fetch_member(
                    int(user_id)
                )
            except discord.HTTPException:
                continue

        overwrite = channel.overwrites_for(
            member
        )
        overwrite.view_channel = True
        overwrite.read_message_history = True
        overwrite.send_messages = bool(enabled)
        overwrite.add_reactions = bool(enabled)
        overwrite.attach_files = bool(enabled)
        overwrite.embed_links = bool(enabled)

        try:
            await channel.set_permissions(
                member,
                overwrite=overwrite,
                reason=(
                    "Ticket chat unlocked"
                    if enabled
                    else "Ticket chat locked"
                )
            )
        except discord.HTTPException:
            logger.exception(
                "Failed to update ticket chat for %s(%s) in %s",
                member,
                member.id,
                channel.id
            )

    ticket["chat_unlocked"] = bool(enabled)
    await save_data()


def role_selection_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    sender = (
        f"<@{ticket['sender_id']}>"
        if ticket.get(
            "sender_id"
        )
        else "..."
    )

    receiver = (
        f"<@{ticket['receiver_id']}>"
        if ticket.get(
            "receiver_id"
        )
        else "..."
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(ROLE_SHIELD_EMOJI)}"
            "• **Select your role**\n\n"
            f"> • __**\"Sender\"**__ if you are "
            f"__Sending__ {asset} to the bot.\n"
            f"> • __**\"Receiver\"**__ if you are "
            f"__Receiving__ {asset} *later* from the bot."
        ),
        colour=COLOR_NEUTRAL
    )

    embed.add_field(
        name="Sender",
        value=sender,
        inline=True
    )

    embed.add_field(
        name="Receiver",
        value=receiver,
        inline=True
    )

    return embed


def role_confirmation_embed(ticket):
    embed = discord.Embed(
        description=(
            f"{emoji_text(BLUE_LOADING_EMOJI)}"
            "• **Is This Information Correct?**"
        ),
        colour=COLOR_NEUTRAL
    )

    embed.add_field(
        name="Sender",
        value=(
            f"<@{ticket['sender_id']}>"
        ),
        inline=True
    )

    embed.add_field(
        name="Receiver",
        value=(
            f"<@{ticket['receiver_id']}>"
        ),
        inline=True
    )

    embed.add_field(
        name=ZERO_WIDTH,
        value=(
            "**Make sure you have selected the right role! "
            "If you didn't then click \"Incorrect\"**"
        ),
        inline=False
    )

    return embed


def role_correct_embed(user):
    return discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"{user.mention} clicked Correct."
        ),
        colour=COLOR_SUCCESS
    )


def role_incorrect_embed(user):
    return discord.Embed(
        description=(
            f"{emoji_text(ANIMATED_X_EMOJI)}"
            f"{user.mention} marked the roles as incorrect. "
            "Please restart the role selection process."
        ),
        colour=COLOR_ERROR
    )


def usd_prompt_embed():
    return discord.Embed(
        description=(
            f"{emoji_text(MONEY_EMOJI)}"
            "• **Set the amount in USD value**"
        ),
        colour=COLOR_NEUTRAL
    )


def usd_confirmation_embed(ticket):
    return discord.Embed(
        description=(
            f"{emoji_text(BLUE_LOADING_EMOJI)}"
            f"• **USD amount set to "
            f"`{money(ticket['usd_amount'])}`**\n\n"
            "Please confirm the USD amount."
        ),
        colour=COLOR_NEUTRAL
    )


def usd_correct_embed(user):
    return discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"{user.mention} confirmed the USD amount."
        ),
        colour=COLOR_SUCCESS
    )


def usd_incorrect_embed(user):
    return discord.Embed(
        description=(
            f"{emoji_text(ANIMATED_X_EMOJI)}"
            f"{user.mention} marked the USD amount as incorrect."
        ),
        colour=COLOR_ERROR
    )


def payment_info_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    emoji = get_asset_emoji(
        ticket
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(SCROLL_EMOJI)}"
            "• **Payment Information**\n\n"
            f"Make sure to send the "
            f"**EXACT** amount in {asset}."
        ),
        colour=COLOR_NEUTRAL
    )

    embed.add_field(
        name="USD Amount",
        value=(
            f"`{money(ticket['usd_amount'])}`"
        ),
        inline=True
    )

    embed.add_field(
        name=(
            f"{emoji_text(emoji)}"
            f"{asset} Amount"
        ),
        value=(
            f"`{required_crypto_display(ticket)}`"
        ),
        inline=True
    )

    embed.add_field(
        name="Payment Address",
        value=(
            f"`{ticket['deposit_address']}`"
        ),
        inline=False
    )

    if ticket[
        "type"
    ] == "ltc":
        footer = (
            f"**Current LTC Price: "
            f"{money(ticket['crypto_price'])}**\n"
        )

    else:
        footer = (
            "**Network: BSC (BEP-20)**\n"
        )

    footer += (
        "**This ticket will be closed within 20 minutes "
        "if no transaction was detected.**"
    )

    embed.add_field(
        name=ZERO_WIDTH,
        value=footer,
        inline=False
    )

    return embed


def transaction_detected_embed(ticket):
    txid = ticket.get(
        "deposit_txid"
    )

    amount = crypto_amount_text(
        ticket,
        ticket.get(
            "deposit_amount"
        )
        or ticket.get(
            "crypto_amount"
        )
        or "0"
    )

    required = required_crypto_display(
        ticket
    )

    asset = get_asset_name(
        ticket
    )

    needed = confirmations_required(
        ticket
    )

    word = (
        "confirmation"
        if needed == 1
        else "confirmations"
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(WARNING_EMOJI)}"
            "• **Transaction Detected**\n\n"
            "The transaction is currently "
            f"**unconfirmed** and waiting for "
            f"{needed} {word}."
        ),
        colour=COLOR_WARNING
    )

    if txid:
        label = (
            "Manual Transaction ID"
            if ticket.get(
                "manual_deposit_override"
            )
            else "Transaction"
        )

        embed.add_field(
            name=label,
            value=(
                f"{tx_display(ticket, txid)} "
                f"({amount} {asset})"
            ),
            inline=False
        )

    embed.add_field(
        name="Amount Received",
        value=(
            f"`{amount}` {asset} "
            f"({money(ticket['usd_amount'])})"
        ),
        inline=True
    )

    embed.add_field(
        name="Required Amount",
        value=(
            f"`{required}` {asset} "
            f"({money(ticket['usd_amount'])})"
        ),
        inline=True
    )

    embed.add_field(
        name=ZERO_WIDTH,
        value=(
            "**You will be notified when the "
            "transaction is confirmed.**"
        ),
        inline=False
    )

    return embed


def transaction_confirmed_embed(ticket):
    txid = ticket.get(
        "deposit_txid"
    )

    amount = crypto_amount_text(
        ticket,
        ticket.get(
            "deposit_amount"
        )
        or ticket.get(
            "crypto_amount"
        )
        or "0"
    )

    asset = get_asset_name(
        ticket
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            "• **Transaction Confirmed!**"
        ),
        colour=COLOR_SUCCESS
    )

    if txid:
        label = (
            "Manual Transaction ID"
            if ticket.get(
                "manual_deposit_override"
            )
            else "Transactions"
        )

        embed.add_field(
            name=label,
            value=(
                f"{tx_display(ticket, txid)} "
                f"({amount} {asset})"
            ),
            inline=False
        )

    embed.add_field(
        name="Total Amount Received",
        value=(
            f"`{amount}` {asset} "
            f"({money(ticket['usd_amount'])})"
        ),
        inline=False
    )

    return embed


def proceed_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    return discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            "• **You may proceed with your trade.**\n\n"
            f"> **1. <@{ticket['receiver_id']}> "
            "Give your trader the items or payment\n"
            "you agreed on.**\n\n"
            f"> **2. <@{ticket['sender_id']}> "
            "Once you have received your items,\n"
            f"click \"Release\" so your trader can claim "
            f"the {asset}.**"
        ),
        colour=COLOR_SUCCESS
    )


def cancellation_embed(ticket):
    uncancel_votes = ticket.get(
        "uncancel_votes",
        []
    )

    cancel_votes = ticket.get(
        "cancel_votes",
        []
    )

    uncancel_text = (
        "\n".join(
            f"<@{user_id}>"
            for user_id
            in uncancel_votes
        )
        if uncancel_votes
        else "None yet"
    )

    cancel_text = (
        "\n".join(
            f"<@{user_id}>"
            for user_id
            in cancel_votes
        )
        if cancel_votes
        else "None yet"
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(WARNING_EMOJI)}"
            "**Cancellation Requested**\n\n"
            "Select `Uncancel` to continue the trade or "
            "`Confirm the Cancellation` to cancel."
        ),
        colour=COLOR_WARNING
    )

    embed.add_field(
        name="Agreed to Uncancel",
        value=uncancel_text,
        inline=False
    )

    embed.add_field(
        name="Confirmed Cancellation",
        value=cancel_text,
        inline=False
    )

    embed.add_field(
        name=ZERO_WIDTH,
        value=(
            "**Both traders must select the same option.**"
        ),
        inline=False
    )

    return embed


def release_confirmation_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    return discord.Embed(
        description=(
            f"{emoji_text(WARNING_EMOJI)}"
            f"**Are you sure you want to release the "
            f"{asset}?** {WARNING_EMOJI}\n\n"
            "Clicking **\"Confirm\"** will give your trader "
            f"permission to withdraw the {asset}.\n"
            f"> <@{ticket['receiver_id']}> will get the {asset}.\n\n"
            "**Staff will never ask you to release/cancel**"
        ),
        colour=COLOR_WARNING
    )


def address_prompt_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    network = (
        ""
        if ticket[
            "type"
        ] == "ltc"
        else " [BEP-20]"
    )

    return discord.Embed(
        description=(
            f"{emoji_text(get_asset_emoji(ticket))}"
            f"• **What's Your {asset}{network} Address?**\n\n"
            f"> **Make sure to paste your correct "
            f"{asset}{network} address.**"
        ),
        colour=COLOR_NEUTRAL
    )


def address_confirmation_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    return discord.Embed(
        description=(
            f"{emoji_text(WARNING_EMOJI)}"
            "• **Confirm Address**\n\n"
            f"> **Address:** "
            f"`{ticket['receiver_address']}`\n\n"
            f"Click **\"Confirm\"** to send {asset} "
            "or **\"Back\"** to cancel."
        ),
        colour=COLOR_WARNING
    )


def sending_embed():
    return discord.Embed(
        description=(
            f"{emoji_text(LOAD_EMOJI)}"
            "• **Sending...**"
        ),
        colour=COLOR_NEUTRAL
    )


def settlement_pending_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    return discord.Embed(
        description=(
            f"{emoji_text(BLUE_LOADING_EMOJI)}"
            "• **Settlement Pending**\n\n"
            f"The {asset} release was authorized and the "
            "destination address was confirmed.\n"
            "The payout is waiting to be settled."
        ),
        colour=COLOR_WARNING
    )


def withdrawal_success_embed(ticket):
    txid = ticket[
        "payout_txid"
    ]

    amount = crypto_amount_text(
        ticket,
        ticket[
            "payout_amount"
        ]
    )

    asset = get_asset_name(
        ticket
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            "• **Withdrawal Successful**\n\n"
            "Use /setprivacy to display your user in "
            f"{get_channel_mention(COMPLETED_TRANSACTION_CHANNEL)}"
        ),
        colour=COLOR_NEUTRAL
    )

    embed.add_field(
        name="Transaction",
        value=tx_display(
            ticket,
            txid
        ),
        inline=True
    )

    embed.add_field(
        name="Amount Sent",
        value=(
            f"`{amount}` {asset} "
            f"({money(ticket['usd_amount'])})"
        ),
        inline=True
    )

    return embed


def completed_embed(ticket):
    asset = get_asset_name(
        ticket
    )

    amount = crypto_amount_text(
        ticket,
        ticket[
            "payout_amount"
        ]
    )

    sender_private = DATA[
        "privacy"
    ].get(
        str(
            ticket[
                "sender_id"
            ]
        ),
        True
    )

    receiver_private = DATA[
        "privacy"
    ].get(
        str(
            ticket[
                "receiver_id"
            ]
        ),
        True
    )

    sender_text = (
        "`Anonymous`"
        if sender_private
        else (
            f"<@{ticket['sender_id']}>"
        )
    )

    receiver_text = (
        "`Anonymous`"
        if receiver_private
        else (
            f"<@{ticket['receiver_id']}>"
        )
    )

    embed = discord.Embed(
        description=(
            f"{emoji_text(get_asset_emoji(ticket))}"
            "• **Trade Completed**\n\n"
            f"`{amount}` {asset} "
            f"({money(ticket['usd_amount'])} USD)"
        ),
        colour=COLOR_NEUTRAL,
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="Sender",
        value=sender_text,
        inline=True
    )

    embed.add_field(
        name="Receiver",
        value=receiver_text,
        inline=True
    )

    embed.add_field(
        name="Transaction ID",
        value=tx_display(
            ticket,
            ticket[
                "payout_txid"
            ]
        ),
        inline=False
    )

    return embed


async def send_role_selection(
    channel,
    ticket
):
    ticket[
        "status"
    ] = "role_selection"

    ticket[
        "sender_id"
    ] = None

    ticket[
        "receiver_id"
    ] = None

    ticket[
        "role_confirmed"
    ] = []

    await save_data()

    message = await channel.send(
        embed=role_selection_embed(
            ticket
        ),
        view=RoleSelectionView()
    )

    ticket[
        "messages"
    ][
        "role_selection"
    ] = message.id

    await save_data()


async def send_role_confirmation(
    channel,
    ticket
):
    ticket[
        "status"
    ] = "role_confirmation"

    ticket[
        "role_confirmed"
    ] = []

    await save_data()

    message = await channel.send(
        content=(
            f"<@{ticket['sender_id']}> "
            f"<@{ticket['receiver_id']}>"
        ),
        embed=role_confirmation_embed(
            ticket
        ),
        view=RoleConfirmationView(),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "role_confirmation"
    ] = message.id

    await save_data()


async def send_usd_prompt(
    channel,
    ticket
):
    ticket[
        "status"
    ] = "usd_prompt"

    await save_data()

    message = await channel.send(
        content=(
            f"<@{ticket['sender_id']}>"
        ),
        embed=usd_prompt_embed(),
        view=UsdPromptView(),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "usd_prompt"
    ] = message.id

    await save_data()


async def send_usd_confirmation(
    channel,
    ticket
):
    ticket[
        "status"
    ] = "usd_confirmation"

    ticket[
        "usd_confirmed"
    ] = []

    await save_data()

    message = await channel.send(
        content=(
            f"<@{ticket['sender_id']}> "
            f"<@{ticket['receiver_id']}>"
        ),
        embed=usd_confirmation_embed(
            ticket
        ),
        view=UsdConfirmationView(),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "usd_confirmation"
    ] = message.id

    await save_data()


async def send_payment_info(
    channel,
    ticket
):
    if ticket[
        "type"
    ] == "ltc":

        price = await get_ltc_price()

        if price is None:
            ticket[
                "status"
            ] = "usd_confirmation"

            ticket[
                "usd_confirmed"
            ] = []

            await save_data()

            await channel.send(
                embed=discord.Embed(
                    description=(
                        f"{emoji_text(ANIMATED_X_EMOJI)}"
                        f"{DOT} "
                        "**Unable to retrieve the current LTC price. "
                        "Please confirm the USD amount again.**"
                    ),
                    colour=COLOR_ERROR
                )
            )

            await send_usd_confirmation(
                channel,
                ticket
            )

            return False

        usd = Decimal(
            str(
                ticket[
                    "usd_amount"
                ]
            )
        )

        crypto_amount = (
            usd
            / price
        ).quantize(
            Decimal(
                "0.00001"
            ),
            rounding=ROUND_DOWN
        )

    else:
        price = Decimal(
            "1.00"
        )

        crypto_amount = Decimal(
            str(
                ticket[
                    "usd_amount"
                ]
            )
        ).quantize(
            Decimal(
                "0.01"
            )
        )

    ticket[
        "crypto_price"
    ] = str(
        price
    )

    ticket[
        "crypto_amount"
    ] = str(
        crypto_amount
    )

    ticket[
        "deposit_address"
    ] = get_deposit_address(
        ticket
    )

    ticket[
        "deposit_txid"
    ] = None

    ticket[
        "deposit_amount"
    ] = None

    ticket[
        "deposit_confirmations"
    ] = 0

    ticket[
        "manual_deposit_override"
    ] = False

    ticket[
        "manual_reference"
    ] = None

    ticket[
        "baseline_ready"
    ] = False

    ticket[
        "status"
    ] = "waiting_deposit"

    ticket[
        "payment_started_at"
    ] = int(
        time.time()
    )

    await save_data()

    start_baseline(
        ticket
    )

    log_action(
        "payment_details_ready",
        ticket=ticket.get(
            "number"
        ),
        asset=get_asset_name(
            ticket
        ),
        usd=money(
            ticket.get(
                "usd_amount"
            )
        ),
        crypto=required_crypto_display(
            ticket
        ),
        address=ticket.get(
            "deposit_address"
        )
    )

    message = await channel.send(
        content=(
            f"<@{ticket['sender_id']}> "
            f"Send the {get_asset_name(ticket)} "
            "to the following address."
        ),
        embed=payment_info_embed(
            ticket
        ),
        view=PaymentInfoView(),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "payment_info"
    ] = message.id

    await save_data()

    await set_ticket_chat_enabled(
        channel,
        ticket,
        True
    )

    ensure_monitor(
        ticket
    )

    return True


async def handle_deposit_detected(
    ticket,
    txid,
    amount,
    confirmations
):
    if (
        txid
        and not await claim_deposit_txid(
            ticket,
            txid
        )
    ):
        log_security(
            "deposit_txid_rejected_already_claimed",
            ticket=ticket.get(
                "number"
            ),
            txid=short_txid(
                txid
            )
        )

        return

    channel_id = int(
        ticket[
            "channel_id"
        ]
    )

    should_send = False
    should_edit_manual = False
    should_confirm = False

    async with get_ticket_lock(
        channel_id
    ):
        current = get_ticket(
            channel_id
        )

        if (
            current is None
            or current.get(
                "status"
            )
            not in {
                "waiting_deposit",
                "deposit_unconfirmed"
            }
        ):
            return

        previous = current.get(
            "deposit_txid"
        )

        replacing_manual = bool(
            current.get(
                "manual_deposit_override"
            )
            and txid
            and current.get(
                "manual_reference"
            )
        )

        if txid:
            current[
                "deposit_txid"
            ] = txid

        current[
            "deposit_amount"
        ] = str(
            amount
        )

        current[
            "deposit_confirmations"
        ] = int(
            confirmations
        )

        if replacing_manual:
            current[
                "manual_deposit_override"
            ] = False

            should_edit_manual = True

        elif (
            txid
            and (
                not previous
                or normalize_txid(
                    previous
                )
                != normalize_txid(
                    txid
                )
            )
        ):
            should_send = True

        current[
            "status"
        ] = "deposit_unconfirmed"

        should_confirm = (
            Decimal(
                str(
                    amount
                )
            )
            >= required_crypto_decimal(
                current
            )
            and int(
                confirmations
            )
            >= confirmations_required(
                current
            )
        )

        await save_data()

    log_action(
        "deposit_detected",
        ticket=ticket.get(
            "number"
        ),
        asset=get_asset_name(
            ticket
        ),
        amount=crypto_amount_text(
            ticket,
            amount
        ),
        confirmations=int(
            confirmations
        ),
        txid=(
            short_txid(
                txid
            )
            if txid
            else "none"
        ),
        source="blockchain"
    )

    channel = await resolve_ticket_channel(
        ticket
    )

    if channel is None:
        logger.error(
            "Ticket channel missing while handling deposit | "
            "ticket=%s | channel=%s",
            ticket.get(
                "number"
            ),
            channel_id
        )

        return

    if should_edit_manual:
        previous_message = await fetch_message(
            channel,
            ticket[
                "messages"
            ].get(
                "deposit_detected"
            )
        )

        if previous_message is not None:
            try:
                await previous_message.edit(
                    embed=transaction_detected_embed(
                        ticket
                    )
                )

            except discord.HTTPException:
                should_send = True

        else:
            should_send = True

    if should_send:
        message = await channel.send(
            embed=transaction_detected_embed(
                ticket
            )
        )

        ticket[
            "messages"
        ][
            "deposit_detected"
        ] = message.id

        await save_data()

    if should_confirm:
        await handle_deposit_confirmed(
            ticket
        )


async def handle_deposit_confirmed(ticket):
    channel_id = int(
        ticket[
            "channel_id"
        ]
    )

    async with get_ticket_lock(
        channel_id
    ):
        current = get_ticket(
            channel_id
        )

        if current is None:
            return

        if current.get(
            "status"
        ) in {
            "deposit_confirmed",
            "trade",
            "cancellation",
            "release_confirmation",
            "address_prompt",
            "address_confirmation",
            "settlement_pending",
            "completed"
        }:
            return

        received = Decimal(
            str(
                current.get(
                    "deposit_amount"
                )
                or "0"
            )
        )

        if (
            received
            < required_crypto_decimal(
                current
            )
        ):
            return

        if int(
            current.get(
                "deposit_confirmations",
                0
            )
        ) < confirmations_required(
            current
        ):
            return

        current[
            "status"
        ] = "deposit_confirmed"

        await save_data()

    log_action(
        "deposit_confirmed",
        ticket=ticket.get(
            "number"
        ),
        asset=get_asset_name(
            ticket
        ),
        amount=crypto_amount_text(
            ticket,
            ticket.get(
                "deposit_amount"
            )
            or ticket.get(
                "crypto_amount"
            )
            or "0"
        ),
        confirmations=ticket.get(
            "deposit_confirmations",
            0
        ),
        txid=(
            short_txid(
                ticket.get(
                    "deposit_txid"
                )
            )
            if ticket.get(
                "deposit_txid"
            )
            else "none"
        ),
        source=(
            "manual"
            if ticket.get(
                "manual_deposit_override"
            )
            else "blockchain"
        )
    )

    channel = await resolve_ticket_channel(
        ticket
    )

    if channel is None:
        return

    confirmed_message = await channel.send(
        embed=transaction_confirmed_embed(
            ticket
        )
    )

    ticket[
        "messages"
    ][
        "deposit_confirmed"
    ] = confirmed_message.id

    proceed_message = await channel.send(
        content=(
            f"<@{ticket['sender_id']}> "
            f"<@{ticket['receiver_id']}>"
        ),
        embed=proceed_embed(
            ticket
        ),
        view=ProceedView(),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "proceed"
    ] = proceed_message.id

    ticket[
        "status"
    ] = "trade"

    await save_data()


async def monitor_ltc_ticket(ticket):
    address = ticket[
        "deposit_address"
    ]

    expected_satoshi = int(
        (
            required_crypto_decimal(
                ticket
            )
            * Decimal(
                "100000000"
            )
        ).to_integral_value(
            rounding=ROUND_DOWN
        )
    )

    current_txid = ticket.get(
        "deposit_txid"
    )

    if ticket.get(
        "manual_deposit_override"
    ):
        current_txid = None

    if current_txid:
        tx = await fetch_ltc_transaction(
            current_txid
        )

        if not isinstance(tx, dict):
            return

        received = ltc_received_by_tx(
            tx,
            address
        )

        if received < expected_satoshi:
            return

        amount = (
            Decimal(
                received
            )
            / Decimal(
                "100000000"
            )
        )

        confirmations = int(
            tx.get(
                "confirmations",
                0
            )
        )

        await handle_deposit_detected(
            ticket,
            current_txid,
            amount,
            confirmations
        )
        return

    txids = await fetch_ltc_address_txids(
        address
    )

    if txids is None:
        return

    baseline = set(
        ticket.get(
            "baseline_txids",
            []
        )
    )

    for txid in txids:
        if not txid:
            continue

        normalized = normalize_txid(
            txid
        )

        if normalized in baseline:
            continue

        claimed_by = DATA[
            "claimed_deposit_txids"
        ].get(
            normalized
        )

        if (
            claimed_by is not None
            and int(
                claimed_by
            )
            != int(
                ticket[
                    "number"
                ]
            )
        ):
            continue

        tx = await fetch_ltc_transaction(
            txid
        )

        if not isinstance(tx, dict):
            continue

        if chain_event_is_before_payment(
            ticket,
            tx.get("confirmed"),
            tx.get("received")
        ):
            continue

        received = ltc_received_by_tx(
            tx,
            address
        )

        if received != expected_satoshi:
            continue

        amount = (
            Decimal(
                received
            )
            / Decimal(
                "100000000"
            )
        )

        confirmations = int(
            tx.get(
                "confirmations",
                0
            )
        )

        await handle_deposit_detected(
            ticket,
            txid,
            amount,
            confirmations
        )
        return


async def monitor_usdt_ticket(ticket):
    address = ticket[
        "deposit_address"
    ]

    transfers = await fetch_usdt_transfers(
        address
    )

    if transfers is None:
        return

    expected_amount = required_crypto_decimal(
        ticket
    )

    current_txid = ticket.get(
        "deposit_txid"
    )

    if ticket.get(
        "manual_deposit_override"
    ):
        current_txid = None

    if current_txid:
        total = Decimal(
            "0"
        )

        confirmations = 0
        found = False

        for transfer in transfers:
            txid = transfer.get(
                "hash"
            )

            if (
                not txid
                or normalize_txid(
                    txid
                )
                != normalize_txid(
                    current_txid
                )
            ):
                continue

            if not valid_usdt_transfer(
                transfer,
                address
            ):
                continue

            amount, count = (
                parse_usdt_transfer(
                    transfer
                )
            )

            total += amount

            confirmations = max(
                confirmations,
                count
            )

            found = True

        if (
            found
            and total >= expected_amount
        ):
            await handle_deposit_detected(
                ticket,
                current_txid,
                total,
                confirmations
            )

        return

    baseline = set(
        ticket.get(
            "baseline_txids",
            []
        )
    )

    grouped = {}

    for transfer in transfers:
        txid = transfer.get(
            "hash"
        )

        if not txid:
            continue

        normalized = normalize_txid(
            txid
        )

        if normalized in baseline:
            continue

        claimed_by = DATA[
            "claimed_deposit_txids"
        ].get(
            normalized
        )

        if (
            claimed_by is not None
            and int(
                claimed_by
            )
            != int(
                ticket[
                    "number"
                ]
            )
        ):
            continue

        if not valid_usdt_transfer(
            transfer,
            address
        ):
            continue

        if chain_event_is_before_payment(
            ticket,
            transfer.get("timeStamp")
        ):
            continue

        amount, confirmations = (
            parse_usdt_transfer(
                transfer
            )
        )

        item = grouped.setdefault(
            normalized,
            {
                "txid": txid,
                "amount": Decimal("0"),
                "confirmations": 0
            }
        )

        item[
            "amount"
        ] += amount

        item[
            "confirmations"
        ] = max(
            item[
                "confirmations"
            ],
            confirmations
        )

    for item in grouped.values():
        if (
            item[
                "amount"
            ]
            != expected_amount
        ):
            continue

        await handle_deposit_detected(
            ticket,
            item[
                "txid"
            ],
            item[
                "amount"
            ],
            item[
                "confirmations"
            ]
        )

        return


async def monitor_ticket(channel_id):
    try:
        while True:
            ticket = get_ticket(
                channel_id
            )

            if ticket is None:
                return

            if ticket.get(
                "status"
            ) not in {
                "waiting_deposit",
                "deposit_unconfirmed",
                "halal_amount"
            }:
                return

            try:
                if is_halal_ticket(ticket):
                    if ticket.get("status") in {
                        "waiting_deposit",
                        "deposit_unconfirmed"
                    }:
                        await monitor_halal_ticket(
                            ticket
                        )
                elif (
                    ticket[
                        "type"
                    ] == "ltc"
                    and AUTO_MONITOR_LTC
                ):
                    await monitor_ltc_ticket(
                        ticket
                    )

                elif (
                    ticket[
                        "type"
                    ] == "usdt"
                    and AUTO_MONITOR_USDT
                ):
                    await monitor_usdt_ticket(
                        ticket
                    )

            except asyncio.CancelledError:
                raise

            except Exception:
                logger.exception(
                    "Deposit monitor iteration failed for channel %s",
                    channel_id
                )

            ticket = get_ticket(
                channel_id
            )

            if ticket is None:
                return

            timeout_limit = (
                HALAL_UNPAID_TIMEOUT_SECONDS
                if is_halal_ticket(ticket)
                else UNPAID_TIMEOUT_SECONDS
            )
            timeout_status = ticket.get("status")
            started = 0
            if timeout_status == "waiting_deposit":
                started = int(
                    ticket.get(
                        "payment_started_at",
                        int(time.time())
                    )
                )
            elif (
                is_halal_ticket(ticket)
                and timeout_status == "halal_amount"
            ):
                started = int(
                    ticket.get(
                        "amount_started_at",
                        int(time.time())
                    )
                )

            if (
                AUTO_CLOSE_UNPAID
                and started
                and (
                    int(time.time()) - started
                    >= timeout_limit
                )
            ):
                    channel = await resolve_ticket_channel(
                        ticket
                    )

                    if channel is not None:
                        await channel.send(
                            embed=discord.Embed(
                                description=(
                                    f"{emoji_text(ANIMATED_X_EMOJI)}"
                                    f"{DOT} "
                                    "**No transaction was detected. "
                                    "Closing ticket...**"
                                ),
                                colour=COLOR_ERROR
                            )
                        )

                        await asyncio.sleep(
                            3
                        )

                        await close_ticket_channel(
                            channel,
                            ticket,
                            "Unpaid ticket timeout"
                        )

                    return

            await asyncio.sleep(
                MONITOR_INTERVAL_SECONDS
            )

    except asyncio.CancelledError:
        return

    finally:
        MONITOR_TASKS.pop(
            str(
                channel_id
            ),
            None
        )


def ensure_monitor(ticket):
    key = str(
        ticket[
            "channel_id"
        ]
    )

    task = MONITOR_TASKS.get(
        key
    )

    if (
        task is not None
        and not task.done()
    ):
        return

    MONITOR_TASKS[
        key
    ] = asyncio.create_task(
        monitor_ticket(
            int(
                ticket[
                    "channel_id"
                ]
            )
        )
    )


def countdown_key(
    channel_id,
    kind
):
    return (
        f"{channel_id}:"
        f"{kind}"
    )


def cancel_countdown(
    channel_id,
    kind
):
    key = countdown_key(
        channel_id,
        kind
    )

    task = COUNTDOWN_TASKS.pop(
        key,
        None
    )

    if (
        task is not None
        and not task.done()
    ):
        task.cancel()


async def stop_ticket_chain(channel_id, reason="channel deleted"):
    if channel_id is None:
        return False

    try:
        channel_id = int(channel_id)
    except (TypeError, ValueError):
        return False

    key = str(channel_id)

    close_task = HALAL_CLOSE_TASKS.pop(key, None)
    if close_task is not None and not close_task.done():
        close_task.cancel()

    baseline_task = BASELINE_TASKS.pop(key, None)
    if baseline_task is not None and not baseline_task.done():
        baseline_task.cancel()

    monitor_task = MONITOR_TASKS.pop(key, None)
    if monitor_task is not None and not monitor_task.done():
        monitor_task.cancel()

    cancel_countdown(channel_id, "release")
    cancel_countdown(channel_id, "address")
    TICKET_LOCKS.pop(key, None)

    async with DATA_LOCK:
        removed = DATA.get("tickets", {}).pop(key, None)
        if removed is not None:
            save_data_now()

    if removed is None and baseline_task is None and monitor_task is None:
        return False

    log_action(
        "ticket_chain_stopped",
        channel_id=channel_id,
        ticket=(removed or {}).get("number"),
        reason=reason
    )
    return True


def start_countdown(
    ticket,
    kind,
    message_id,
    resume=False
):
    key = countdown_key(
        ticket[
            "channel_id"
        ],
        kind
    )

    old = COUNTDOWN_TASKS.get(
        key
    )

    if (
        old is not None
        and not old.done()
    ):
        old.cancel()

    if not resume:
        ticket[
            f"{kind}_countdown_end"
        ] = (
            time.time()
            + 3
        )

    COUNTDOWN_TASKS[
        key
    ] = asyncio.create_task(
        run_countdown(
            int(
                ticket[
                    "channel_id"
                ]
            ),
            kind,
            int(
                message_id
            )
        )
    )


async def run_countdown(
    channel_id,
    kind,
    message_id
):
    key = countdown_key(
        channel_id,
        kind
    )

    try:
        while True:
            ticket = get_ticket(
                channel_id
            )

            if ticket is None:
                return

            end_time = float(
                ticket.get(
                    f"{kind}_countdown_end",
                    0
                )
            )

            remaining = math.ceil(
                max(
                    0,
                    end_time
                    - time.time()
                )
            )

            channel = await resolve_ticket_channel(
                ticket
            )

            if channel is None:
                return

            message = await fetch_message(
                channel,
                message_id
            )

            if message is None:
                return

            if remaining <= 0:
                if kind == "release":
                    ticket[
                        "release_confirm_ready"
                    ] = True

                    view = (
                        ReleaseConfirmationView()
                    )

                else:
                    ticket[
                        "address_confirm_ready"
                    ] = True

                    view = (
                        AddressConfirmationView()
                    )

                await save_data()

                await message.edit(
                    view=view
                )

                return

            shown = min(
                3,
                max(
                    1,
                    remaining
                )
            )

            view = (
                ReleaseConfirmationView(
                    countdown=shown
                )
                if kind == "release"
                else AddressConfirmationView(
                    countdown=shown
                )
            )

            await message.edit(
                view=view
            )

            await asyncio.sleep(
                1
            )

    except asyncio.CancelledError:
        return

    except Exception:
        logger.exception(
            "Countdown failed for %s %s",
            channel_id,
            kind
        )

    finally:
        COUNTDOWN_TASKS.pop(
            key,
            None
        )


async def send_release_confirmation(
    channel,
    ticket
):
    ticket[
        "status"
    ] = "release_confirmation"

    ticket[
        "release_confirm_ready"
    ] = False

    ticket[
        "release_countdown_end"
    ] = (
        time.time()
        + 3
    )

    await save_data()

    message = await channel.send(
        content=(
            f"<@{ticket['sender_id']}>"
        ),
        embed=release_confirmation_embed(
            ticket
        ),
        view=ReleaseConfirmationView(
            countdown=3
        ),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "release_confirmation"
    ] = message.id

    await save_data()

    start_countdown(
        ticket,
        "release",
        message.id,
        resume=True
    )


async def send_address_prompt(
    channel,
    ticket
):
    ticket[
        "status"
    ] = "address_prompt"

    await save_data()

    message = await channel.send(
        content=(
            f"<@{ticket['receiver_id']}>"
        ),
        embed=address_prompt_embed(
            ticket
        ),
        view=AddressPromptView(
            ticket=ticket
        ),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "address_prompt"
    ] = message.id

    await save_data()


async def send_address_confirmation(
    channel,
    ticket
):
    ticket[
        "status"
    ] = "address_confirmation"

    ticket[
        "address_confirm_ready"
    ] = False

    ticket[
        "address_countdown_end"
    ] = (
        time.time()
        + 3
    )

    await save_data()

    message = await channel.send(
        content=(
            f"<@{ticket['receiver_id']}>"
        ),
        embed=address_confirmation_embed(
            ticket
        ),
        view=AddressConfirmationView(
            countdown=3
        ),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
    )

    ticket[
        "messages"
    ][
        "address_confirmation"
    ] = message.id

    await save_data()

    start_countdown(
        ticket,
        "address",
        message.id,
        resume=True
    )


async def verify_ltc_payout(
    ticket,
    txid,
    requested_amount
):
    tx = await fetch_ltc_transaction(
        txid
    )

    if not isinstance(
        tx,
        dict
    ):
        return (
            False,
            None,
            0,
            "The Litecoin transaction could not be retrieved."
        )

    amount = (
        Decimal(
            ltc_received_by_tx(
                tx,
                ticket[
                    "receiver_address"
                ]
            )
        )
        / Decimal(
            "100000000"
        )
    )

    confirmations = int(
        tx.get(
            "confirmations",
            0
        )
    )

    if amount < requested_amount:
        return (
            False,
            amount,
            confirmations,
            "The transaction does not send the requested "
            "amount to the confirmed receiver address."
        )

    if (
        confirmations
        < LTC_CONFIRMATIONS_REQUIRED
    ):
        return (
            False,
            amount,
            confirmations,
            "The payout transaction does not have enough confirmations yet."
        )

    return (
        True,
        amount,
        confirmations,
        ""
    )


async def verify_usdt_payout(
    ticket,
    txid,
    requested_amount
):
    transfers = await fetch_usdt_transfers(
        ticket[
            "receiver_address"
        ]
    )

    if transfers is None:
        return (
            False,
            None,
            0,
            "The BSC token transfer could not be retrieved."
        )

    total = Decimal(
        "0"
    )

    confirmations = 0
    found = False

    for transfer in transfers:
        hash_value = transfer.get(
            "hash"
        )

        if (
            not hash_value
            or normalize_txid(
                hash_value
            )
            != normalize_txid(
                txid
            )
        ):
            continue

        if not valid_usdt_transfer(
            transfer,
            ticket[
                "receiver_address"
            ]
        ):
            continue

        amount, count = (
            parse_usdt_transfer(
                transfer
            )
        )

        total += amount

        confirmations = max(
            confirmations,
            count
        )

        found = True

    if not found:
        return (
            False,
            None,
            0,
            "The transaction does not contain the expected USDT "
            "transfer to the confirmed receiver address."
        )

    if total < requested_amount:
        return (
            False,
            total,
            confirmations,
            "The USDT transaction amount is below the "
            "requested payout amount."
        )

    if (
        confirmations
        < USDT_CONFIRMATIONS_REQUIRED
    ):
        return (
            False,
            total,
            confirmations,
            "The payout transaction does not have enough confirmations yet."
        )

    return (
        True,
        total,
        confirmations,
        ""
    )


async def verify_payout(
    ticket,
    txid,
    requested_amount
):
    if ticket[
        "type"
    ] == "ltc":
        return await verify_ltc_payout(
            ticket,
            txid,
            requested_amount
        )

    return await verify_usdt_payout(
        ticket,
        txid,
        requested_amount
    )


async def send_settlement_request(ticket):
    guild = bot.get_guild(
        int(
            ticket[
                "guild_id"
            ]
        )
    )

    if guild is None:
        return False

    channel = await get_configured_channel(
        guild,
        SETTLEMENT_CHANNEL
    )

    if channel is None:
        return False

    asset = get_asset_name(
        ticket
    )

    embed = discord.Embed(
        title=(
            f"Settlement Request "
            f"{ticket['number']}"
        ),
        description=(
            f"Ticket: "
            f"<{chr(35)}{ticket['channel_id']}>"
        ),
        colour=COLOR_WARNING,
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="Sender",
        value=(
            f"<@{ticket['sender_id']}>"
        ),
        inline=True
    )

    embed.add_field(
        name="Receiver",
        value=(
            f"<@{ticket['receiver_id']}>"
        ),
        inline=True
    )

    embed.add_field(
        name="USD Value",
        value=money(
            ticket[
                "usd_amount"
            ]
        ),
        inline=True
    )

    embed.add_field(
        name="Asset",
        value=asset,
        inline=True
    )

    embed.add_field(
        name="Amount Received",
        value=(
            f"{crypto_amount_text(ticket, ticket['deposit_amount'])} "
            f"{asset}"
        ),
        inline=True
    )

    embed.add_field(
        name="Receiver Address",
        value=(
            f"`{ticket['receiver_address']}`"
        ),
        inline=False
    )

    embed.add_field(
        name=(
            "Deposit Transaction"
            if not ticket.get(
                "manual_deposit_override"
            )
            else "Manual Deposit Reference"
        ),
        value=tx_display(
            ticket,
            ticket.get(
                "deposit_txid"
            )
        ),
        inline=False
    )

    embed.add_field(
        name="Settlement Command",
        value=(
            f"`/settle "
            f"ticket_number:{ticket['number']} "
            "payout_txid:<transaction> "
            "payout_amount:<amount>`"
        ),
        inline=False
    )

    await channel.send(
        embed=embed
    )

    log_action(
        "settlement_request_sent",
        ticket=ticket.get(
            "number"
        ),
        asset=asset,
        receiver=ticket.get(
            "receiver_id"
        ),
        address=ticket.get(
            "receiver_address"
        )
    )

    return True


async def send_completion_outputs(ticket):
    guild = bot.get_guild(
        int(
            ticket[
                "guild_id"
            ]
        )
    )

    if guild is None:
        return

    ticket_channel = await resolve_ticket_channel(
        ticket
    )

    if (
        ticket_channel is not None
        and not ticket.get(
            "withdrawal_success_sent"
        )
    ):
        address_message = await fetch_message(
            ticket_channel,
            ticket[
                "messages"
            ].get(
                "address_confirmation"
            )
        )

        kwargs = {
            "content": (
                f"<@{ticket['receiver_id']}>"
            ),
            "embed": withdrawal_success_embed(
                ticket
            ),
            "view": CloseTicketView(),
            "allowed_mentions": discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False
            )
        }

        if address_message is not None:
            kwargs[
                "reference"
            ] = address_message

            kwargs[
                "mention_author"
            ] = False

        try:
            message = await ticket_channel.send(
                **kwargs
            )

            ticket[
                "messages"
            ][
                "withdrawal_success"
            ] = message.id

            ticket[
                "withdrawal_success_sent"
            ] = True

            await save_data()

        except discord.HTTPException:
            logger.exception(
                "Failed to send withdrawal success for ticket %s",
                ticket[
                    "number"
                ]
            )

    if not ticket.get(
        "completed_channel_sent"
    ):
        completed_channel = (
            await get_configured_channel(
                guild,
                COMPLETED_TRANSACTION_CHANNEL
            )
        )

        if completed_channel is not None:
            try:
                await completed_channel.send(
                    embed=completed_embed(
                        ticket
                    )
                )

                ticket[
                    "completed_channel_sent"
                ] = True

                await save_data()

            except discord.HTTPException:
                logger.exception(
                    "Failed to send completed trade log for ticket %s",
                    ticket[
                        "number"
                    ]
                )


async def finalize_withdrawal(
    ticket,
    payout_txid,
    payout_amount,
    simulation=False
):
    channel_id = int(
        ticket[
            "channel_id"
        ]
    )

    recorded_users = []

    async with get_ticket_lock(
        channel_id
    ):
        current = get_ticket(
            channel_id
        )

        if current is None:
            return

        current[
            "payout_txid"
        ] = payout_txid

        current[
            "payout_amount"
        ] = str(
            Decimal(
                str(
                    payout_amount
                )
            )
        )

        current[
            "payout_is_simulation"
        ] = bool(
            simulation
        )

        current[
            "status"
        ] = "completed"

        current[
            "completed_at"
        ] = int(
            time.time()
        )

        recorded_users = []

        if not current.get(
            "stats_recorded"
        ):
            deal_usd = Decimal(
                str(
                    current[
                        "usd_amount"
                    ]
                )
            ).quantize(
                Decimal(
                    "0.01"
                )
            )

            for user_id in {
                str(
                    current[
                        "sender_id"
                    ]
                ),
                str(
                    current[
                        "receiver_id"
                    ]
                )
            }:
                stats = get_user_stats(
                    user_id
                )

                stats[
                    "deals_completed"
                ] = (
                    int(
                        stats.get(
                            "deals_completed",
                            0
                        )
                    )
                    + 1
                )

                total = (
                    Decimal(
                        str(
                            stats.get(
                                "total_usd_value",
                                "0"
                            )
                        )
                    )
                    + deal_usd
                )

                stats[
                    "total_usd_value"
                ] = str(
                    total.quantize(
                        Decimal(
                            "0.01"
                        )
                    )
                )

                biggest = Decimal(
                    str(
                        stats.get(
                            "biggest_deal",
                            "0"
                        )
                        or "0"
                    )
                )

                if deal_usd > biggest:
                    stats[
                        "biggest_deal"
                    ] = str(
                        deal_usd
                    )

                recorded_users.append(
                    user_id
                )

            current[
                "stats_recorded"
            ] = True

        current[
            "completed_logged"
        ] = True

        await save_data()

    log_action(
        "withdrawal_finalized",
        ticket=ticket.get(
            "number"
        ),
        asset=get_asset_name(
            ticket
        ),
        amount=crypto_amount_text(
            ticket,
            payout_amount
        ),
        txid=short_txid(
            payout_txid
        ),
        simulation=simulation
    )

    if is_halal_ticket(ticket):
        await send_halal_completion(
            ticket
        )
    else:
        await send_completion_outputs(
            ticket
        )

    guild = bot.get_guild(
        int(
            ticket[
                "guild_id"
            ]
        )
    )

    for user_id in recorded_users:
        await sync_rank_roles(
            guild,
            user_id
        )


async def build_transcript(channel):
    lines = []

    async for message in channel.history(
        limit=None,
        oldest_first=True
    ):
        timestamp = (
            message.created_at.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        )

        lines.append(
            f"[{timestamp}] "
            f"{message.author} "
            f"({message.author.id})"
        )

        if message.reference:
            lines.append(
                f"REPLY: "
                f"{message.reference.message_id}"
            )

        if message.content:
            lines.append(
                message.content
            )

        for index, embed in enumerate(
            message.embeds,
            start=1
        ):
            lines.append(
                f"EMBED {index}"
            )

            if embed.title:
                lines.append(
                    f"TITLE: "
                    f"{embed.title}"
                )

            if embed.description:
                lines.append(
                    f"DESCRIPTION: "
                    f"{embed.description}"
                )

            if embed.colour:
                lines.append(
                    f"COLOR: "
                    f"{embed.colour}"
                )

            for field in embed.fields:
                lines.append(
                    f"FIELD {field.name}: "
                    f"{field.value}"
                )

            if (
                embed.footer
                and embed.footer.text
            ):
                lines.append(
                    f"FOOTER: "
                    f"{embed.footer.text}"
                )

        for attachment in message.attachments:
            lines.append(
                f"ATTACHMENT: "
                f"{attachment.filename} "
                f"{attachment.url}"
            )

        lines.append("")

    return "\n".join(
        lines
    )


async def close_ticket_channel(
    channel,
    ticket,
    reason
):
    log_action(
        "ticket_close_started",
        ticket=ticket.get(
            "number"
        ),
        channel=(
            f"{channel.name}"
            f"({channel.id})"
        ),
        reason=reason
    )

    guild = channel.guild

    transcript_channel = (
        await get_configured_channel(
            guild,
            TRANSCRIPT_CHANNEL
        )
    )

    if transcript_channel is None:
        await channel.send(
            embed=discord.Embed(
                description=(
                    f"{emoji_text(ANIMATED_X_EMOJI)}"
                    f"{DOT} "
                    "**The transcript channel could not be found. "
                    "The ticket was not deleted.**"
                ),
                colour=COLOR_ERROR
            )
        )

        return False

    transcript_text = await build_transcript(
        channel
    )

    opener = guild.get_member(
        int(
            ticket[
                "opener_id"
            ]
        )
    )

    trader = guild.get_member(
        int(
            ticket[
                "trader_id"
            ]
        )
    )

    try:
        await transcript_channel.send(
            view=TranscriptLogLayout(
                ticket,
                opener,
                trader,
                reason
            ),
            allowed_mentions=discord.AllowedMentions.none()
        )

        transcript_file = discord.File(
            io.BytesIO(
                transcript_text.encode(
                    "utf-8"
                )
            ),
            filename=(
                f"ticket-"
                f"{ticket['number']}-"
                "transcript.txt"
            )
        )

        await transcript_channel.send(
            file=transcript_file
        )

    except discord.HTTPException:
        logger.exception(
            "Failed to log transcript for ticket %s",
            ticket[
                "number"
            ]
        )

        await channel.send(
            embed=discord.Embed(
                description=(
                    f"{emoji_text(ANIMATED_X_EMOJI)}"
                    f"{DOT} "
                    "**The transcript could not be saved. "
                    "The ticket was not deleted.**"
                ),
                colour=COLOR_ERROR
            )
        )

        return False

    async with DATA_LOCK:
        DATA[
            "tickets"
        ].pop(
            str(
                channel.id
            ),
            None
        )

        save_data_now()

    monitor_task = MONITOR_TASKS.pop(
        str(
            channel.id
        ),
        None
    )

    if (
        monitor_task is not None
        and not monitor_task.done()
    ):
        monitor_task.cancel()

    baseline_task = BASELINE_TASKS.pop(
        str(
            channel.id
        ),
        None
    )

    if (
        baseline_task is not None
        and not baseline_task.done()
    ):
        baseline_task.cancel()

    cancel_countdown(
        channel.id,
        "release"
    )

    cancel_countdown(
        channel.id,
        "address"
    )

    TICKET_LOCKS.pop(
        str(
            channel.id
        ),
        None
    )

    try:
        await channel.delete(
            reason=reason
        )

    except discord.HTTPException:
        logger.exception(
            "Failed to delete ticket channel %s",
            channel.id
        )

        return False

    log_action(
        "ticket_closed",
        ticket=ticket.get(
            "number"
        ),
        channel_id=channel.id
    )

    return True


class RequestModal(
    discord.ui.Modal
):
    def __init__(
        self,
        ticket_type
    ):
        super().__init__(
            title="Fill out the format",
            timeout=300
        )

        self.ticket_type = ticket_type

        self.trader = discord.ui.TextInput(
            label=(
                "Paste Your Trader's Username or ID"
            ),
            placeholder=(
                "e.g.: kookie.py / 693059117761429610"
            ),
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=100
        )

        self.your_item = discord.ui.TextInput(
            label="What are You giving?",
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=2,
            max_length=1000
        )

        self.trader_item = discord.ui.TextInput(
            label=(
                "What is Your Trader giving?"
            ),
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=2,
            max_length=1000
        )

        self.add_item(
            self.trader
        )

        self.add_item(
            self.your_item
        )

        self.add_item(
            self.trader_item
        )

    async def on_submit(
        self,
        interaction
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Tickets can only be created inside a server.",
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        trader = await resolve_trader(
            interaction.guild,
            self.trader.value
        )

        if trader is None:
            await interaction.followup.send(
                "I could not find that trader. "
                "Use their exact username, mention, or user ID.",
                ephemeral=True
            )

            return

        if trader.bot:
            await interaction.followup.send(
                "The trader cannot be a bot.",
                ephemeral=True
            )

            return

        if (
            trader.id
            == interaction.user.id
        ):
            await interaction.followup.send(
                "You cannot open a ticket with yourself.",
                ephemeral=True
            )

            return

        category = await get_ticket_category(
            interaction.guild
        )

        if category is None:
            await interaction.followup.send(
                "The ticket category could not be found. "
                "Set TICKET_CATEGORY to a category ID.",
                ephemeral=True
            )

            return

        number = await reserve_ticket_number()

        opener = interaction.user

        channel_name = (
            f"{self.ticket_type}-"
            f"{clean_channel_name(opener.display_name)}-"
            f"{number}"
        )

        try:
            channel = await create_ticket_channel(
                interaction.guild,
                channel_name,
                opener,
                trader,
                (
                    f"Middleman ticket {number}"
                )
            )

        except RuntimeError:
            await interaction.followup.send(
                "The ticket category could not be found. "
                "Set TICKET_CATEGORY to a category ID.",
                ephemeral=True
            )

            return

        except discord.HTTPException:
            logger.exception(
                "Failed to create ticket channel"
            )

            await interaction.followup.send(
                "Discord rejected the ticket creation request. "
                "Check the bot's Manage Channels permission and ticket category.",
                ephemeral=True
            )

            return

        ticket = {
            "number": number,
            "guild_id": interaction.guild.id,
            "channel_id": channel.id,
            "type": self.ticket_type,
            "opener_id": opener.id,
            "trader_id": trader.id,
            "opener_side": self.your_item.value,
            "trader_side": self.trader_item.value,
            "sender_id": None,
            "receiver_id": None,
            "role_confirmed": [],
            "usd_amount": None,
            "usd_confirmed": [],
            "crypto_price": None,
            "crypto_amount": None,
            "deposit_address": None,
            "deposit_txid": None,
            "deposit_amount": None,
            "deposit_confirmations": 0,
            "baseline_txids": [],
            "manual_deposit_override": False,
            "manual_reference": None,
            "receiver_address": None,
            "release_authorized": False,
            "release_confirm_ready": False,
            "release_countdown_end": 0,
            "address_confirm_ready": False,
            "address_countdown_end": 0,
            "payout_txid": None,
            "payout_amount": None,
            "payout_is_simulation": False,
            "uncancel_votes": [],
            "cancel_votes": [],
            "status": "created",
            "created_at": int(
                time.time()
            ),
            "completed_at": None,
            "stats_recorded": False,
            "completed_logged": False,
            "withdrawal_success_sent": False,
            "completed_channel_sent": False,
            "messages": {}
        }

        DATA[
            "tickets"
        ][
            str(
                channel.id
            )
        ] = ticket

        await save_data()

        opener_message = await channel.send(
            view=TicketOpenerLayout(
                opener,
                trader,
                ticket
            ),
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False
            )
        )

        ticket[
            "messages"
        ][
            "opener"
        ] = opener_message.id

        await save_data()

        log_action(
            "ticket_created",
            ticket=number,
            type=self.ticket_type,
            channel=(
                f"{channel.name}"
                f"({channel.id})"
            ),
            opener=(
                f"{opener}"
                f"({opener.id})"
            ),
            trader=(
                f"{trader}"
                f"({trader.id})"
            )
        )

        await send_role_selection(
            channel,
            ticket
        )

        await interaction.followup.send(
            f"**Ticket Created!** -> "
            f"{WORD_JOINER}"
            f"{channel.mention}",
            ephemeral=True
        )


class UsdAmountModal(
    discord.ui.Modal
):
    def __init__(self):
        super().__init__(
            title="Set USD Amount",
            timeout=300
        )

        self.amount = discord.ui.TextInput(
            label=(
                "Please state the amount in USD value"
            ),
            placeholder="e.g.: 435.20",
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=20
        )

        self.add_item(
            self.amount
        )

    async def on_submit(
        self,
        interaction
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_sender(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the selected sender can set the USD amount.",
                ephemeral=True
            )

            return

        amount = parse_positive_decimal(
            self.amount.value
        )

        if amount is None:
            await interaction.response.send_message(
                "Enter a valid USD amount.",
                ephemeral=True
            )

            return

        amount = amount.quantize(
            Decimal(
                "0.01"
            )
        )

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "usd_prompt"
            ):
                await interaction.response.send_message(
                    "This USD amount prompt is no longer active.",
                    ephemeral=True
                )

                return

            ticket[
                "usd_amount"
            ] = str(
                amount
            )

            ticket[
                "usd_confirmed"
            ] = []

            await save_data()

        old = await fetch_message(
            interaction.channel,
            ticket[
                "messages"
            ].get(
                "usd_prompt"
            )
        )

        if old is not None:
            try:
                await old.edit(
                    view=UsdPromptView(
                        disabled=True
                    )
                )

            except discord.HTTPException:
                pass

        await interaction.response.send_message(
            "USD amount submitted.",
            ephemeral=True
        )

        await send_usd_confirmation(
            interaction.channel,
            ticket
        )


class AddressModal(
    discord.ui.Modal
):
    def __init__(
        self,
        ticket
    ):
        title = (
            "Your LTC Address"
            if ticket[
                "type"
            ] == "ltc"
            else "Your USDT Address"
        )

        super().__init__(
            title=title,
            timeout=300
        )

        self.address = discord.ui.TextInput(
            label=title,
            placeholder=(
                f"Enter your "
                f"{get_asset_name(ticket)} address"
            ),
            style=discord.TextStyle.short,
            required=True,
            min_length=10,
            max_length=120
        )

        self.add_item(
            self.address
        )

    async def on_submit(
        self,
        interaction
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_receiver(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the receiver can submit the withdrawal address.",
                ephemeral=True
            )

            return

        address = self.address.value.strip()

        if (
            ticket[
                "type"
            ] == "usdt"
            and not re.fullmatch(
                r"0x[a-fA-F0-9]{40}",
                address
            )
        ):
            await interaction.response.send_message(
                "Enter a valid BSC address.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "address_prompt"
            ):
                await interaction.response.send_message(
                    "This address prompt is no longer active.",
                    ephemeral=True
                )

                return

            ticket[
                "receiver_address"
            ] = address

            await save_data()

            log_action(
                "receiver_address_submitted",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                ),
                asset=get_asset_name(
                    ticket
                ),
                address=address
            )

        old = await fetch_message(
            interaction.channel,
            ticket[
                "messages"
            ].get(
                "address_prompt"
            )
        )

        if old is not None:
            try:
                await old.edit(
                    view=AddressPromptView(
                        ticket=ticket,
                        disabled=True
                    )
                )

            except discord.HTTPException:
                pass

        await interaction.response.send_message(
            "Address submitted.",
            ephemeral=True
        )

        await send_address_confirmation(
            interaction.channel,
            ticket
        )


class RequestLTCButton(
    discord.ui.Button
):
    def __init__(self):
        super().__init__(
            label="Request LTC",
            style=discord.ButtonStyle.primary,
            emoji=custom_emoji(
                LTC_EMOJI
            ),
            custom_id="jace_mm_request_ltc"
        )

    async def callback(
        self,
        interaction
    ):
        log_action(
            "panel_request_clicked",
            user=(
                f"{interaction.user}"
                f"({interaction.user.id})"
            ),
            asset="LTC",
            guild=interaction.guild_id
        )

        await interaction.response.send_modal(
            RequestModal(
                "ltc"
            )
        )


class RequestUSDTButton(
    discord.ui.Button
):
    def __init__(self):
        super().__init__(
            label="Request USDT [BEP-20]",
            style=discord.ButtonStyle.success,
            emoji=custom_emoji(
                USDT_EMOJI
            ),
            custom_id="jace_mm_request_usdt"
        )

    async def callback(
        self,
        interaction
    ):
        log_action(
            "panel_request_clicked",
            user=(
                f"{interaction.user}"
                f"({interaction.user.id})"
            ),
            asset="USDT",
            guild=interaction.guild_id
        )

        await interaction.response.send_modal(
            RequestModal(
                "usdt"
            )
        )


class DeleteTicketButton(
    discord.ui.Button
):
    def __init__(self):
        super().__init__(
            label=(
                f"{DOT} Delete Ticket"
            ),
            style=discord.ButtonStyle.danger,
            emoji=custom_emoji(
                ANIMATED_X_EMOJI
            ),
            custom_id="jace_mm_delete_ticket"
        )

    async def callback(
        self,
        interaction
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if ticket is None:
            await interaction.response.send_message(
                "This ticket is no longer active.",
                ephemeral=True
            )

            return

        if (
            not is_admin(
                interaction.user
            )
            and not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "You cannot delete this ticket.",
                ephemeral=True
            )

            return

        funded_statuses = {
            "deposit_unconfirmed",
            "deposit_confirmed",
            "trade",
            "cancellation",
            "release_confirmation",
            "address_prompt",
            "address_confirmation",
            "settlement_pending",
            "completed"
        }

        if (
            ticket.get(
                "status"
            )
            in funded_statuses
            and not is_admin(
                interaction.user
            )
        ):
            await interaction.response.send_message(
                "Only an administrator can delete a funded ticket.",
                ephemeral=True
            )

            return

        log_action(
            "ticket_delete_requested",
            ticket=ticket.get(
                "number"
            ),
            user=(
                f"{interaction.user}"
                f"({interaction.user.id})"
            )
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    f"{emoji_text(ANIMATED_X_EMOJI)}"
                    f"{DOT} "
                    "**Deleting ticket...**"
                ),
                colour=COLOR_ERROR
            )
        )

        await asyncio.sleep(
            2
        )

        await close_ticket_channel(
            interaction.channel,
            ticket,
            (
                f"Ticket deleted by "
                f"{interaction.user}"
            )
        )


class MiddlemanPanel(
    discord.ui.LayoutView
):
    def __init__(self):
        super().__init__(
            timeout=None
        )

        tutorial_button = (
            discord.ui.Button(
                label="Tutorial",
                style=discord.ButtonStyle.link,
                url=TUTORIAL_URL
            )
        )

        header = discord.ui.Section(
            discord.ui.TextDisplay(
                f"{H1} "
                "Jace's Auto Middleman"
            ),
            discord.ui.TextDisplay(
                "> • **Paid Service**\n"
                
                "> • Read our ToS before using the bot: "
                f"{get_channel_mention(MM_TOS_CHANNEL)}"
            ),
            accessory=tutorial_button
        )

        fees = discord.ui.TextDisplay(
            f"{H2} Fees:\n"
            "\n"
            "> • Deals $250+: $1.50\n"
            
            "> • Deals under $250: $0.50\n"
            
            "> • Deals under $50 are __FREE__"
        )

        main_container = (
            discord.ui.Container(
                header,
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                fees,
                accent_colour=COLOR_NEUTRAL
            )
        )

        ltc_container = (
            discord.ui.Container(
                discord.ui.TextDisplay(
                    f"{H1} "
                    f"{LTC_EMOJI} "
                    "• Request Litecoin • "
                    f"{LTC_EMOJI}"
                ),
                discord.ui.ActionRow(
                    RequestLTCButton()
                ),
                accent_colour=COLOR_NEUTRAL
            )
        )

        usdt_container = (
            discord.ui.Container(
                discord.ui.TextDisplay(
                    f"{H1} "
                    f"{USDT_EMOJI} "
                    "• Request USDT [BEP-20] • "
                    f"{USDT_EMOJI}\n"
                    "\n"
                    "> • Network: **BSC (BEP-20)**"
                ),
                discord.ui.ActionRow(
                    RequestUSDTButton()
                ),
                accent_colour=COLOR_USDT
            )
        )

        self.add_item(
            main_container
        )

        self.add_item(
            ltc_container
        )

        self.add_item(
            usdt_container
        )

        biggest_trade_label = (
            f"[> Biggest Trade]({BIGGEST_TRADE_MESSAGE_URL})"
            if BIGGEST_TRADE_MESSAGE_URL
            else "> Biggest Trade"
        )

        self.add_item(
            discord.ui.TextDisplay(
                f"{biggest_trade_label}: "
                f"{get_channel_mention(DEMO_COMPLETED_TRANSACTION_CHANNEL)} "
                f"💬 `${BIGGEST_TRADE_USD:,.0f}`"
            )
        )


class TicketOpenerLayout(
    discord.ui.LayoutView
):
    def __init__(
        self,
        opener,
        trader,
        ticket
    ):
        super().__init__(
            timeout=None
        )

        mentions = (
            discord.ui.TextDisplay(
                f"{opener.mention} "
                f"{trader.mention}"
            )
        )

        title = discord.ui.TextDisplay(
            f"{H2} "
            f"{ANIMATED_WAVE_EMOJI} "
            f"{DOT} "
            "Jace's Auto Middleman Service"
        )

        instructions = (
            discord.ui.TextDisplay(
                "> Make sure to follow the steps and read "
                "the instructions thoroughly.\n"
                "> Please explicitly state the trade details "
                "if the information below is inaccurate.\n"
                "> By using this bot, you agree to our ToS "
                f"{get_channel_mention(MM_TOS_CHANNEL)}."
            )
        )

        opener_section = (
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"{opener.mention}'s side:"
                ),
                discord.ui.TextDisplay(
                    "```"
                    f"{safe_code_text(ticket['opener_side'])}"
                    "```"
                ),
                accessory=discord.ui.Thumbnail(
                    str(
                        opener.display_avatar.url
                    )
                )
            )
        )

        trader_section = (
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"{trader.mention}'s side:"
                ),
                discord.ui.TextDisplay(
                    "```"
                    f"{safe_code_text(ticket['trader_side'])}"
                    "```"
                ),
                accessory=discord.ui.Thumbnail(
                    str(
                        trader.display_avatar.url
                    )
                )
            )
        )

        container = discord.ui.Container(
            title,
            instructions,
            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small
            ),
            opener_section,
            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small
            ),
            trader_section,
            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small
            ),
            discord.ui.ActionRow(
                DeleteTicketButton()
            ),
            accent_colour=COLOR_NEUTRAL
        )

        self.add_item(
            mentions
        )

        self.add_item(
            container
        )


class TranscriptLogLayout(
    discord.ui.LayoutView
):
    def __init__(
        self,
        ticket,
        opener,
        trader,
        reason
    ):
        super().__init__(
            timeout=None
        )

        opener_name = (
            opener.mention
            if opener is not None
            else (
                f"<@{ticket['opener_id']}>"
            )
        )

        trader_name = (
            trader.mention
            if trader is not None
            else (
                f"<@{ticket['trader_id']}>"
            )
        )

        fallback_avatar = (
            str(
                bot.user.display_avatar.url
            )
            if bot.user is not None
            else (
                "https://cdn.discordapp.com/"
                "embed/avatars/0.png"
            )
        )

        opener_avatar = (
            str(
                opener.display_avatar.url
            )
            if opener is not None
            else fallback_avatar
        )

        trader_avatar = (
            str(
                trader.display_avatar.url
            )
            if trader is not None
            else fallback_avatar
        )

        sender_id = ticket.get(
            "sender_id"
        )

        receiver_id = ticket.get(
            "receiver_id"
        )

        deposit_amount = (
            ticket.get(
                "deposit_amount"
            )
            or "0"
        )

        payout_amount = (
            ticket.get(
                "payout_amount"
            )
            or "0"
        )

        title = discord.ui.TextDisplay(
            f"{H2} "
            f"Ticket {ticket['number']} Transcript"
        )

        timing = discord.ui.TextDisplay(
            f"Created: <t:{ticket['created_at']}:F>\n"
            f"Closed: <t:{int(time.time())}:F>\n"
            f"Reason: **{safe_code_text(reason)}**"
        )

        opener_section = (
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"{H2} Opener"
                ),
                discord.ui.TextDisplay(
                    f"{opener_name}\n"
                    f"ID: `{ticket['opener_id']}`\n"
                    "Trade info:\n"
                    "```"
                    f"{safe_code_text(ticket['opener_side'])}"
                    "```"
                ),
                accessory=discord.ui.Thumbnail(
                    opener_avatar
                )
            )
        )

        trader_section = (
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"{H2} Trader"
                ),
                discord.ui.TextDisplay(
                    f"{trader_name}\n"
                    f"ID: `{ticket['trader_id']}`\n"
                    "Trade info:\n"
                    "```"
                    f"{safe_code_text(ticket['trader_side'])}"
                    "```"
                ),
                accessory=discord.ui.Thumbnail(
                    trader_avatar
                )
            )
        )

        summary = discord.ui.TextDisplay(
            f"{H2} Trade Summary\n"
            f"Asset: **{get_asset_long_name(ticket)}**\n"
            f"Sender: "
            f"{f'<@{sender_id}>' if sender_id else 'Not selected'}\n"
            f"Receiver: "
            f"{f'<@{receiver_id}>' if receiver_id else 'Not selected'}\n"
            f"USD value: "
            f"**{money(ticket.get('usd_amount') or '0')}**\n"
            f"Amount received by escrow address: "
            f"**{crypto_amount_text(ticket, deposit_amount)} "
            f"{get_asset_name(ticket)}**\n"
            f"Escrow deposit address: "
            f"`{ticket.get('deposit_address') or 'N/A'}`\n"
            f"Deposit reference: "
            f"`{ticket.get('deposit_txid') or 'N/A'}`\n"
            f"Receiver payout address: "
            f"`{ticket.get('receiver_address') or 'N/A'}`\n"
            f"Amount sent to receiver: "
            f"**{crypto_amount_text(ticket, payout_amount)} "
            f"{get_asset_name(ticket)}**\n"
            f"Payout transaction: "
            f"`{ticket.get('payout_txid') or 'N/A'}`"
        )

        container = discord.ui.Container(
            title,
            timing,
            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small
            ),
            opener_section,
            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small
            ),
            trader_section,
            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small
            ),
            summary,
            accent_colour=(
                COLOR_SUCCESS
                if ticket.get(
                    "status"
                )
                == "completed"
                else COLOR_NEUTRAL
            )
        )

        self.add_item(
            container
        )


class PanelButtonsPersistentView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=None
        )

        self.add_item(
            RequestLTCButton()
        )

        self.add_item(
            RequestUSDTButton()
        )


class DeleteTicketPersistentView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=None
        )

        self.add_item(
            DeleteTicketButton()
        )


class RoleSelectionView(
    discord.ui.View
):
    def __init__(
        self,
        ticket=None,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        if ticket is not None:
            self.sender_button.disabled = (
                disabled
                or bool(
                    ticket.get(
                        "sender_id"
                    )
                )
            )

            self.receiver_button.disabled = (
                disabled
                or bool(
                    ticket.get(
                        "receiver_id"
                    )
                )
            )

            self.reset_button.disabled = (
                disabled
            )

        elif disabled:
            self.sender_button.disabled = True
            self.receiver_button.disabled = True
            self.reset_button.disabled = True

    async def choose(
        self,
        interaction,
        role
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can select roles.",
                ephemeral=True
            )

            return

        complete = False

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "role_selection"
            ):
                await interaction.response.send_message(
                    "Role selection is no longer active.",
                    ephemeral=True
                )

                return

            user_id = interaction.user.id

            if (
                ticket.get(
                    "sender_id"
                )
                == user_id
                or ticket.get(
                    "receiver_id"
                )
                == user_id
            ):
                await interaction.response.send_message(
                    "You already selected a role.",
                    ephemeral=True
                )

                return

            key = (
                f"{role}_id"
            )

            if ticket.get(
                key
            ):
                await interaction.response.send_message(
                    "That role has already been selected.",
                    ephemeral=True
                )

                return

            ticket[
                key
            ] = user_id

            complete = bool(
                ticket.get(
                    "sender_id"
                )
                and ticket.get(
                    "receiver_id"
                )
            )

            await save_data()

            log_action(
                "role_selected",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                ),
                role=role
            )

        await interaction.response.edit_message(
            embed=role_selection_embed(
                ticket
            ),
            view=RoleSelectionView(
                ticket,
                disabled=complete
            )
        )

        if complete:
            await send_role_confirmation(
                interaction.channel,
                ticket
            )

    @discord.ui.button(
        label="Sender",
        style=discord.ButtonStyle.primary,
        custom_id="jace_mm_role_sender"
    )
    async def sender_button(
        self,
        interaction,
        button
    ):
        await self.choose(
            interaction,
            "sender"
        )

    @discord.ui.button(
        label="Receiver",
        style=discord.ButtonStyle.primary,
        custom_id="jace_mm_role_receiver"
    )
    async def receiver_button(
        self,
        interaction,
        button
    ):
        await self.choose(
            interaction,
            "receiver"
        )

    @discord.ui.button(
        label="Reset",
        style=discord.ButtonStyle.danger,
        custom_id="jace_mm_role_reset"
    )
    async def reset_button(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if ticket is None:
            await interaction.response.send_message(
                "This ticket is no longer active.",
                ephemeral=True
            )

            return

        if (
            not is_ticket_party(
                interaction,
                ticket
            )
            and not is_admin(
                interaction.user
            )
        ):
            await interaction.response.send_message(
                "You cannot reset this selection.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "role_selection"
            ):
                await interaction.response.send_message(
                    "Role selection is no longer active.",
                    ephemeral=True
                )

                return

            ticket[
                "sender_id"
            ] = None

            ticket[
                "receiver_id"
            ] = None

            ticket[
                "role_confirmed"
            ] = []

            await save_data()

        await interaction.response.edit_message(
            embed=role_selection_embed(
                ticket
            ),
            view=RoleSelectionView(
                ticket
            )
        )


class RoleConfirmationView(
    discord.ui.View
):
    def __init__(
        self,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        self.correct.disabled = disabled
        self.incorrect.disabled = disabled

    @discord.ui.button(
        label="Correct",
        style=discord.ButtonStyle.success,
        emoji=custom_emoji(
            GREEN_TICK_EMOJI
        ),
        custom_id="jace_mm_roles_correct"
    )
    async def correct(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can confirm the roles.",
                ephemeral=True
            )

            return

        both = False

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "role_confirmation"
            ):
                await interaction.response.send_message(
                    "This confirmation is no longer active.",
                    ephemeral=True
                )

                return

            user_id = interaction.user.id

            if user_id in ticket[
                "role_confirmed"
            ]:
                await interaction.response.send_message(
                    "You already confirmed the roles.",
                    ephemeral=True
                )

                return

            ticket[
                "role_confirmed"
            ].append(
                user_id
            )

            both = {
                int(
                    ticket[
                        "sender_id"
                    ]
                ),
                int(
                    ticket[
                        "receiver_id"
                    ]
                )
            }.issubset(
                set(
                    ticket[
                        "role_confirmed"
                    ]
                )
            )

            if both:
                ticket[
                    "status"
                ] = "role_confirmation_complete"

            await save_data()

            log_action(
                "roles_confirmed_click",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                ),
                both_confirmed=both
            )

        if both:
            await interaction.response.edit_message(
                view=RoleConfirmationView(
                    disabled=True
                )
            )

        else:
            await interaction.response.defer()

        await interaction.followup.send(
            embed=role_correct_embed(
                interaction.user
            ),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
        )

        if both:
            await send_usd_prompt(
                interaction.channel,
                ticket
            )

    @discord.ui.button(
        label="Incorrect",
        style=discord.ButtonStyle.danger,
        emoji=custom_emoji(
            ANIMATED_X_EMOJI
        ),
        custom_id="jace_mm_roles_incorrect"
    )
    async def incorrect(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can mark the roles incorrect.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "role_confirmation"
            ):
                await interaction.response.send_message(
                    "This confirmation is no longer active.",
                    ephemeral=True
                )

                return

            ticket[
                "status"
            ] = "role_resetting"

            await save_data()

            log_action(
                "roles_marked_incorrect",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                )
            )

        await interaction.response.edit_message(
            view=RoleConfirmationView(
                disabled=True
            )
        )

        await interaction.followup.send(
            embed=role_incorrect_embed(
                interaction.user
            ),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
        )

        await send_role_selection(
            interaction.channel,
            ticket
        )


class UsdPromptView(
    discord.ui.View
):
    def __init__(
        self,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        self.set_amount.disabled = (
            disabled
        )

    @discord.ui.button(
        label="Set USD Amount",
        style=discord.ButtonStyle.primary,
        custom_id="jace_mm_set_usd"
    )
    async def set_amount(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_sender(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the sender can set the USD amount.",
                ephemeral=True
            )

            return

        if ticket.get(
            "status"
        ) != "usd_prompt":
            await interaction.response.send_message(
                "The USD amount is no longer being set here.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            UsdAmountModal()
        )


class UsdConfirmationView(
    discord.ui.View
):
    def __init__(
        self,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        self.correct.disabled = disabled
        self.incorrect.disabled = disabled

    @discord.ui.button(
        label="Correct",
        style=discord.ButtonStyle.success,
        emoji=custom_emoji(
            GREEN_TICK_EMOJI
        ),
        custom_id="jace_mm_usd_correct"
    )
    async def correct(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can confirm the amount.",
                ephemeral=True
            )

            return

        both = False

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "usd_confirmation"
            ):
                await interaction.response.send_message(
                    "This amount confirmation is no longer active.",
                    ephemeral=True
                )

                return

            user_id = interaction.user.id

            if user_id in ticket[
                "usd_confirmed"
            ]:
                await interaction.response.send_message(
                    "You already confirmed the USD amount.",
                    ephemeral=True
                )

                return

            ticket[
                "usd_confirmed"
            ].append(
                user_id
            )

            both = {
                int(
                    ticket[
                        "sender_id"
                    ]
                ),
                int(
                    ticket[
                        "receiver_id"
                    ]
                )
            }.issubset(
                set(
                    ticket[
                        "usd_confirmed"
                    ]
                )
            )

            if both:
                ticket[
                    "status"
                ] = "usd_confirmation_complete"

            await save_data()

            log_action(
                "usd_amount_confirmed_click",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                ),
                both_confirmed=both
            )

        if both:
            await interaction.response.edit_message(
                view=UsdConfirmationView(
                    disabled=True
                )
            )

        else:
            await interaction.response.defer()

        await interaction.followup.send(
            embed=usd_correct_embed(
                interaction.user
            ),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
        )

        if both:
            await send_payment_info(
                interaction.channel,
                ticket
            )

    @discord.ui.button(
        label="Incorrect",
        style=discord.ButtonStyle.danger,
        emoji=custom_emoji(
            ANIMATED_X_EMOJI
        ),
        custom_id="jace_mm_usd_incorrect"
    )
    async def incorrect(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can mark the amount incorrect.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "usd_confirmation"
            ):
                await interaction.response.send_message(
                    "This amount confirmation is no longer active.",
                    ephemeral=True
                )

                return

            ticket[
                "usd_amount"
            ] = None

            ticket[
                "usd_confirmed"
            ] = []

            ticket[
                "status"
            ] = "usd_resetting"

            await save_data()

            log_action(
                "usd_amount_marked_incorrect",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                )
            )

        await interaction.response.edit_message(
            view=UsdConfirmationView(
                disabled=True
            )
        )

        await interaction.followup.send(
            embed=usd_incorrect_embed(
                interaction.user
            ),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
        )

        await send_usd_prompt(
            interaction.channel,
            ticket
        )


class PaymentInfoView(
    discord.ui.View
):
    def __init__(
        self,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        self.copy_details.disabled = (
            disabled
        )

    @discord.ui.button(
        label="Copy Details",
        style=discord.ButtonStyle.primary,
        custom_id="jace_mm_copy_details"
    )
    async def copy_details(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can use this button.",
                ephemeral=True
            )

            return

        log_action(
            "payment_details_copied",
            ticket=ticket.get(
                "number"
            ),
            user=(
                f"{interaction.user}"
                f"({interaction.user.id})"
            )
        )

        await interaction.response.edit_message(
            view=PaymentInfoView(
                disabled=True
            )
        )

        await interaction.followup.send(
            ticket[
                "deposit_address"
            ]
        )

        await interaction.followup.send(
            required_crypto_display(
                ticket
            )
        )


class ProceedView(
    discord.ui.View
):
    def __init__(
        self,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        self.release.disabled = disabled
        self.cancel.disabled = disabled

    @discord.ui.button(
        label="Release",
        style=discord.ButtonStyle.success,
        custom_id="jace_mm_release"
    )
    async def release(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_sender(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the sender can release the escrow.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "trade"
            ):
                await interaction.response.send_message(
                    "The trade is not currently ready for release.",
                    ephemeral=True
                )

                return

            ticket[
                "status"
            ] = "release_starting"

            await save_data()

            log_action(
                "release_requested",
                ticket=ticket.get(
                    "number"
                ),
                sender=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                )
            )

        await interaction.response.defer()

        await send_release_confirmation(
            interaction.channel,
            ticket
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="jace_mm_cancel"
    )
    async def cancel(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can request cancellation.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "trade"
            ):
                await interaction.response.send_message(
                    "Cancellation is not available right now.",
                    ephemeral=True
                )

                return

            ticket[
                "uncancel_votes"
            ] = []

            ticket[
                "cancel_votes"
            ] = []

            ticket[
                "status"
            ] = "cancellation"

            await save_data()

            log_action(
                "cancellation_requested",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                )
            )

        await interaction.response.send_message(
            content=(
                f"<@{ticket['sender_id']}> "
                f"<@{ticket['receiver_id']}>"
            ),
            embed=cancellation_embed(
                ticket
            ),
            view=CancellationView(),
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False
            )
        )

        message = (
            await interaction.original_response()
        )

        ticket[
            "messages"
        ][
            "cancellation"
        ] = message.id

        await save_data()


class CancellationView(
    discord.ui.View
):
    def __init__(
        self,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        self.uncancel.disabled = disabled
        self.confirm_cancel.disabled = disabled

    async def vote(
        self,
        interaction,
        choice
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_ticket_party(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the two traders can vote on cancellation.",
                ephemeral=True
            )

            return

        uncancel_done = False
        cancel_done = False

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "cancellation"
            ):
                await interaction.response.send_message(
                    "This cancellation vote is no longer active.",
                    ephemeral=True
                )

                return

            user_id = interaction.user.id

            if choice == "uncancel":
                if user_id not in ticket[
                    "uncancel_votes"
                ]:
                    ticket[
                        "uncancel_votes"
                    ].append(
                        user_id
                    )

                ticket[
                    "cancel_votes"
                ] = [
                    value
                    for value
                    in ticket[
                        "cancel_votes"
                    ]
                    if value
                    != user_id
                ]

            else:
                if user_id not in ticket[
                    "cancel_votes"
                ]:
                    ticket[
                        "cancel_votes"
                    ].append(
                        user_id
                    )

                ticket[
                    "uncancel_votes"
                ] = [
                    value
                    for value
                    in ticket[
                        "uncancel_votes"
                    ]
                    if value
                    != user_id
                ]

            parties = {
                int(
                    ticket[
                        "sender_id"
                    ]
                ),
                int(
                    ticket[
                        "receiver_id"
                    ]
                )
            }

            uncancel_done = (
                parties.issubset(
                    set(
                        ticket[
                            "uncancel_votes"
                        ]
                    )
                )
            )

            cancel_done = (
                parties.issubset(
                    set(
                        ticket[
                            "cancel_votes"
                        ]
                    )
                )
            )

            if uncancel_done:
                ticket[
                    "status"
                ] = "trade"

            elif cancel_done:
                ticket[
                    "status"
                ] = "cancelled_pending_settlement"

            await save_data()

            log_action(
                "cancellation_vote",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                ),
                choice=choice,
                uncancel_complete=uncancel_done,
                cancel_complete=cancel_done
            )

        await interaction.response.edit_message(
            embed=cancellation_embed(
                ticket
            ),
            view=CancellationView(
                disabled=(
                    uncancel_done
                    or cancel_done
                )
            )
        )

        if uncancel_done:
            ticket[
                "uncancel_votes"
            ] = []

            ticket[
                "cancel_votes"
            ] = []

            await save_data()

            proceed_message = await fetch_message(
                interaction.channel,
                ticket[
                    "messages"
                ].get(
                    "proceed"
                )
            )

            kwargs = {
                "content": (
                    f"{emoji_text(GREEN_TICK_EMOJI)}"
                    "Trade Resumed"
                )
            }

            if proceed_message is not None:
                kwargs[
                    "reference"
                ] = proceed_message

                kwargs[
                    "mention_author"
                ] = False

            await interaction.followup.send(
                **kwargs
            )

        elif cancel_done:
            await interaction.followup.send(
                embed=discord.Embed(
                    description=(
                        f"{emoji_text(ANIMATED_X_EMOJI)}"
                        f"{DOT} "
                        "**Cancellation Confirmed**\n\n"
                        "The trade has been cancelled. "
                        "Any deposited funds require settlement "
                        "or refund handling before this ticket is closed."
                    ),
                    colour=COLOR_ERROR
                )
            )

    @discord.ui.button(
        label="Uncancel",
        style=discord.ButtonStyle.secondary,
        custom_id="jace_mm_uncancel"
    )
    async def uncancel(
        self,
        interaction,
        button
    ):
        await self.vote(
            interaction,
            "uncancel"
        )

    @discord.ui.button(
        label="Confirm Cancellation",
        style=discord.ButtonStyle.danger,
        custom_id="jace_mm_confirm_cancel"
    )
    async def confirm_cancel(
        self,
        interaction,
        button
    ):
        await self.vote(
            interaction,
            "cancel"
        )


class ReleaseConfirmationView(
    discord.ui.View
):
    def __init__(
        self,
        countdown=None,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        if countdown is not None:
            self.confirm.label = (
                f"Confirm ({countdown})"
            )

            self.confirm.disabled = True

        if disabled:
            self.confirm.disabled = True
            self.back.disabled = True

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
        custom_id="jace_mm_release_confirm"
    )
    async def confirm(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_sender(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the sender can confirm the release.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "release_confirmation"
            ):
                await interaction.response.send_message(
                    "This release confirmation is no longer active.",
                    ephemeral=True
                )

                return

            ready = (
                ticket.get(
                    "release_confirm_ready"
                )
                or time.time()
                >= float(
                    ticket.get(
                        "release_countdown_end",
                        0
                    )
                )
            )

            if not ready:
                await interaction.response.send_message(
                    "Please wait for the confirmation countdown.",
                    ephemeral=True
                )

                return

            ticket[
                "release_authorized"
            ] = True

            ticket[
                "release_confirm_ready"
            ] = True

            ticket[
                "status"
            ] = "address_starting"

            await save_data()

            log_action(
                "release_confirmed",
                ticket=ticket.get(
                    "number"
                ),
                sender=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                )
            )

        cancel_countdown(
            interaction.channel_id,
            "release"
        )

        await interaction.response.edit_message(
            view=ReleaseConfirmationView(
                disabled=True
            )
        )

        await send_address_prompt(
            interaction.channel,
            ticket
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        custom_id="jace_mm_release_back"
    )
    async def back(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_sender(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the sender can use this button.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "release_confirmation"
            ):
                await interaction.response.send_message(
                    "This release confirmation is no longer active.",
                    ephemeral=True
                )

                return

            ticket[
                "status"
            ] = "trade"

            ticket[
                "release_confirm_ready"
            ] = False

            ticket[
                "release_countdown_end"
            ] = 0

            await save_data()

            log_action(
                "release_confirmation_back",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                )
            )

        cancel_countdown(
            interaction.channel_id,
            "release"
        )

        await interaction.response.edit_message(
            view=ReleaseConfirmationView(
                disabled=True
            )
        )


class AddressPromptView(
    discord.ui.View
):
    def __init__(
        self,
        ticket=None,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        if (
            ticket is not None
            and ticket.get(
                "type"
            )
            == "usdt"
        ):
            self.enter_address.label = (
                "Enter Your USDT Address"
            )

        self.enter_address.disabled = (
            disabled
        )

    @discord.ui.button(
        label="Enter Your LTC Address",
        style=discord.ButtonStyle.primary,
        custom_id="jace_mm_enter_address"
    )
    async def enter_address(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_receiver(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the receiver can enter the withdrawal address.",
                ephemeral=True
            )

            return

        if ticket.get(
            "status"
        ) != "address_prompt":
            await interaction.response.send_message(
                "This address prompt is no longer active.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            AddressModal(
                ticket
            )
        )


class AddressConfirmationView(
    discord.ui.View
):
    def __init__(
        self,
        countdown=None,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        if countdown is not None:
            self.confirm.label = (
                f"Confirm ({countdown})"
            )

            self.confirm.disabled = True

        if disabled:
            self.confirm.disabled = True
            self.back.disabled = True

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
        custom_id="jace_mm_address_confirm"
    )
    async def confirm(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_receiver(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the receiver can confirm this address.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "address_confirmation"
            ):
                await interaction.response.send_message(
                    "This address confirmation is no longer active.",
                    ephemeral=True
                )

                return

            ready = (
                ticket.get(
                    "address_confirm_ready"
                )
                or time.time()
                >= float(
                    ticket.get(
                        "address_countdown_end",
                        0
                    )
                )
            )

            if not ready:
                await interaction.response.send_message(
                    "Please wait for the confirmation countdown.",
                    ephemeral=True
                )

                return

            ticket[
                "address_confirm_ready"
            ] = True

            ticket[
                "status"
            ] = "settlement_pending"

            await save_data()

            log_action(
                "receiver_address_confirmed",
                ticket=ticket.get(
                    "number"
                ),
                receiver=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                ),
                address=ticket.get(
                    "receiver_address"
                )
            )

        cancel_countdown(
            interaction.channel_id,
            "address"
        )

        await interaction.response.edit_message(
            view=AddressConfirmationView(
                disabled=True
            )
        )

        sending_message = (
            await interaction.channel.send(
                embed=sending_embed()
            )
        )

        await asyncio.sleep(
            2
        )

        try:
            await sending_message.delete()

        except discord.HTTPException:
            pass

        if (
            SETTLEMENT_MODE.lower()
            == "simulation"
        ):
            fake_reference = (
                f"SIMULATION-"
                f"{secrets.token_hex(24).upper()}"
            )

            await finalize_withdrawal(
                ticket,
                fake_reference,
                ticket[
                    "deposit_amount"
                ],
                simulation=True
            )

            return

        await interaction.channel.send(
            embed=settlement_pending_embed(
                ticket
            )
        )

        if not await send_settlement_request(
            ticket
        ):
            await interaction.channel.send(
                embed=discord.Embed(
                    description=(
                        f"{emoji_text(ANIMATED_X_EMOJI)}"
                        f"{DOT} "
                        "**The settlement channel could not be found. "
                        "An administrator must resolve the configuration.**"
                    ),
                    colour=COLOR_ERROR
                )
            )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        custom_id="jace_mm_address_back"
    )
    async def back(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if (
            ticket is None
            or not is_receiver(
                interaction,
                ticket
            )
        ):
            await interaction.response.send_message(
                "Only the receiver can use this button.",
                ephemeral=True
            )

            return

        async with get_ticket_lock(
            interaction.channel_id
        ):
            ticket = get_ticket(
                interaction.channel_id
            )

            if (
                ticket is None
                or ticket.get(
                    "status"
                )
                != "address_confirmation"
            ):
                await interaction.response.send_message(
                    "This address confirmation is no longer active.",
                    ephemeral=True
                )

                return

            ticket[
                "receiver_address"
            ] = None

            ticket[
                "address_confirm_ready"
            ] = False

            ticket[
                "address_countdown_end"
            ] = 0

            ticket[
                "status"
            ] = "address_prompt"

            await save_data()

            log_action(
                "receiver_address_back",
                ticket=ticket.get(
                    "number"
                ),
                user=(
                    f"{interaction.user}"
                    f"({interaction.user.id})"
                )
            )

        cancel_countdown(
            interaction.channel_id,
            "address"
        )

        await interaction.response.edit_message(
            view=AddressConfirmationView(
                disabled=True
            )
        )

        await send_address_prompt(
            interaction.channel,
            ticket
        )


class CloseTicketView(
    discord.ui.View
):
    def __init__(
        self,
        disabled=False
    ):
        super().__init__(
            timeout=None
        )

        self.close_ticket.disabled = (
            disabled
        )

    @discord.ui.button(
        label=f"{DOT} Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji=custom_emoji(
            LOCK_EMOJI
        ),
        custom_id="jace_mm_close_ticket"
    )
    async def close_ticket(
        self,
        interaction,
        button
    ):
        ticket = get_ticket(
            interaction.channel_id
        )

        if ticket is None:
            await interaction.response.send_message(
                "This ticket is no longer active.",
                ephemeral=True
            )

            return

        if (
            not is_ticket_party(
                interaction,
                ticket
            )
            and not is_admin(
                interaction.user
            )
        ):
            await interaction.response.send_message(
                "You cannot close this ticket.",
                ephemeral=True
            )

            return

        if ticket.get(
            "status"
        ) != "completed":
            await interaction.response.send_message(
                "This ticket has not been completed yet.",
                ephemeral=True
            )

            return

        log_action(
            "ticket_close_button_clicked",
            ticket=ticket.get(
                "number"
            ),
            user=(
                f"{interaction.user}"
                f"({interaction.user.id})"
            )
        )

        await send_completion_outputs(
            ticket
        )

        if not ticket.get(
            "completed_channel_sent"
        ):
            await interaction.response.send_message(
                "The completed transaction log could not be saved, "
                "so the ticket was not closed.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            view=None
        )

        await interaction.followup.send(
            embed=discord.Embed(
                description=(
                    f"{emoji_text(ANIMATED_X_EMOJI)}"
                    f"{DOT} "
                    "**Closing ticket...**"
                ),
                colour=COLOR_ERROR
            )
        )

        await asyncio.sleep(
            3
        )

        await close_ticket_channel(
            interaction.channel,
            ticket,
            (
                "Completed ticket closed by "
                f"{interaction.user}"
            )
        )




def automm_tos_notice_text():
    return (
        f"> The ToS in {get_channel_mention(MM_TOS_CHANNEL)} also apply here.\n"
        "> You can start a trade with the Automatic MM Bot here: "
        f"{get_channel_mention(AUTOMM_TRADE_CHANNEL)}"
    )


def automm_tos_embed():
    return discord.Embed(
        description=(
            "While using our Automatic Middleman Bot, you must agree to a few things.\n"
            "\n"
            "`1` We are not responsible for any losses caused by user mistakes, such as sending funds to the wrong address or network, entering incorrect amounts/addresses, discord account getting compromised, etc.\n"
            "\n"
            "`2` We are not responsible for losses caused by third-party interruptions, such as rollbacks, terminations, or duped items.\n"
            "\n"
            "`3` Trades involving prohibited items (e.g., Nitro, Gift Cards / Codes, Accounts, Joins, Scripts, Methods, Discord Assets, Suppliers, Contacts, Websites, Files, Links, UGC, KYC, Auths, Phone Numbers, Credentials, Services, Advertisements, Subscriptions) are not allowed.\n"
            "\n"
            "`•` We are not responsible for any consequences if such trades proceed, and we will not provide support for prohibited trades in case of a dispute.\n"
            "\n"
            "`4` Disputes are handled fairly; however, if a party is inactive or uncooperative, funds may be released to the other trader. Traders (usually the Receiver) have 24 hours to respond to a cancellation request before funds are returned to the Sender.\n"
            "\n"
            "`5` You may impose your own ToS/rules/warranties for deals, but they must be stated in the ticket via your own message **BEFORE** the deal starts, and explicitly agreed to by your trader. If your trader does not notice or agree to them, they do not apply. Edited ToS messages especially in DMs will be voided.\n"
            "\n"
            "`•` You cannot impose absurd, illegal (by law), or predatory rules. Our ToS and judgment overrule yours if we deem them unreasonable or illogical.\n"
            "\n"
            "`•` You cannot refuse to refund a refundable payment (mostly exchangers). If your trader gives you something that was not as described and you are able to refund it, you must do so.\n"
            "\n"
            "`•` Any third-party fees incurred during a refund (e.g. network/app handling fees, NOT your own personal fee) shall be covered by the other trader.\n"
            "\n"
            "`6` For currency trades (Crypto, PayPal, Robux, etc.), fees and taxes must be agreed upon beforehand. The receiver is entitled to the full agreed amount unless otherwise stated."
        ),
        colour=COLOR_NEUTRAL
    )


class AutoMMTosView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="View ToS",
        style=discord.ButtonStyle.primary,
        custom_id="jace_mm_view_tos"
    )
    async def view_tos(
        self,
        interaction,
        button
    ):
        await interaction.response.send_message(
            embed=automm_tos_embed(),
            ephemeral=True
        )


HALAL_DEAL_TYPES = [
    (
        "ingame",
        "In-Game",
        "Before continuing, please state the game, items, usernames, and delivery method.",
        "Ex. 10k coins via in-game mail, SellerUser → BuyerUser"
    ),
    (
        "robux",
        "Robux",
        "Before continuing, please state the Robux amount, delivery method (game pass, group payout, or ingame gift), and both Roblox usernames.",
        "Ex. 50,000 Robux via gamepass, SellerUser → BuyerUser"
    ),
    (
        "adoptme",
        "Adopt Me",
        "Before continuing, please state the Adopt Me items, both Roblox usernames, and how the items will be delivered.",
        "Ex. Frost Dragon via trade, SellerUser → BuyerUser"
    ),
    (
        "mm2",
        "MM2",
        "Before continuing, please state the Murder Mystery 2 items, both Roblox usernames, and how they will be traded.",
        "Ex. Chroma Laser via trade, SellerUser → BuyerUser"
    ),
    (
        "limiteds",
        "Limiteds",
        "Before continuing, please state the limited items, both Roblox usernames, and the delivery method.",
        "Ex. Korblox via trade, SellerUser → BuyerUser"
    ),
    (
        "nitro",
        "Discord Nitro",
        "Before continuing, please state the Nitro type, duration, and how it will be delivered.",
        "Ex. Nitro Boost 1 month via gift link"
    ),
    (
        "accounts",
        "Accounts",
        "Before continuing, please state the account type and what is included.",
        "Ex. Roblox account with limiteds, delivered via login"
    ),
    (
        "other",
        "Other",
        "Before continuing, please state exactly what is being traded and how it will be delivered.",
        "Ex. Describe the deal clearly"
    )
]


def halal_md_link(label, url):
    url = cleaned_secret(url)
    if not url:
        return label
    return f"[{label}]({url})"


def halal_thumb(url):
    url = cleaned_secret(url)
    if not url:
        return None
    return discord.ui.Thumbnail(url)


def qr_image_url(data):
    return (
        "https://api.qrserver.com/v1/create-qr-code/"
        f"?size=180x180&data={quote(str(data or ''), safe='')}"
    )


def halal_emoji_or(configured, fallback):
    return cleaned_secret(configured) or fallback


def halal_coins():
    return {
        "btc": {
            "key": "btc",
            "label": "Bitcoin",
            "short": "BTC",
            "panel": "Bitcoin",
            "complete": "Bitcoin",
            "group": "crypto",
            "family": "utxo",
            "chain": "btc",
            "decimals": 8,
            "price": "BTC-USD",
            "confirmations": 1,
            "explorer": "BlockCypher",
            "emoji": halal_emoji_or(HALAL_BTC_EMOJI, "₿"),
            "address": cleaned_secret(HALAL_BTC_ADDRESS)
        },
        "eth": {
            "key": "eth",
            "label": "Ethereum",
            "short": "ETH",
            "panel": "Ethereum",
            "complete": "Ethereum",
            "group": "crypto",
            "family": "eth",
            "chain_id": "1",
            "decimals": 18,
            "display_decimals": 8,
            "price": "ETH-USD",
            "confirmations": 1,
            "explorer": "Etherscan",
            "emoji": halal_emoji_or(HALAL_ETH_EMOJI, "◆"),
            "address": cleaned_secret(HALAL_ETH_ADDRESS)
        },
        "ltc": {
            "key": "ltc",
            "label": "Litecoin",
            "short": "LTC",
            "panel": "Litecoin",
            "complete": "Litecoin",
            "group": "crypto",
            "family": "utxo",
            "chain": "ltc",
            "decimals": 8,
            "price": "LTC-USD",
            "confirmations": LTC_CONFIRMATIONS_REQUIRED,
            "explorer": "BlockCypher",
            "emoji": halal_emoji_or(HALAL_LTC_EMOJI, LTC_EMOJI or "Ł"),
            "address": cleaned_secret(HALAL_LTC_ADDRESS) or LTC_DEPOSIT_ADDRESS
        },
        "sol": {
            "key": "sol",
            "label": "Solana",
            "short": "SOL",
            "panel": "Solana",
            "complete": "Solana",
            "group": "crypto",
            "family": "sol",
            "decimals": 9,
            "display_decimals": 8,
            "price": "SOL-USD",
            "confirmations": 1,
            "explorer": "Solscan",
            "emoji": halal_emoji_or(HALAL_SOL_EMOJI, "◎"),
            "address": cleaned_secret(HALAL_SOL_ADDRESS)
        },
        "usdt_erc20": {
            "key": "usdt_erc20",
            "label": "USDT [ERC-20]",
            "short": "USDT",
            "panel": "USDT [ERC-20]",
            "complete": "USDT [ERC-20]",
            "group": "stable",
            "family": "erc20",
            "chain_id": "1",
            "contract": USDT_ERC20_CONTRACT,
            "decimals": 6,
            "display_decimals": 4,
            "price": None,
            "confirmations": 1,
            "explorer": "Etherscan",
            "emoji": halal_emoji_or(HALAL_USDT_ERC20_EMOJI, HALAL_USDT_EMOJI or USDT_EMOJI or "₮"),
            "address": cleaned_secret(HALAL_USDT_ERC20_ADDRESS)
        },
        "usdc_erc20": {
            "key": "usdc_erc20",
            "label": "USDC [ERC-20]",
            "short": "USDC",
            "panel": "USDC [ERC-20]",
            "complete": "USDC [ERC-20]",
            "group": "stable",
            "family": "erc20",
            "chain_id": "1",
            "contract": USDC_ERC20_CONTRACT,
            "decimals": 6,
            "display_decimals": 4,
            "price": None,
            "confirmations": 1,
            "explorer": "Etherscan",
            "emoji": halal_emoji_or(HALAL_USDC_ERC20_EMOJI, HALAL_USDC_EMOJI or "USD"),
            "address": cleaned_secret(HALAL_USDC_ERC20_ADDRESS)
        },
        "usdt_bep20": {
            "key": "usdt_bep20",
            "label": "USDT [BEP-20]",
            "short": "USDT",
            "panel": "USDT [BEP-20]",
            "complete": "USDT [BEP-20]",
            "group": "stable",
            "family": "bep20",
            "chain_id": BSC_CHAIN_ID,
            "contract": USDT_BEP20_CONTRACT,
            "decimals": 18,
            "display_decimals": 4,
            "price": None,
            "confirmations": USDT_CONFIRMATIONS_REQUIRED,
            "explorer": "Bscscan",
            "emoji": halal_emoji_or(HALAL_USDT_BEP20_EMOJI, HALAL_USDT_EMOJI or USDT_EMOJI or "₮"),
            "address": cleaned_secret(HALAL_USDT_BEP20_ADDRESS) or USDT_DEPOSIT_ADDRESS
        },
        "usdt_sol": {
            "key": "usdt_sol",
            "label": "USDT [SOL]",
            "short": "USDT",
            "panel": "USDT [SOL]",
            "complete": "USDT [SOL]",
            "group": "stable",
            "family": "spl",
            "mint": USDT_SOL_MINT,
            "decimals": 6,
            "display_decimals": 4,
            "price": None,
            "confirmations": 1,
            "explorer": "Solscan",
            "emoji": halal_emoji_or(HALAL_USDT_SOL_EMOJI, HALAL_USDT_EMOJI or USDT_EMOJI or "₮"),
            "address": cleaned_secret(HALAL_USDT_SOL_ADDRESS)
        },
        "usdc_sol": {
            "key": "usdc_sol",
            "label": "USDC [SOL]",
            "short": "USDC",
            "panel": "USDC [SOL]",
            "complete": "USDC [SOL]",
            "group": "stable",
            "family": "spl",
            "mint": USDC_SOL_MINT,
            "decimals": 6,
            "display_decimals": 4,
            "price": None,
            "confirmations": 1,
            "explorer": "Solscan",
            "emoji": halal_emoji_or(HALAL_USDC_SOL_EMOJI, HALAL_USDC_EMOJI or "USD"),
            "address": cleaned_secret(HALAL_USDC_SOL_ADDRESS)
        }
    }


def apply_guild_halal_emojis(coins, guild):
    if guild is None:
        return coins
    by_name = {emoji.name: str(emoji) for emoji in getattr(guild, "emojis", [])}
    names = {
        "btc": ("halal_btc",),
        "eth": ("halal_eth",),
        "ltc": ("halal_ltc",),
        "sol": ("halal_sol",),
        "usdt_erc20": ("halal_usdteth", "halal_usdt_erc20"),
        "usdc_erc20": ("halal_usdceth", "halal_usdc_erc20"),
        "usdt_bep20": ("halal_usdtbep", "halal_usdt_bep20", "halal_usdtbnb"),
        "usdt_sol": ("halal_usdtsol", "halal_usdt_sol"),
        "usdc_sol": ("halal_usdcsol", "halal_usdc_sol"),
    }
    for key, options in names.items():
        coin = coins.get(key)
        if not coin:
            continue
        for name in options:
            if name in by_name:
                coin["emoji"] = by_name[name]
                break
    return coins


def halal_coin(ticket_or_key, guild=None):
    if isinstance(ticket_or_key, dict):
        key = ticket_or_key.get("type")
        if guild is None and ticket_or_key.get("guild_id"):
            guild = bot.get_guild(int(ticket_or_key["guild_id"]))
    else:
        key = ticket_or_key
    coins = apply_guild_halal_emojis(halal_coins(), guild)
    return coins.get(str(key or ""), {})


def is_halal_ticket(ticket):
    return isinstance(ticket, dict) and ticket.get("system") == "halal"


def halal_deal_type(ticket):
    key = str(ticket.get("deal_type") or "")
    for item in HALAL_DEAL_TYPES:
        if item[0] == key:
            return item
    return None


def format_crypto_precise(amount, decimals):
    quantized = Decimal(str(amount)).quantize(
        Decimal(10) ** -int(decimals),
        rounding=ROUND_DOWN
    )
    text = f"{quantized:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def halal_amount_text(ticket, value=None):
    coin = halal_coin(ticket)
    decimals = int(coin.get("display_decimals") or coin.get("decimals") or 8)
    if value is None:
        value = ticket.get("crypto_amount") or "0"
    return format_crypto_precise(value, decimals)


def halal_min_usd():
    try:
        amount = Decimal(str(HALAL_MIN_USD))
    except (InvalidOperation, TypeError):
        amount = Decimal("1.00")
    if amount <= 0:
        amount = Decimal("1.00")
    return amount.quantize(Decimal("0.01"))


async def get_coinbase_spot(pair):
    data = await http_get_json(
        f"https://api.coinbase.com/v2/prices/{pair}/spot",
        headers={"Accept": "application/json"},
        attempts=3,
        timeout=10
    )
    if not isinstance(data, dict):
        return None
    try:
        price = Decimal(str(data["data"]["amount"]))
        if price.is_finite() and price > 0:
            return price
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return None
    return None


def mention_or_none(user_id):
    if not user_id:
        return "None"
    return f"<@{int(user_id)}>"


def party_ids(ticket):
    ids = set()
    for key in ("opener_id", "trader_id", "sender_id", "receiver_id"):
        value = ticket.get(key)
        if value:
            ids.add(int(value))
    return ids


def is_halal_party(user, ticket):
    try:
        return int(user.id) in party_ids(ticket)
    except (TypeError, ValueError, AttributeError):
        return False


async def get_halal_ticket_category(guild):
    channel_id = int(HALAL_TICKET_CATEGORY or 0) or TICKET_CATEGORY
    configured = guild.get_channel(channel_id)
    if configured is None:
        try:
            configured = await bot.fetch_channel(channel_id)
        except discord.HTTPException:
            return None
    if isinstance(configured, discord.CategoryChannel):
        return configured
    category = getattr(configured, "category", None)
    if isinstance(category, discord.CategoryChannel):
        return category
    return None


def record_deal_started(ticket):
    for user_id in {str(ticket.get("opener_id") or ""), str(ticket.get("trader_id") or "")}:
        if not user_id:
            continue
        stats = get_user_stats(user_id)
        stats["deals_started"] = int(stats.get("deals_started") or 0) + 1


def completion_rate_text(stats):
    started = int(stats.get("deals_started") or 0)
    completed = int(stats.get("deals_completed") or 0)
    if started <= 0:
        if completed <= 0:
            return "100%"
        started = completed
    rate = min(100.0, (completed / started) * 100.0)
    if rate >= 100:
        return "100%"
    if rate == int(rate):
        return f"{int(rate)}%"
    return f"{rate:.1f}%"


def halal_stats_embed(user):
    data = get_user_stats(user.id)
    embed = discord.Embed(
        title=user.name,
        colour=COLOR_HALAL_GREEN
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(
        name="Deals completed",
        value=str(int(data.get("deals_completed") or 0)),
        inline=False
    )
    embed.add_field(
        name="Total USD Value",
        value=money(data.get("total_usd_value") or "0"),
        inline=False
    )
    embed.add_field(
        name="Completion rate",
        value=completion_rate_text(data),
        inline=False
    )
    return embed


def explorer_name_for(ticket):
    return halal_coin(ticket).get("explorer") or "Explorer"


class TinyLayout(discord.ui.LayoutView):
    def __init__(self, *items, accent=COLOR_HALAL_GRAY):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Container(*items, accent_colour=accent))


async def halal_deadend(interaction, text):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)
    except discord.HTTPException:
        pass


def halal_text_container(text, accent):
    view = TinyLayout(
        discord.ui.TextDisplay(text),
        accent=accent
    )
    return view


def with_optional_thumb(text, image_url, fallback_url=None):
    thumb = halal_thumb(image_url) or halal_thumb(fallback_url)
    body = discord.ui.TextDisplay(text)
    if thumb is None:
        return [body]
    return [discord.ui.Section(body, accessory=thumb)]


def custom_emoji_cdn_url(emoji):
    match = re.fullmatch(r"<(a?):[A-Za-z0-9_]+:(\d+)>", str(emoji or "").strip())
    if not match:
        return ""
    ext = "gif" if match.group(1) == "a" else "png"
    return f"https://cdn.discordapp.com/emojis/{match.group(2)}.{ext}"


def halal_short_txid(txid):
    txid = str(txid or "")
    if len(txid) <= 16:
        return txid
    return f"{txid[:6]}...{txid[-8:]}"


def halal_privacy_name(user_id, private=True):
    if private or not user_id:
        return "`Anonymous`"
    return f"<@{int(user_id)}>"


def halal_complete_title(coin):
    name = coin.get("complete") or coin.get("label") or "Deal"
    return f"{name} Deal Complete"


def build_halal_complete_layout(
    title,
    amount,
    short,
    usd,
    sender,
    receiver,
    txid,
    asset,
    explorer,
    emoji=""
):
    link = tx_link(txid, asset) if txid else ""
    short_tx = halal_short_txid(txid) if txid else ""
    real_tx = bool(
        txid
        and link
        and not is_manual_reference(txid)
        and not is_simulation_reference(txid)
    )
    tx_md = (
        f"[{short_tx} (View Transaction)]({link})"
        if real_tx
        else f"`{short_tx or 'Manual'}`"
    )
    emoji_url = custom_emoji_cdn_url(emoji)
    heading = (
        f"{H2} {emoji} {title}"
        if emoji and not emoji_url
        else f"{H2} {title}"
    )
    text = (
        f"{heading}\n"
        f"**Amount**\n`{amount}` {short} ({money(usd)} USD)\n"
        f"**Sender** {sender}    **Receiver** {receiver}\n"
        f"**Transaction**\n{tx_md}"
    )
    items = with_optional_thumb(text, emoji_url)
    if real_tx:
        items.append(
            discord.ui.ActionRow(
                discord.ui.Button(
                    label=f"View on {explorer}",
                    style=discord.ButtonStyle.secondary,
                    url=link
                )
            )
        )
    view = discord.ui.LayoutView(timeout=None)
    view.add_item(
        discord.ui.Container(*items, accent_colour=COLOR_HALAL_GREEN)
    )
    return view


class HalalStartButton(discord.ui.Button):
    def __init__(self, coin_key):
        super().__init__(
            label="Start",
            style=discord.ButtonStyle.success,
            custom_id=f"halal_start_{coin_key}"
        )
        self.coin_key = coin_key

    async def callback(self, interaction):
        await start_halal_ticket(interaction, self.coin_key)


class HalalPanel(discord.ui.LayoutView):
    @staticmethod
    def coin_groups(guild=None):
        coins = apply_guild_halal_emojis(halal_coins(), guild)
        tos = halal_md_link("Terms of Service", HALAL_TOS_URL)
        website = halal_md_link("website", HALAL_WEBSITE_URL)
        crypto_items = [
            discord.ui.TextDisplay(
                f"{H2} Start Cryptocurrency Deal\n"
                "Use the selection below to start a deal using the appropriate "
                "coin & network. Please be sure all deals abide by the "
                f"{tos}. Refer to our {website} for a detailed overview of "
                "service fees & supported networks."
            )
        ]
        stable_items = [
            discord.ui.TextDisplay(
                f"{H2} Stablecoins\n"
                "Start a deal with USDT or USDC on the network that matches "
                "your wallet. Please be sure to select the correct network."
            )
        ]
        first_crypto = True
        first_stable = True
        for coin in coins.values():
            row = discord.ui.Section(
                discord.ui.TextDisplay(
                    f"{coin['emoji']}  **{coin['panel']}**"
                    if coin["emoji"] else f"**{coin['panel']}**"
                ),
                accessory=HalalStartButton(coin["key"])
            )
            if coin["group"] == "crypto":
                if not first_crypto:
                    crypto_items.append(
                        discord.ui.Separator(
                            visible=True,
                            spacing=discord.SeparatorSpacing.small
                        )
                    )
                crypto_items.append(row)
                first_crypto = False
            else:
                if not first_stable:
                    stable_items.append(
                        discord.ui.Separator(
                            visible=True,
                            spacing=discord.SeparatorSpacing.small
                        )
                    )
                stable_items.append(row)
                first_stable = False
        return crypto_items, stable_items

    @classmethod
    def split_views(cls, guild=None):
        crypto_items, stable_items = cls.coin_groups(guild)
        crypto = discord.ui.LayoutView(timeout=None)
        stables = discord.ui.LayoutView(timeout=None)
        crypto.add_item(
            discord.ui.Container(*crypto_items, accent_colour=COLOR_HALAL_GREEN)
        )
        stables.add_item(
            discord.ui.Container(*stable_items, accent_colour=COLOR_HALAL_GREEN)
        )
        return crypto, stables

    def __init__(self, guild=None):
        super().__init__(timeout=None)
        crypto_items, stable_items = self.coin_groups(guild)
        self.add_item(
            discord.ui.Container(*crypto_items, accent_colour=COLOR_HALAL_GREEN)
        )
        self.add_item(
            discord.ui.Container(*stable_items, accent_colour=COLOR_HALAL_GREEN)
        )


class HalalCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Close",
            style=discord.ButtonStyle.secondary,
            custom_id="halal_close_ticket"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket):
            await interaction.response.send_message(
                "This ticket is no longer active.",
                ephemeral=True
            )
            return
        if (
            not is_halal_party(interaction.user, ticket)
            and not is_admin(interaction.user)
        ):
            await interaction.response.send_message(
                "You cannot close this ticket.",
                ephemeral=True
            )
            return
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await close_ticket_channel(
            interaction.channel,
            ticket,
            f"Halal ticket closed by {interaction.user}"
        )


class HalalCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HalalCloseButton())


class HalalDealTypeSelect(discord.ui.Select):
    def __init__(self, selected=None, locked=False):
        options = []
        for key, label, _prompt, _example in HALAL_DEAL_TYPES:
            options.append(
                discord.SelectOption(
                    label=label,
                    value=key,
                    default=(key == selected)
                )
            )
        super().__init__(
            placeholder="Select Deal Type",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="halal_deal_type",
            disabled=bool(locked)
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket):
            await halal_deadend(
                interaction,
                "This ticket is no longer active."
            )
            return
        if int(interaction.user.id) != int(ticket.get("opener_id") or 0) and not is_admin(interaction.user):
            await halal_deadend(
                interaction,
                "Only the ticket opener can select the deal type."
            )
            return
        if ticket.get("deal_type"):
            await interaction.response.edit_message(
                view=HalalDealTypeLayout(ticket, locked=True)
            )
            await send_halal_lets_start(interaction.channel, ticket)
            return
        if ticket.get("status") not in {
            "halal_setup",
            "halal_waiting_trader"
        }:
            await interaction.response.send_message(
                "The deal type can no longer be changed.",
                ephemeral=True
            )
            return
        ticket["deal_type"] = self.values[0]
        if not ticket.get("trader_id"):
            ticket["status"] = "halal_waiting_trader"
        await save_data()
        await interaction.response.edit_message(
            view=HalalDealTypeLayout(ticket, locked=True)
        )
        await send_halal_lets_start(interaction.channel, ticket)
        await maybe_start_halal_roles(interaction.channel, ticket)


class HalalDealTypeLayout(discord.ui.LayoutView):
    def __init__(self, ticket=None, locked=False):
        super().__init__(timeout=None)
        selected = ticket.get("deal_type") if ticket else None
        locked = bool(locked or selected)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Deal Type"),
                discord.ui.TextDisplay(
                    "To best serve you, we need to know a few deal details. Please use the dropdown menu below to select the deal type:"
                ),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.ActionRow(
                    HalalDealTypeSelect(selected, locked=locked)
                ),
                accent_colour=COLOR_HALAL_GREEN
            )
        )


class HalalLetsStartLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        how = halal_md_link("How?", HALAL_HOW_USERID_URL)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Let's start!"),
                discord.ui.TextDisplay(
                    f"Please paste the UserID of the user you are dealing with {how}\n\n"
                    "Ex. @User\n"
                    "Ex. 123456789123456789"
                ),
                accent_colour=COLOR_HALAL_GREEN
            )
        )


async def send_halal_lets_start(channel, ticket, force=False):
    if ticket.get("messages", {}).get("trader_prompt") and not force:
        return
    if force:
        await delete_halal_keys(channel, ticket, "trader_prompt")
    message = await channel.send(view=HalalLetsStartLayout())
    ticket.setdefault("messages", {})["trader_prompt"] = message.id
    await save_data()


async def send_halal_layout(channel, view, ping=None, ticket=None, ping_key=None):
    if ping:
        try:
            ping_msg = await channel.send(
                content=ping,
                allowed_mentions=discord.AllowedMentions(
                    users=True, roles=False, everyone=False
                )
            )
            if ticket is not None and ping_key:
                ticket.setdefault("messages", {})[ping_key] = ping_msg.id
        except discord.HTTPException:
            logger.exception("Failed to send Halal ping")
    return await channel.send(view=view)


async def ack_halal_interaction(interaction):
    try:
        if not interaction.response.is_done():
            await interaction.response.defer()
    except discord.HTTPException:
        pass


async def delete_ticket_message(channel, message_id):
    if not message_id or channel is None:
        return
    message = await fetch_message(channel, message_id)
    if message is None:
        return
    try:
        await message.delete()
    except discord.HTTPException:
        pass


async def delete_chat_message(message):
    if message is None:
        return
    try:
        await message.delete()
    except discord.HTTPException:
        pass


def remember_halal_message(ticket, key, message_id):
    if ticket is None or not message_id:
        return
    messages = ticket.setdefault("messages", {})
    existing = messages.get(key)
    if existing is None:
        messages[key] = message_id
    elif isinstance(existing, list):
        if message_id not in existing:
            existing.append(message_id)
    elif existing != message_id:
        messages[key] = [existing, message_id]


async def delete_halal_keys(channel, ticket, *keys):
    messages = ticket.setdefault("messages", {})
    for key in keys:
        value = messages.pop(key, None)
        ids = value if isinstance(value, list) else [value]
        for message_id in ids:
            await delete_ticket_message(channel, message_id)


async def consume_halal_prompt(interaction, ticket, *keys):
    await ack_halal_interaction(interaction)
    try:
        await interaction.message.delete()
    except discord.HTTPException:
        pass
    if ticket is not None:
        await delete_halal_keys(interaction.channel, ticket, *keys)
        await save_data()


async def send_halal_correct(channel, ticket, user, key):
    message = await channel.send(
        view=halal_text_container(
            f"{user.mention} has responded with 'Correct'",
            COLOR_HALAL_GRAY
        ),
        allowed_mentions=discord.AllowedMentions(
            users=True, roles=False, everyone=False
        )
    )
    remember_halal_message(ticket, key, message.id)
    return message


async def redo_halal_userid_prompt(channel, ticket, error_text):
    await delete_halal_keys(channel, ticket, "userid_error")
    err = await channel.send(error_text)
    ticket.setdefault("messages", {})["userid_error"] = err.id
    await send_halal_lets_start(channel, ticket, force=True)
    await save_data()


class HalalSelectRoleButton(discord.ui.Button):
    def __init__(self, role, disabled=False):
        super().__init__(
            label="Select",
            style=discord.ButtonStyle.success,
            custom_id=f"halal_role_select_{role}",
            disabled=disabled
        )
        self.role = role

    async def callback(self, interaction):
        await choose_halal_role(interaction, self.role)


class HalalResetRolesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Reset",
            style=discord.ButtonStyle.danger,
            custom_id="halal_role_reset"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or ticket.get("status") != "halal_role_selection":
            await halal_deadend(
                interaction,
                "Role selection is no longer active."
            )
            return
        if not is_halal_party(interaction.user, ticket) and not is_admin(interaction.user):
            await halal_deadend(
                interaction,
                "You cannot reset this selection."
            )
            return
        ticket["sender_id"] = None
        ticket["receiver_id"] = None
        ticket["role_confirmed"] = []
        await save_data()
        await interaction.response.edit_message(view=HalalRoleSelectionLayout(ticket))


class HalalRoleSelectionLayout(discord.ui.LayoutView):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        coin = halal_coin(ticket)
        label = coin.get("label") or "Crypto"
        sender = mention_or_none(ticket.get("sender_id"))
        receiver = mention_or_none(ticket.get("receiver_id"))
        sender_taken = bool(ticket.get("sender_id"))
        receiver_taken = bool(ticket.get("receiver_id"))
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Role Selection"),
                discord.ui.TextDisplay(
                    "Select one of the following buttons that corresponds to your role in this deal."
                ),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.Section(
                    discord.ui.TextDisplay(f"Sending {label}: {sender}"),
                    accessory=HalalSelectRoleButton("sender", disabled=sender_taken)
                ),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.Section(
                    discord.ui.TextDisplay(f"Receiving {label}: {receiver}"),
                    accessory=HalalSelectRoleButton("receiver", disabled=receiver_taken)
                ),
                accent_colour=COLOR_HALAL_GREEN
            )
        )
        self.add_item(discord.ui.ActionRow(HalalResetRolesButton()))


class HalalRoleConfirmButton(discord.ui.Button):
    def __init__(self, role):
        super().__init__(
            label="Confirm",
            style=discord.ButtonStyle.success,
            custom_id=f"halal_role_confirm_{role}"
        )
        self.role = role

    async def callback(self, interaction):
        await confirm_halal_role(interaction, self.role)


class HalalReturnButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Return",
            style=discord.ButtonStyle.danger,
            custom_id="halal_role_return"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or ticket.get("status") != "halal_role_confirmation":
            await halal_deadend(
                interaction,
                "This confirmation is no longer active."
            )
            return
        if not is_halal_party(interaction.user, ticket):
            await halal_deadend(
                interaction,
                "Only the two traders can use this."
            )
            return
        await consume_halal_prompt(
            interaction,
            ticket,
            "role_confirmation",
            "role_correct"
        )
        await send_halal_role_selection(interaction.channel, ticket)


class HalalRoleConfirmationLayout(discord.ui.LayoutView):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        coin = halal_coin(ticket)
        label = coin.get("label") or "Crypto"
        confirmed = {int(user_id) for user_id in (ticket.get("role_confirmed") or [])}
        sender_done = int(ticket.get("sender_id") or 0) in confirmed
        receiver_done = int(ticket.get("receiver_id") or 0) in confirmed
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Role Confirmation"),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.Section(
                    discord.ui.TextDisplay(
                        f"Sending {label}: <@{ticket['sender_id']}>"
                    ),
                    accessory=HalalRoleConfirmButton("sender", disabled=sender_done)
                ),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.Section(
                    discord.ui.TextDisplay(
                        f"Receiving {label}: <@{ticket['receiver_id']}>"
                    ),
                    accessory=HalalRoleConfirmButton("receiver", disabled=receiver_done)
                ),
                discord.ui.TextDisplay(
                    "Selecting the wrong role will result in getting scammed!"
                ),
                accent_colour=COLOR_HALAL_GREEN
            )
        )
        self.add_item(discord.ui.ActionRow(HalalReturnButton()))


class HalalCorrectButton(discord.ui.Button):
    def __init__(self, kind):
        super().__init__(
            label="Correct",
            style=discord.ButtonStyle.success,
            custom_id=f"halal_{kind}_correct"
        )
        self.kind = kind

    async def callback(self, interaction):
        if self.kind == "details":
            await confirm_halal_details(interaction, True)
        else:
            await confirm_halal_amount(interaction, True)


class HalalIncorrectButton(discord.ui.Button):
    def __init__(self, kind):
        super().__init__(
            label="Incorrect",
            style=discord.ButtonStyle.secondary,
            custom_id=f"halal_{kind}_incorrect"
        )
        self.kind = kind

    async def callback(self, interaction):
        if self.kind == "details":
            await confirm_halal_details(interaction, False)
        else:
            await confirm_halal_amount(interaction, False)


class HalalDetailsLayout(discord.ui.LayoutView):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        deal = halal_deal_type(ticket)
        label = deal[1] if deal else "Deal"
        details = safe_code_text(ticket.get("deal_details") or "")
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Confirm Details"),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.TextDisplay(f"**Type:** {label}"),
                discord.ui.TextDisplay(f"```{details}```"),
                discord.ui.TextDisplay(
                    "Review the deal type and description before confirming. "
                    "Errors may result in getting scammed!"
                ),
                discord.ui.ActionRow(
                    HalalCorrectButton("details"),
                    HalalIncorrectButton("details")
                ),
                accent_colour=COLOR_HALAL_GREEN
            )
        )


class HalalAmountLayout(discord.ui.LayoutView):
    def __init__(self, ticket, disabled=False):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Amount Confirmation"),
                discord.ui.TextDisplay("Both users must confirm the USD deal amount"),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.TextDisplay(
                    f"**Amount:** `{money(ticket.get('usd_amount') or '0')}`"
                ),
                discord.ui.ActionRow(
                    HalalCorrectButton("amount"),
                    HalalIncorrectButton("amount")
                ),
                accent_colour=COLOR_HALAL_GRAY
            )
        )


class HalalCopyFieldButton(discord.ui.Button):
    def __init__(self, field):
        super().__init__(
            label="Copy",
            style=discord.ButtonStyle.secondary,
            custom_id=f"halal_copy_{field}"
        )
        self.field = field

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
            await interaction.response.send_message(
                "Only the two traders can use this button.",
                ephemeral=True
            )
            return
        if self.field == "address":
            value = ticket.get("deposit_address") or ""
        else:
            value = halal_amount_text(ticket)
        await interaction.response.send_message(value, ephemeral=True)


class HalalCopyDetailsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Copy Details",
            style=discord.ButtonStyle.secondary,
            custom_id="halal_copy_details"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
            await halal_deadend(
                interaction,
                "Only the two traders can use this button."
            )
            return
        ticket["copied_details"] = True
        await save_data()
        await interaction.response.edit_message(
            view=HalalInvoiceLayout(ticket, copied=True)
        )
        await interaction.channel.send(
            f"{ticket.get('deposit_address')}\n"
            f"{halal_amount_text(ticket)}\n"
            "Copy the payment details above. No funds have been received yet."
        )


class HalalCancelDealButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Cancel deal",
            style=discord.ButtonStyle.danger,
            custom_id="halal_cancel_deal"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
            await halal_deadend(
                interaction,
                "Only the two traders can cancel this deal."
            )
            return
        if ticket.get("status") not in {"waiting_deposit", "halal_waiting_deposit"}:
            await halal_deadend(
                interaction,
                "This deal can no longer be cancelled from here."
            )
            return
        await interaction.response.send_message("Cancelling deal...", ephemeral=True)
        await close_ticket_channel(
            interaction.channel,
            ticket,
            f"Deal cancelled by {interaction.user}"
        )


class HalalCheckDepositButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Check deposit",
            style=discord.ButtonStyle.secondary,
            custom_id="halal_check_deposit"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
            await halal_deadend(
                interaction,
                "Only the two traders can use this button."
            )
            return
        await interaction.response.defer(ephemeral=True)
        before = ticket.get("status")
        await monitor_halal_ticket(ticket)
        current = get_ticket(interaction.channel_id)
        if current is None:
            return
        if current.get("status") == before:
            await interaction.followup.send(
                "No funds have been received yet.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Deposit updated.",
                ephemeral=True
            )


class HalalInvoiceLayout(discord.ui.LayoutView):
    def __init__(self, ticket, copied=False):
        super().__init__(timeout=None)
        coin = halal_coin(ticket)
        address = ticket.get("deposit_address") or ""
        amount = halal_amount_text(ticket)
        usd = money(ticket.get("usd_amount") or "0")
        rate = ticket.get("crypto_price")
        rate_line = ""
        if rate and coin.get("price"):
            rate_line = (
                f"Exchange Rate: 1 {coin.get('short')} = "
                f"{money(rate)} USD"
            )
        sender = f"<@{ticket['sender_id']}>"
        summary_text = (
            f"{H2} Deal Summary\n"
            "Refer to this deal summary for any reaffirmations. "
            "Notify staff for any support required.\n\n"
            f"**Sender:** <@{ticket['sender_id']}>\n"
            f"**Receiver:** <@{ticket['receiver_id']}>\n"
            f"**Coin:** {coin.get('emoji', '')} {coin.get('label')}\n"
            f"**Deal Amount:** `{usd}`\n"
            f"**Deal:** {halal_deal_type(ticket)[1] if halal_deal_type(ticket) else 'Deal'}"
            f" - {ticket.get('deal_details') or ''}"
        )
        invoice_header = (
            f"{H2} Payment Invoice\n"
            f"{sender} Send the funds as part of the deal to the Middleman "
            "address specified below. Please copy the amount provided."
        )
        buttons = []
        if not copied and not ticket.get("copied_details"):
            buttons.append(HalalCopyDetailsButton())
        buttons.extend([HalalCancelDealButton(), HalalCheckDepositButton()])
        self.add_item(
            discord.ui.Container(
                *with_optional_thumb(
                    summary_text,
                    custom_emoji_cdn_url(coin.get("emoji"))
                ),
                accent_colour=COLOR_HALAL_GRAY
            )
        )
        self.add_item(discord.ui.TextDisplay(sender))
        invoice_items = with_optional_thumb(
            invoice_header,
            qr_image_url(address)
        )
        invoice_items.extend([
            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small
            ),
            discord.ui.Section(
                discord.ui.TextDisplay(f"**Address:**\n`{address}`"),
                accessory=HalalCopyFieldButton("address")
            ),
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"**Amount:**\n`{amount}` {coin.get('short')} ({usd} USD)"
                ),
                accessory=HalalCopyFieldButton("amount")
            )
        ])
        if rate_line:
            invoice_items.append(discord.ui.TextDisplay(rate_line))
        invoice_items.append(discord.ui.ActionRow(*buttons))
        self.add_item(
            discord.ui.Container(*invoice_items, accent_colour=COLOR_HALAL_GRAY)
        )


class HalalProceedReleaseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Release",
            style=discord.ButtonStyle.success,
            custom_id="halal_release"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_sender(interaction, ticket):
            await halal_deadend(
                interaction,
                "Only the sender can release the escrow."
            )
            return
        if ticket.get("status") != "trade":
            await halal_deadend(
                interaction,
                "The trade is not currently ready for release."
            )
            return
        await interaction.response.defer()
        await send_halal_release_confirmation(interaction.channel, ticket)


class HalalProceedCancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="halal_proceed_cancel"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
            await halal_deadend(
                interaction,
                "Only the two traders can cancel."
            )
            return
        if ticket.get("status") != "trade":
            await halal_deadend(
                interaction,
                "Cancellation is not available right now."
            )
            return
        ticket["status"] = "cancellation"
        ticket["cancel_votes"] = []
        ticket["uncancel_votes"] = []
        await save_data()
        await interaction.response.send_message(
            content=f"<@{ticket['sender_id']}> <@{ticket['receiver_id']}>",
            embed=cancellation_embed(ticket),
            view=CancellationView(),
            allowed_mentions=discord.AllowedMentions(
                users=True, roles=False, everyone=False
            )
        )
        message = await interaction.original_response()
        ticket["messages"]["cancellation"] = message.id
        await save_data()


class HalalProceedLayout(discord.ui.LayoutView):
    def __init__(self, ticket, released=False):
        super().__init__(timeout=None)
        coin = halal_coin(ticket)
        if released:
            body = (
                f"{H2} You may now proceed with the deal\n"
                f"Release has been requested by the sender (<@{ticket['sender_id']}>).\n\n"
                f"The receiver (<@{ticket['receiver_id']}>) must provide a "
                f"{coin.get('label')} payout address before funds can be released."
            )
            self.add_item(
                discord.ui.TextDisplay(
                    f"<@{ticket['sender_id']}> <@{ticket['receiver_id']}>"
                )
            )
            self.add_item(
                discord.ui.Container(
                    discord.ui.TextDisplay(body),
                    accent_colour=COLOR_HALAL_GREEN
                )
            )
            return
        body = (
            f"{H2} You may now proceed with the deal\n"
            f"The receiver (<@{ticket['receiver_id']}>) may now provide the goods "
            f"to the sender (<@{ticket['sender_id']}>).\n\n"
            "Once the deal is complete, the sender must click the **Release** "
            "button below to release the funds to the receiver & complete the deal."
        )
        self.add_item(
            discord.ui.TextDisplay(
                f"<@{ticket['sender_id']}> <@{ticket['receiver_id']}>"
            )
        )
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(body),
                discord.ui.ActionRow(
                    HalalProceedReleaseButton(),
                    HalalProceedCancelButton()
                ),
                accent_colour=COLOR_HALAL_GREEN
            )
        )


class HalalReleaseConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Confirm",
            style=discord.ButtonStyle.success,
            custom_id="halal_release_confirm"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_sender(interaction, ticket):
            await halal_deadend(
                interaction,
                "Only the sender can confirm the release."
            )
            return
        if ticket.get("status") != "release_confirmation":
            await halal_deadend(
                interaction,
                "This release confirmation is no longer active."
            )
            return
        ticket["release_authorized"] = True
        ticket["status"] = "address_prompt"
        await save_data()
        await ack_halal_interaction(interaction)
        await update_halal_proceed_released(interaction.channel, ticket)
        await send_halal_address_prompt(interaction.channel, ticket)


class HalalReleaseBackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="halal_release_back"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_sender(interaction, ticket):
            await halal_deadend(
                interaction,
                "Only the sender can use this button."
            )
            return
        ticket["status"] = "trade"
        await save_data()
        await ack_halal_interaction(interaction)


class HalalReleaseLayout(discord.ui.LayoutView):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        self.add_item(discord.ui.TextDisplay(f"<@{ticket['sender_id']}>"))
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Release Confirmation"),
                discord.ui.TextDisplay(
                    f"Are you sure you want to release the funds to <@{ticket['receiver_id']}>?\n\n"
                    "Once confirmed, the funds will be released and the deal will be "
                    "marked as complete. This action cannot be undone."
                ),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.TextDisplay(
                    "Staff will never DM you asking to release funds."
                ),
                discord.ui.ActionRow(
                    HalalReleaseConfirmButton(),
                    HalalReleaseBackButton()
                ),
                accent_colour=COLOR_HALAL_ORANGE
            )
        )


class HalalAddressConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Confirm",
            style=discord.ButtonStyle.success,
            custom_id="halal_address_confirm"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_receiver(interaction, ticket):
            await interaction.response.send_message(
                "Only the receiver can confirm this address.",
                ephemeral=True
            )
            return
        if ticket.get("status") != "address_confirmation":
            await interaction.response.send_message(
                "This address confirmation is no longer active.",
                ephemeral=True
            )
            return
        await ack_halal_interaction(interaction)
        await finish_halal_address_confirm(interaction.channel, ticket)


class HalalAddressBackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="halal_address_back"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket) or not is_receiver(interaction, ticket):
            await halal_deadend(
                interaction,
                "Only the receiver can use this button."
            )
            return
        ticket["receiver_address"] = None
        ticket["status"] = "address_prompt"
        await save_data()
        await consume_halal_prompt(
            interaction,
            ticket,
            "address_confirmation"
        )
        await send_halal_address_prompt(interaction.channel, ticket)


class HalalAddressConfirmLayout(discord.ui.LayoutView):
    def __init__(self, ticket):
        super().__init__(timeout=None)
        coin = halal_coin(ticket)
        self.add_item(discord.ui.TextDisplay(f"<@{ticket['receiver_id']}>"))
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    f"{H2} Is this your {coin.get('label')} address?"
                ),
                discord.ui.TextDisplay(
                    "Please verify that the address you provided is correct. "
                    "Once the funds are released, they cannot be retrieved."
                ),
                discord.ui.Separator(
                    visible=True,
                    spacing=discord.SeparatorSpacing.small
                ),
                discord.ui.TextDisplay(
                    f"**Address**\n`{ticket.get('receiver_address')}`"
                ),
                discord.ui.ActionRow(
                    HalalAddressConfirmButton(),
                    HalalAddressBackButton()
                ),
                accent_colour=COLOR_HALAL_ORANGE
            )
        )


class HalalCompleteCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Close",
            style=discord.ButtonStyle.secondary,
            custom_id="halal_complete_close"
        )

    async def callback(self, interaction):
        ticket = get_ticket(interaction.channel_id)
        if not is_halal_ticket(ticket):
            await interaction.response.send_message(
                "This ticket is no longer active.",
                ephemeral=True
            )
            return
        if (
            not is_halal_party(interaction.user, ticket)
            and not is_admin(interaction.user)
        ):
            await interaction.response.send_message(
                "You cannot close this ticket.",
                ephemeral=True
            )
            return
        await interaction.response.defer()
        await close_ticket_channel(
            interaction.channel,
            ticket,
            f"Completed Halal ticket closed by {interaction.user}"
        )


class HalalCompleteLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"{H2} Deal Complete"),
                discord.ui.TextDisplay(
                    "Thank you for using Halal. This deal has been successfully completed.\n\n"
                    "If you'd like to make your vouch public, use `/setprivacy` in Halal MM.\n\n"
                    "This ticket will automatically close in 5 minutes."
                ),
                discord.ui.ActionRow(HalalCompleteCloseButton()),
                accent_colour=COLOR_HALAL_GRAY
            )
        )


class HalalStatsLayout(discord.ui.LayoutView):
    def __init__(self, user):
        super().__init__(timeout=None)
        data = get_user_stats(user.id)
        text = (
            f"{H2} {user.name}\n"
            f"**Deals started:** {int(data.get('deals_started') or 0)}\n"
            f"**Deals completed:** {int(data.get('deals_completed') or 0)}\n"
            f"**Total USD Value:** {money(data.get('total_usd_value') or '0')}\n"
            f"**Completion rate:** {completion_rate_text(data)}"
        )
        self.add_item(
            discord.ui.Container(
                *with_optional_thumb(text, str(user.display_avatar.url)),
                accent_colour=COLOR_HALAL_GREEN
            )
        )


def HalalCompletedLogLayout(ticket):
    coin = halal_coin(ticket)
    amount = halal_amount_text(
        ticket,
        ticket.get("payout_amount") or ticket.get("deposit_amount")
    )
    sender_private = DATA["privacy"].get(str(ticket.get("sender_id")), True)
    receiver_private = DATA["privacy"].get(str(ticket.get("receiver_id")), True)
    return build_halal_complete_layout(
        title=halal_complete_title(coin),
        amount=amount,
        short=coin.get("short") or "",
        usd=ticket.get("usd_amount") or "0",
        sender=halal_privacy_name(ticket.get("sender_id"), sender_private),
        receiver=halal_privacy_name(ticket.get("receiver_id"), receiver_private),
        txid=ticket.get("payout_txid") or "",
        asset=ticket.get("type"),
        explorer=explorer_name_for(ticket),
        emoji=coin.get("emoji") or ""
    )


def detected_layout(ticket):
    coin = halal_coin(ticket)
    txid = ticket.get("deposit_txid") or ""
    amount = halal_amount_text(
        ticket,
        ticket.get("deposit_amount") or ticket.get("crypto_amount")
    )
    needed = int(coin.get("confirmations") or 1)
    word = "confirmation" if needed == 1 else "confirmations"
    if (
        ticket.get("manual_deposit_override")
        or is_manual_reference(txid)
        or is_simulation_reference(txid)
        or not txid
    ):
        tx_line = f"**Transaction**\n`{short_txid(txid) if txid else 'Manual'}`"
    else:
        tx_line = (
            f"**Transaction**\n[{short_txid(txid)}]({tx_link(txid, ticket.get('type'))})"
        )
    text = (
        f"{H2} Transaction Detected\n"
        "The transaction is currently **unconfirmed** and waiting for "
        f"{needed} {word}.\n\n"
        f"{tx_line}\n"
        f"**Amount Received**\n`{amount}` {coin.get('short')} "
        f"({money(ticket.get('usd_amount') or '0')})\n"
        f"**Required Amount**\n`{halal_amount_text(ticket)}` {coin.get('short')} "
        f"({money(ticket.get('usd_amount') or '0')})"
    )
    return TinyLayout(
        *with_optional_thumb(text, custom_emoji_cdn_url(coin.get("emoji"))),
        accent=COLOR_HALAL_ORANGE
    )


def received_layout(ticket):
    coin = halal_coin(ticket)
    txid = ticket.get("deposit_txid") or ""
    amount = halal_amount_text(
        ticket,
        ticket.get("deposit_amount") or ticket.get("crypto_amount")
    )
    if (
        ticket.get("manual_deposit_override")
        or is_manual_reference(txid)
        or is_simulation_reference(txid)
        or not txid
    ):
        tx_line = f"**Transaction**\n`{short_txid(txid) if txid else 'Manual'}`"
    else:
        tx_line = (
            f"**Transaction**\n[{short_txid(txid)}]({tx_link(txid, ticket.get('type'))})"
        )
    text = (
        f"{H2} Transaction Confirmed!\n"
        f"{tx_line}\n"
        f"**Total Amount Received**\n`{amount}` {coin.get('short')} "
        f"({money(ticket.get('usd_amount') or '0')})"
    )
    return TinyLayout(
        *with_optional_thumb(text, custom_emoji_cdn_url(coin.get("emoji"))),
        accent=COLOR_HALAL_GREEN
    )


def released_layout(ticket):
    coin = halal_coin(ticket)
    txid = ticket.get("payout_txid") or ""
    amount = halal_amount_text(
        ticket,
        ticket.get("payout_amount") or ticket.get("deposit_amount")
    )
    link = tx_link(txid, ticket.get("type"))
    text = (
        f"{H2} Payment Released\n"
        f"The funds have been successfully released to the provided {coin.get('label')} address.\n\n"
        f"**Amount**\n`{amount}` {coin.get('short')} ≈ "
        f"{money(ticket.get('usd_amount') or '0')} USD\n"
        f"**Transaction**\n[{short_txid(txid)}]({link})"
    )
    return TinyLayout(
        *with_optional_thumb(text, custom_emoji_cdn_url(coin.get("emoji"))),
        accent=COLOR_HALAL_GREEN
    )


async def start_halal_ticket(interaction, coin_key):
    coin = halal_coin(coin_key, interaction.guild)
    if not coin:
        await interaction.response.send_message(
            "That coin is not available.",
            ephemeral=True
        )
        return
    if interaction.guild is None:
        await interaction.response.send_message(
            "Tickets can only be created inside a server.",
            ephemeral=True
        )
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    category = await get_halal_ticket_category(interaction.guild)
    if category is None:
        await interaction.followup.send(
            "The Halal ticket category could not be found. "
            "Set HALAL_TICKET_CATEGORY or TICKET_CATEGORY.",
            ephemeral=True
        )
        return
    number = await reserve_halal_ticket_number()
    name = f"auto-{number}"
    topic = f"Halal MM | auto-{number} | {secrets.token_hex(16)}"
    opener = interaction.user
    try:
        channel = await interaction.guild.create_text_channel(
            name=name,
            category=category,
            topic=topic,
            overwrites=ticket_channel_overwrites(
                interaction.guild,
                opener,
                None,
                can_chat=True
            ),
            reason=f"Halal ticket {number}"
        )
    except discord.HTTPException:
        logger.exception("Failed to create Halal ticket channel")
        await interaction.followup.send(
            "Discord rejected the ticket creation request.",
            ephemeral=True
        )
        return

    ticket = {
        "system": "halal",
        "number": number,
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "type": coin_key,
        "opener_id": opener.id,
        "trader_id": None,
        "deal_type": None,
        "deal_details": None,
        "opener_side": "",
        "trader_side": "",
        "sender_id": None,
        "receiver_id": None,
        "role_confirmed": [],
        "usd_amount": None,
        "usd_confirmed": [],
        "crypto_price": None,
        "crypto_amount": None,
        "deposit_address": None,
        "deposit_txid": None,
        "deposit_amount": None,
        "deposit_confirmations": 0,
        "baseline_txids": [],
        "baseline_ready": False,
        "manual_deposit_override": False,
        "manual_reference": None,
        "receiver_address": None,
        "release_authorized": False,
        "payout_txid": None,
        "payout_amount": None,
        "payout_is_simulation": False,
        "uncancel_votes": [],
        "cancel_votes": [],
        "copied_details": False,
        "status": "halal_setup",
        "created_at": int(time.time()),
        "completed_at": None,
        "stats_recorded": False,
        "completed_logged": False,
        "withdrawal_success_sent": False,
        "completed_channel_sent": False,
        "chat_unlocked": False,
        "messages": {}
    }
    DATA["tickets"][str(channel.id)] = ticket
    await save_data()

    website = halal_md_link("website", HALAL_WEBSITE_URL)
    coin_emoji = coin.get("emoji") or ""
    started = f"{coin_emoji} Deal Started" if coin_emoji else "Deal Started"
    welcome = TinyLayout(
        *with_optional_thumb(
            (
                f"{H2} {started}\n"
                "Welcome to our automated cryptocurrency Middleman system! "
                "Your cryptocurrency will be stored securely for the duration of this deal. "
                f"Please notify support or check our {website} for assistance."
            ),
            HALAL_WELCOME_IMAGE
        ),
        accent=COLOR_HALAL_GREEN
    )
    scams = halal_md_link("known scams", HALAL_KNOWN_SCAMS_URL)
    safety = TinyLayout(
        discord.ui.TextDisplay(f"{H2} Safety Warning"),
        discord.ui.TextDisplay(
            "The bot and our support team will NEVER direct message you. "
            "Ensure all conversations related to the deal are done within this ticket. "
            f"Review our {scams} section to stay safe."
        ),
        accent=COLOR_HALAL_RED
    )
    await channel.send(view=welcome)
    await channel.send(view=safety)
    await channel.send(view=HalalCloseView())
    type_message = await channel.send(view=HalalDealTypeLayout(ticket))
    ticket["messages"]["deal_type"] = type_message.id
    await save_data()
    log_action(
        "halal_ticket_created",
        ticket=number,
        type=coin_key,
        channel=f"{channel.name}({channel.id})",
        opener=f"{opener}({opener.id})"
    )
    await interaction.followup.send(
        f"**Ticket Created!** -> {WORD_JOINER}{channel.mention}",
        ephemeral=True
    )


async def add_halal_trader(channel, ticket, trader):
    guild = channel.guild
    overwrite = ticket_member_overwrite(True)
    try:
        await channel.set_permissions(
            trader,
            overwrite=overwrite,
            reason="Halal trader added"
        )
    except discord.HTTPException:
        logger.exception("Failed to add Halal trader permissions")
    ticket["trader_id"] = trader.id
    if not ticket.get("deal_type"):
        ticket["status"] = "halal_waiting_trader"
    record_deal_started(ticket)
    await delete_halal_keys(channel, ticket, "trader_prompt", "userid_error")
    await save_data()
    await maybe_start_halal_roles(channel, ticket)


async def maybe_start_halal_roles(channel, ticket):
    if not ticket.get("deal_type") or not ticket.get("trader_id"):
        return
    if ticket.get("messages", {}).get("role_selection") and ticket.get("status") in {
        "halal_role_selection",
        "halal_role_confirmation",
        "halal_details",
        "halal_details_confirm",
        "halal_amount",
        "halal_amount_confirm",
        "waiting_deposit",
        "trade"
    }:
        return
    if ticket.get("status") in {
        "halal_role_confirmation",
        "halal_details",
        "halal_details_confirm",
        "halal_amount",
        "halal_amount_confirm",
        "waiting_deposit",
        "trade",
        "completed"
    }:
        return
    welcome = (
        f"<@{ticket['trader_id']}> Welcome! Select roles below."
        if int(ticket.get("opener_id") or 0) != int(ticket.get("trader_id") or 0)
        else "Select roles below."
    )
    await send_halal_role_selection(channel, ticket, ping=welcome)


async def send_halal_role_selection(channel, ticket, ping=None):
    ticket["status"] = "halal_role_selection"
    ticket["sender_id"] = None
    ticket["receiver_id"] = None
    ticket["role_confirmed"] = []
    await save_data()
    message = await send_halal_layout(
        channel,
        HalalRoleSelectionLayout(ticket),
        ping=ping,
        ticket=ticket,
        ping_key="role_ping"
    )
    ticket.setdefault("messages", {})["role_selection"] = message.id
    await save_data()


async def choose_halal_role(interaction, role):
    ticket = get_ticket(interaction.channel_id)
    if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
        await halal_deadend(
            interaction,
            "Only the two traders can select roles."
        )
        return
    if ticket.get("status") != "halal_role_selection":
        await halal_deadend(
            interaction,
            "Role selection is no longer active."
        )
        return
    user_id = interaction.user.id
    if ticket.get("sender_id") == user_id or ticket.get("receiver_id") == user_id:
        await halal_deadend(
            interaction,
            "You already selected a role."
        )
        return
    key = f"{role}_id"
    if ticket.get(key):
        await halal_deadend(
            interaction,
            "That role has already been selected."
        )
        return
    ticket[key] = user_id
    complete = bool(ticket.get("sender_id") and ticket.get("receiver_id"))
    await save_data()
    if complete:
        ticket["status"] = "halal_role_confirmation"
        ticket["role_confirmed"] = []
        await save_data()
        await consume_halal_prompt(
            interaction,
            ticket,
            "role_selection",
            "role_ping"
        )
        message = await interaction.channel.send(
            view=HalalRoleConfirmationLayout(ticket)
        )
        ticket["messages"]["role_confirmation"] = message.id
        await save_data()
        return
    await interaction.response.edit_message(view=HalalRoleSelectionLayout(ticket))


async def confirm_halal_role(interaction, role):
    ticket = get_ticket(interaction.channel_id)
    if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
        await halal_deadend(
            interaction,
            "You are not assigned to this role slot."
        )
        return
    if ticket.get("status") != "halal_role_confirmation":
        await halal_deadend(
            interaction,
            "This confirmation is no longer active."
        )
        return
    expected = int(ticket.get(f"{role}_id") or 0)
    if interaction.user.id != expected:
        await interaction.response.send_message(
            "Only the trader for that role can confirm it.",
            ephemeral=True
        )
        return
    confirmed = list(ticket.get("role_confirmed") or [])
    if interaction.user.id in confirmed:
        await halal_deadend(
            interaction,
            "You already confirmed."
        )
        return
    confirmed.append(interaction.user.id)
    ticket["role_confirmed"] = confirmed
    both = {
        int(ticket["sender_id"]),
        int(ticket["receiver_id"])
    }.issubset(set(confirmed))
    if both:
        ticket["status"] = "halal_details"
    await save_data()
    await ack_halal_interaction(interaction)
    await send_halal_correct(
        interaction.channel,
        ticket,
        interaction.user,
        "role_correct"
    )
    if both:
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass
        await delete_halal_keys(
            interaction.channel,
            ticket,
            "role_confirmation",
            "role_selection",
            "role_ping",
            "role_correct"
        )
        await save_data()
        await send_halal_details_prompt(interaction.channel, ticket)
        return
    try:
        await interaction.message.edit(view=HalalRoleConfirmationLayout(ticket))
    except discord.HTTPException:
        pass
    await save_data()


async def send_halal_details_prompt(channel, ticket):
    deal = halal_deal_type(ticket)
    label = deal[1] if deal else "Deal"
    prompt = deal[2] if deal else "Please state the deal details."
    example = deal[3] if deal else ""
    ticket["status"] = "halal_details"
    ticket["deal_details"] = None
    await save_data()
    items = [
        discord.ui.TextDisplay(f"{H2} Deal Details"),
        discord.ui.TextDisplay(prompt),
        discord.ui.TextDisplay(f"**Type:** {label}"),
        discord.ui.Separator(
            visible=True,
            spacing=discord.SeparatorSpacing.small
        )
    ]
    if example:
        items.append(discord.ui.TextDisplay(f"`{example}`"))
    view = TinyLayout(
        *items,
        accent=COLOR_HALAL_GREEN
    )
    message = await send_halal_layout(
        channel,
        view,
        ping=f"<@{ticket['sender_id']}>",
        ticket=ticket,
        ping_key="details_ping"
    )
    ticket["messages"]["deal_details"] = message.id
    await save_data()


async def send_halal_amount_prompt(channel, ticket):
    ticket["status"] = "halal_amount"
    ticket["usd_amount"] = None
    ticket["usd_confirmed"] = []
    ticket["amount_started_at"] = int(time.time())
    await save_data()
    view = TinyLayout(
        discord.ui.TextDisplay(f"{H2} Deal Amount"),
        discord.ui.TextDisplay(
            "State the amount the bot is expected to receive in USD (eg. 100.59)"
        ),
        discord.ui.TextDisplay(
            "Ticket will be closed in 30 minutes if left unattended"
        ),
        accent=COLOR_HALAL_GRAY
    )
    message = await send_halal_layout(
        channel,
        view,
        ping=f"<@{ticket['sender_id']}>",
        ticket=ticket,
        ping_key="amount_ping"
    )
    ticket["messages"]["deal_amount"] = message.id
    await save_data()
    ensure_monitor(ticket)


async def confirm_halal_details(interaction, correct):
    ticket = get_ticket(interaction.channel_id)
    if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
        await halal_deadend(
            interaction,
            "Only the other party can confirm these deal details."
        )
        return
    if ticket.get("status") != "halal_details_confirm":
        await halal_deadend(
            interaction,
            "This confirmation is no longer active."
        )
        return
    if int(interaction.user.id) == int(ticket.get("sender_id") or 0):
        await halal_deadend(
            interaction,
            "Only the other party can confirm these deal details."
        )
        return
    await consume_halal_prompt(
        interaction,
        ticket,
        "details_confirm",
        "details_confirm_ping",
        "deal_details",
        "details_ping",
        "user_details"
    )
    if not correct:
        await send_halal_details_prompt(interaction.channel, ticket)
        return
    await send_halal_amount_prompt(interaction.channel, ticket)


async def confirm_halal_amount(interaction, correct):
    ticket = get_ticket(interaction.channel_id)
    if not is_halal_ticket(ticket) or not is_halal_party(interaction.user, ticket):
        await halal_deadend(
            interaction,
            "Only the two traders can confirm the amount."
        )
        return
    if ticket.get("status") != "halal_amount_confirm":
        await halal_deadend(
            interaction,
            "This confirmation is no longer active."
        )
        return
    if not correct:
        ticket["usd_amount"] = None
        ticket["usd_confirmed"] = []
        await save_data()
        await consume_halal_prompt(
            interaction,
            ticket,
            "amount_confirm",
            "amount_correct",
            "amount_error",
            "user_amount"
        )
        await send_halal_amount_prompt(interaction.channel, ticket)
        return
    confirmed = list(ticket.get("usd_confirmed") or [])
    if interaction.user.id in confirmed:
        await halal_deadend(
            interaction,
            "You already confirmed the USD amount."
        )
        return
    confirmed.append(interaction.user.id)
    ticket["usd_confirmed"] = confirmed
    both = {
        int(ticket["sender_id"]),
        int(ticket["receiver_id"])
    }.issubset(set(confirmed))
    await save_data()
    await ack_halal_interaction(interaction)
    await send_halal_correct(
        interaction.channel,
        ticket,
        interaction.user,
        "amount_correct"
    )
    if both:
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass
        await delete_halal_keys(
            interaction.channel,
            ticket,
            "amount_confirm",
            "deal_amount",
            "amount_ping",
            "amount_correct",
            "amount_error",
            "user_amount"
        )
        await save_data()
        await send_halal_payment(interaction.channel, ticket)
        return
    await save_data()


def valid_crypto_address(coin, address):
    address = str(address or "").strip()
    family = coin.get("family")
    if family == "utxo":
        if coin.get("key") == "ltc":
            return bool(re.fullmatch(r"(ltc1|[LM3])[a-zA-HJ-NP-Z0-9]{25,62}", address))
        return bool(re.fullmatch(r"(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}", address))
    if family in {"eth", "erc20", "bep20"}:
        return bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", address))
    if family in {"sol", "spl"}:
        return bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", address))
    return len(address) >= 20


async def handle_halal_chat(message, ticket):
    content = (message.content or "").strip()
    status = ticket.get("status")
    staff = is_staff_command_user(message.author) or is_admin(message.author)
    if staff and content.startswith("!"):
        return False

    unlocked = bool(ticket.get("chat_unlocked")) or status in {
        "waiting_deposit",
        "deposit_unconfirmed",
        "waiting_release",
        "release_confirmation",
        "address_prompt",
        "address_confirmation",
        "sending_crypto",
        "settlement_pending",
        "completed"
    }

    async def reject():
        if staff:
            return False
        try:
            await message.delete()
        except discord.HTTPException:
            pass
        return True

    if (
        ticket.get("deal_type")
        and ticket.get("trader_id")
        and not ticket.get("messages", {}).get("role_selection")
        and status in {
            "halal_setup",
            "halal_waiting_trader",
            "halal_role_selection"
        }
    ):
        await maybe_start_halal_roles(message.channel, ticket)
        return True

    waiting_trader = (
        status in {"halal_setup", "halal_waiting_trader"}
        or (
            bool(ticket.get("deal_type"))
            and not ticket.get("trader_id")
            and status not in {
                "halal_role_selection",
                "halal_role_confirmation",
                "halal_details",
                "halal_details_confirm",
                "halal_amount",
                "halal_amount_confirm",
                "waiting_deposit",
                "trade"
            }
        )
    )
    if waiting_trader and not ticket.get("trader_id"):
        if not ticket.get("deal_type"):
            return await reject()
        opener = int(ticket.get("opener_id") or 0)
        if int(message.author.id) != opener and not staff:
            return await reject()
        if not content:
            return await reject()
        trader = None
        for user_id in extract_user_ids(content):
            trader = await resolve_trader(message.guild, str(user_id))
            if trader is not None:
                break
        if trader is None:
            trader = await resolve_trader(message.guild, content)
        if trader is None:
            await delete_chat_message(message)
            await redo_halal_userid_prompt(
                message.channel,
                ticket,
                "That user is not in this server. They must join, then paste their UserID or @mention."
            )
            return True
        if trader.bot or trader.id == message.author.id:
            await delete_chat_message(message)
            await redo_halal_userid_prompt(
                message.channel,
                ticket,
                "Please paste the UserID of the user you are dealing with."
            )
            return True
        await delete_chat_message(message)
        try:
            await add_halal_trader(message.channel, ticket, trader)
        except Exception:
            logger.exception("Failed to add Halal trader / start roles")
            ticket["trader_id"] = None
            ticket["status"] = "halal_waiting_trader"
            ticket.get("messages", {}).pop("role_selection", None)
            await save_data()
            await redo_halal_userid_prompt(
                message.channel,
                ticket,
                "Could not start role selection. Paste the UserID again."
            )
        return True

    if status == "halal_details":
        if int(message.author.id) != int(ticket.get("sender_id") or 0):
            return await reject()
        if not content:
            return await reject()
        ticket["deal_details"] = content[:1000]
        ticket["status"] = "halal_details_confirm"
        await delete_chat_message(message)
        await delete_halal_keys(
            message.channel,
            ticket,
            "deal_details",
            "details_ping"
        )
        await save_data()
        other = ticket.get("receiver_id")
        confirm = await send_halal_layout(
            message.channel,
            HalalDetailsLayout(ticket),
            ping=f"<@{other}>",
            ticket=ticket,
            ping_key="details_confirm_ping"
        )
        ticket["messages"]["details_confirm"] = confirm.id
        await save_data()
        return True

    if status == "halal_amount":
        if int(message.author.id) != int(ticket.get("sender_id") or 0):
            return await reject()
        if not content:
            return await reject()
        amount = parse_positive_decimal(content)
        await delete_chat_message(message)
        if amount is None:
            await delete_halal_keys(message.channel, ticket, "amount_error")
            err = await message.channel.send("Enter a valid USD amount.")
            ticket.setdefault("messages", {})["amount_error"] = err.id
            await save_data()
            return True
        amount = amount.quantize(Decimal("0.01"))
        if amount < halal_min_usd():
            await delete_halal_keys(message.channel, ticket, "amount_error")
            err = await message.channel.send(
                view=halal_text_container(
                    f"{money(halal_min_usd())} USD Minimum",
                    COLOR_HALAL_RED
                )
            )
            ticket.setdefault("messages", {})["amount_error"] = err.id
            await save_data()
            return True
        ticket["usd_amount"] = str(amount)
        ticket["usd_confirmed"] = []
        ticket["status"] = "halal_amount_confirm"
        await delete_halal_keys(
            message.channel,
            ticket,
            "deal_amount",
            "amount_ping",
            "amount_error"
        )
        await save_data()
        confirm = await message.channel.send(view=HalalAmountLayout(ticket))
        ticket["messages"]["amount_confirm"] = confirm.id
        await save_data()
        return True

    if status == "address_prompt":
        if int(message.author.id) != int(ticket.get("receiver_id") or 0):
            return await reject()
        if not content:
            return await reject()
        coin = halal_coin(ticket)
        address = content.split()[0]
        await delete_chat_message(message)
        if not valid_crypto_address(coin, address):
            await delete_halal_keys(message.channel, ticket, "address_error")
            err = await message.channel.send(
                f"That does not look like a valid {coin.get('label')} address."
            )
            ticket.setdefault("messages", {})["address_error"] = err.id
            await save_data()
            return True
        ticket["receiver_address"] = address
        ticket["status"] = "address_confirmation"
        await delete_halal_keys(
            message.channel,
            ticket,
            "address_prompt",
            "address_ping",
            "address_error"
        )
        await save_data()
        message_sent = await message.channel.send(
            view=HalalAddressConfirmLayout(ticket),
            allowed_mentions=discord.AllowedMentions(
                users=True, roles=False, everyone=False
            )
        )
        ticket["messages"]["address_confirmation"] = message_sent.id
        await save_data()
        return True

    if not unlocked:
        return await reject()

    if not is_halal_party(message.author, ticket) and not staff:
        return await reject()

    return False


async def send_halal_payment(channel, ticket):
    coin = halal_coin(ticket)
    address = coin.get("address") or ""
    if not address:
        await channel.send(
            "A deposit address has not been set for this coin. "
            "Fill the HALAL_*_ADDRESS values in the bot file."
        )
        ticket["status"] = "halal_amount_confirm"
        ticket["usd_confirmed"] = []
        await save_data()
        return
    usd = Decimal(str(ticket.get("usd_amount") or "0"))
    if coin.get("price"):
        price = await get_coinbase_spot(coin["price"])
        if price is None:
            await channel.send(
                "Unable to retrieve the current price. Please confirm the USD amount again."
            )
            ticket["status"] = "halal_amount_confirm"
            ticket["usd_confirmed"] = []
            await save_data()
            await channel.send(view=HalalAmountLayout(ticket))
            return
        decimals = int(coin.get("display_decimals") or coin.get("decimals") or 8)
        crypto_amount = (usd / price).quantize(
            Decimal(10) ** -decimals,
            rounding=ROUND_DOWN
        )
    else:
        price = Decimal("1.00")
        decimals = int(coin.get("display_decimals") or 4)
        crypto_amount = usd.quantize(
            Decimal(10) ** -decimals,
            rounding=ROUND_DOWN
        )
    ticket["crypto_price"] = str(price)
    ticket["crypto_amount"] = str(crypto_amount)
    ticket["deposit_address"] = address
    ticket["deposit_txid"] = None
    ticket["deposit_amount"] = None
    ticket["deposit_confirmations"] = 0
    ticket["manual_deposit_override"] = False
    ticket["manual_reference"] = None
    ticket["baseline_ready"] = False
    ticket["copied_details"] = False
    ticket["status"] = "waiting_deposit"
    ticket["payment_started_at"] = int(time.time())
    ticket["chat_unlocked"] = True
    await save_data()
    start_baseline(ticket)
    message = await send_halal_layout(
        channel,
        HalalInvoiceLayout(ticket),
        ping=f"<@{ticket['sender_id']}> <@{ticket['receiver_id']}>"
    )
    ticket["messages"]["payment_info"] = message.id
    waiting = await channel.send(
        view=halal_text_container("Awaiting transaction...", COLOR_HALAL_GREEN)
    )
    ticket["messages"]["awaiting"] = waiting.id
    await save_data()
    ensure_monitor(ticket)


async def update_awaiting(channel, ticket, text):
    message = await fetch_message(channel, ticket.get("messages", {}).get("awaiting"))
    if message is None:
        return
    try:
        await message.edit(view=halal_text_container(text, COLOR_HALAL_GREEN))
    except discord.HTTPException:
        pass


async def send_halal_release_confirmation(channel, ticket):
    ticket["status"] = "release_confirmation"
    await save_data()
    message = await channel.send(view=HalalReleaseLayout(ticket))
    ticket["messages"]["release_confirmation"] = message.id
    await save_data()


async def update_halal_proceed_released(channel, ticket):
    old = await fetch_message(channel, ticket.get("messages", {}).get("proceed"))
    if old is None:
        return
    try:
        await old.edit(view=HalalProceedLayout(ticket, released=True))
    except discord.HTTPException:
        pass


async def send_halal_address_prompt(channel, ticket):
    coin = halal_coin(ticket)
    ticket["status"] = "address_prompt"
    await save_data()
    view = TinyLayout(
        discord.ui.TextDisplay(
            f"{H2} Provide your {coin.get('label')} address"
        ),
        discord.ui.TextDisplay(
            f"The deal is now complete! Paste your {coin.get('label')} address "
            "below to initiate the release from the Middleman wallet."
        ),
        accent=COLOR_HALAL_GRAY
    )
    message = await send_halal_layout(
        channel,
        view,
        ping=f"<@{ticket['receiver_id']}>",
        ticket=ticket,
        ping_key="address_ping"
    )
    ticket["messages"]["address_prompt"] = message.id
    await save_data()


async def finish_halal_address_confirm(channel, ticket):
    ticket["status"] = "settlement_pending"
    await save_data()
    if SETTLEMENT_MODE.lower() == "simulation":
        fake = f"SIMULATION-{secrets.token_hex(24).upper()}"
        await finalize_withdrawal(
            ticket,
            fake,
            ticket.get("deposit_amount") or ticket.get("crypto_amount"),
            simulation=True
        )
        return
    await channel.send(
        view=halal_text_container(
            "Settlement is pending. Staff will release the funds shortly.",
            COLOR_HALAL_ORANGE
        )
    )
    await send_settlement_request(ticket)


async def send_halal_completion(ticket):
    channel = await resolve_ticket_channel(ticket)
    if channel is not None and not ticket.get("withdrawal_success_sent"):
        await send_halal_layout(
            channel,
            released_layout(ticket),
            ping=f"<@{ticket['sender_id']}> <@{ticket['receiver_id']}>"
        )
        complete = await channel.send(view=HalalCompleteLayout())
        ticket["messages"]["withdrawal_success"] = complete.id
        ticket["withdrawal_success_sent"] = True
        await save_data()
        ensure_halal_auto_close(ticket)
    if not ticket.get("completed_channel_sent"):
        guild = bot.get_guild(int(ticket["guild_id"]))
        dest_id = int(HALAL_COMPLETED_CHANNEL or 0) or COMPLETED_TRANSACTION_CHANNEL
        completed_channel = await get_configured_channel(guild, dest_id)
        if completed_channel is not None:
            try:
                await completed_channel.send(view=HalalCompletedLogLayout(ticket))
                ticket["completed_channel_sent"] = True
                await save_data()
            except discord.HTTPException:
                logger.exception(
                    "Failed to send Halal completed log for ticket %s",
                    ticket.get("number")
                )


def ensure_halal_auto_close(ticket):
    key = str(ticket.get("channel_id"))
    existing = HALAL_CLOSE_TASKS.get(key)
    if existing is not None and not existing.done():
        return
    HALAL_CLOSE_TASKS[key] = asyncio.create_task(halal_auto_close(ticket))


async def halal_auto_close(ticket):
    key = str(ticket.get("channel_id"))
    try:
        await asyncio.sleep(max(5, int(HALAL_AUTO_CLOSE_SECONDS)))
        current = get_ticket(ticket.get("channel_id"))
        if current is None or current.get("status") != "completed":
            return
        channel = await resolve_ticket_channel(current)
        if channel is None:
            return
        await close_ticket_channel(
            channel,
            current,
            "Halal ticket auto-closed after completion"
        )
    except asyncio.CancelledError:
        return
    finally:
        HALAL_CLOSE_TASKS.pop(key, None)


async def handle_halal_deposit_detected(ticket, txid, amount, confirmations):
    if txid and not await claim_deposit_txid(ticket, txid):
        return
    channel_id = int(ticket["channel_id"])
    should_send = False
    should_confirm = False
    async with get_ticket_lock(channel_id):
        current = get_ticket(channel_id)
        if current is None or current.get("status") not in {
            "waiting_deposit",
            "deposit_unconfirmed"
        }:
            return
        previous = current.get("deposit_txid")
        if txid:
            current["deposit_txid"] = txid
        current["deposit_amount"] = str(amount)
        current["deposit_confirmations"] = int(confirmations)
        current["manual_deposit_override"] = bool(current.get("manual_deposit_override"))
        if txid and (
            not previous or normalize_txid(previous) != normalize_txid(txid)
        ):
            should_send = True
        current["status"] = "deposit_unconfirmed"
        coin = halal_coin(current)
        needed = int(coin.get("confirmations") or 1)
        should_confirm = (
            Decimal(str(amount)) >= required_crypto_decimal(current)
            and int(confirmations) >= needed
        )
        await save_data()
    channel = await resolve_ticket_channel(ticket)
    if channel is None:
        return
    if should_send:
        await update_awaiting(channel, ticket, "Awaiting confirmation...")
        message = await channel.send(view=detected_layout(ticket))
        ticket["messages"]["deposit_detected"] = message.id
        await save_data()
    if should_confirm:
        await handle_halal_deposit_confirmed(ticket)


async def handle_halal_deposit_confirmed(ticket):
    channel_id = int(ticket["channel_id"])
    async with get_ticket_lock(channel_id):
        current = get_ticket(channel_id)
        if current is None:
            return
        if current.get("status") in {
            "deposit_confirmed",
            "trade",
            "cancellation",
            "release_confirmation",
            "address_prompt",
            "address_confirmation",
            "settlement_pending",
            "completed"
        }:
            return
        coin = halal_coin(current)
        needed = int(coin.get("confirmations") or 1)
        received = Decimal(str(current.get("deposit_amount") or "0"))
        if received < required_crypto_decimal(current):
            return
        if int(current.get("deposit_confirmations") or 0) < needed:
            return
        current["status"] = "deposit_confirmed"
        await save_data()
    channel = await resolve_ticket_channel(ticket)
    if channel is None:
        return
    await channel.send(view=received_layout(ticket))
    proceed = await channel.send(
        view=HalalProceedLayout(ticket),
        allowed_mentions=discord.AllowedMentions(
            users=True, roles=False, everyone=False
        )
    )
    ticket["messages"]["proceed"] = proceed.id
    ticket["status"] = "trade"
    await save_data()


async def fetch_blockcypher_address(chain, address):
    url = f"https://api.blockcypher.com/v1/{chain}/main/addrs/{address}"
    token = ticket_blockcypher_token()
    params = {"limit": 50}
    if token:
        params["token"] = token

    async def load():
        return await http_get_json(
            url,
            params=params,
            timeout=20,
            wait_on_rate_limit=True
        )

    return await cached_ticket_chain_get(
        f"{chain}:addr:{address}:{token}",
        load,
        ttl=12
    )


async def fetch_blockcypher_tx(chain, txid):
    token = ticket_blockcypher_token()

    async def load():
        url = f"https://api.blockcypher.com/v1/{chain}/main/txs/{txid}"
        params = {}
        if token:
            params["token"] = token
        return await http_get_json(
            url,
            params=params,
            wait_on_rate_limit=True
        )

    return await cached_ticket_chain_get(
        f"{chain}:tx:{txid}:{token}",
        load,
        ttl=12
    )


def utxo_received(tx, address):
    total = 0
    for output in tx.get("outputs") or []:
        addresses = output.get("addresses") or []
        if address in addresses:
            total += int(output.get("value") or 0)
    return total


async def fetch_etherscan_list(action, address, chain_id, contract=None):
    api_key = ticket_etherscan_key()
    if not api_key:
        return None
    params = {
        "chainid": str(chain_id),
        "module": "account",
        "action": action,
        "address": address,
        "page": 1,
        "offset": 100,
        "sort": "desc",
        "apikey": api_key
    }
    if contract:
        params["contractaddress"] = contract
    data = await http_get_json(
        "https://api.etherscan.io/v2/api",
        params=params,
        wait_on_rate_limit=True
    )
    if data is None:
        return None
    status = str(data.get("status") or "")
    message = str(data.get("message") or "").lower()
    result = data.get("result")
    if status == "0" and "no transactions" in message:
        return []
    if status != "1":
        return None
    return result if isinstance(result, list) else None


async def solana_rpc(method, params):
    data = await http_post_json(
        cleaned_secret(HALAL_SOLANA_RPC) or "https://api.mainnet-beta.solana.com",
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    )
    if not isinstance(data, dict):
        return None
    return data.get("result")


async def create_halal_baseline_once(ticket):
    coin = halal_coin(ticket)
    address = ticket.get("deposit_address")
    started = payment_started_unix(ticket)
    family = coin.get("family")
    if not address:
        ticket["baseline_txids"] = []
        return True
    if family == "utxo":
        data = await fetch_blockcypher_address(coin.get("chain"), address)
        if not isinstance(data, dict):
            return False
        baseline = []
        for item in data.get("txrefs") or []:
            txid = item.get("tx_hash") or item.get("hash")
            if not txid:
                continue
            if started:
                timestamp = parse_chain_timestamp(
                    item.get("confirmed") or item.get("received")
                )
                if not timestamp or timestamp >= started:
                    continue
            baseline.append(normalize_txid(txid))
        ticket["baseline_txids"] = baseline
        return True
    if family in {"eth", "erc20", "bep20"}:
        action = "txlist" if family == "eth" else "tokentx"
        transfers = await fetch_etherscan_list(
            action,
            address,
            coin.get("chain_id"),
            coin.get("contract")
        )
        if transfers is None:
            return False
        baseline = []
        for item in transfers:
            txid = item.get("hash")
            if not txid:
                continue
            if started:
                timestamp = parse_chain_timestamp(item.get("timeStamp"))
                if timestamp >= started:
                    continue
            baseline.append(normalize_txid(txid))
        ticket["baseline_txids"] = baseline
        return True
    if family in {"sol", "spl"}:
        sigs = await solana_rpc(
            "getSignaturesForAddress",
            [address, {"limit": 25}]
        )
        if not isinstance(sigs, list):
            return False
        baseline = []
        for item in sigs:
            txid = item.get("signature")
            if not txid:
                continue
            if started:
                timestamp = parse_chain_timestamp(item.get("blockTime"))
                if timestamp >= started:
                    continue
            baseline.append(normalize_txid(txid))
        ticket["baseline_txids"] = baseline
        return True
    ticket["baseline_txids"] = []
    return True


def expected_base_units(ticket):
    coin = halal_coin(ticket)
    decimals = int(coin.get("decimals") or 8)
    amount = required_crypto_decimal(ticket)
    return int(
        (amount * (Decimal(10) ** decimals)).to_integral_value(rounding=ROUND_DOWN)
    )


async def monitor_halal_ticket(ticket):
    coin = halal_coin(ticket)
    address = ticket.get("deposit_address")
    if not address:
        return
    family = coin.get("family")
    expected = expected_base_units(ticket)
    baseline = set(ticket.get("baseline_txids") or [])
    current_txid = ticket.get("deposit_txid")
    if ticket.get("manual_deposit_override"):
        current_txid = None

    if family == "utxo":
        chain = coin.get("chain")
        if current_txid:
            tx = await fetch_blockcypher_tx(chain, current_txid)
            if not isinstance(tx, dict):
                return
            received = utxo_received(tx, address)
            if received < expected:
                return
            amount = Decimal(received) / (Decimal(10) ** int(coin["decimals"]))
            await handle_halal_deposit_detected(
                ticket,
                current_txid,
                amount,
                int(tx.get("confirmations") or 0)
            )
            return
        data = await fetch_blockcypher_address(chain, address)
        if not isinstance(data, dict):
            return
        hashes = []
        for key in ("unconfirmed_txrefs", "txrefs"):
            for item in data.get(key) or []:
                txid = item.get("tx_hash") or item.get("hash")
                if txid:
                    hashes.append(txid)
        for txid in hashes:
            normalized = normalize_txid(txid)
            if normalized in baseline:
                continue
            claimed = DATA["claimed_deposit_txids"].get(normalized)
            if claimed is not None and int(claimed) != int(ticket["number"]):
                continue
            tx = await fetch_blockcypher_tx(chain, txid)
            if not isinstance(tx, dict):
                continue
            if chain_event_is_before_payment(
                ticket,
                tx.get("confirmed"),
                tx.get("received")
            ):
                continue
            received = utxo_received(tx, address)
            if received != expected:
                continue
            amount = Decimal(received) / (Decimal(10) ** int(coin["decimals"]))
            await handle_halal_deposit_detected(
                ticket,
                txid,
                amount,
                int(tx.get("confirmations") or 0)
            )
            return
        return

    if family in {"eth", "erc20", "bep20"}:
        action = "txlist" if family == "eth" else "tokentx"
        transfers = await fetch_etherscan_list(
            action,
            address,
            coin.get("chain_id"),
            coin.get("contract")
        )
        if transfers is None:
            return
        for item in transfers:
            txid = item.get("hash")
            if not txid:
                continue
            if str(item.get("to") or "").lower() != address.lower():
                continue
            if family != "eth":
                if str(item.get("contractAddress") or "").lower() != str(coin.get("contract") or "").lower():
                    continue
            if family == "eth" and int(item.get("isError") or 0) != 0:
                continue
            normalized = normalize_txid(txid)
            if current_txid and normalized != normalize_txid(current_txid):
                continue
            if not current_txid:
                if normalized in baseline:
                    continue
                claimed = DATA["claimed_deposit_txids"].get(normalized)
                if claimed is not None and int(claimed) != int(ticket["number"]):
                    continue
                if chain_event_is_before_payment(ticket, item.get("timeStamp")):
                    continue
            value = Decimal(str(item.get("value") or "0"))
            if int(value) != expected:
                continue
            amount = value / (Decimal(10) ** int(coin["decimals"]))
            await handle_halal_deposit_detected(
                ticket,
                txid,
                amount,
                int(item.get("confirmations") or 0)
            )
            return
        return

    if family in {"sol", "spl"}:
        sigs = await solana_rpc(
            "getSignaturesForAddress",
            [address, {"limit": 20}]
        )
        if not isinstance(sigs, list):
            return
        for item in sigs:
            txid = item.get("signature")
            if not txid:
                continue
            normalized = normalize_txid(txid)
            if current_txid and normalized != normalize_txid(current_txid):
                continue
            if not current_txid:
                if normalized in baseline:
                    continue
                claimed = DATA["claimed_deposit_txids"].get(normalized)
                if claimed is not None and int(claimed) != int(ticket["number"]):
                    continue
                if chain_event_is_before_payment(ticket, item.get("blockTime")):
                    continue
            tx = await solana_rpc(
                "getTransaction",
                [txid, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
            )
            if not isinstance(tx, dict):
                continue
            received = solana_received(tx, address, coin)
            if received != expected:
                continue
            amount = Decimal(received) / (Decimal(10) ** int(coin["decimals"]))
            slot_meta = tx.get("meta") or {}
            confirmations = 1 if item.get("confirmationStatus") == "finalized" else 0
            if slot_meta.get("err"):
                continue
            await handle_halal_deposit_detected(
                ticket,
                txid,
                amount,
                confirmations
            )
            return


def solana_received(tx, address, coin):
    message = ((tx.get("transaction") or {}).get("message") or {})
    instructions = message.get("instructions") or []
    total = 0
    family = coin.get("family")
    mint = str(coin.get("mint") or "")
    for ins in instructions:
        parsed = ins.get("parsed") if isinstance(ins, dict) else None
        if not isinstance(parsed, dict):
            continue
        info = parsed.get("info") or {}
        kind = parsed.get("type")
        if family == "sol" and kind == "transfer":
            if str(info.get("destination") or "") == address:
                total += int(info.get("lamports") or 0)
        if family == "spl" and kind in {"transfer", "transferChecked"}:
            dest = str(
                info.get("destination")
                or (info.get("tokenAmount") and "")
                or ""
            )
            token_mint = str(info.get("mint") or "")
            if mint and token_mint and token_mint != mint:
                continue
            amount = info.get("tokenAmount", {}).get("amount") if isinstance(info.get("tokenAmount"), dict) else info.get("amount")
            account = str(info.get("destination") or "")
            if account == address or str(info.get("authority") or "") == address:
                try:
                    total += int(amount or 0)
                except (TypeError, ValueError):
                    pass
    if family == "spl" and total == 0:
        meta = tx.get("meta") or {}
        post = meta.get("postTokenBalances") or []
        pre = {
            (item.get("accountIndex"), item.get("mint")): item
            for item in meta.get("preTokenBalances") or []
        }
        for item in post:
            if str(item.get("mint") or "") != mint:
                continue
            owner = str((item.get("owner") or item.get("owner")) or "")
            if owner != address:
                continue
            post_amount = Decimal(str(((item.get("uiTokenAmount") or {}).get("amount") or "0")))
            before = pre.get((item.get("accountIndex"), item.get("mint"))) or {}
            pre_amount = Decimal(str(((before.get("uiTokenAmount") or {}).get("amount") or "0")))
            delta = int(post_amount - pre_amount)
            if delta > 0:
                total += delta
    return total


class HalalPanelPersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for key in (
            "btc",
            "eth",
            "ltc",
            "sol",
            "usdt_erc20",
            "usdc_erc20",
            "usdt_bep20",
            "usdt_sol",
            "usdc_sol"
        ):
            self.add_item(HalalStartButton(key))


class HalalFlowPersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HalalDealTypeSelect())
        self.add_item(HalalSelectRoleButton("sender"))
        self.add_item(HalalSelectRoleButton("receiver"))
        self.add_item(HalalResetRolesButton())
        self.add_item(HalalRoleConfirmButton("sender"))
        self.add_item(HalalRoleConfirmButton("receiver"))
        self.add_item(HalalReturnButton())
        self.add_item(HalalCorrectButton("details"))
        self.add_item(HalalIncorrectButton("details"))
        self.add_item(HalalCorrectButton("amount"))
        self.add_item(HalalIncorrectButton("amount"))
        self.add_item(HalalCloseButton())


class HalalPayPersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HalalCopyFieldButton("address"))
        self.add_item(HalalCopyFieldButton("amount"))
        self.add_item(HalalCopyDetailsButton())
        self.add_item(HalalCancelDealButton())
        self.add_item(HalalCheckDepositButton())
        self.add_item(HalalProceedReleaseButton())
        self.add_item(HalalProceedCancelButton())
        self.add_item(HalalReleaseConfirmButton())
        self.add_item(HalalReleaseBackButton())
        self.add_item(HalalAddressConfirmButton())
        self.add_item(HalalAddressBackButton())
        self.add_item(HalalCompleteCloseButton())


def default_jaces_guild_state():
    return {
        "active": False,
        "mode": "normal",
        "show_channel_ids": [],
        "normal_channel_ids": [],
        "halal_channel_ids": []
    }


def jaces_guild_state(guild_id):
    root = DATA.setdefault(
        "jaces",
        {
            "guilds": {}
        }
    )

    guilds = root.setdefault(
        "guilds",
        {}
    )

    key = str(guild_id)
    state = guilds.get(key)

    if not isinstance(state, dict):
        state = default_jaces_guild_state()
        guilds[key] = state
        return state

    state.setdefault("active", False)
    state.setdefault("show_channel_ids", [])
    state.setdefault("normal_channel_ids", [])
    state.setdefault("halal_channel_ids", [])
    if state.get("mode") not in {"jaces", "normal", "halal"}:
        state["mode"] = "jaces" if state.get("active") else "normal"

    # Older saves used hider_channel_ids for the normal/hidden set.
    if state.get("hider_channel_ids"):
        state["normal_channel_ids"] = store_id_list(
            unique_snowflakes(
                state.get("normal_channel_ids", []),
                state.get("hider_channel_ids", [])
            )
        )
        state.pop("hider_channel_ids", None)

    return state


def unique_snowflakes(*groups):
    seen = []
    seen_set = set()

    for group in groups:
        if not group:
            continue

        for value in group:
            try:
                snowflake = int(value)
            except (TypeError, ValueError):
                continue

            if snowflake <= 0 or snowflake in seen_set:
                continue

            seen.append(snowflake)
            seen_set.add(snowflake)

    return seen


def store_id_list(values):
    return [str(value) for value in unique_snowflakes(values)]


def jaces_show_ids(state):
    return unique_snowflakes(
        state.get("show_channel_ids", [])
    )


def jaces_normal_ids(state):
    return unique_snowflakes(
        state.get("normal_channel_ids", []),
        state.get("hider_channel_ids", [])
    )


def jaces_halal_ids(state):
    return unique_snowflakes(
        state.get("halal_channel_ids", [])
    )


def guild_mode(state):
    mode = str(state.get("mode") or "")
    if mode in {"jaces", "normal", "halal"}:
        return mode
    return "jaces" if state.get("active") else "normal"


def ticket_channel_id_set():
    ids = set()

    for ticket in DATA.get("tickets", {}).values():
        if not isinstance(ticket, dict):
            continue

        try:
            ids.add(int(ticket.get("channel_id")))
        except (TypeError, ValueError):
            continue

    return ids


def is_jaces_ticket_target(channel):
    if channel is None:
        return True

    if get_ticket(channel.id):
        return True

    return False


def is_jaces_admin_user(user):
    if user is None:
        return False

    if int(user.id) == int(YOUR_USER):
        return True

    return (
        isinstance(user, discord.Member)
        and user.guild_permissions.administrator
    )


def staff_command_role_id():
    try:
        return int(STAFF_COMMAND_ROLE or 0)
    except (TypeError, ValueError):
        return 0


def is_staff_command_user(user):
    if is_jaces_admin_user(user):
        return True

    if not isinstance(user, discord.Member):
        return False

    role_id = staff_command_role_id()
    if role_id <= 0:
        return False

    return any(role.id == role_id for role in user.roles)


PRESENCE_ACTIVITY_TYPES = {
    "playing": discord.ActivityType.playing,
    "watching": discord.ActivityType.watching,
    "listening": discord.ActivityType.listening,
    "competing": discord.ActivityType.competing,
    "custom": discord.ActivityType.custom
}

PRESENCE_STATUSES = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible
}


def presence_state():
    state = DATA.get("presence")
    if not isinstance(state, dict):
        state = default_presence()
        DATA["presence"] = state
        return state

    state.setdefault("type", "playing")
    state.setdefault("text", "")
    state.setdefault("status", "online")
    return state


def build_bot_activity(state):
    text = str(state.get("text") or "").strip()
    if not text:
        return None

    kind = str(state.get("type") or "playing").lower()
    if kind == "custom":
        return discord.CustomActivity(name=text[:128])

    activity_type = PRESENCE_ACTIVITY_TYPES.get(
        kind,
        discord.ActivityType.playing
    )
    return discord.Activity(
        type=activity_type,
        name=text[:128]
    )


def bot_status_from_state(state):
    return PRESENCE_STATUSES.get(
        str(state.get("status") or "online").lower(),
        discord.Status.online
    )


def presence_label(state):
    text = str(state.get("text") or "").strip()
    if not text:
        return "cleared"

    kind = str(state.get("type") or "playing").title()
    if kind.lower() == "listening":
        return f"Listening to {text}"
    if kind.lower() == "competing":
        return f"Competing in {text}"
    if kind.lower() == "custom":
        return text
    return f"{kind} {text}"


async def apply_bot_presence():
    state = presence_state()
    await bot.change_presence(
        activity=build_bot_activity(state),
        status=bot_status_from_state(state)
    )


async def apply_bot_bio(text):
    bio = str(text or "").strip()
    if not bio:
        return None

    try:
        app = await bot.application_info()
    except discord.HTTPException as error:
        return f"bot bio failed: {error}"

    current = str(getattr(app, "description", None) or "").strip()
    if current == bio:
        return None

    try:
        await app.edit(description=bio[:400])
    except (TypeError, discord.HTTPException) as error:
        return f"bot bio failed: {error}"

    return "bot bio updated"


async def apply_profile_presence(profile):
    notes = []
    status = str(profile.get("bot_status") or "").strip().lower()
    activity_type = str(
        profile.get("bot_activity_type") or "playing"
    ).strip().lower()
    activity_text = str(profile.get("bot_activity") or "").strip()[:128]
    bio = str(profile.get("bot_bio") or "").strip()

    changed = False
    state = presence_state()

    noted_presence = False
    if status in PRESENCE_STATUSES:
        state["status"] = status
        changed = True
        noted_presence = True

    if activity_text:
        if activity_type not in PRESENCE_ACTIVITY_TYPES:
            activity_type = "playing"
        state["type"] = activity_type
        state["text"] = activity_text
        changed = True
        noted_presence = True
    elif state.get("text"):
        state["text"] = ""
        changed = True

    if changed:
        await save_data()
        try:
            await apply_bot_presence()
            if noted_presence:
                notes.append("bot activity updated")
        except discord.HTTPException as error:
            if noted_presence:
                notes.append(f"bot activity failed: {error}")

    if bio:
        note = await apply_bot_bio(bio)
        if note:
            notes.append(note)
    else:
        await apply_bot_bio("", clear_if_empty=True)

    return notes


def mark_channel_list(state, list_key, other_key, channel_id):
    current = unique_snowflakes(state.get(list_key, []), [channel_id])
    state[list_key] = store_id_list(current)
    others = [other_key] if isinstance(other_key, str) else list(other_key or [])
    for extra in ("show_channel_ids", "normal_channel_ids", "halal_channel_ids"):
        if extra != list_key and extra not in others:
            others.append(extra)
    for key in others:
        if not key or key == list_key:
            continue
        state[key] = store_id_list(
            [
                value
                for value in unique_snowflakes(state.get(key, []))
                if value != int(channel_id)
            ]
        )


async def read_asset_bytes(source):
    if not source:
        return None

    text = str(source).strip()
    if not text:
        return None

    if text.startswith("http://") or text.startswith("https://"):
        try:
            async with bot.session.get(
                text,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:
                if response.status != 200:
                    return None
                return await response.read()
        except Exception:
            logger.exception("Failed to download jaces asset %s", text)
            return None

    path = Path(text)
    if not path.is_file():
        path = JACES_ASSETS_DIR / text
    if not path.is_file():
        return None

    try:
        return path.read_bytes()
    except OSError:
        logger.exception("Failed to read jaces asset %s", path)
        return None


def get_bot_managed_role(guild):
    me = guild.me
    if me is None:
        return None

    for role in reversed(me.roles):
        tags = getattr(role, "tags", None)
        if tags is not None and tags.bot_id == me.id:
            return role

        if role.is_bot_managed():
            return role

    return None


def config_branding(prefix):
    return {
        "server_name": globals()[f"{prefix}_SERVER_NAME"],
        "server_description": globals()[f"{prefix}_SERVER_DESCRIPTION"],
        "server_icon": globals()[f"{prefix}_SERVER_ICON"],
        "server_banner": globals()[f"{prefix}_SERVER_BANNER"],
        "bot_name": globals()[f"{prefix}_BOT_NAME"],
        "bot_avatar": globals()[f"{prefix}_BOT_AVATAR"],
        "bot_banner": globals()[f"{prefix}_BOT_BANNER"],
        "bot_role_name": globals()[f"{prefix}_BOT_ROLE_NAME"],
        "bot_status": globals()[f"{prefix}_BOT_STATUS"],
        "bot_activity_type": globals()[f"{prefix}_BOT_ACTIVITY_TYPE"],
        "bot_activity": globals()[f"{prefix}_BOT_ACTIVITY"],
        "bot_bio": globals()[f"{prefix}_BOT_BIO"]
    }


def branding_has_values(profile):
    if not isinstance(profile, dict):
        return False

    return any(
        str(profile.get(key) or "").strip()
        for key in (
            "server_name",
            "server_description",
            "server_icon",
            "server_banner",
            "bot_name",
            "bot_avatar",
            "bot_banner",
            "bot_role_name",
            "bot_status",
            "bot_activity_type",
            "bot_activity",
            "bot_bio"
        )
    )


async def wait_for_jaces_rate_gate():
    while True:
        delay = JACES_RATE_WAIT_UNTIL - time.monotonic()
        if delay <= 0:
            return
        await asyncio.sleep(delay)


async def trip_jaces_rate_gate(seconds):
    global JACES_RATE_WAIT_UNTIL

    wait = max(
        float(JACES_RATE_RETRY_SECONDS),
        float(seconds or 0)
    )
    until = time.monotonic() + wait
    if until > JACES_RATE_WAIT_UNTIL:
        JACES_RATE_WAIT_UNTIL = until

    log_action(
        "jaces_rate_limited",
        retry_in=int(wait)
    )
    await asyncio.sleep(wait)


def rate_limit_retry_after(error):
    retry = getattr(error, "retry_after", None)
    if retry is not None:
        try:
            return max(
                float(JACES_RATE_RETRY_SECONDS),
                float(retry)
            )
        except (TypeError, ValueError):
            pass

    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None) or {}
    raw = None
    if hasattr(headers, "get"):
        raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is not None:
        try:
            return max(
                float(JACES_RATE_RETRY_SECONDS),
                float(raw)
            )
        except (TypeError, ValueError):
            pass

    return float(JACES_RATE_RETRY_SECONDS)


def is_discord_rate_limit(error):
    rate_limited = getattr(discord, "RateLimited", None)
    if rate_limited is not None and isinstance(error, rate_limited):
        return True

    return (
        isinstance(error, discord.HTTPException)
        and getattr(error, "status", None) == 429
    )


async def call_until_not_rate_limited(label, func):
    while True:
        await wait_for_jaces_rate_gate()
        try:
            return await func()
        except Exception as error:
            if not is_discord_rate_limit(error):
                raise

            log_action(
                "jaces_rate_limited_retry",
                action=label,
                retry_in=int(rate_limit_retry_after(error))
            )
            await trip_jaces_rate_gate(
                rate_limit_retry_after(error)
            )


def clone_permission_overwrite(overwrite):
    if overwrite is None:
        return discord.PermissionOverwrite()

    allow, deny = overwrite.pair()
    return discord.PermissionOverwrite.from_pair(allow, deny)


def overwrite_for_target(channel, target):
    overwrites = getattr(channel, "overwrites", None) or {}
    target_id = getattr(target, "id", None)

    for obj, overwrite in overwrites.items():
        if getattr(obj, "id", None) == target_id:
            return overwrite

    return None


async def set_view_channel_only(channel, target, value, reason):
    overwrite = clone_permission_overwrite(
        overwrite_for_target(channel, target)
    )
    desired = bool(value)

    if overwrite.view_channel is desired:
        return "skipped"

    overwrite.view_channel = desired

    try:
        await call_until_not_rate_limited(
            f"view_channel:{getattr(channel, 'id', channel)}",
            lambda: channel.set_permissions(
                target,
                overwrite=overwrite,
                reason=reason
            )
        )
    except discord.HTTPException as error:
        return f"error:{error}"

    return "updated"


async def apply_everyone_view(channel, visible, reason):
    return await set_view_channel_only(
        channel,
        channel.guild.default_role,
        bool(visible),
        reason
    )


async def resolve_guild_channel(guild, channel_id):
    channel = guild.get_channel(channel_id)
    if channel is not None:
        return channel

    try:
        fetched = await call_until_not_rate_limited(
            f"fetch_channel:{channel_id}",
            lambda: bot.fetch_channel(channel_id)
        )
    except discord.HTTPException:
        return None

    if getattr(fetched, "guild", None) is None:
        return None

    if fetched.guild.id != guild.id:
        return None

    return fetched


async def apply_one_edit(label, editor):
    try:
        await call_until_not_rate_limited(label, editor)
        return f"{label} updated"
    except TypeError as error:
        return f"{label} failed: {error}"
    except discord.HTTPException as error:
        return f"{label} failed: {error}"


async def apply_branding_profile(guild, profile, reason):
    notes = []

    if not branding_has_values(profile):
        notes.extend(await apply_profile_presence(profile))
        return notes

    server_name = str(profile.get("server_name") or "").strip()
    description = str(profile.get("server_description") or "").strip()
    icon_bytes = await read_asset_bytes(profile.get("server_icon"))
    banner_bytes = await read_asset_bytes(profile.get("server_banner"))

    if server_name and guild.name != server_name:
        notes.append(
            await apply_one_edit(
                "server name",
                lambda: guild.edit(name=server_name, reason=reason)
            )
        )

    if description:
        notes.append(
            await apply_one_edit(
                "server description",
                lambda: guild.edit(description=description, reason=reason)
            )
        )
    elif getattr(guild, "description", None):
        try:
            await guild.edit(description="", reason=reason)
        except (TypeError, discord.HTTPException):
            pass

    if icon_bytes:
        notes.append(
            await apply_one_edit(
                "server icon",
                lambda: guild.edit(icon=icon_bytes, reason=reason)
            )
        )

    if banner_bytes:
        notes.append(
            await apply_one_edit(
                "server banner",
                lambda: guild.edit(banner=banner_bytes, reason=reason)
            )
        )

    bot_name = str(profile.get("bot_name") or "").strip()
    avatar_bytes = await read_asset_bytes(profile.get("bot_avatar"))
    banner_user_bytes = await read_asset_bytes(profile.get("bot_banner"))

    if bot.user is not None:
        if bot_name and bot.user.name != bot_name:
            notes.append(
                await apply_one_edit(
                    "bot name",
                    lambda: bot.user.edit(username=bot_name)
                )
            )

        if avatar_bytes:
            notes.append(
                await apply_one_edit(
                    "bot avatar",
                    lambda: bot.user.edit(avatar=avatar_bytes)
                )
            )

        if banner_user_bytes:
            notes.append(
                await apply_one_edit(
                    "bot banner",
                    lambda: bot.user.edit(banner=banner_user_bytes)
                )
            )
        elif not str(profile.get("bot_banner") or "").strip():
            try:
                await bot.user.edit(banner=None)
            except (TypeError, discord.HTTPException):
                pass

    role_name = str(profile.get("bot_role_name") or "").strip()
    if role_name:
        role = get_bot_managed_role(guild)
        if role is None:
            notes.append("bot role not found")
        elif role.name != role_name:
            notes.append(
                await apply_one_edit(
                    "bot role",
                    lambda: role.edit(name=role_name, reason=reason)
                )
            )

    notes.extend(await apply_profile_presence(profile))

    return notes


async def run_channel_jobs(jobs):
    semaphore = asyncio.Semaphore(JACES_PERM_CONCURRENCY)

    async def run_job(job):
        async with semaphore:
            return await job()

    if not jobs:
        return []

    return await asyncio.gather(
        *(run_job(job) for job in jobs),
        return_exceptions=True
    )


def jaces_result_embed(title, colour, lines):
    description = "\n".join(lines) if lines else "Done."
    if len(description) > 3900:
        description = description[:3900] + "\n…"

    return discord.Embed(
        title=title,
        description=description,
        colour=colour
    )


async def set_channel_visibility(guild, channel_id, visible, reason, ticket_ids):
    if channel_id in ticket_ids:
        return ("skipped", channel_id, None)

    channel = await resolve_guild_channel(guild, channel_id)
    if channel is None:
        return ("missing", channel_id, None)

    if is_jaces_ticket_target(channel):
        return ("skipped", channel_id, None)

    result = await apply_everyone_view(channel, visible, reason)
    kind = "shown" if visible else "hidden"
    return (kind, channel_id, result)


def summarize_visibility(channel_results):
    results = {
        "shown": 0,
        "hidden": 0,
        "skipped": 0,
        "missing": 0,
        "errors": []
    }

    for item in channel_results:
        if isinstance(item, Exception):
            results["errors"].append(str(item))
            continue

        kind = item[0]
        if kind in {"shown", "hidden"}:
            results[kind] += 1
            status = item[2]
            if status not in {"updated", "skipped"}:
                results["errors"].append(str(status))
        elif kind == "missing":
            results["missing"] += 1
        else:
            results["skipped"] += 1

    return results


async def execute_guild_mode(guild, mode):
    state = jaces_guild_state(guild.id)
    ticket_ids = ticket_channel_id_set()
    jaces_ids = jaces_show_ids(state)
    normal_ids = jaces_normal_ids(state)
    halal_ids = jaces_halal_ids(state)

    if mode == "jaces":
        show_ids = jaces_ids
        hide_ids = [
            channel_id
            for channel_id in unique_snowflakes(normal_ids, halal_ids)
            if channel_id not in show_ids
        ]
        branding = "JACES"
        reason = JACES_REASON_ON
        title = "Jaces mode on"
        colour = COLOR_SUCCESS
        shown_label = "!savejaces"
        hidden_label = "!savenormall / !savehalal"
        active = True
    elif mode == "halal":
        show_ids = halal_ids
        hide_ids = [
            channel_id
            for channel_id in unique_snowflakes(jaces_ids, normal_ids)
            if channel_id not in show_ids
        ]
        branding = "HALAL"
        reason = JACES_REASON_HALAL
        title = "Halal mode on"
        colour = COLOR_HALAL_GREEN
        shown_label = "!savehalal"
        hidden_label = "!savejaces / !savenormall"
        active = False
    else:
        mode = "normal"
        show_ids = normal_ids
        hide_ids = [
            channel_id
            for channel_id in unique_snowflakes(jaces_ids, halal_ids)
            if channel_id not in show_ids
        ]
        branding = "NORMAL"
        reason = JACES_REASON_OFF
        title = "Jaces mode off"
        colour = COLOR_NEUTRAL
        shown_label = "!savenormall"
        hidden_label = "!savejaces / !savehalal"
        active = False

    jobs = []
    jobs.extend(
        lambda channel_id=channel_id: set_channel_visibility(
            guild,
            channel_id,
            True,
            reason,
            ticket_ids
        )
        for channel_id in show_ids
    )
    jobs.extend(
        lambda channel_id=channel_id: set_channel_visibility(
            guild,
            channel_id,
            False,
            reason,
            ticket_ids
        )
        for channel_id in hide_ids
    )

    channel_task = asyncio.create_task(run_channel_jobs(jobs))
    branding_task = asyncio.create_task(
        apply_branding_profile(
            guild,
            config_branding(branding),
            reason
        )
    )

    channel_results, branding_notes = await asyncio.gather(
        channel_task,
        branding_task
    )

    results = summarize_visibility(channel_results)
    state["active"] = active
    state["mode"] = mode
    await save_data()

    branding_notes = [note for note in (branding_notes or []) if note]

    lines = [
        f"{emoji_text(GREEN_TICK_EMOJI)}Shown ({shown_label}): **{results['shown']}**",
        f"{emoji_text(LOCK_EMOJI)}Hidden ({hidden_label}): **{results['hidden']}**"
    ]

    if results["skipped"]:
        lines.append(f"Tickets skipped: **{results['skipped']}**")
    if results["missing"]:
        lines.append(f"Missing channels: **{results['missing']}**")
    if branding_notes:
        lines.append("Look: " + "; ".join(branding_notes))
    if results["errors"]:
        lines.append("Issues:")
        lines.extend(f"- {error}" for error in results["errors"][:8])

    log_action(
        f"{mode}_mode_enabled",
        guild=guild.id,
        shown=results["shown"],
        hidden=results["hidden"]
    )

    return jaces_result_embed(
        title,
        colour,
        lines
    )


async def execute_jaces_mode(guild):
    return await execute_guild_mode(guild, "jaces")


async def execute_nonjaces_mode(guild):
    return await execute_guild_mode(guild, "normal")


async def execute_halal_mode(guild):
    return await execute_guild_mode(guild, "halal")


def saveable_guild_channel(channel):
    if channel is None:
        return False, "Use this in a server channel."

    if isinstance(channel, discord.Thread):
        return False, "This does not apply to tickets or threads."

    if is_jaces_ticket_target(channel):
        return False, "This does not apply to tickets."

    if not isinstance(channel, discord.abc.GuildChannel):
        return False, "This channel cannot be saved."

    return True, None


intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class JaceBot(
    commands.Bot
):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            case_insensitive=True
        )

        self.session = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()

        self.add_view(
            PanelButtonsPersistentView()
        )

        self.add_view(
            DeleteTicketPersistentView()
        )

        self.add_view(
            RoleSelectionView()
        )

        self.add_view(
            RoleConfirmationView()
        )

        self.add_view(
            UsdPromptView()
        )

        self.add_view(
            UsdConfirmationView()
        )

        self.add_view(
            PaymentInfoView()
        )

        self.add_view(
            ProceedView()
        )

        self.add_view(
            CancellationView()
        )

        self.add_view(
            ReleaseConfirmationView()
        )

        self.add_view(
            AddressPromptView()
        )

        self.add_view(
            AddressConfirmationView()
        )

        self.add_view(
            CloseTicketView()
        )

        self.add_view(
            AutoMMTosView()
        )

        self.add_view(
            HalalPanelPersistentView()
        )

        self.add_view(
            HalalFlowPersistentView()
        )

        self.add_view(
            HalalPayPersistentView()
        )

    async def close(self):
        for task in list(
            MONITOR_TASKS.values()
        ):
            if not task.done():
                task.cancel()

        for task in list(
            BASELINE_TASKS.values()
        ):
            if not task.done():
                task.cancel()

        for task in list(
            COUNTDOWN_TASKS.values()
        ):
            if not task.done():
                task.cancel()

        for task in list(
            HALAL_CLOSE_TASKS.values()
        ):
            if not task.done():
                task.cancel()

        global DEMO_ACTIVITY_TASK

        if (
            DEMO_ACTIVITY_TASK is not None
            and not DEMO_ACTIVITY_TASK.done()
        ):
            DEMO_ACTIVITY_TASK.cancel()

        if (
            self.session is not None
            and not self.session.closed
        ):
            await self.session.close()

        await super().close()


bot = JaceBot()

SLASH_SYNCED_GUILDS = set()


async def sync_slash_commands(guild=None):
    targets = [guild] if guild is not None else list(bot.guilds)
    synced_names = []

    for target in targets:
        if target is None:
            continue

        try:
            bot.tree.copy_global_to(guild=target)
            synced = await bot.tree.sync(guild=target)
            names = [command.name for command in synced]
            synced_names = names
            SLASH_SYNCED_GUILDS.add(target.id)
            log_action(
                "slash_commands_synced",
                guild=target.id,
                count=len(synced),
                names=", ".join(names) if names else "none"
            )
        except Exception:
            logger.exception(
                "Failed to sync slash commands for guild %s",
                getattr(target, "id", target)
            )

    return synced_names


async def resume_ticket_tasks():
    for ticket in list(
        DATA[
            "tickets"
        ].values()
    ):
        channel = await resolve_ticket_channel(
            ticket
        )

        if channel is None:
            await stop_ticket_chain(
                ticket.get("channel_id"),
                "ticket channel missing"
            )
            continue

        status = ticket.get(
            "status"
        )

        if status in {
            "waiting_deposit",
            "deposit_unconfirmed",
            "halal_amount"
        }:
            if (
                status == "waiting_deposit"
                and not ticket.get("baseline_ready")
            ):
                start_baseline(
                    ticket
                )

            ensure_monitor(
                ticket
            )

        elif status == "release_confirmation":
            message_id = ticket[
                "messages"
            ].get(
                "release_confirmation"
            )

            if message_id:
                start_countdown(
                    ticket,
                    "release",
                    message_id,
                    resume=True
                )

        elif status == "address_confirmation":
            message_id = ticket[
                "messages"
            ].get(
                "address_confirmation"
            )

            if message_id:
                start_countdown(
                    ticket,
                    "address",
                    message_id,
                    resume=True
                )

        elif status == "completed":
            if is_halal_ticket(ticket):
                await send_halal_completion(ticket)
            else:
                await send_completion_outputs(
                    ticket
                )


@bot.event
async def on_ready():
    global READY_RESUMED

    print_watermark()

    log_action(
        "bot_ready",
        user=bot.user,
        user_id=bot.user.id,
        guilds=len(
            bot.guilds
        )
    )

    async with READY_RESUME_LOCK:
        if not READY_RESUMED:
            READY_RESUMED = True

            await resume_ticket_tasks()

    missing = [
        guild
        for guild in bot.guilds
        if guild.id not in SLASH_SYNCED_GUILDS
    ]

    if missing:
        for guild in missing:
            await sync_slash_commands(guild)

    ensure_demo_activity_task()

    try:
        await apply_bot_presence()
        log_action(
            "bot_presence_applied",
            activity=presence_label(presence_state())
        )
    except discord.HTTPException:
        logger.exception(
            "Failed to apply saved bot activity"
        )


@bot.event
async def on_guild_join(guild):
    await sync_slash_commands(guild)


@bot.event
async def on_raw_channel_delete(payload):
    await stop_ticket_chain(
        payload.channel_id,
        "channel deleted"
    )


@bot.event
async def on_guild_channel_delete(channel):
    await stop_ticket_chain(
        getattr(channel, "id", None),
        "channel deleted"
    )


@bot.event
async def on_error(
    event_method,
    *args,
    **kwargs
):
    logger.error(
        "Unhandled Discord event error | "
        "event=%s\n%s",
        event_method,
        traceback.format_exc()
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        try:
            await ctx.reply(
                "You do not have permission to use this command.",
                mention_author=False
            )
        except discord.HTTPException:
            pass
        return

    if isinstance(error, commands.NoPrivateMessage):
        return

    logger.error(
        "Unhandled prefix command error | user=%s(%s) | command=%s\n%s",
        ctx.author,
        ctx.author.id,
        getattr(ctx.command, "qualified_name", "unknown"),
        "".join(
            traceback.format_exception(
                type(error),
                error,
                error.__traceback__
            )
        )
    )


@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return

    ticket = get_ticket(message.channel.id)
    if ticket is not None and is_halal_ticket(ticket):
        try:
            handled = await handle_halal_chat(message, ticket)
        except Exception:
            logger.exception(
                "Halal ticket chat failed | channel=%s",
                message.channel.id
            )
            handled = False
        if handled:
            return

    await bot.process_commands(message)


@bot.tree.command(
    name="panel",
    description="Send the Auto Middleman panel"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def panel(
    interaction: discord.Interaction
):
    log_action(
        "panel_sent",
        user=(
            f"{interaction.user}"
            f"({interaction.user.id})"
        ),
        guild=interaction.guild_id,
        channel=interaction.channel_id
    )

    await interaction.response.send_message(
        "Panel posted.",
        ephemeral=True
    )

    if interaction.channel is None:
        return

    try:
        await interaction.channel.send(
            view=MiddlemanPanel()
        )

    except discord.HTTPException:
        logger.exception(
            "Failed to post middleman panel"
        )

        await interaction.followup.send(
            "The panel could not be posted in this channel.",
            ephemeral=True
        )


@bot.tree.command(
    name="halalpanel",
    description="Send the Halal Auto Middleman panel"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def halalpanel(
    interaction: discord.Interaction
):
    log_action(
        "halal_panel_sent",
        user=f"{interaction.user}({interaction.user.id})",
        guild=interaction.guild_id,
        channel=interaction.channel_id
    )

    await interaction.response.send_message(
        "Panel posted.",
        ephemeral=True
    )

    if interaction.channel is None:
        return

    try:
        await interaction.channel.send(
            view=HalalPanel(interaction.guild)
        )
    except ValueError:
        crypto, stables = HalalPanel.split_views(interaction.guild)
        await interaction.channel.send(view=crypto)
        await interaction.channel.send(view=stables)
    except discord.HTTPException:
        logger.exception("Failed to post Halal middleman panel")
        await interaction.followup.send(
            "The panel could not be posted in this channel.",
            ephemeral=True
        )


@bot.tree.command(
    name="stats",
    description="View a user's middleman stats"
)
@app_commands.guild_only()
@app_commands.describe(
    user=(
        "The user whose stats you want to view"
    )
)
async def stats(
    interaction: discord.Interaction,
    user: discord.Member = None
):
    target = user or interaction.user

    log_action(
        "stats_viewed",
        requester=(
            f"{interaction.user}"
            f"({interaction.user.id})"
        ),
        target=(
            f"{target}"
            f"({target.id})"
        )
    )

    if (
        interaction.guild is not None
        and guild_mode(jaces_guild_state(interaction.guild.id)) == "halal"
    ):
        await interaction.response.send_message(
            view=HalalStatsLayout(target)
        )
        return

    await interaction.response.send_message(
        embed=stats_embed(target)
    )


@bot.tree.command(
    name="setprivacy",
    description=(
        "Control whether completed trades display your Discord user"
    )
)
@app_commands.guild_only()
@app_commands.describe(
    private=(
        "True hides your identity in completed trade posts"
    )
)
async def setprivacy(
    interaction: discord.Interaction,
    private: bool
):
    DATA[
        "privacy"
    ][
        str(
            interaction.user.id
        )
    ] = bool(
        private
    )

    await save_data()

    text = (
        "Your completed-trade identity is now hidden."
        if private
        else (
            "Your completed-trade identity will now be displayed."
        )
    )

    log_action(
        "privacy_changed",
        user=(
            f"{interaction.user}"
            f"({interaction.user.id})"
        ),
        private=bool(
            private
        )
    )

    await interaction.response.send_message(
        text,
        ephemeral=True
    )


async def mark_halal_deposit(interaction, ticket, parsed_amount, confirmation):
    if not ticket.get("crypto_amount"):
        await interaction.response.send_message(
            "The ticket has not reached the payment stage yet.",
            ephemeral=True
        )
        return

    channel = await resolve_ticket_channel(ticket)
    if channel is None:
        await interaction.response.send_message(
            "The ticket channel could not be found.",
            ephemeral=True
        )
        return

    first_manual_reference = False

    async with get_ticket_lock(ticket["channel_id"]):
        ticket = get_ticket(ticket["channel_id"])
        if ticket is None:
            await interaction.response.send_message(
                "The ticket is no longer active.",
                ephemeral=True
            )
            return

        if ticket.get("status") not in {
            "waiting_deposit",
            "deposit_unconfirmed"
        }:
            await interaction.response.send_message(
                "The ticket is not waiting for a deposit.",
                ephemeral=True
            )
            return

        exact_required_amount = required_crypto_decimal(ticket)
        if parsed_amount != exact_required_amount:
            await interaction.response.send_message(
                (
                    "The amount must exactly match the deal amount of "
                    f"{halal_amount_text(ticket, exact_required_amount)} "
                    f"{halal_coin(ticket)['short']}."
                ),
                ephemeral=True
            )
            return

        if not ticket.get("manual_reference"):
            ticket["manual_reference"] = secrets.token_hex(32)
            first_manual_reference = True

        ticket["deposit_txid"] = ticket["manual_reference"]
        ticket["deposit_amount"] = str(exact_required_amount)
        ticket["deposit_confirmations"] = int(confirmation)
        ticket["manual_deposit_override"] = True
        ticket["status"] = "deposit_unconfirmed"
        await save_data()

    previous_detected = await fetch_message(
        channel,
        ticket["messages"].get("deposit_detected")
    )

    if previous_detected is not None and not first_manual_reference:
        try:
            await previous_detected.edit(
                view=detected_layout(ticket)
            )
        except discord.HTTPException:
            previous_detected = None

    if previous_detected is None or first_manual_reference:
        detected_message = await channel.send(
            view=detected_layout(ticket)
        )
        ticket["messages"]["deposit_detected"] = detected_message.id
        await save_data()

    log_action(
        "manual_deposit_marked",
        actor=f"{interaction.user}({interaction.user.id})",
        ticket=ticket.get("number"),
        asset=get_asset_name(ticket),
        amount=halal_amount_text(
            ticket,
            ticket.get("deposit_amount") or "0"
        ),
        confirmations=int(confirmation),
        txid=ticket.get("manual_reference")
    )

    await interaction.response.send_message(
        "Deposit shown.",
        ephemeral=True
    )

    if int(confirmation) >= confirmations_required(ticket):
        await handle_halal_deposit_confirmed(ticket)
    else:
        ensure_monitor(ticket)


@bot.tree.command(
    name="mark-deposit",
    description=(
        "Manually show or confirm a deposit state"
    )
)
@app_commands.guild_only()
@app_commands.describe(
    ticket_number="The ticket number",
    amount="Amount received",
    confirmation=(
        "0 for unconfirmed, 1 or higher for confirmed"
    )
)
async def mark_deposit(
    interaction: discord.Interaction,
    ticket_number: int,
    amount: str,
    confirmation: app_commands.Range[
        int,
        0,
        100000
    ]
):
    if not is_staff_command_user(interaction.user):
        log_security(
            "unauthorized_mark_deposit_attempt",
            user=(
                f"{interaction.user}"
                f"({interaction.user.id})"
            ),
            ticket=ticket_number
        )

        await interaction.response.send_message(
            "You cannot use this command.",
            ephemeral=True
        )

        return

    ticket = get_ticket_by_number(
        ticket_number
    )

    if ticket is None:
        await interaction.response.send_message(
            "Ticket not found.",
            ephemeral=True
        )

        return

    parsed_amount = parse_positive_decimal(
        amount
    )

    if parsed_amount is None:
        await interaction.response.send_message(
            "Enter a valid positive deposit amount.",
            ephemeral=True
        )

        return

    if is_halal_ticket(ticket):
        await mark_halal_deposit(
            interaction,
            ticket,
            parsed_amount,
            confirmation
        )
        return

    if not ticket.get(
        "crypto_amount"
    ):
        await interaction.response.send_message(
            "The ticket has not reached the payment stage yet.",
            ephemeral=True
        )

        return

    channel = await resolve_ticket_channel(
        ticket
    )

    if channel is None:
        await interaction.response.send_message(
            "The ticket channel could not be found.",
            ephemeral=True
        )

        return

    first_manual_reference = False

    async with get_ticket_lock(
        ticket[
            "channel_id"
        ]
    ):
        ticket = get_ticket(
            ticket[
                "channel_id"
            ]
        )

        if ticket is None:
            await interaction.response.send_message(
                "The ticket is no longer active.",
                ephemeral=True
            )

            return

        if ticket.get(
            "status"
        ) not in {
            "waiting_deposit",
            "deposit_unconfirmed"
        }:
            await interaction.response.send_message(
                "The ticket is not waiting for a deposit.",
                ephemeral=True
            )

            return

        exact_required_amount = (
            required_crypto_decimal(
                ticket
            )
        )

        if (
            ticket[
                "type"
            ] == "ltc"
            and parsed_amount
            != exact_required_amount
        ):
            await interaction.response.send_message(
                (
                    "The LTC amount must exactly match the deal "
                    f"amount of "
                    f"{crypto_amount_text(ticket, exact_required_amount)} "
                    "LTC."
                ),
                ephemeral=True
            )

            return

        if not ticket.get(
            "manual_reference"
        ):
            ticket[
                "manual_reference"
            ] = secrets.token_hex(
                32
            )

            first_manual_reference = True

        ticket[
            "deposit_txid"
        ] = ticket[
            "manual_reference"
        ]

        ticket[
            "deposit_amount"
        ] = str(
            exact_required_amount
            if ticket[
                "type"
            ] == "ltc"
            else parsed_amount
        )

        ticket[
            "deposit_confirmations"
        ] = int(
            confirmation
        )

        ticket[
            "manual_deposit_override"
        ] = True

        ticket[
            "status"
        ] = "deposit_unconfirmed"

        await save_data()

    previous_detected = await fetch_message(
        channel,
        ticket[
            "messages"
        ].get(
            "deposit_detected"
        )
    )

    if (
        previous_detected is not None
        and not first_manual_reference
    ):
        try:
            await previous_detected.edit(
                embed=transaction_detected_embed(
                    ticket
                )
            )

        except discord.HTTPException:
            previous_detected = None

    if (
        previous_detected is None
        or first_manual_reference
    ):
        detected_message = await channel.send(
            embed=transaction_detected_embed(
                ticket
            )
        )

        ticket[
            "messages"
        ][
            "deposit_detected"
        ] = detected_message.id

        await save_data()

    log_action(
        "manual_deposit_marked",
        actor=(
            f"{interaction.user}"
            f"({interaction.user.id})"
        ),
        ticket=ticket.get(
            "number"
        ),
        asset=get_asset_name(
            ticket
        ),
        amount=crypto_amount_text(
            ticket,
            ticket.get(
                "deposit_amount"
            )
            or "0"
        ),
        confirmations=int(
            confirmation
        ),
        txid=ticket.get(
            "manual_reference"
        )
    )

    await interaction.response.send_message(
        "Deposit embed shown.",
        ephemeral=True
    )

    if (
        Decimal(
            str(
                ticket.get(
                    "deposit_amount"
                )
                or "0"
            )
        )
        >= required_crypto_decimal(
            ticket
        )
        and int(
            confirmation
        )
        >= confirmations_required(
            ticket
        )
    ):
        await handle_deposit_confirmed(
            ticket
        )

    else:
        ensure_monitor(
            ticket
        )


@bot.tree.command(
    name="settle",
    description=(
        "Verify and record a completed payout"
    )
)
@app_commands.guild_only()
@app_commands.describe(
    ticket_number="The ticket number",
    payout_txid="The blockchain payout transaction ID",
    payout_amount="Amount sent to the receiver"
)
async def settle(
    interaction: discord.Interaction,
    ticket_number: int,
    payout_txid: str,
    payout_amount: str
):
    if not is_staff_command_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    ticket = get_ticket_by_number(
        ticket_number
    )

    if ticket is None:
        await interaction.response.send_message(
            "Ticket not found.",
            ephemeral=True
        )

        return

    if ticket.get(
        "status"
    ) != "settlement_pending":
        await interaction.response.send_message(
            "That ticket is not waiting for settlement.",
            ephemeral=True
        )

        return

    amount = parse_positive_decimal(
        payout_amount
    )

    if amount is None:
        await interaction.response.send_message(
            "Enter a valid positive payout amount.",
            ephemeral=True
        )

        return

    if not ticket.get(
        "receiver_address"
    ):
        await interaction.response.send_message(
            "The receiver has not confirmed a payout address.",
            ephemeral=True
        )

        return

    minimum_payout = Decimal(
        str(
            ticket.get(
                "deposit_amount"
            )
            or "0"
        )
    )

    if amount < minimum_payout:
        await interaction.response.send_message(
            (
                "The payout amount cannot be below the escrowed "
                f"amount of "
                f"{crypto_amount_text(ticket, minimum_payout)} "
                f"{get_asset_name(ticket)}."
            ),
            ephemeral=True
        )

        return

    log_action(
        "settlement_verification_started",
        admin=(
            f"{interaction.user}"
            f"({interaction.user.id})"
        ),
        ticket=ticket.get(
            "number"
        ),
        asset=get_asset_name(
            ticket
        ),
        requested_amount=crypto_amount_text(
            ticket,
            amount
        ),
        txid=short_txid(
            payout_txid.strip()
        )
    )

    await interaction.response.defer(
        ephemeral=True,
        thinking=True
    )

    verified, actual_amount, confirmations, error = (
        await verify_payout(
            ticket,
            payout_txid.strip(),
            amount
        )
    )

    if not verified:
        log_security(
            "settlement_verification_failed",
            ticket=ticket.get(
                "number"
            ),
            txid=short_txid(
                payout_txid.strip()
            ),
            confirmations=confirmations,
            error=error
        )

        await interaction.followup.send(
            (
                f"Settlement verification failed: {error}\n"
                f"Confirmations detected: {confirmations}"
            ),
            ephemeral=True
        )

        return

    await finalize_withdrawal(
        ticket,
        payout_txid.strip(),
        actual_amount,
        simulation=False
    )

    log_action(
        "settlement_verified",
        admin=(
            f"{interaction.user}"
            f"({interaction.user.id})"
        ),
        ticket=ticket.get(
            "number"
        ),
        asset=get_asset_name(
            ticket
        ),
        amount=crypto_amount_text(
            ticket,
            actual_amount
        ),
        txid=short_txid(
            payout_txid.strip()
        )
    )

    await interaction.followup.send(
        (
            "Settlement verified and recorded. "
            f"Confirmed payout amount: "
            f"{crypto_amount_text(ticket, actual_amount)} "
            f"{get_asset_name(ticket)}."
        ),
        ephemeral=True
    )



async def reply_missing_jaces_admin(interaction):
    await interaction.response.send_message(
        "You do not have permission to use this command.",
        ephemeral=True
    )


async def save_marked_channel(guild, channel, list_key, other_key):
    ok, error = saveable_guild_channel(channel)
    if not ok:
        return False, error, None, None

    async with JACES_LOCK:
        state = jaces_guild_state(guild.id)
        mark_channel_list(
            state,
            list_key,
            other_key,
            channel.id
        )
        mode = guild_mode(state)
        await save_data()

        visible = (
            (mode == "jaces" and list_key == "show_channel_ids")
            or (mode == "normal" and list_key == "normal_channel_ids")
            or (mode == "halal" and list_key == "halal_channel_ids")
        )
        reason = {
            "jaces": JACES_REASON_ON,
            "halal": JACES_REASON_HALAL
        }.get(mode, JACES_REASON_OFF)
        perm_result = await apply_everyone_view(
            channel,
            visible,
            reason
        )

    return True, None, visible, perm_result


def view_update_text(visible, perm_result):
    visibility = (
        "Hidden from @everyone"
        if not visible
        else "Shown to @everyone"
    )
    extra = ""
    if perm_result and str(perm_result).startswith("error:"):
        extra = (
            "\nView Channel could not be updated: "
            f"{str(perm_result)[6:]}"
        )

    return (
        f"{visibility} (`View Channel` only). "
        "Every other permission is unchanged."
        f"{extra}"
    )


def savejaces_embed(channel, visible, perm_result):
    return discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"Saved {channel.mention} for `/jaces`.\n"
            f"{view_update_text(visible, perm_result)}\n"
            "`/jaces` shows it. `/nonjaces` hides it."
        ),
        colour=COLOR_SUCCESS
    )


def savenormall_embed(channel, visible, perm_result):
    return discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"Saved {channel.mention} for `/nonjaces`.\n"
            f"{view_update_text(visible, perm_result)}\n"
            "`/nonjaces` shows it. `/jaces` hides it."
        ),
        colour=COLOR_SUCCESS
    )


def savehalal_embed(channel, visible, perm_result):
    return discord.Embed(
        description=(
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"Saved {channel.mention} for `/halal`.\n"
            f"{view_update_text(visible, perm_result)}\n"
            "`/halal` shows it. `/jaces` and `/nonjaces` hide it."
        ),
        colour=COLOR_SUCCESS
    )


def format_saved_channel_lines(guild, channel_ids):
    if not channel_ids:
        return ["None"]

    lines = []
    for channel_id in channel_ids:
        channel = guild.get_channel(channel_id)
        if channel is None:
            lines.append(f"- `{channel_id}` (deleted)")
        else:
            lines.append(f"- {channel.mention}")

    if len(lines) > 40:
        extra = len(lines) - 40
        lines = lines[:40]
        lines.append(f"- …and {extra} more")

    return lines


def assigned_channels_embed(guild):
    state = jaces_guild_state(guild.id)
    mode = guild_mode(state).title()
    jaces_lines = format_saved_channel_lines(
        guild,
        jaces_show_ids(state)
    )
    normal_lines = format_saved_channel_lines(
        guild,
        jaces_normal_ids(state)
    )
    halal_lines = format_saved_channel_lines(
        guild,
        jaces_halal_ids(state)
    )

    embed = discord.Embed(
        title="Saved channels",
        colour=COLOR_NEUTRAL
    )
    embed.add_field(
        name="!savejaces  ·  shown by /jaces",
        value="\n".join(jaces_lines)[:1024],
        inline=False
    )
    embed.add_field(
        name="!savenormall  ·  shown by /nonjaces",
        value="\n".join(normal_lines)[:1024],
        inline=False
    )
    embed.add_field(
        name="!savehalal  ·  shown by /halal",
        value="\n".join(halal_lines)[:1024],
        inline=False
    )
    embed.set_footer(
        text=f"Current mode: {mode}  ·  View Channel only"
    )
    return embed


@bot.tree.command(
    name="jaces",
    description="Show saved Jaces channels and hide saved normal channels"
)
@app_commands.guild_only()
async def jaces_command(
    interaction: discord.Interaction
):
    if not is_staff_command_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    async with JACES_LOCK:
        embed = await execute_jaces_mode(interaction.guild)

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(
    name="nonjaces",
    description="Show saved normal channels and hide saved Jaces channels"
)
@app_commands.guild_only()
async def nonjaces_command(
    interaction: discord.Interaction
):
    if not is_staff_command_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    async with JACES_LOCK:
        embed = await execute_nonjaces_mode(interaction.guild)

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(
    name="halal",
    description="Show saved Halal channels and hide saved Jaces and normal channels"
)
@app_commands.guild_only()
async def halal_command(
    interaction: discord.Interaction
):
    if not is_staff_command_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    async with JACES_LOCK:
        embed = await execute_halal_mode(interaction.guild)

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(
    name="savejaces",
    description="Mark this channel to show during /jaces"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def savejaces_slash(
    interaction: discord.Interaction
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    ok, error, visible, perm_result = await save_marked_channel(
        interaction.guild,
        interaction.channel,
        "show_channel_ids",
        "normal_channel_ids"
    )
    if not ok:
        await interaction.response.send_message(error, ephemeral=True)
        return

    log_action(
        "jaces_channel_saved",
        user=f"{interaction.user}({interaction.user.id})",
        channel=f"{interaction.channel}({interaction.channel.id})"
    )

    await interaction.response.send_message(
        embed=savejaces_embed(
            interaction.channel,
            visible,
            perm_result
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="savenormall",
    description="Mark this channel to show during /nonjaces"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def savenormall_slash(
    interaction: discord.Interaction
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    ok, error, visible, perm_result = await save_marked_channel(
        interaction.guild,
        interaction.channel,
        "normal_channel_ids",
        "show_channel_ids"
    )
    if not ok:
        await interaction.response.send_message(error, ephemeral=True)
        return

    log_action(
        "jaces_normal_channel_saved",
        user=f"{interaction.user}({interaction.user.id})",
        channel=f"{interaction.channel}({interaction.channel.id})"
    )

    await interaction.response.send_message(
        embed=savenormall_embed(
            interaction.channel,
            visible,
            perm_result
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="savehalal",
    description="Mark this channel to show during /halal"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def savehalal_slash(
    interaction: discord.Interaction
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    ok, error, visible, perm_result = await save_marked_channel(
        interaction.guild,
        interaction.channel,
        "halal_channel_ids",
        ["show_channel_ids", "normal_channel_ids"]
    )
    if not ok:
        await interaction.response.send_message(error, ephemeral=True)
        return

    log_action(
        "halal_channel_saved",
        user=f"{interaction.user}({interaction.user.id})",
        channel=f"{interaction.channel}({interaction.channel.id})"
    )

    await interaction.response.send_message(
        embed=savehalal_embed(
            interaction.channel,
            visible,
            perm_result
        ),
        ephemeral=True
    )


@bot.command(name="jaces")
@commands.guild_only()
async def jaces_prefix(ctx):
    if not is_staff_command_user(ctx.author):
        return

    async with JACES_LOCK:
        embed = await execute_jaces_mode(ctx.guild)

    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="nonjaces")
@commands.guild_only()
async def nonjaces_prefix(ctx):
    if not is_staff_command_user(ctx.author):
        return

    async with JACES_LOCK:
        embed = await execute_nonjaces_mode(ctx.guild)

    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="halal")
@commands.guild_only()
async def halal_prefix(ctx):
    if not is_staff_command_user(ctx.author):
        return

    async with JACES_LOCK:
        embed = await execute_halal_mode(ctx.guild)

    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="sync")
@commands.guild_only()
async def sync_prefix(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    names = await sync_slash_commands(ctx.guild)
    listed = ", ".join(f"`/{name}`" for name in names) or "none"
    await ctx.reply(
        f"Slash commands are now registered in this server: {listed}",
        mention_author=False
    )


@bot.command(name="savejaces")
@commands.guild_only()
async def savejaces(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    ok, error, visible, perm_result = await save_marked_channel(
        ctx.guild,
        ctx.channel,
        "show_channel_ids",
        "normal_channel_ids"
    )
    if not ok:
        await ctx.reply(error, mention_author=False)
        return

    log_action(
        "jaces_channel_saved",
        user=f"{ctx.author}({ctx.author.id})",
        channel=f"{ctx.channel}({ctx.channel.id})"
    )

    await ctx.reply(
        embed=savejaces_embed(
            ctx.channel,
            visible,
            perm_result
        ),
        mention_author=False
    )


@bot.command(name="savenormall", aliases=["savenormal"])
@commands.guild_only()
async def savenormall(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    ok, error, visible, perm_result = await save_marked_channel(
        ctx.guild,
        ctx.channel,
        "normal_channel_ids",
        "show_channel_ids"
    )
    if not ok:
        await ctx.reply(error, mention_author=False)
        return

    log_action(
        "jaces_normal_channel_saved",
        user=f"{ctx.author}({ctx.author.id})",
        channel=f"{ctx.channel}({ctx.channel.id})"
    )

    await ctx.reply(
        embed=savenormall_embed(
            ctx.channel,
            visible,
            perm_result
        ),
        mention_author=False
    )


@bot.command(name="savehalal")
@commands.guild_only()
async def savehalal(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    ok, error, visible, perm_result = await save_marked_channel(
        ctx.guild,
        ctx.channel,
        "halal_channel_ids",
        ["show_channel_ids", "normal_channel_ids"]
    )
    if not ok:
        await ctx.reply(error, mention_author=False)
        return

    log_action(
        "halal_channel_saved",
        user=f"{ctx.author}({ctx.author.id})",
        channel=f"{ctx.channel}({ctx.channel.id})"
    )

    await ctx.reply(
        embed=savehalal_embed(
            ctx.channel,
            visible,
            perm_result
        ),
        mention_author=False
    )


@bot.command(name="show")
@commands.guild_only()
async def show_saved_channels(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    await ctx.reply(
        embed=assigned_channels_embed(ctx.guild),
        mention_author=False
    )


@bot.tree.command(
    name="show",
    description="List channels saved for /jaces, /nonjaces, and /halal"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def show_saved_channels_slash(
    interaction: discord.Interaction
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    await interaction.response.send_message(
        embed=assigned_channels_embed(interaction.guild),
        ephemeral=True
    )



@bot.command(name="autommtos")
@commands.guild_only()
async def autommtos(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    await ctx.channel.send(
        content=automm_tos_notice_text(),
        view=AutoMMTosView()
    )

    log_action(
        "automm_tos_posted",
        user=f"{ctx.author}({ctx.author.id})",
        channel=f"{ctx.channel}({ctx.channel.id})"
    )


@bot.tree.command(
    name="autommtos",
    description="Post the Automatic MM ToS notice with a View ToS button"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def autommtos_slash(
    interaction: discord.Interaction
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    if interaction.channel is None:
        await interaction.response.send_message(
            "Use this in a server channel.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "ToS notice posted.",
        ephemeral=True
    )

    try:
        await interaction.channel.send(
            content=automm_tos_notice_text(),
            view=AutoMMTosView()
        )
    except discord.HTTPException:
        await interaction.followup.send(
            "The ToS notice could not be posted in this channel.",
            ephemeral=True
        )
        return

    log_action(
        "automm_tos_posted",
        user=f"{interaction.user}({interaction.user.id})",
        channel=f"{interaction.channel}({interaction.channel.id})"
    )


@bot.tree.command(
    name="set_role",
    description="Set a rank role and the USD total needed to reach it"
)
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    role="Role given when the user reaches this USD total",
    amount="USD total required to reach this role"
)
async def set_role_slash(
    interaction: discord.Interaction,
    role: discord.Role,
    amount: str
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    parsed = parse_money_amount(amount, allow_zero=True)
    if parsed is None:
        await interaction.response.send_message(
            "Enter a valid USD amount.",
            ephemeral=True
        )
        return

    if role.is_default() or role.managed:
        await interaction.response.send_message(
            "That role cannot be used as a rank.",
            ephemeral=True
        )
        return

    roles = [
        item for item in rank_roles()
        if int(item["role_id"]) != role.id
    ]
    roles.append({
        "role_id": str(role.id),
        "amount": str(parsed)
    })
    roles.sort(key=lambda item: Decimal(item["amount"]))
    DATA["rank_roles"] = roles
    await save_data()

    await interaction.response.defer(ephemeral=True, thinking=True)
    notes = await sync_all_rank_roles(interaction.guild)

    log_action(
        "rank_role_set",
        user=f"{interaction.user}({interaction.user.id})",
        role=f"{role}({role.id})",
        amount=money_compact(parsed)
    )

    extra = ""
    if notes:
        extra = "\n" + "\n".join(f"- {note}" for note in notes[:12])

    await interaction.followup.send(
        (
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"{role.mention} is now reached at "
            f"**{money_compact(parsed)}**."
            f"{extra}"
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="set_biggest_deal",
    description="Set a user's biggest deal amount"
)
@app_commands.guild_only()
@app_commands.describe(
    user="The user to update",
    amount="Biggest deal USD amount"
)
async def set_biggest_deal_slash(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: str
):
    if not is_staff_command_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    parsed = parse_money_amount(amount, allow_zero=True)
    if parsed is None:
        await interaction.response.send_message(
            "Enter a valid USD amount.",
            ephemeral=True
        )
        return

    stats = get_user_stats(user.id)
    stats["biggest_deal"] = str(parsed)
    await save_data()

    log_action(
        "stats_biggest_deal_set",
        admin=f"{interaction.user}({interaction.user.id})",
        target=f"{user}({user.id})",
        amount=money(parsed)
    )

    await interaction.response.send_message(
        (
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"Biggest deal for {user.mention} is now "
            f"**{money(parsed)}**."
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="set_totalvalue",
    description="Set a user's total USD value"
)
@app_commands.guild_only()
@app_commands.describe(
    user="The user to update",
    amount="Total USD value"
)
async def set_totalvalue_slash(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: str
):
    if not is_staff_command_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    parsed = parse_money_amount(amount, allow_zero=True)
    if parsed is None:
        await interaction.response.send_message(
            "Enter a valid USD amount.",
            ephemeral=True
        )
        return

    stats = get_user_stats(user.id)
    stats["total_usd_value"] = str(parsed)
    await save_data()

    await interaction.response.defer(ephemeral=True, thinking=True)
    notes = await sync_rank_roles(interaction.guild, user.id)

    log_action(
        "stats_total_value_set",
        admin=f"{interaction.user}({interaction.user.id})",
        target=f"{user}({user.id})",
        amount=money(parsed)
    )

    extra = ""
    if notes:
        extra = "\n" + "\n".join(f"- {note}" for note in notes)

    await interaction.followup.send(
        (
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"Total USD value for {user.mention} is now "
            f"**{money(parsed)}**."
            f"{extra}"
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="set_totaldeals",
    description="Set a user's completed deal count"
)
@app_commands.guild_only()
@app_commands.describe(
    user="The user to update",
    amount="Number of completed deals"
)
async def set_totaldeals_slash(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: str
):
    if not is_staff_command_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    parsed = parse_non_negative_int(amount)
    if parsed is None:
        await interaction.response.send_message(
            "Enter a valid deal count.",
            ephemeral=True
        )
        return

    stats = get_user_stats(user.id)
    stats["deals_completed"] = parsed
    await save_data()

    log_action(
        "stats_total_deals_set",
        admin=f"{interaction.user}({interaction.user.id})",
        target=f"{user}({user.id})",
        amount=parsed
    )

    await interaction.response.send_message(
        (
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"Deals completed for {user.mention} is now "
            f"**{parsed}**."
        ),
        ephemeral=True
    )


@bot.tree.command(
    name="show_roles",
    description="Show rank roles and the USD total needed to reach them"
)
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def show_roles_slash(
    interaction: discord.Interaction
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    roles = rank_roles()
    if not roles:
        await interaction.response.send_message(
            "No rank roles have been set.",
            ephemeral=True
        )
        return

    lines = []
    for item in roles:
        role_id = int(item["role_id"])
        role = interaction.guild.get_role(role_id)
        mention = role.mention if role is not None else f"`{role_id}`"
        lines.append(
            f"{mention} — **{money_compact(item['amount'])}**"
        )

    embed = discord.Embed(
        title="Rank roles",
        description="\n".join(lines),
        colour=COLOR_NEUTRAL
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


set_group = app_commands.Group(
    name="set",
    description="Configure the bot",
    default_permissions=discord.Permissions(
        administrator=True
    )
)


@set_group.command(
    name="activity",
    description="Set the bot's Discord activity"
)
@app_commands.guild_only()
@app_commands.describe(
    text="Activity text shown on the bot. Use a dash (-) to clear it.",
    type="Activity type",
    status="Online status"
)
@app_commands.choices(
    type=[
        app_commands.Choice(
            name="Playing",
            value="playing"
        ),
        app_commands.Choice(
            name="Watching",
            value="watching"
        ),
        app_commands.Choice(
            name="Listening",
            value="listening"
        ),
        app_commands.Choice(
            name="Competing",
            value="competing"
        ),
        app_commands.Choice(
            name="Custom",
            value="custom"
        )
    ],
    status=[
        app_commands.Choice(
            name="Online",
            value="online"
        ),
        app_commands.Choice(
            name="Idle",
            value="idle"
        ),
        app_commands.Choice(
            name="Do Not Disturb",
            value="dnd"
        ),
        app_commands.Choice(
            name="Invisible",
            value="invisible"
        )
    ]
)
async def set_activity_slash(
    interaction: discord.Interaction,
    text: str,
    type: app_commands.Choice[str] = None,
    status: app_commands.Choice[str] = None
):
    if not is_jaces_admin_user(interaction.user):
        await reply_missing_jaces_admin(interaction)
        return

    cleaned = str(text or "").strip()[:128]
    if cleaned.lower() in {"-", "clear", "none", "off"}:
        cleaned = ""

    activity_type = (
        type.value
        if type is not None
        else "playing"
    )
    status_value = (
        status.value
        if status is not None
        else "online"
    )

    state = presence_state()
    state["type"] = activity_type
    state["text"] = cleaned
    state["status"] = status_value
    await save_data()

    try:
        await apply_bot_presence()
    except discord.HTTPException:
        logger.exception("Failed to set bot activity")
        await interaction.response.send_message(
            "Discord rejected the activity update.",
            ephemeral=True
        )
        return

    label = presence_label(state)
    log_action(
        "bot_activity_set",
        user=f"{interaction.user}({interaction.user.id})",
        activity=label,
        status=status_value
    )

    if cleaned:
        message = (
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            f"Activity set to **{label}**."
        )
    else:
        message = (
            f"{emoji_text(GREEN_TICK_EMOJI)}"
            "Bot activity cleared."
        )

    await interaction.response.send_message(
        message,
        ephemeral=True
    )


bot.tree.add_command(set_group)


@bot.tree.error
async def app_command_error(
    interaction,
    error
):
    if isinstance(
        error,
        app_commands.MissingPermissions
    ):
        message = (
            "You do not have permission to use this command."
        )

    elif isinstance(
        error,
        app_commands.NoPrivateMessage
    ):
        message = (
            "This command can only be used inside a server."
        )

    else:
        logger.error(
            "Unhandled application command error | "
            "user=%s(%s) | command=%s\n%s",
            interaction.user,
            interaction.user.id,
            getattr(
                interaction.command,
                "qualified_name",
                "unknown"
            ),
            "".join(
                traceback.format_exception(
                    type(error),
                    error,
                    error.__traceback__
                )
            )
        )

        message = (
            "An unexpected error occurred while processing the command."
        )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                message,
                ephemeral=True
            )

        else:
            await interaction.response.send_message(
                message,
                ephemeral=True
            )

    except discord.HTTPException:
        pass


def validate_config():
    errors = []

    if not TOKEN.strip():
        errors.append(
            "TOKEN"
        )

    required_ids = {
        "YOUR_USER": YOUR_USER,
        "TOS_CHANNEL": TOS_CHANNEL,
        "MM_TOS_CHANNEL": MM_TOS_CHANNEL,
        "TICKET_CATEGORY": TICKET_CATEGORY,
        "TRANSCRIPT_CHANNEL": TRANSCRIPT_CHANNEL,
        "COMPLETED_TRANSACTION_CHANNEL": COMPLETED_TRANSACTION_CHANNEL,
        "SETTLEMENT_CHANNEL": SETTLEMENT_CHANNEL
    }

    if DEMO_ACTIVITY_ENABLED:
        required_ids[
            "DEMO_COMPLETED_TRANSACTION_CHANNEL"
        ] = DEMO_COMPLETED_TRANSACTION_CHANNEL

    for name, value in required_ids.items():
        if (
            not isinstance(
                value,
                int
            )
            or value <= 0
        ):
            errors.append(
                name
            )

    if (
        not LTC_DEPOSIT_ADDRESS
        or len(
            LTC_DEPOSIT_ADDRESS
        )
        < 10
    ):
        errors.append(
            "LTC_DEPOSIT_ADDRESS"
        )

    if not re.fullmatch(
        r"0x[a-fA-F0-9]{40}",
        USDT_DEPOSIT_ADDRESS
    ):
        errors.append(
            "USDT_DEPOSIT_ADDRESS"
        )

    if not re.fullmatch(
        r"0x[a-fA-F0-9]{40}",
        USDT_BEP20_CONTRACT
    ):
        errors.append(
            "USDT_BEP20_CONTRACT"
        )

    if (
        AUTO_MONITOR_USDT
        and not ticket_etherscan_key()
    ):
        errors.append(
            "TICKET_ETHERSCAN_API_KEY or ETHERSCAN_API_KEY"
        )

    if SETTLEMENT_MODE.lower() not in {
        "manual",
        "simulation"
    }:
        errors.append(
            "SETTLEMENT_MODE"
        )

    if DEMO_ACTIVITY_ENABLED:
        if (
            DEMO_COMPLETED_TRANSACTION_CHANNEL
            == COMPLETED_TRANSACTION_CHANNEL
        ):
            errors.append(
                "DEMO_COMPLETED_TRANSACTION_CHANNEL "
                "must differ from COMPLETED_TRANSACTION_CHANNEL"
            )

        if (
            DEMO_BASE_INTERVAL_SECONDS
            < 60
        ):
            errors.append(
                "DEMO_BASE_INTERVAL_SECONDS"
            )

        if (
            DEMO_JITTER_MIN_SECONDS
            < 0
            or DEMO_JITTER_MAX_SECONDS
            < DEMO_JITTER_MIN_SECONDS
        ):
            errors.append(
                "DEMO_JITTER_MIN_SECONDS/"
                "DEMO_JITTER_MAX_SECONDS"
            )

        if (
            DEMO_MIN_CONFIRMATIONS
            < 1
        ):
            errors.append(
                "DEMO_MIN_CONFIRMATIONS"
            )

    if discord.version_info < (
        2,
        6,
        0
    ):
        errors.append(
            "discord.py >= 2.6"
        )

    if errors:
        raise RuntimeError(
            "Configure the following values before starting the bot: "
            + ", ".join(
                errors
            )
        )


validate_config()

bot.run(
    TOKEN
)
