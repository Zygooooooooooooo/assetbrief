import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import plotly.graph_objects as go
import json
import re
import math
from datetime import datetime, timedelta, timezone
from html import escape
from textwrap import dedent
from openai import OpenAI

st.set_page_config(page_title="AssetBrief", layout="wide")

# =========================
# SECRETS
# =========================
ALPHA_VANTAGE_API_KEY = st.secrets["ALPHA_VANTAGE_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MARKETAUX_API_KEY = st.secrets["MARKETAUX_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# GLOBAL STYLE
# =========================
st.markdown("""
<style>
.stApp {
    background: #f3f6fb;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1180px;
}

h1 {
    font-size: 3rem !important;
    font-weight: 850 !important;
    letter-spacing: -0.045em;
    color: #0f172a;
}

h2, h3 {
    color: #0f172a;
    letter-spacing: -0.025em;
}

p, li, label {
    color: #334155;
}

[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

[data-testid="stTextInput"] input {
    border-radius: 16px !important;
    border: 1px solid #d8e0ea !important;
    padding: 0.95rem 1rem !important;
    font-size: 1rem !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.04);
}

[data-testid="stTextInput"] input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

.stButton > button,
[data-testid="stFormSubmitButton"] button {
    border-radius: 14px !important;
    padding: 0.8rem 1.5rem !important;
    font-weight: 750 !important;
    border: none !important;
    background: #2563eb !important;
    color: #ffffff !important;
    transition: all 0.15s ease-in-out !important;
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22) !important;
}

.stButton > button *,
[data-testid="stFormSubmitButton"] button * {
    color: #ffffff !important;
}

.stButton > button p,
[data-testid="stFormSubmitButton"] button p {
    color: #ffffff !important;
}

.stButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    background: #1d4ed8 !important;
    color: #ffffff !important;
    transform: translateY(-1px);
}

.stButton > button:hover *,
[data-testid="stFormSubmitButton"] button:hover * {
    color: #ffffff !important;
}

.stButton > button:active,
[data-testid="stFormSubmitButton"] button:active {
    background: #1e40af !important;
    color: #ffffff !important;
}

[data-testid="stMetric"] {
    background: #ffffff;
    padding: 1.15rem;
    border-radius: 18px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.055);
}

[data-testid="stMetricLabel"] {
    color: #64748b;
    font-weight: 650;
}

[data-testid="stMetricValue"] {
    color: #0f172a;
    font-weight: 850;
}

[data-testid="stPlotlyChart"] {
    background: #ffffff;
    padding: 1rem;
    border-radius: 22px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.055);
}

[data-testid="stSelectbox"] {
    max-width: 280px;
}

.hero-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
    padding: 2rem;
    border-radius: 28px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
    margin-bottom: 1.5rem;
}

.asset-card {
    background: #ffffff;
    padding: 1.6rem;
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
    margin-bottom: 1.5rem;
}

.section-card {
    background: #ffffff;
    padding: 1.5rem;
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.045);
    margin-bottom: 1.5rem;
    overflow: hidden;
}

.small-muted {
    color: #64748b;
    font-size: 0.95rem;
}

hr {
    margin-top: 2rem;
    margin-bottom: 2rem;
}

.choice-card {
    background: #ffffff;
    padding: 1.35rem;
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
    min-height: 155px;
    transition: all 0.18s ease-in-out;
    margin-bottom: 0.9rem;
}

.choice-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
    border-color: #cbd5e1;
}

.choice-ticker {
    font-size: 1.55rem;
    font-weight: 850;
    color: #0f172a;
    letter-spacing: -0.03em;
    margin-bottom: 0.35rem;
}

.choice-name {
    font-size: 1rem;
    line-height: 1.45;
    color: #334155;
    min-height: 34px;
    margin-bottom: 1rem;
}

.choice-meta {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #2563eb;
    background: #dbeafe;
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
}

.tech-signal-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
    padding: 1.6rem;
    border-radius: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
    margin-bottom: 1.5rem;
}

.tech-card {
    background: #ffffff;
    padding: 1.15rem;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.04);
    margin-bottom: 1rem;
    min-height: 128px;
}

.tech-label {
    font-size: 0.82rem;
    color: #64748b;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.45rem;
}

.tech-value {
    font-size: 1.45rem;
    color: #0f172a;
    font-weight: 850;
    letter-spacing: -0.03em;
    margin-bottom: 0.35rem;
}

.tech-note {
    font-size: 0.88rem;
    color: #64748b;
    line-height: 1.35;
}

.signal-pill {
    display: inline-block;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 850;
    letter-spacing: 0.04em;
}
</style>
""", unsafe_allow_html=True)

# =========================
# CONFIG
# =========================
DISPLAY_PERIODS = {
    "1D": 1,
    "7D": 7,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
    "5Y": 365 * 5,
}

DEFAULT_CHART_PERIOD = "1M"

KNOWN_FX_CODES = {
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD",
    "CNY", "CNH", "HKD", "SGD", "SEK", "NOK", "DKK", "MXN",
    "BRL", "ZAR", "TRY", "PLN", "CZK", "HUF", "ILS", "INR",
    "KRW", "TWD", "THB", "MYR", "IDR", "PHP", "RUB", "AED",
    "SAR"
}

# =========================
# HELPERS
# =========================
def render_html(html):
    clean_html = dedent(html).strip()
    st.html(clean_html)


def clean_text(value):
    if value is None:
        return "N/A"
    text = str(value).strip()
    return text if text else "N/A"


def is_missing(value):
    if value is None:
        return True
    if isinstance(value, str) and value.strip().upper() in ["", "N/A", "NONE", "NAN"]:
        return True
    return False


def safe_float(value):
    try:
        if value is None:
            return None
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def format_large_number(value):
    if value is None:
        return "N/A"

    try:
        value = float(value)
        abs_value = abs(value)

        if abs_value >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.2f}T"
        if abs_value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        if abs_value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"

        return f"{value:,.0f}"
    except Exception:
        return "N/A"


def format_price(value, currency=None, asset_type=None):
    if value is None:
        return "N/A"

    try:
        value = float(value)

        if asset_type == "fx":
            return f"{value:.4f}"

        currency_symbols = {
            "USD": "$",
            "EUR": "EUR ",
            "GBP": "GBP ",
            "JPY": "JPY ",
            "CHF": "CHF ",
            "CNY": "CNY ",
            "HKD": "HKD ",
            "CAD": "CAD ",
            "AUD": "AUD ",
            "KRW": "KRW ",
        }

        prefix = currency_symbols.get(str(currency).upper(), f"{currency} " if currency else "")
        return f"{prefix}{value:.2f}"
    except Exception:
        return "N/A"


def format_percent(value, multiply_by_100=False):
    if value is None:
        return "N/A"

    try:
        value = float(value)
        if multiply_by_100:
            value *= 100
        return f"{value:.2f}%"
    except Exception:
        return "N/A"


def format_ratio(value):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.2f}"
    except Exception:
        return "N/A"


def format_range(low, high, currency=None, asset_type=None):
    if low is None or high is None:
        return "N/A"

    return f"{format_price(low, currency, asset_type)} - {format_price(high, currency, asset_type)}"


def format_technical_value(value, suffix="", decimals=2):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.{decimals}f}{suffix}"
    except Exception:
        return "N/A"


def detect_asset_type(ticker, info):
    quote_type = str(info.get("quoteType", "")).lower()
    name = str(info.get("longName") or info.get("shortName") or "").lower()
    ticker_upper = str(ticker).upper()

    if quote_type in ["equity", "stock"]:
        return "equity"
    if quote_type == "etf":
        return "etf"
    if quote_type == "index":
        return "index"
    if quote_type in ["mutualfund", "fund"]:
        return "fund"
    if "bond" in name:
        return "bond"
    if ticker_upper.endswith("=X"):
        return "fx"
    if ticker_upper.endswith("=F"):
        return "commodity"
    if ticker_upper.startswith("^"):
        return "index"

    return "other"


