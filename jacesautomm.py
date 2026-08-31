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
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from pathlib import Path

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from colorama import Fore, Style, init as colorama_init


TOKEN = "MTU0MzY0MTI3ODQ5ODIxODE2NA.G6WRHu.Vp9ZvOW4ZNSe0RsFBqJ99f5Pw5_OnBZAqt3N3M" # Get from Discord Developer Portal
YOUR_USER = 1506688372045910227 # Your User ID
TOS_CHANNEL = 1543637559463256214 # Middleman ToS Channel ID
MM_TOS_CHANNEL = 1543637611070095421 # Auto Middleman ToS Channel ID
AUTOMM_TRADE_CHANNEL = 1480211838317629541 # Channel linked in !autommtos ("start a trade here")
TICKET_CATEGORY = 1543637510264061992 # Auto Middleman Tickets Category ID
TRANSCRIPT_CHANNEL = 1543639036017508372 # Auto Middleman Tickets Logging Channel ID
COMPLETED_TRANSACTION_CHANNEL = 1543639026605625354 # Completed Auto Middleman Embeds Channel ID
SETTLEMENT_CHANNEL = 1543639018879713372
DEMO_COMPLETED_TRANSACTION_CHANNEL = 1543637640459325551 # Must be different from COMPLETED_TRANSACTION_CHANNEL
TUTORIAL_URL = "https://www.youtube.com/watch?v=XIkpcT2WNPI" # For Tutorial Button in Panel

LTC_DEPOSIT_ADDRESS = "LduBxCtH1jTrhmccGvZExDQHmhWB9r2d9D" # Your Litecoin Address
USDT_DEPOSIT_ADDRESS = "0x4675Bf0637fFd33A32419C0fDcD7b677A6ca146e" # Your USDT Address

BLOCKCYPHER_TOKEN = "692da515d0ed4d4e9fd6352efcbe727b" # Get from https://www.blockcypher.com/apis.html
ETHERSCAN_API_KEY = "5M7Q4T5GX35IUUJ49HSC71JUUAD2F726E1" # Get from https://etherscan.io/api

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
DEMO_BASE_INTERVAL_SECONDS = 420
DEMO_JITTER_MIN_SECONDS = 60
DEMO_JITTER_MAX_SECONDS = 180
DEMO_MIN_CONFIRMATIONS = 6
DEMO_RECENT_BLOCK_WINDOW = 500

STARTING_TICKET_NUMBER = 12077

BIGGEST_TRADE_USD = 29996 # Biggest completed trade amount shown on the panel footer
BIGGEST_TRADE_MESSAGE_URL = "" # Message link to the biggest completed trade (e.g. https://discord.com/channels/guild/channel/message)

# ===== Jaces mode =====
# Put image files next to this script or inside jaces_assets/. Leave "" to skip that field.
# Example: JACES_SERVER_ICON = "jaces_server_icon.png"

JACES_SERVER_NAME = ""
JACES_SERVER_DESCRIPTION = ""
JACES_SERVER_ICON = ""
JACES_SERVER_BANNER = ""
JACES_BOT_NAME = ""
JACES_BOT_AVATAR = ""
JACES_BOT_BANNER = ""
JACES_BOT_ROLE_NAME = ""

NORMAL_SERVER_NAME = ""
NORMAL_SERVER_DESCRIPTION = ""
NORMAL_SERVER_ICON = ""
NORMAL_SERVER_BANNER = ""
NORMAL_BOT_NAME = ""
NORMAL_BOT_AVATAR = ""
NORMAL_BOT_BANNER = ""
NORMAL_BOT_ROLE_NAME = ""


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
JACES_RATE_WAIT_UNTIL = 0.0

TICKET_LOCKS = {}
MONITOR_TASKS = {}
COUNTDOWN_TASKS = {}

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


