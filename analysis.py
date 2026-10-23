"""Event-study maths: day-0 reaction, multi-day drift, and comparison with normal days."""
import numpy as np
import pandas as pd
from scipy import stats

HORIZONS = [0, 1, 5]  # trading days after the event (0 = event day itself)


def event_returns(prices, events, horizons=HORIZONS):
    """Cumulative % return from the close BEFORE the event to the close k days after.
    Both NFP (08:30 ET) and FOMC (14:00 ET) land inside day 0, so day 0 captures the reaction."""
    rows = []
    for _, e in events.iterrows():
        if e["date"] not in prices.index:
            continue  # holiday / missing data
        i = prices.index.get_loc(e["date"])
        if i < 1 or i + max(horizons) >= len(prices):
            continue
        base = prices.iloc[i - 1]
        for k in horizons:
            r = (prices.iloc[i + k] / base - 1) * 100
            for m, v in r.items():
                rows.append({"date": e["date"], "event_type": e["event_type"], "fed_change_bp": e.get("fed_change_bp"),
                             "market": m, "horizon": k, "ret_pct": v})
    return pd.DataFrame(rows)


def volatility_comparison(prices, events):
    """Is the event-day move bigger than a normal day's move? (absolute % returns)"""
    daily = prices.pct_change().dropna() * 100
    out = []
    for etype, grp in events.groupby("event_type"):
        ev_days = daily.index.intersection(grp["date"])
        normal = daily.drop(ev_days)
        for m in daily:
            a, b = daily.loc[ev_days, m].abs(), normal[m].abs()
            p = stats.mannwhitneyu(a, b, alternative="greater").pvalue
            out.append({"event_type": etype, "market": m, "n_events": len(a),
                        "avg_abs_move_event_%": a.mean(), "avg_abs_move_normal_%": b.mean(),
                        "ratio": a.mean() / b.mean(), "p_value": p})
    return pd.DataFrame(out).round(3)


def fomc_by_outcome(rets):
    """Average reaction split into hike / hold / cut (outcome of the meeting, not the 'surprise')."""
    f = rets[(rets.event_type == "FOMC") & (rets.horizon == 0)].copy()
    f["outcome"] = np.sign(f["fed_change_bp"].astype(float)).map({1: "hike", 0: "hold", -1: "cut"})
    return f.groupby(["outcome", "market"])["ret_pct"].agg(["mean", "count"]).round(3)


def intraday_reaction(series, release_times, offsets_min=(5, 15, 30, 60)):
    """% move from the last bar before release to each offset after it.
    `series`: close prices indexed by tz-aware (America/New_York) timestamps.
    `release_times`: list of tz-aware Timestamps."""
    rows = []
    for t in release_times:
        before = series[series.index < t]
        if before.empty:
            continue
        p0 = before.iloc[-1]
        row = {"release": t}
        for m in offsets_min:
            after = series[series.index >= t + pd.Timedelta(minutes=m)]
            row[f"+{m}m_%"] = (after.iloc[0] / p0 - 1) * 100 if not after.empty else np.nan
        rows.append(row)
    df = pd.DataFrame(rows)
    num = df.columns.drop("release")
    df[num] = df[num].round(3)
    return df