def is_valid_yfinance_ticker(candidate):
    try:
        ticker_obj = yf.Ticker(candidate)
        hist = ticker_obj.history(period="1mo")

        if hist.empty:
            return False

        try:
            fast = ticker_obj.fast_info or {}
        except Exception:
            fast = {}

        last_price = fast.get("lastPrice")

        if last_price is None:
            close_series = hist["Close"].dropna()
            last_price = close_series.iloc[-1] if not close_series.empty else None

        return last_price is not None
    except Exception:
        return False


def extract_json_array(text):
    try:
        return json.loads(text)
    except Exception:
        pass

    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\[.*\]", text, re.DOTALL)

    if match:
        return json.loads(match.group(0))

    raise ValueError("No valid JSON array found.")


def ai_markdown_to_html(text):
    if text is None:
        return ""

    lines = str(text).split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        line = line.strip()

        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<br>")
            continue

        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False

            title = line.replace("### ", "").strip()
            html_lines.append(
                f"<h4 style='margin: 1rem 0 0.6rem 0; color: #0f172a; font-size: 1.15rem;'>{title}</h4>"
            )
            continue

        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul style='margin-top: 0.4rem; padding-left: 1.25rem;'>")
                in_list = True

            bullet = line[2:].strip()
            bullet = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", bullet)

            html_lines.append(
                f"<li style='margin-bottom: 0.65rem; line-height: 1.65; color: #334155;'>{bullet}</li>"
            )
            continue

        if in_list:
            html_lines.append("</ul>")
            in_list = False

        line = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)

        html_lines.append(
            f"<p style='margin: 0 0 0.75rem 0; line-height: 1.7; color: #334155;'>{line}</p>"
        )

    if in_list:
        html_lines.append("</ul>")

    return "".join(html_lines)


def split_bull_bear_case(text):
    if text is None:
        return "", ""

    text = str(text)

    if "### Bear Case" in text:
        parts = text.split("### Bear Case", 1)
        bull_part = parts[0].replace("### Bull Case", "").strip()
        bear_part = parts[1].strip()
    else:
        bull_part = text.strip()
        bear_part = ""

    return bull_part, bear_part


def escape_html(value):
    if value is None:
        return ""
    return escape(str(value), quote=True)


def parse_marketaux_date(value):
    if not value:
        return None

    try:
        clean_value = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(clean_value)
    except Exception:
        return None


def format_news_date(value):
    parsed = parse_marketaux_date(value)

    if parsed is None:
        return escape_html(value or "Unknown date")

    return parsed.strftime("%d %b %Y")


def get_news_sentiment_label(sentiment):
    try:
        sentiment = float(sentiment)
    except Exception:
        return "Neutral", "#e0f2fe", "#075985"

    if sentiment >= 0.15:
        return "Positive", "#dcfce7", "#166534"
    if sentiment <= -0.15:
        return "Negative", "#fee2e2", "#991b1b"

    return "Neutral", "#e0f2fe", "#075985"


def score_news_item(item, display_name, ticker):
    title = str(item.get("title") or "")
    description = str(item.get("description") or "")
    source = str(item.get("source") or "")
    text = f"{title} {description} {source}".lower()

    bad_terms = [
        "consensus rating", "analyst rating", "brokerages", "target price",
        "price target", "etf daily news", "stocknews.com", "zacks",
        "ticker report", "american banking", "marketbeat"
    ]

    operational_terms = [
        "contract", "order", "deal", "agreement", "framework", "procurement",
        "delivery", "deliveries", "ammunition", "munition", "artillery",
        "ukraine", "germany", "german", "bundeswehr", "defence", "defense",
        "military", "army", "tank", "vehicle", "drone", "missile",
        "plant", "factory", "production", "capacity", "acquisition",
        "takeover", "joint venture", "naval", "warship", "cannon", "weapon"
    ]

    financial_terms = [
        "earnings", "revenue", "guidance", "backlog", "margin",
        "forecast", "sales", "profit", "ebitda", "cash flow"
    ]

    score = 0

    for term in operational_terms:
        if term in text:
            score += 3

    for term in financial_terms:
        if term in text:
            score += 1

    for term in bad_terms:
        if term in text:
            score -= 8

    clean_ticker = str(ticker).split(".")[0].replace("^", "").replace("=F", "").replace("=X", "").lower()
    company_tokens = [token for token in re.split(r"\W+", str(display_name).lower()) if len(token) >= 4]

    if clean_ticker and clean_ticker in text:
        score += 2

    for token in company_tokens[:3]:
        if token in text:
            score += 2

    published_at = parse_marketaux_date(item.get("published_at"))

    if published_at is not None:
        now = datetime.now(timezone.utc)

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        age_days = (now - published_at).days

        if age_days <= 30:
            score += 5
        elif age_days <= 90:
            score += 3
        elif age_days <= 180:
            score += 1
        elif age_days > 365:
            score -= 10

    return score


