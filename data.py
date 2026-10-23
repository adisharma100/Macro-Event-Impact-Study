"""Data loading: live daily prices (yfinance), 5-minute prices, or a synthetic demo."""
import numpy as np
import pandas as pd

# A small, interpretable set of markets: equities, long bonds, US dollar, gold.
MARKETS = {"SPY": "US equities", "TLT": "US long bonds", "UUP": "US dollar", "GLD": "Gold"}


def load_events(path="events.csv"):
    ev = pd.read_csv(path, parse_dates=["date"])
    return ev.sort_values("date").reset_index(drop=True)


def load_daily_live(start, end):
    import yfinance as yf  # imported here so --demo works without it
    px = yf.download(list(MARKETS), start=start, end=end, auto_adjust=True, progress=False)["Close"]
    return px.dropna()


def load_5min_live(ticker):
    """Yahoo only serves ~60 days of 5-minute bars, so this suits *recent* events only."""
    import yfinance as yf
    df = yf.download(ticker, period="60d", interval="5m", auto_adjust=True, progress=False)
    df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_convert("America/New_York")
    return df["Close"]


def synthetic_daily(events, start="2022-12-01", end="2025-01-31", seed=7):
    """DEMO ONLY. Random prices with extra volatility on event days.
    Results from this are built-in artefacts, NOT market findings."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, end)
    vol = {"SPY": 0.008, "TLT": 0.007, "UUP": 0.003, "GLD": 0.007}
    boost = {"FOMC": 1.8, "NFP": 1.5}
    mult = pd.Series(1.0, index=idx)
    for _, e in events.iterrows():
        if e["date"] in mult.index:
            mult[e["date"]] = boost[e["event_type"]]
    rets = pd.DataFrame({m: rng.normal(0, v, len(idx)) * mult.values for m, v in vol.items()}, index=idx)
    return 100 * (1 + rets).cumprod()