def default_data():
    return {
        "next_ticket_number": STARTING_TICKET_NUMBER,
        "tickets": {},
        "stats": {},
        "privacy": {},
        "claimed_deposit_txids": {},
        "jaces": {
            "guilds": {}
        }
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


def crypto_amount_text(
    ticket,
    value=None
):
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
    if asset == "ltc":
        return (
            "https://live.blockcypher.com/"
            f"ltc/tx/{txid}/"
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


async def http_get_json(
    url,
    params=None,
    headers=None,
    attempts=3,
    timeout=15
):
    last_error = None

    for attempt in range(
        attempts
    ):
        try:
            async with bot.session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(
                    total=timeout
                )
            ) as response:

                if response.status == 200:
                    return await response.json()

                body = await response.text()

                last_error = RuntimeError(
                    f"HTTP {response.status}: "
                    f"{body[:300]}"
                )

        except Exception as error:
            last_error = error

        if attempt + 1 < attempts:
            await asyncio.sleep(
                1.5
                * (
                    attempt + 1
                )
            )

    if last_error:
        logger.warning(
            "HTTP request failed for %s: %s",
            url,
            last_error
        )

    return None


async def fetch_ltc_chain_overview():
    url = (
        "https://api.blockcypher.com/"
        "v1/ltc/main"
    )

    params = {}

    if BLOCKCYPHER_TOKEN:
        params[
            "token"
        ] = BLOCKCYPHER_TOKEN

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

    if BLOCKCYPHER_TOKEN:
        params[
            "token"
        ] = BLOCKCYPHER_TOKEN

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
                txid
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


async def send_demo_completed_activity():
    if not DEMO_ACTIVITY_ENABLED:
        return False

    channel = bot.get_channel(
        DEMO_COMPLETED_TRANSACTION_CHANNEL
    )

    if channel is None:
        try:
            channel = await bot.fetch_channel(
                DEMO_COMPLETED_TRANSACTION_CHANNEL
            )

        except discord.HTTPException as exc:
            logger.error(
                "Demo activity channel lookup failed | "
                "channel_id=%s | error=%s",
                DEMO_COMPLETED_TRANSACTION_CHANNEL,
                exc
            )

            return False

    if not hasattr(
        channel,
        "send"
    ):
        logger.error(
            "Demo activity channel is not messageable | "
            "channel_id=%s",
            DEMO_COMPLETED_TRANSACTION_CHANNEL
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

    embed = demo_completed_embed(
        sample,
        ltc_price
    )

    try:
        await channel.send(
            embed=embed
        )

    except discord.HTTPException as exc:
        logger.error(
            "Demo activity send failed | "
            "channel_id=%s | error=%s",
            DEMO_COMPLETED_TRANSACTION_CHANNEL,
            exc
        )

        return False

    log_action(
        "demo_completed_activity_sent",
        channel_id=DEMO_COMPLETED_TRANSACTION_CHANNEL,
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


async def fetch_ltc_transactions(address):
    url = (
        "https://api.blockcypher.com/"
        f"v1/ltc/main/addrs/{address}/full"
    )

    params = {
        "limit": 50
    }

    if BLOCKCYPHER_TOKEN:
        params[
            "token"
        ] = BLOCKCYPHER_TOKEN

    data = await http_get_json(
        url,
        params=params
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


async def fetch_ltc_transaction(txid):
    url = (
        "https://api.blockcypher.com/"
        f"v1/ltc/main/txs/{txid}"
    )

    params = {}

    if BLOCKCYPHER_TOKEN:
        params[
            "token"
        ] = BLOCKCYPHER_TOKEN

    return await http_get_json(
        url,
        params=params
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


async def fetch_usdt_transfers(address):
    if not ETHERSCAN_API_KEY:
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
        "apikey": ETHERSCAN_API_KEY
    }

    data = await http_get_json(
        url,
        params=params
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


async def create_baseline(ticket):
    if ticket[
        "type"
    ] == "ltc":

        if not AUTO_MONITOR_LTC:
            ticket[
                "baseline_txids"
            ] = []

            return True

        txs = await fetch_ltc_transactions(
            ticket[
                "deposit_address"
            ]
        )

        if txs is None:
            return False

        ticket[
            "baseline_txids"
        ] = [
            normalize_txid(
                tx.get(
                    "hash"
                )
            )
            for tx in txs
            if tx.get(
                "hash"
            )
        ]

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

    ticket[
        "baseline_txids"
    ] = [
        normalize_txid(
            item.get(
                "hash"
            )
        )
        for item
        in transfers
        if item.get(
            "hash"
        )
    ]

    return True


async def resolve_trader(
    guild,
    value
):
    value = value.strip()

    mention = re.fullmatch(
        r"<@!?(\d+)>",
        value
    )

    if mention:
        user_id = int(
            mention.group(1)
        )

        member = guild.get_member(
            user_id
        )

        if member is not None:
            return member

        try:
            return await guild.fetch_member(
                user_id
            )

        except discord.HTTPException:
            return None

    if value.isdigit():
        user_id = int(
            value
        )

        member = guild.get_member(
            user_id
        )

        if member is not None:
            return member

        try:
            return await guild.fetch_member(
                user_id
            )

        except discord.HTTPException:
            return None

    lowered = (
        value.lower()
        .lstrip("@")
    )

    for member in guild.members:
        if lowered in {
            member.name.lower(),
            member.display_name.lower(),
            str(member).lower()
        }:
            return member

    return None


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


def is_private_thread_parent(
    channel
):
    return (
        isinstance(
            channel,
            discord.TextChannel
        )
        and not isinstance(
            channel,
            discord.Thread
        )
    )


def thread_parent_from(
    channel
):
    if isinstance(
        channel,
        discord.Thread
    ):
        return channel.parent

    return channel


async def prepare_ticket_thread(
    channel
):
    if not isinstance(
        channel,
        discord.Thread
    ):
        return channel

    try:
        edits = {}

        if channel.archived:
            edits["archived"] = False

        if channel.locked:
            edits["locked"] = False

        if edits:
            await channel.edit(
                **edits
            )

    except discord.HTTPException:
        pass

    return channel


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

    return await prepare_ticket_thread(
        channel
    )


async def get_ticket_thread_parent(
    interaction
):
    guild = interaction.guild
    configured = None

    if guild is not None:
        configured = guild.get_channel(
            TICKET_CATEGORY
        )

        if configured is None:
            try:
                configured = await bot.fetch_channel(
                    TICKET_CATEGORY
                )

            except discord.HTTPException:
                configured = None

    if is_private_thread_parent(
        configured
    ):
        return configured

    parent = thread_parent_from(
        interaction.channel
    )

    if is_private_thread_parent(
        parent
    ):
        return parent

    return None


async def ensure_parent_access(
    parent,
    opener,
    trader
):
    for member in (
        opener,
        trader
    ):
        if member is None:
            continue

        permissions = parent.permissions_for(
            member
        )

        if permissions.view_channel:
            continue

        try:
            await parent.set_permissions(
                member,
                view_channel=True,
                read_message_history=True,
                send_messages=False,
                send_messages_in_threads=True,
                create_public_threads=False,
                create_private_threads=False,
                add_reactions=True,
                attach_files=True,
                embed_links=True
            )

        except discord.HTTPException:
            logger.exception(
                "Failed to grant ticket parent access to %s(%s)",
                member,
                member.id
            )


async def create_ticket_thread(
    parent,
    name,
    reason
):
    last_error = None

    for duration in (
        10080,
        4320,
        1440,
        60
    ):
        try:
            return await parent.create_thread(
                name=name,
                type=discord.ChannelType.private_thread,
                invitable=False,
                auto_archive_duration=duration,
                reason=reason
            )

        except discord.HTTPException as error:
            last_error = error

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "Failed to create private ticket thread"
    )


async def delete_thread_join_messages(
    thread
):
    try:
        async for message in thread.history(
            limit=20
        ):
            if message.type is discord.MessageType.recipient_add:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

    except discord.HTTPException:
        logger.exception(
            "Failed to delete thread join messages for %s",
            thread.id
        )


async def add_ticket_thread_members(
    thread,
    opener,
    trader
):
    for member in (
        opener,
        trader
    ):
        if member is None:
            continue

        try:
            await thread.add_user(
                member
            )

        except discord.HTTPException:
            logger.exception(
                "Failed to add %s(%s) to ticket thread %s",
                member,
                member.id,
                thread.id
            )

    await asyncio.sleep(0.5)
    await delete_thread_join_messages(
        thread
    )


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

    baseline_ok = await create_baseline(
        ticket
    )

    if not baseline_ok:
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
                    "**Unable to initialize blockchain monitoring. "
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

    ticket[
        "status"
    ] = "waiting_deposit"

    ticket[
        "payment_started_at"
    ] = int(
        time.time()
    )

    await save_data()

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

    txs = await fetch_ltc_transactions(
        address
    )

    if txs is None:
        return

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
        for tx in txs:
            txid = tx.get(
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
                txid,
                amount,
                confirmations
            )

            return

        return

    baseline = set(
        ticket.get(
            "baseline_txids",
            []
        )
    )

    for tx in txs:
        txid = tx.get(
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
                "deposit_unconfirmed"
            }:
                return

            try:
                if (
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

            if (
                AUTO_CLOSE_UNPAID
                and ticket.get(
                    "status"
                )
                == "waiting_deposit"
            ):
                started = int(
                    ticket.get(
                        "payment_started_at",
                        int(
                            time.time()
                        )
                    )
                )

                if (
                    int(
                        time.time()
                    )
                    - started
                    >= UNPAID_TIMEOUT_SECONDS
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

        if not current.get(
            "stats_recorded"
        ):
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
                stats = DATA[
                    "stats"
                ].setdefault(
                    user_id,
                    {
                        "deals_completed": 0,
                        "total_usd_value": "0.00"
                    }
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
                    + Decimal(
                        str(
                            current[
                                "usd_amount"
                            ]
                        )
                    )
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

    await send_completion_outputs(
        ticket
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

    channel = await prepare_ticket_thread(
        channel
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

        parent = await get_ticket_thread_parent(
            interaction
        )

        if parent is None:
            await interaction.followup.send(
                "Private ticket threads can only be created from a text channel.",
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

        await ensure_parent_access(
            parent,
            opener,
            trader
        )

        try:
            channel = await create_ticket_thread(
                parent,
                channel_name,
                (
                    f"Middleman ticket {number}"
                )
            )

            await add_ticket_thread_members(
                channel,
                opener,
                trader
            )

        except discord.HTTPException:
            logger.exception(
                "Failed to create ticket thread"
            )

            await interaction.followup.send(
                "Discord rejected the ticket creation request. "
                "Check the bot's Create Private Threads and Manage Threads permissions.",
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
                f"{get_channel_mention(TOS_CHANNEL)}"
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
                f"{get_channel_mention(COMPLETED_TRANSACTION_CHANNEL)} "
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
                f"{get_channel_mention(TOS_CHANNEL)}."
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


def default_jaces_guild_state():
    return {
        "active": False,
        "show_channel_ids": [],
        "normal_channel_ids": []
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

    if isinstance(channel, discord.Thread):
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


def mark_channel_list(state, list_key, other_key, channel_id):
    current = unique_snowflakes(state.get(list_key, []), [channel_id])
    other = [
        value
        for value in unique_snowflakes(state.get(other_key, []))
        if value != int(channel_id)
    ]
    state[list_key] = store_id_list(current)
    state[other_key] = store_id_list(other)


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
        "bot_role_name": globals()[f"{prefix}_BOT_ROLE_NAME"]
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
            "bot_role_name"
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


async def execute_jaces_mode(guild):
    state = jaces_guild_state(guild.id)
    ticket_ids = ticket_channel_id_set()
    show_ids = jaces_show_ids(state)
    hide_ids = [
        channel_id
        for channel_id in jaces_normal_ids(state)
        if channel_id not in show_ids
    ]

    jobs = []
    jobs.extend(
        lambda channel_id=channel_id: set_channel_visibility(
            guild,
            channel_id,
            True,
            JACES_REASON_ON,
            ticket_ids
        )
        for channel_id in show_ids
    )
    jobs.extend(
        lambda channel_id=channel_id: set_channel_visibility(
            guild,
            channel_id,
            False,
            JACES_REASON_ON,
            ticket_ids
        )
        for channel_id in hide_ids
    )

    channel_task = asyncio.create_task(run_channel_jobs(jobs))
    branding_task = asyncio.create_task(
        apply_branding_profile(
            guild,
            config_branding("JACES"),
            JACES_REASON_ON
        )
    )

    channel_results, branding_notes = await asyncio.gather(
        channel_task,
        branding_task
    )

    results = summarize_visibility(channel_results)
    state["active"] = True
    await save_data()

    lines = [
        f"{emoji_text(GREEN_TICK_EMOJI)}Shown (!savejaces): **{results['shown']}**",
        f"{emoji_text(LOCK_EMOJI)}Hidden (!savenormall): **{results['hidden']}**"
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
        "jaces_mode_enabled",
        guild=guild.id,
        shown=results["shown"],
        hidden=results["hidden"]
    )

    return jaces_result_embed(
        "Jaces mode on",
        COLOR_SUCCESS,
        lines
    )


async def execute_nonjaces_mode(guild):
    state = jaces_guild_state(guild.id)
    ticket_ids = ticket_channel_id_set()
    show_ids = jaces_normal_ids(state)
    hide_ids = [
        channel_id
        for channel_id in jaces_show_ids(state)
        if channel_id not in show_ids
    ]

    jobs = []
    jobs.extend(
        lambda channel_id=channel_id: set_channel_visibility(
            guild,
            channel_id,
            True,
            JACES_REASON_OFF,
            ticket_ids
        )
        for channel_id in show_ids
    )
    jobs.extend(
        lambda channel_id=channel_id: set_channel_visibility(
            guild,
            channel_id,
            False,
            JACES_REASON_OFF,
            ticket_ids
        )
        for channel_id in hide_ids
    )

    channel_task = asyncio.create_task(run_channel_jobs(jobs))
    branding_task = asyncio.create_task(
        apply_branding_profile(
            guild,
            config_branding("NORMAL"),
            JACES_REASON_OFF
        )
    )

    channel_results, branding_notes = await asyncio.gather(
        channel_task,
        branding_task
    )

    results = summarize_visibility(channel_results)
    state["active"] = False
    await save_data()

    lines = [
        f"{emoji_text(GREEN_TICK_EMOJI)}Shown (!savenormall): **{results['shown']}**",
        f"{emoji_text(LOCK_EMOJI)}Hidden (!savejaces): **{results['hidden']}**"
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
        "jaces_mode_disabled",
        guild=guild.id,
        shown=results["shown"],
        hidden=results["hidden"]
    )

    return jaces_result_embed(
        "Jaces mode off",
        COLOR_NEUTRAL,
        lines
    )


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

    async def close(self):
        for task in list(
            MONITOR_TASKS.values()
        ):
            if not task.done():
                task.cancel()

        for task in list(
            COUNTDOWN_TASKS.values()
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
        status = ticket.get(
            "status"
        )

        if status in {
            "waiting_deposit",
            "deposit_unconfirmed"
        }:
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


@bot.event
async def on_guild_join(guild):
    await sync_slash_commands(guild)


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


@bot.listen("on_message")
async def delete_ticket_join_system_messages(message):
    if message.type is not discord.MessageType.recipient_add:
        return

    if not isinstance(message.channel, discord.Thread):
        return

    if message.guild is None or bot.user is None:
        return

    if message.author.id != bot.user.id:
        return

    try:
        await message.delete()
    except discord.HTTPException:
        pass


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
    user: discord.Member
):
    log_action(
        "stats_viewed",
        requester=(
            f"{interaction.user}"
            f"({interaction.user.id})"
        ),
        target=(
            f"{user}"
            f"({user.id})"
        )
    )

    data = DATA[
        "stats"
    ].get(
        str(
            user.id
        ),
        {
            "deals_completed": 0,
            "total_usd_value": "0.00"
        }
    )

    embed = discord.Embed(
        title=user.name,
        description=(
            "**Deals Completed**\n"
            f"{int(data.get('deals_completed', 0))}"
            "\n\n"
            "**Total USD Value**\n"
            f"{money(data.get('total_usd_value', '0'))}"
        ),
        colour=COLOR_NEUTRAL
    )

    embed.set_thumbnail(
        url=user.display_avatar.url
    )

    await interaction.response.send_message(
        embed=embed
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


@bot.tree.command(
    name="mark-deposit",
    description=(
        "Manually show or confirm a deposit state"
    )
)
@app_commands.guild_only()
@app_commands.describe(
    ticket_number="The ticket number",
    amount="Amount of LTC or USDT received",
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
    if (
        interaction.user.id
        != YOUR_USER
    ):
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
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
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
        active = bool(state.get("active"))
        await save_data()

        visible = (
            active
            if list_key == "show_channel_ids"
            else (not active)
        )
        perm_result = await apply_everyone_view(
            channel,
            visible,
            JACES_REASON_ON if active else JACES_REASON_OFF
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
    mode = "Jaces" if state.get("active") else "Normal"
    jaces_lines = format_saved_channel_lines(
        guild,
        jaces_show_ids(state)
    )
    normal_lines = format_saved_channel_lines(
        guild,
        jaces_normal_ids(state)
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
    embed.set_footer(
        text=f"Current mode: {mode}  ·  View Channel only"
    )
    return embed


@bot.tree.command(
    name="jaces",
    description="Show saved Jaces channels and hide saved normal channels"
)
@app_commands.guild_only()
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def jaces_command(
    interaction: discord.Interaction
):
    if (
        not is_jaces_admin_user(interaction.user)
    ):
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
@app_commands.default_permissions(
    administrator=True
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def nonjaces_command(
    interaction: discord.Interaction
):
    if (
        not is_jaces_admin_user(interaction.user)
    ):
        await reply_missing_jaces_admin(interaction)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    async with JACES_LOCK:
        embed = await execute_nonjaces_mode(interaction.guild)

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


@bot.command(name="jaces")
@commands.guild_only()
async def jaces_prefix(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    async with JACES_LOCK:
        embed = await execute_jaces_mode(ctx.guild)

    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="nonjaces")
@commands.guild_only()
async def nonjaces_prefix(ctx):
    if not is_jaces_admin_user(ctx.author):
        return

    async with JACES_LOCK:
        embed = await execute_nonjaces_mode(ctx.guild)

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
    description="List channels saved for /jaces and /nonjaces"
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
        and not ETHERSCAN_API_KEY.strip()
    ):
        errors.append(
            "ETHERSCAN_API_KEY"
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