# =========================
# ASSET RESOLUTION
# =========================
def resolve_asset_candidates_with_openai(query: str, max_candidates=3):
    prompt = f"""
You are a financial asset search engine for a user-facing financial dashboard.

User searched for: "{query}"

The user may search by:
- common asset name, such as Apple, Nvidia, Gold, S&P 500, EUR/USD
- ISIN, such as US0378331005
- local ticker, such as ASML
- Yahoo Finance ticker, such as AAPL, ASML.AS, GC=F, ^GSPC

Your task:
Return the 3 most likely Yahoo Finance-compatible instruments matching the user's query.

Important rules:
- If the query is an ISIN, identify the actual instrument behind the ISIN and return its Yahoo Finance ticker.
- If the query is a European stock, ETF or fund, return the Yahoo Finance-compatible ticker internally, including suffix if Yahoo requires it.
- The user does not need to know exchange suffixes; you must resolve that internally.
- If the query is a broad asset like S&P 500, Gold, Oil, Nasdaq, or EUR/USD, return the most natural market instruments.
- For S&P 500, prefer the index and major ETFs.
- For gold or oil, prefer futures and major ETFs.
- For FX, use Yahoo Finance FX format.
- Do not return obscure mutual funds unless the query clearly refers to that fund.
- Do not invent tickers.
- Return only valid JSON.

Output format:
[
  {{
    "ticker": "string",
    "name": "string",
    "type": "equity | index | commodity | fx | etf | fund | other",
    "region": "string"
  }}
]
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    raw_text = response.output_text.strip()

    try:
        candidates = extract_json_array(raw_text)
    except Exception:
        return []

    valid_candidates = []
    seen = set()

    for candidate in candidates:
        ticker = str(candidate.get("ticker", "")).strip().upper()

        if not ticker or ticker in seen:
            continue

        if is_valid_yfinance_ticker(ticker):
            valid_candidates.append({
                "ticker": ticker,
                "name": candidate.get("name", ticker),
                "type": candidate.get("type", "other"),
                "region": candidate.get("region", "N/A"),
                "source": "openai",
            })

            seen.add(ticker)

        if len(valid_candidates) >= max_candidates:
            break

    return valid_candidates


# =========================
# MARKET DATA
# =========================
def get_combined_info(stock, data):
    combined = {}

    try:
        fast = stock.fast_info or {}
        if fast:
            combined.update(dict(fast))
    except Exception:
        pass

    try:
        full = stock.info or {}
        if full:
            combined.update(full)
    except Exception:
        pass

    try:
        if "previousClose" not in combined and len(data) > 1:
            combined["previousClose"] = float(data["Close"].iloc[-2])
    except Exception:
        pass

    try:
        if "open" not in combined and "Open" in data.columns and not data["Open"].dropna().empty:
            combined["open"] = float(data["Open"].iloc[-1])
    except Exception:
        pass

    try:
        if "dayLow" not in combined and "Low" in data.columns and not data["Low"].dropna().empty:
            combined["dayLow"] = float(data["Low"].iloc[-1])
    except Exception:
        pass

    try:
        if "dayHigh" not in combined and "High" in data.columns and not data["High"].dropna().empty:
            combined["dayHigh"] = float(data["High"].iloc[-1])
    except Exception:
        pass

    try:
        if "volume" not in combined and "Volume" in data.columns and not data["Volume"].dropna().empty:
            combined["volume"] = float(data["Volume"].iloc[-1])
    except Exception:
        pass

    try:
        if "fiftyTwoWeekHigh" not in combined and "yearHigh" in combined:
            combined["fiftyTwoWeekHigh"] = combined["yearHigh"]
    except Exception:
        pass

    try:
        if "fiftyTwoWeekLow" not in combined and "yearLow" in combined:
            combined["fiftyTwoWeekLow"] = combined["yearLow"]
    except Exception:
        pass

    return combined


def fetch_marketaux_news(display_name, ticker, limit=6):
    url = "https://api.marketaux.com/v1/news/all"

    clean_ticker = (
        ticker
        .split(".")[0]
        .replace("^", "")
        .replace("=F", "")
        .replace("=X", "")
    )

    company_query = str(display_name).replace("AG", "").replace("SE", "").strip()
    published_after = (datetime.now(timezone.utc) - timedelta(days=240)).strftime("%Y-%m-%dT%H:%M:%S")

    focused_query = (
        f'"{company_query}" '
        f'+(contract | order | deal | agreement | Ukraine | Germany | Bundeswehr | '
        f'ammunition | artillery | defence | defense | military | tank | vehicle | drone | '
        f'production | plant | acquisition | procurement | delivery | backlog | earnings) '
        f'-"consensus rating" -"target price" -brokerages -analysts -"ETF Daily News"'
    )

    broad_query = f'"{company_query}" {clean_ticker}'.strip()

    queries = [focused_query, broad_query]
    collected = []
    seen_urls = set()

    for query in queries:
        params = {
            "api_token": MARKETAUX_API_KEY,
            "search": query,
            "limit": 25,
            "sort": "published_desc",
            "published_after": published_after,
            "must_have_entities": "false",
            "filter_entities": "true",
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception:
            continue

        for item in data.get("data", []):
            url_value = item.get("url") or item.get("uuid") or item.get("title")

            if not url_value or url_value in seen_urls:
                continue

            seen_urls.add(url_value)

            news_item = {
                "title": item.get("title"),
                "description": item.get("description") or item.get("snippet"),
                "source": item.get("source"),
                "published_at": item.get("published_at"),
                "url": item.get("url"),
                "sentiment": item.get("sentiment"),
                "entities": item.get("entities", []),
            }

            news_item["score"] = score_news_item(news_item, display_name, ticker)
            collected.append(news_item)

    if not collected:
        return []

    strong_items = [item for item in collected if item.get("score", 0) >= 2]

    if not strong_items:
        strong_items = collected

    strong_items.sort(
        key=lambda item: (
            item.get("score", 0),
            parse_marketaux_date(item.get("published_at")) or datetime.min.replace(tzinfo=timezone.utc)
        ),
        reverse=True
    )

    return strong_items[:limit]


def fetch_full_chart_data(ticker):
    stock = yf.Ticker(ticker)

    daily = stock.history(period="5y", interval="1d")
    intraday_7d = stock.history(period="7d", interval="30m")
    intraday_1d = stock.history(period="1d", interval="5m")

    for df in [daily, intraday_7d, intraday_1d]:
        if not df.empty:
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)

    return {
        "daily": daily,
        "intraday_7d": intraday_7d,
        "intraday_1d": intraday_1d,
    }


def get_display_data(chart_store, selected_period):
    if selected_period == "1D" and not chart_store["intraday_1d"].empty:
        return chart_store["intraday_1d"].copy()

    if selected_period == "7D" and not chart_store["intraday_7d"].empty:
        return chart_store["intraday_7d"].copy()

    base = chart_store["daily"].copy()

    if base.empty:
        return base

    days = DISPLAY_PERIODS[selected_period]
    cutoff = base.index.max() - pd.Timedelta(days=days)
    filtered = base[base.index >= cutoff]

    return filtered if not filtered.empty else base.tail(1)


def compute_performance_metrics(data):
    if data.empty or "Close" not in data.columns:
        return None, None, None

    close = data["Close"].dropna()

    if close.empty:
        return None, None, None

    current_price = float(close.iloc[-1])
    start_price = float(close.iloc[0])

    if start_price != 0:
        period_change = ((current_price - start_price) / start_price) * 100
    else:
        period_change = 0.0

    if len(close) > 1:
        previous_price = float(close.iloc[-2])

        if previous_price != 0:
            latest_move = ((current_price - previous_price) / previous_price) * 100
        else:
            latest_move = 0.0
    else:
        latest_move = 0.0

    return current_price, period_change, latest_move


# =========================
# TECHNICAL ANALYSIS
# =========================
def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_cci(data, period=20):
    if data.empty or not {"High", "Low", "Close"}.issubset(data.columns):
        return pd.Series(dtype=float)

    typical_price = (data["High"] + data["Low"] + data["Close"]) / 3
    sma_tp = typical_price.rolling(period).mean()
    mean_deviation = typical_price.rolling(period).apply(
        lambda x: (abs(x - x.mean())).mean(),
        raw=False
    )

    cci = (typical_price - sma_tp) / (0.015 * mean_deviation.replace(0, pd.NA))

    return cci


def calculate_atr(data, period=14):
    if data.empty or not {"High", "Low", "Close"}.issubset(data.columns):
        return pd.Series(dtype=float)

    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift()).abs()
    low_close = (data["Low"] - data["Close"].shift()).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(period).mean()

    return atr


def calculate_fibonacci_levels(data):
    if data.empty or not {"High", "Low"}.issubset(data.columns):
        return {}

    high = safe_float(data["High"].dropna().max())
    low = safe_float(data["Low"].dropna().min())

    if high is None or low is None or high == low:
        return {}

    diff = high - low

    return {
        "0.0%": high,
        "23.6%": high - diff * 0.236,
        "38.2%": high - diff * 0.382,
        "50.0%": high - diff * 0.500,
        "61.8%": high - diff * 0.618,
        "78.6%": high - diff * 0.786,
        "100.0%": low,
    }


def calculate_technical_analysis(daily_data, display_data):
    if daily_data.empty or "Close" not in daily_data.columns:
        return None

    data = daily_data.copy()
    data = data.dropna(subset=["Close"])

    if data.empty:
        return None

    close = data["Close"]
    current_price = safe_float(close.iloc[-1])

    sma_20_series = close.rolling(20).mean()
    sma_50_series = close.rolling(50).mean()
    sma_200_series = close.rolling(200).mean()

    rsi_series = calculate_rsi(close, 14)

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd_series = ema_12 - ema_26
    macd_signal_series = macd_series.ewm(span=9, adjust=False).mean()
    macd_hist_series = macd_series - macd_signal_series

    bb_middle_series = close.rolling(20).mean()
    bb_std_series = close.rolling(20).std()
    bb_upper_series = bb_middle_series + (2 * bb_std_series)
    bb_lower_series = bb_middle_series - (2 * bb_std_series)

    cci_series = calculate_cci(data, 20)
    atr_series = calculate_atr(data, 14)

    returns = close.pct_change().dropna()
    annualized_volatility = None

    if not returns.empty:
        annualized_volatility = safe_float(returns.std() * math.sqrt(252) * 100)

    volume_ratio = None
    current_volume = None
    avg_volume_20 = None

    if "Volume" in data.columns and not data["Volume"].dropna().empty:
        current_volume = safe_float(data["Volume"].dropna().iloc[-1])
        avg_volume_series = data["Volume"].rolling(20).mean().dropna()
        avg_volume_20 = safe_float(avg_volume_series.iloc[-1]) if not avg_volume_series.empty else None

        if current_volume is not None and avg_volume_20 not in [None, 0]:
            volume_ratio = current_volume / avg_volume_20

    recent_20_high = safe_float(data["High"].rolling(20).max().dropna().iloc[-1]) if "High" in data.columns and len(data) >= 20 else None
    recent_20_low = safe_float(data["Low"].rolling(20).min().dropna().iloc[-1]) if "Low" in data.columns and len(data) >= 20 else None
    recent_50_high = safe_float(data["High"].rolling(50).max().dropna().iloc[-1]) if "High" in data.columns and len(data) >= 50 else None
    recent_50_low = safe_float(data["Low"].rolling(50).min().dropna().iloc[-1]) if "Low" in data.columns and len(data) >= 50 else None

    fib_base = display_data.copy()

    if fib_base.empty or not {"High", "Low"}.issubset(fib_base.columns):
        fib_base = data.tail(180)

    fibonacci_levels = calculate_fibonacci_levels(fib_base)

    period_change = None

    if not display_data.empty and "Close" in display_data.columns:
        display_close = display_data["Close"].dropna()

        if len(display_close) >= 2 and display_close.iloc[0] != 0:
            period_change = ((display_close.iloc[-1] - display_close.iloc[0]) / display_close.iloc[0]) * 100

    sma_20 = safe_float(sma_20_series.dropna().iloc[-1]) if not sma_20_series.dropna().empty else None
    sma_50 = safe_float(sma_50_series.dropna().iloc[-1]) if not sma_50_series.dropna().empty else None
    sma_200 = safe_float(sma_200_series.dropna().iloc[-1]) if not sma_200_series.dropna().empty else None

    rsi = safe_float(rsi_series.dropna().iloc[-1]) if not rsi_series.dropna().empty else None
    macd = safe_float(macd_series.dropna().iloc[-1]) if not macd_series.dropna().empty else None
    macd_signal = safe_float(macd_signal_series.dropna().iloc[-1]) if not macd_signal_series.dropna().empty else None
    macd_hist = safe_float(macd_hist_series.dropna().iloc[-1]) if not macd_hist_series.dropna().empty else None

    bb_upper = safe_float(bb_upper_series.dropna().iloc[-1]) if not bb_upper_series.dropna().empty else None
    bb_middle = safe_float(bb_middle_series.dropna().iloc[-1]) if not bb_middle_series.dropna().empty else None
    bb_lower = safe_float(bb_lower_series.dropna().iloc[-1]) if not bb_lower_series.dropna().empty else None

    cci = safe_float(cci_series.dropna().iloc[-1]) if not cci_series.dropna().empty else None
    atr = safe_float(atr_series.dropna().iloc[-1]) if not atr_series.dropna().empty else None

    score = 0
    reasons = []

    if current_price is not None and sma_50 is not None:
        if current_price > sma_50:
            score += 1
            reasons.append("Price is above the 50-day moving average.")
        else:
            score -= 1
            reasons.append("Price is below the 50-day moving average.")

    if current_price is not None and sma_200 is not None:
        if current_price > sma_200:
            score += 1
            reasons.append("Price is above the 200-day moving average.")
        else:
            score -= 1
            reasons.append("Price is below the 200-day moving average.")

    if sma_50 is not None and sma_200 is not None:
        if sma_50 > sma_200:
            score += 1
            reasons.append("The 50-day average is above the 200-day average.")
        else:
            score -= 1
            reasons.append("The 50-day average is below the 200-day average.")

    if rsi is not None:
        if 45 <= rsi <= 70:
            score += 1
            reasons.append("RSI shows constructive momentum without extreme overbought pressure.")
        elif rsi > 75:
            score -= 1
            reasons.append("RSI is very high, suggesting possible overbought conditions.")
        elif rsi < 30:
            score += 0.5
            reasons.append("RSI is oversold, which may indicate a potential rebound zone.")
        elif rsi < 45:
            score -= 0.5
            reasons.append("RSI is weak, suggesting soft momentum.")

    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            score += 1
            reasons.append("MACD is above its signal line.")
        else:
            score -= 1
            reasons.append("MACD is below its signal line.")

    if cci is not None:
        if cci > 100:
            score += 0.5
            reasons.append("CCI indicates strong positive momentum.")
        elif cci < -100:
            score -= 0.5
            reasons.append("CCI indicates strong negative momentum.")

    if current_price is not None and bb_upper is not None and bb_lower is not None:
        if current_price > bb_upper:
            score -= 0.5
            reasons.append("Price is above the upper Bollinger Band, suggesting possible overextension.")
        elif current_price < bb_lower:
            score += 0.5
            reasons.append("Price is below the lower Bollinger Band, suggesting possible mean-reversion potential.")

    if current_price is not None and recent_20_low is not None and recent_20_high is not None:
        if recent_20_low != 0 and abs((current_price - recent_20_low) / recent_20_low) <= 0.03:
            score += 0.5
            reasons.append("Price is close to recent support.")

        if current_price != 0 and abs((recent_20_high - current_price) / current_price) <= 0.03:
            score -= 0.5
            reasons.append("Price is close to recent resistance.")

    if volume_ratio is not None and period_change is not None:
        if volume_ratio > 1.2 and period_change > 0:
            score += 1
            reasons.append("Recent upside move is supported by above-average volume.")
        elif volume_ratio > 1.2 and period_change < 0:
            score -= 1
            reasons.append("Recent downside move is confirmed by above-average volume.")

    if score >= 3:
        technical_signal = "BUY"
    elif score <= -3:
        technical_signal = "SELL"
    else:
        technical_signal = "HOLD"

    abs_score = abs(score)

    if abs_score >= 5:
        confidence = "High"
    elif abs_score >= 3:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "current_price": current_price,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "rsi": rsi,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "cci": cci,
        "bb_upper": bb_upper,
        "bb_middle": bb_middle,
        "bb_lower": bb_lower,
        "atr": atr,
        "annualized_volatility": annualized_volatility,
        "volume_ratio": volume_ratio,
        "current_volume": current_volume,
        "avg_volume_20": avg_volume_20,
        "recent_20_high": recent_20_high,
        "recent_20_low": recent_20_low,
        "recent_50_high": recent_50_high,
        "recent_50_low": recent_50_low,
        "fibonacci_levels": fibonacci_levels,
        "technical_score": score,
        "technical_signal": technical_signal,
        "confidence": confidence,
        "reasons": reasons[:6],
    }


def get_signal_style(signal):
    if signal == "BUY":
        return {"bg": "#dcfce7", "color": "#166534", "border": "#86efac"}
    if signal == "SELL":
        return {"bg": "#fee2e2", "color": "#991b1b", "border": "#fecaca"}
    return {"bg": "#e0f2fe", "color": "#075985", "border": "#bae6fd"}


def technical_note(label, value):
    if label == "RSI":
        if value is None:
            return "Not enough data."
        if value > 70:
            return "Overbought zone."
        if value < 30:
            return "Oversold zone."
        return "Neutral momentum zone."

    if label == "MACD":
        if value is None:
            return "Not enough data."
        return "Above signal is bullish; below signal is bearish."

    if label == "CCI":
        if value is None:
            return "Not enough data."
        if value > 100:
            return "Strong positive momentum."
        if value < -100:
            return "Strong negative momentum."
        return "Neutral trend pressure."

    if label == "Volume":
        if value is None:
            return "Not enough data."
        if value > 1.2:
            return "Above-average participation."
        if value < 0.8:
            return "Below-average participation."
        return "Normal participation."

    return ""


def render_technical_card(label, value, note):
    render_html(f"""
    <div class="tech-card">
        <div class="tech-label">{label}</div>
        <div class="tech-value">{value}</div>
        <div class="tech-note">{note}</div>
    </div>
    """)


def render_fibonacci_levels(fibonacci_levels, currency=None, asset_type=None):
    if not fibonacci_levels:
        render_html("""
        <div class="section-card">
            <h4 style="margin: 0 0 1rem 0; color: #0f172a;">Fibonacci Levels</h4>
            <p style="margin: 0; color: #64748b;">Not enough data to calculate Fibonacci levels.</p>
        </div>
        """)
        return

    rows_html = ""

    for index, (level, price) in enumerate(fibonacci_levels.items()):
        border = "border-bottom: 1px solid #e2e8f0;" if index < len(fibonacci_levels) - 1 else ""

        rows_html += f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.72rem 0; {border}">
    <span style="color: #64748b; font-weight: 800;">{level}</span>
    <span style="color: #0f172a; font-weight: 850;">{format_price(price, currency, asset_type)}</span>
</div>
"""

    render_html(f"""
    <div class="section-card">
        <h4 style="margin: 0 0 1rem 0; color: #0f172a;">Fibonacci Levels</h4>
        {rows_html}
    </div>
    """)


def display_technical_analysis(technical, display_name, ticker, currency, asset_type, selected_label):
    if technical is None:
        st.warning("Not enough market data to calculate technical analysis.")
        return

    signal = technical.get("technical_signal", "HOLD")
    confidence = technical.get("confidence", "Low")
    score = technical.get("technical_score", 0)
    signal_style = get_signal_style(signal)

    reasons_html = ""

    for reason in technical.get("reasons", []):
        reasons_html += f"<li style='margin-bottom: 0.45rem; color: #334155;'>{reason}</li>"

    render_html(f"""
    <div class="tech-signal-card" style="border: 1px solid {signal_style["border"]};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap;">
            <div>
                <div style="font-size: 0.85rem; color: #64748b; font-weight: 850; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.4rem;">
                    Chart-based Technical Signal
                </div>
                <div style="font-size: 2.1rem; font-weight: 900; color: #0f172a; letter-spacing: -0.05em;">
                    {signal}
                </div>
                <div style="margin-top: 0.4rem; color: #64748b;">
                    Score: <strong>{score:.1f}</strong> | Confidence: <strong>{confidence}</strong> | Period: <strong>{selected_label}</strong>
                </div>
            </div>
            <div>
                <span class="signal-pill" style="background: {signal_style["bg"]}; color: {signal_style["color"]};">
                    {signal} / {confidence}
                </span>
            </div>
        </div>
        <ul style="margin: 1.1rem 0 0 1.2rem; padding: 0;">
            {reasons_html}
        </ul>
        <p style="margin: 1rem 0 0 0; color: #64748b; font-size: 0.9rem;">
            This is a technical signal based only on chart indicators. It is not a complete investment recommendation.
        </p>
    </div>
    """)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_technical_card(
            "RSI 14",
            format_technical_value(technical.get("rsi")),
            technical_note("RSI", technical.get("rsi"))
        )

    with col2:
        macd_value = technical.get("macd")
        macd_signal = technical.get("macd_signal")

        if macd_value is not None and macd_signal is not None:
            macd_label = "Bullish" if macd_value > macd_signal else "Bearish"
        else:
            macd_label = "N/A"

        render_technical_card(
            "MACD",
            macd_label,
            f"MACD: {format_technical_value(macd_value)} | Signal: {format_technical_value(macd_signal)}"
        )

    with col3:
        render_technical_card(
            "CCI 20",
            format_technical_value(technical.get("cci")),
            technical_note("CCI", technical.get("cci"))
        )

    with col4:
        render_technical_card(
            "Volume Ratio",
            format_technical_value(technical.get("volume_ratio"), "x"),
            technical_note("Volume", technical.get("volume_ratio"))
        )

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        render_technical_card(
            "SMA 50",
            format_price(technical.get("sma_50"), currency, asset_type),
            "Medium-term trend reference."
        )

    with col6:
        render_technical_card(
            "SMA 200",
            format_price(technical.get("sma_200"), currency, asset_type),
            "Long-term trend reference."
        )

    with col7:
        render_technical_card(
            "ATR 14",
            format_price(technical.get("atr"), currency, asset_type),
            "Average trading range."
        )

    with col8:
        render_technical_card(
            "Volatility",
            format_technical_value(technical.get("annualized_volatility"), "%"),
            "Annualized daily volatility."
        )

    col9, col10 = st.columns(2)

    with col9:
        support_rows = [
            ("20D Support", format_price(technical.get("recent_20_low"), currency, asset_type)),
            ("20D Resistance", format_price(technical.get("recent_20_high"), currency, asset_type)),
            ("50D Support", format_price(technical.get("recent_50_low"), currency, asset_type)),
            ("50D Resistance", format_price(technical.get("recent_50_high"), currency, asset_type)),
        ]

        support_rows_html = ""

        for index, (label, value) in enumerate(support_rows):
            border = "border-bottom: 1px solid #e2e8f0;" if index < len(support_rows) - 1 else ""

            support_rows_html += f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.72rem 0; {border}">
    <span style="color: #64748b; font-weight: 800;">{label}</span>
    <span style="color: #0f172a; font-weight: 850;">{value}</span>
</div>
"""

        render_html(f"""
        <div class="section-card">
            <h4 style="margin: 0 0 1rem 0; color: #0f172a;">Support & Resistance</h4>
            {support_rows_html}
        </div>
        """)

    with col10:
        render_fibonacci_levels(
            technical.get("fibonacci_levels"),
            currency,
            asset_type
        )


# =========================
# CHART
# =========================
def build_price_chart(data, display_name, technical=None):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name=display_name,
            line=dict(width=3, color="#2563eb"),
        )
    )

    if "Close" in data.columns:
        if len(data) >= 20:
            sma_20 = data["Close"].rolling(20).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=sma_20,
                    mode="lines",
                    name="SMA 20",
                    line=dict(width=1.5, color="#64748b", dash="dot"),
                )
            )

        if len(data) >= 50:
            sma_50 = data["Close"].rolling(50).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=sma_50,
                    mode="lines",
                    name="SMA 50",
                    line=dict(width=1.5, color="#0f172a", dash="dash"),
                )
            )

    if technical and technical.get("bb_upper") and technical.get("bb_lower"):
        fig.add_hline(
            y=technical["bb_upper"],
            line_dash="dot",
            line_color="#94a3b8",
            annotation_text="Upper Bollinger",
            annotation_position="top left"
        )

        fig.add_hline(
            y=technical["bb_lower"],
            line_dash="dot",
            line_color="#94a3b8",
            annotation_text="Lower Bollinger",
            annotation_position="bottom left"
        )

    if technical and technical.get("fibonacci_levels"):
        for level, price in technical["fibonacci_levels"].items():
            if level in ["38.2%", "50.0%", "61.8%"]:
                fig.add_hline(
                    y=price,
                    line_dash="dash",
                    line_color="#cbd5e1",
                    annotation_text=f"Fib {level}",
                    annotation_position="right"
                )

    fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
            fixedrange=False,
            showgrid=False,
        ),
        yaxis=dict(
            fixedrange=False,
            showgrid=True,
            gridcolor="#e2e8f0",
        ),
        dragmode="zoom",
        showlegend=True,
        hovermode="x unified",
        font=dict(
            family="Inter, Arial, sans-serif",
            size=13,
            color="#0f172a"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


# =========================
# AI SECTIONS
# =========================
def generate_asset_description(display_name, ticker, asset_type, info):
    prompt = f"""
You are writing a short financial description for an asset dashboard.

Asset name: {display_name}
Ticker: {ticker}
Asset type: {asset_type}
Exchange: {info.get("exchange")}
Currency: {info.get("currency")}
Sector: {info.get("sector")}
Industry: {info.get("industry")}
Category: {info.get("category")}
Short name: {info.get("shortName")}
Long name: {info.get("longName")}

Write a concise 5-7 line description explaining:
1. what this asset is,
2. what role it plays in markets,
3. what mainly drives its value.

Rules:
- Be clear and professional.
- Do not invent precise figures.
- If the asset is an index, explain what it tracks.
- If it is a commodity, explain its economic role.
- If it is an equity, explain the business briefly.
- If data is limited, still provide a useful general explanation.
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text.strip()


def generate_technical_reading(display_name, ticker, technical):
    prompt = f"""
You are writing a short technical analysis reading for a financial dashboard.

Asset: {display_name}
Ticker: {ticker}

Technical data:
- Technical Signal: {technical.get("technical_signal")}
- Confidence: {technical.get("confidence")}
- Technical Score: {technical.get("technical_score")}
- RSI 14: {technical.get("rsi")}
- MACD: {technical.get("macd")}
- MACD Signal: {technical.get("macd_signal")}
- MACD Histogram: {technical.get("macd_hist")}
- CCI 20: {technical.get("cci")}
- Price: {technical.get("current_price")}
- SMA 20: {technical.get("sma_20")}
- SMA 50: {technical.get("sma_50")}
- SMA 200: {technical.get("sma_200")}
- Bollinger Upper: {technical.get("bb_upper")}
- Bollinger Lower: {technical.get("bb_lower")}
- ATR 14: {technical.get("atr")}
- Volume Ratio: {technical.get("volume_ratio")}
- Recent 20D High: {technical.get("recent_20_high")}
- Recent 20D Low: {technical.get("recent_20_low")}
- Main scoring reasons: {technical.get("reasons")}

Task:
Write a concise chart-based technical reading.

Output format:
### Technical Reading
- **Signal**: explain the BUY/HOLD/SELL signal.
- **Trend**: explain moving average structure.
- **Momentum**: explain RSI, MACD, and CCI.
- **Risk level**: explain volatility, Bollinger Bands, ATR, or volume.

Rules:
- This is a chart-based signal only, not full investment advice.
- Do not mention that you are an AI.
- Do not invent data.
- Keep it concise and professional.
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text.strip()


def generate_geopolitical_drivers(display_name, ticker, asset_type, info):
    prompt = f"""
You are writing a short geopolitical risk and market drivers section for a financial dashboard.

Asset name: {display_name}
Ticker: {ticker}
Asset type: {asset_type}
Exchange: {info.get("exchange")}
Currency: {info.get("currency")}
Sector: {info.get("sector")}
Industry: {info.get("industry")}
Category: {info.get("category")}
Short name: {info.get("shortName")}
Long name: {info.get("longName")}
Business summary: {info.get("longBusinessSummary")}

Task:
Write 5 concise bullet points explaining the main geopolitical or macro-political factors that can influence this asset. Put in bold the factor in each bullet point and then do ":" and explain.

Rules:
- Be specific and market-relevant.
- Focus on geopolitical, policy, trade, sanctions, war, regulation, energy security, sovereign risk, interest-rate regime, or supply-chain exposure when relevant.
- Adapt the answer to the asset type.
- Do not invent company-specific facts that are not clearly implied by the asset type or description.
- If geopolitics is only moderately relevant, say so and mention the most important external policy drivers instead.
- Keep each bullet short and professional.
- Output only bullet points, nothing else.
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text.strip()


def generate_bull_bear_case(display_name, ticker, asset_type, info):
    prompt = f"""
You are writing a Bull vs Bear Case section for a financial dashboard.

Asset name: {display_name}
Ticker: {ticker}
Asset type: {asset_type}
Exchange: {info.get("exchange")}
Currency: {info.get("currency")}
Sector: {info.get("sector")}
Industry: {info.get("industry")}
Category: {info.get("category")}
Short name: {info.get("shortName")}
Long name: {info.get("longName")}
Business summary: {info.get("longBusinessSummary")}

Task:
Write a structured Bull vs Bear Case for this asset.

Output format:
### Bull Case
- **Factor name**: short explanation
- **Factor name**: short explanation
- **Factor name**: short explanation

### Bear Case
- **Risk name**: short explanation
- **Risk name**: short explanation
- **Risk name**: short explanation

Rules:
- Give exactly 3 bullet points for Bull Case and 3 bullet points for Bear Case.
- Be specific and market-relevant.
- Adapt to the asset type.
- For equities, focus on growth, margins, valuation, competitive position, regulation, demand, and macro sensitivity.
- For indices, focus on earnings, market breadth, rates, macro cycle, and concentration risk.
- For commodities, focus on supply-demand, inventories, geopolitics, and growth/inflation sensitivity.
- For FX, focus on rates, central bank divergence, growth, inflation, and risk sentiment.
- Do not invent precise facts or figures.
- Keep each bullet concise and professional.
- Output only the formatted section, nothing else.
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text.strip()


# =========================
# METRICS
# =========================
def get_metric_definitions(asset_type, info):
    currency = clean_text(info.get("currency"))
    currency = None if currency == "N/A" else currency

    previous_close = info.get("previousClose")
    open_price = info.get("open")
    volume = info.get("volume")
    day_low = info.get("dayLow")
    day_high = info.get("dayHigh")
    week_52_high = info.get("fiftyTwoWeekHigh")
    week_52_low = info.get("fiftyTwoWeekLow")
    market_cap = info.get("marketCap")
    enterprise_value = info.get("enterpriseValue")
    total_revenue = info.get("totalRevenue")
    ebitda = info.get("ebitda")
    enterprise_to_ebitda = info.get("enterpriseToEbitda")
    profit_margins = info.get("profitMargins")
    free_cashflow = info.get("freeCashflow")
    debt_to_equity = info.get("debtToEquity")
    pe_ratio = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    dividend_yield = info.get("dividendYield")
    beta = info.get("beta")
    open_interest = info.get("openInterest")
    total_assets = info.get("totalAssets")
    sector = clean_text(info.get("sector"))
    industry = clean_text(info.get("industry"))
    category = clean_text(info.get("category"))
    exchange = clean_text(info.get("exchange"))
    country = clean_text(info.get("country"))
    fund_family = clean_text(info.get("fundFamily"))
    yield_value = info.get("yield")
    three_year_avg_return = info.get("threeYearAverageReturn")
    five_year_avg_return = info.get("fiveYearAverageReturn")

    if enterprise_to_ebitda is None and enterprise_value not in [None, 0] and ebitda not in [None, 0]:
        try:
            enterprise_to_ebitda = float(enterprise_value) / float(ebitda)
        except Exception:
            enterprise_to_ebitda = None

    common = [
        ("Previous Close", format_price(previous_close, currency, asset_type)),
        ("Open", format_price(open_price, currency, asset_type)),
        ("Day Range", format_range(day_low, day_high, currency, asset_type)),
        ("52W Range", format_range(week_52_low, week_52_high, currency, asset_type)),
    ]

    if asset_type == "equity":
        metrics = common + [
            ("Market Cap", format_large_number(market_cap)),
            ("Revenue", format_large_number(total_revenue)),
            ("EBITDA", format_large_number(ebitda)),
            ("EV/EBITDA", format_ratio(enterprise_to_ebitda)),
            ("Profit Margin", format_percent(profit_margins, multiply_by_100=True)),
            ("Free Cash Flow", format_large_number(free_cashflow)),
            ("Debt/Equity", format_ratio(debt_to_equity)),
            ("Trailing P/E", format_ratio(pe_ratio)),
            ("Forward P/E", format_ratio(forward_pe)),
            ("Dividend Yield", format_percent(dividend_yield, multiply_by_100=True)),
            ("Beta", format_ratio(beta)),
            ("Volume", format_large_number(volume)),
            ("Sector", sector),
            ("Industry", industry),
            ("Country", country),
        ]
    elif asset_type == "index":
        metrics = common + [
            ("Exchange", exchange),
            ("Currency", clean_text(info.get("currency"))),
            ("Country", country),
            ("Volume", format_large_number(volume)),
        ]
    elif asset_type == "commodity":
        metrics = common + [
            ("Open Interest", format_large_number(open_interest)),
            ("Volume", format_large_number(volume)),
            ("Exchange", exchange),
            ("Currency", clean_text(info.get("currency"))),
        ]
    elif asset_type == "bond":
        metrics = common + [
            ("Yield", format_percent(yield_value, multiply_by_100=True)),
            ("Category", category),
            ("Fund Family", fund_family),
            ("Total Assets", format_large_number(total_assets)),
            ("3Y Avg Return", format_percent(three_year_avg_return, multiply_by_100=True)),
            ("5Y Avg Return", format_percent(five_year_avg_return, multiply_by_100=True)),
        ]
    elif asset_type == "etf":
        metrics = common + [
            ("Total Assets", format_large_number(total_assets)),
            ("Category", category),
            ("Yield", format_percent(yield_value, multiply_by_100=True)),
            ("Beta", format_ratio(beta)),
            ("Volume", format_large_number(volume)),
            ("Fund Family", fund_family),
        ]
    elif asset_type == "fund":
        metrics = common + [
            ("Total Assets", format_large_number(total_assets)),
            ("Category", category),
            ("Fund Family", fund_family),
            ("Yield", format_percent(yield_value, multiply_by_100=True)),
            ("3Y Avg Return", format_percent(three_year_avg_return, multiply_by_100=True)),
            ("5Y Avg Return", format_percent(five_year_avg_return, multiply_by_100=True)),
        ]
    elif asset_type == "fx":
        metrics = common + [
            ("Exchange", exchange),
            ("Currency", clean_text(info.get("currency"))),
        ]
    else:
        metrics = common + [
            ("Volume", format_large_number(volume)),
            ("Exchange", exchange),
            ("Currency", clean_text(info.get("currency"))),
            ("Category", category),
        ]

    return [(label, value) for label, value in metrics if not is_missing(value)]


def display_metrics_grid(metrics, columns_per_row=3):
    for i in range(0, len(metrics), columns_per_row):
        row_metrics = metrics[i:i + columns_per_row]
        cols = st.columns(len(row_metrics))

        for col, (label, value) in zip(cols, row_metrics):
            with col:
                render_html(f"""
                <div style="
                    background: white;
                    padding: 1.1rem;
                    border-radius: 18px;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.04);
                    margin-bottom: 1rem;
                ">
                    <div style="font-size: 0.85rem; color: #64748b; font-weight: 700; margin-bottom: 0.4rem;">
                        {label}
                    </div>
                    <div style="font-size: 1.35rem; color: #0f172a; font-weight: 800;">
                        {value}
                    </div>
                </div>
                """)


def load_selected_asset(ticker, resolved_name, original_query):
    stock = yf.Ticker(ticker)
    chart_store = fetch_full_chart_data(ticker)

    if (
        chart_store["daily"].empty
        and chart_store["intraday_7d"].empty
        and chart_store["intraday_1d"].empty
    ):
        st.error("No price data found for this asset.")
        return

    base_for_info = chart_store["daily"]

    if base_for_info.empty:
        base_for_info = chart_store["intraday_7d"]

    if base_for_info.empty:
        base_for_info = chart_store["intraday_1d"]

    info = get_combined_info(stock, base_for_info)

    display_name = (
        info.get("longName")
        or info.get("shortName")
        or resolved_name
        or original_query.strip()
        or ticker
    )

    asset_type = detect_asset_type(ticker, info)

    st.session_state.asset_payload = {
        "ticker": ticker,
        "resolved_name": resolved_name,
        "display_name": display_name,
        "asset_type": asset_type,
        "info": info,
        "chart_store": chart_store,
        "original_query": original_query,
        "description": None,
        "geopolitical_drivers": None,
        "bull_bear_case": None,
    }

    st.session_state.asset_loaded = True


# =========================
# SESSION STATE
# =========================
if "asset_loaded" not in st.session_state:
    st.session_state.asset_loaded = False

if "asset_payload" not in st.session_state:
    st.session_state.asset_payload = {}

if "search_candidates" not in st.session_state:
    st.session_state.search_candidates = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""


# =========================
# UI HEADER
# =========================
render_html("""
<div class="hero-card">
    <h1 style="margin-bottom: 0.35rem;">AssetBrief</h1>
    <p style="font-size: 1.15rem; color: #64748b; max-width: 760px; margin-bottom: 0;">
        Search any stock, index, commodity, ETF or FX pair and generate a structured market brief.
    </p>
</div>
""")


with st.form("search_form"):
    user_input = st.text_input(
        "Search an asset",
        placeholder="Try: Apple, AAPL, US0378331005"
    ).strip()

    search_clicked = st.form_submit_button("Search")


# =========================
# SEARCH STEP
# =========================
if search_clicked:
    if not user_input:
        st.warning("Please enter a valid asset name, ticker or ISIN.")
    else:
        try:
            with st.spinner("Searching matching assets..."):
                candidates = resolve_asset_candidates_with_openai(
                    user_input,
                    max_candidates=3
                )

            if not candidates:
                st.error("No matching asset found.")
                st.session_state.search_candidates = []
                st.session_state.pending_query = ""
                st.session_state.asset_loaded = False
            else:
                st.session_state.search_candidates = candidates
                st.session_state.pending_query = user_input
                st.session_state.asset_loaded = False

        except Exception as e:
            st.error(f"An error occurred during search: {e}")


# =========================
# USER CHOOSES FROM SEARCH RESULTS
# =========================
if st.session_state.search_candidates and not st.session_state.asset_loaded:
    render_html("""
    <div class="asset-card">
        <h3 style="margin-top: 0; margin-bottom: 0.35rem;">Select the correct asset</h3>
        <p class="small-muted" style="margin-bottom: 0;">
            Click one of the options below to launch the analysis.
        </p>
    </div>
    """)

    cols = st.columns(len(st.session_state.search_candidates), gap="large")

    for idx, candidate in enumerate(st.session_state.search_candidates):
        ticker = candidate.get("ticker", "N/A")
        name = candidate.get("name", "N/A")
        asset_type = candidate.get("type", "N/A")
        region = candidate.get("region", "N/A")

        with cols[idx]:
            render_html(f"""
            <div class="choice-card">
                <div class="choice-ticker">{ticker}</div>
                <div class="choice-name">{name}</div>
                <div class="choice-meta">{asset_type} | {region}</div>
            </div>
            """)

            if st.button(
                f"Analyze {ticker}",
                key=f"analyze_candidate_{idx}",
                use_container_width=True
            ):
                try:
                    with st.spinner("Loading selected asset..."):
                        load_selected_asset(
                            ticker=ticker,
                            resolved_name=name,
                            original_query=st.session_state.pending_query
                        )

                    st.session_state.search_candidates = []
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred while loading selected asset: {e}")


# =========================
# DISPLAY STORED RESULT
# =========================
if st.session_state.asset_loaded:
    payload = st.session_state.asset_payload

    ticker = payload["ticker"]
    resolved_name = payload["resolved_name"]
    display_name = payload["display_name"]
    asset_type = payload["asset_type"]
    info = payload["info"]
    chart_store = payload["chart_store"]

    render_html(f"""
    <div class="asset-card">
        <div style="color: #64748b; font-size: 0.95rem; font-weight: 700; margin-bottom: 0.4rem;">
            Resolved asset
        </div>
        <h2 style="margin: 0 0 0.3rem 0;">{display_name}</h2>
        <p style="margin: 0; color: #64748b;">
            Ticker: <strong>{ticker}</strong> | Type: <strong>{asset_type.capitalize()}</strong> | Match: {resolved_name}
        </p>
    </div>
    """)

    selected_label = st.selectbox(
        "Select chart period",
        list(DISPLAY_PERIODS.keys()),
        index=list(DISPLAY_PERIODS.keys()).index(DEFAULT_CHART_PERIOD),
        key="chart_period_selector",
    )

    data = get_display_data(chart_store, selected_label)

    if data.empty:
        st.error("No chart data available for the selected period.")
    else:
        current_price, period_change, latest_move = compute_performance_metrics(data)

        currency = clean_text(info.get("currency"))
        currency = None if currency == "N/A" else currency

        technical = calculate_technical_analysis(chart_store["daily"], data)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Price", format_price(current_price, currency, asset_type))
        col2.metric(f"Return ({selected_label})", f"{period_change:.2f}%")
        col3.metric("Latest Move", f"{latest_move:.2f}%")
        col4.metric("Ticker", ticker.upper())

        st.divider()

        st.write("### Key Metrics")
        st.write(f"**Asset Type:** {asset_type.capitalize()}")

        metrics = get_metric_definitions(asset_type=asset_type, info=info)
        display_metrics_grid(metrics, columns_per_row=3)

        st.divider()

        st.write(f"### Price Chart ({selected_label})")
        fig = build_price_chart(data, display_name, technical)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.write("### Technical Analysis")

        display_technical_analysis(
            technical=technical,
            display_name=display_name,
            ticker=ticker,
            currency=currency,
            asset_type=asset_type,
            selected_label=selected_label
        )

        if technical is not None:
            technical_key = f"technical_reading_{selected_label}"

            if not st.session_state.asset_payload.get(technical_key):
                with st.spinner("Generating technical reading..."):
                    st.session_state.asset_payload[technical_key] = generate_technical_reading(
                        display_name=display_name,
                        ticker=ticker,
                        technical=technical
                    )

            technical_reading = st.session_state.asset_payload[technical_key]
            technical_reading_html = ai_markdown_to_html(technical_reading)

            render_html(f"""
            <div class="section-card">
                {technical_reading_html}
            </div>
            """)

        st.divider()

        st.write("### Overview")

        description_from_api = clean_text(info.get("longBusinessSummary"))
        country = clean_text(info.get("country"))
        website = clean_text(info.get("website"))
        exchange = clean_text(info.get("exchange"))
        sector = clean_text(info.get("sector"))
        industry = clean_text(info.get("industry"))

        if asset_type in ["index", "commodity", "fx", "bond", "etf", "fund"]:
            description_from_api = "N/A"

        overview_lines = []

        if asset_type == "equity":
            if sector != "N/A":
                overview_lines.append(f"<strong>Sector:</strong> {sector}")
            if industry != "N/A":
                overview_lines.append(f"<strong>Industry:</strong> {industry}")
            if country != "N/A":
                overview_lines.append(f"<strong>Country:</strong> {country}")
            if website != "N/A":
                overview_lines.append(f"<strong>Website:</strong> {website}")
        else:
            if exchange != "N/A":
                overview_lines.append(f"<strong>Exchange:</strong> {exchange}")
            if currency:
                overview_lines.append(f"<strong>Currency:</strong> {currency}")
            if country != "N/A":
                overview_lines.append(f"<strong>Country:</strong> {country}")

        if description_from_api != "N/A":
            description = description_from_api
            st.session_state.asset_payload["description"] = description
        else:
            if not st.session_state.asset_payload.get("description"):
                with st.spinner("Generating asset description..."):
                    st.session_state.asset_payload["description"] = generate_asset_description(
                        display_name=display_name,
                        ticker=ticker,
                        asset_type=asset_type,
                        info=info
                    )

            description = st.session_state.asset_payload["description"]

        overview_meta_html = ""

        if overview_lines:
            overview_meta_html = "<div style='margin-bottom: 1.1rem;'>" + "".join(
                f"<p style='margin: 0 0 0.55rem 0;'>{line}</p>" for line in overview_lines
            ) + "</div>"

        description_html = str(description).replace("\n", "<br>")

        render_html(f"""
        <div class="section-card">
            {overview_meta_html}
            <div style="line-height: 1.7; color: #334155; font-size: 1rem;">
                {description_html}
            </div>
        </div>
        """)

        st.divider()

        st.write("### Key Geopolitical Drivers")

        if not st.session_state.asset_payload.get("geopolitical_drivers"):
            with st.spinner("Generating geopolitical drivers..."):
                st.session_state.asset_payload["geopolitical_drivers"] = generate_geopolitical_drivers(
                    display_name=display_name,
                    ticker=ticker,
                    asset_type=asset_type,
                    info=info
                )

        geopolitical_drivers = st.session_state.asset_payload["geopolitical_drivers"]
        geopolitical_drivers_html = ai_markdown_to_html(geopolitical_drivers)

        render_html(f"""
        <div class="section-card">
            {geopolitical_drivers_html}
        </div>
        """)

        st.divider()

        st.write("### Latest News")

        news_key = f"latest_news_{ticker}_{display_name}"

        if not st.session_state.asset_payload.get(news_key):
            with st.spinner("Fetching latest news..."):
                st.session_state.asset_payload[news_key] = fetch_marketaux_news(
                    display_name=display_name,
                    ticker=ticker,
                    limit=6
                )

        news_items = st.session_state.asset_payload.get(news_key, [])

        if not news_items:
            st.warning("No recent operational news found for this asset.")
        else:
            for item in news_items:
                title = escape_html(item.get("title") or "No title")
                description = escape_html(item.get("description") or "")
                source = escape_html(item.get("source") or "Unknown source")
                published_at = format_news_date(item.get("published_at"))
                url = escape_html(item.get("url") or "#")
                sentiment_label, sentiment_bg, sentiment_color = get_news_sentiment_label(item.get("sentiment"))

                render_html(f"""
                <div class="section-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 0.7rem; flex-wrap: wrap;">
                        <div style="font-size: 0.85rem; color: #64748b; font-weight: 750;">
                            {source} | {published_at}
                        </div>
                        <div style="background: {sentiment_bg}; color: {sentiment_color}; padding: 0.28rem 0.65rem; border-radius: 999px; font-size: 0.78rem; font-weight: 850;">
                            {sentiment_label}
                        </div>
                    </div>
                    <h4 style="margin: 0 0 0.75rem 0; color: #0f172a; line-height: 1.35;">
                        <a href="{url}" target="_blank" style="color: #0f172a; text-decoration: none;">
                            {title}
                        </a>
                    </h4>
                    <p style="margin: 0; color: #475569; line-height: 1.6;">
                        {description}
                    </p>
                </div>
                """)

        st.divider()

        st.write("### Bull vs Bear Case")

        if not st.session_state.asset_payload.get("bull_bear_case"):
            with st.spinner("Generating bull vs bear case..."):
                st.session_state.asset_payload["bull_bear_case"] = generate_bull_bear_case(
                    display_name=display_name,
                    ticker=ticker,
                    asset_type=asset_type,
                    info=info
                )

        bull_bear_case = st.session_state.asset_payload["bull_bear_case"]

        bull_case_text, bear_case_text = split_bull_bear_case(bull_bear_case)

        bull_case_html = ai_markdown_to_html(bull_case_text)
        bear_case_html = ai_markdown_to_html(bear_case_text)

        bull_col, bear_col = st.columns(2, gap="large")

        with bull_col:
            render_html(f"""
            <div class="section-card" style="border-left: 5px solid #22c55e;">
                <h4 style="margin: 0 0 1rem 0; color: #166534;">Bull Case</h4>
                {bull_case_html}
            </div>
            """)

        with bear_col:
            render_html(f"""
            <div class="section-card" style="border-left: 5px solid #ef4444;">
                <h4 style="margin: 0 0 1rem 0; color: #991b1b;">Bear Case</h4>
                {bear_case_html}
            </div>
            """)


# streamlit run c:/Users/emili/OneDrive/Documents/Project/app.py