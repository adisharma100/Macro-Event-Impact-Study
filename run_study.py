"""Run the macro event impact study.
   python run_study.py --demo                 # synthetic data, works offline
   python run_study.py --start 2022-12-01 --end 2025-01-31   # real daily data (needs internet + yfinance)
   python run_study.py --intraday SPY         # 5-min reaction for events in the last ~60 days
"""
import argparse, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import data, analysis

RELEASE_TIME = {"NFP": "08:30", "FOMC": "14:00"}  # New York time


def plot_vol(vc, path, title):
    pv = vc.pivot(index="market", columns="event_type", values="ratio")
    ax = pv.plot.bar(figsize=(7, 4), rot=0)
    ax.axhline(1, color="k", lw=1, ls="--")
    ax.set_ylabel("Event-day move / normal-day move")
    ax.set_title(title)
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()


def plot_paths(prices, events, path, title):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    for ax, etype in zip(axes, ["FOMC", "NFP"]):
        r = analysis.event_returns(prices, events[events.event_type == etype], horizons=[0, 1, 2, 3, 4, 5])
        avg = r.groupby(["market", "horizon"])["ret_pct"].mean().unstack(0)
        avg.loc[-1] = 0
        avg.sort_index().plot(ax=ax, marker="o")
        ax.axvline(0, color="grey", ls=":")
        ax.set_title(f"{etype}: avg cumulative return"); ax.set_xlabel("Trading days after event"); ax.set_ylabel("%")
    fig.suptitle(title); plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--start", default="2022-12-01")
    ap.add_argument("--end", default="2025-01-31")
    ap.add_argument("--intraday", metavar="TICKER")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    events = data.load_events()

    if a.intraday:
        s = data.load_5min_live(a.intraday)
        days = set(s.index.date)
        recent = events[events.date.dt.date.isin(days)]
        if recent.empty:
            print("No events in the last ~60 days of events.csv. Add recent dates (e.g. this month's NFP / FOMC) and rerun."); return
        times = [pd.Timestamp(f"{d.date()} {RELEASE_TIME[t]}", tz="America/New_York")
                 for d, t in zip(recent.date, recent.event_type)]
        res = analysis.intraday_reaction(s, times)
        res.insert(1, "event", recent.event_type.values)
        print(res.to_string(index=False)); res.to_csv(f"{a.out}/intraday_{a.intraday}.csv", index=False); return

    prices = data.synthetic_daily(events) if a.demo else data.load_daily_live(a.start, a.end)
    tag = "DEMO (synthetic data)" if a.demo else "real data"
    rets = analysis.event_returns(prices, events)
    vc = analysis.volatility_comparison(prices, events)
    summary = rets.groupby(["event_type", "market", "horizon"])["ret_pct"].agg(["mean", "std", "count"]).round(3)
    fomc = analysis.fomc_by_outcome(rets)

    rets.to_csv(f"{a.out}/event_returns.csv", index=False)
    vc.to_csv(f"{a.out}/volatility_comparison.csv", index=False)
    summary.to_csv(f"{a.out}/summary.csv")
    plot_vol(vc, f"{a.out}/vol_ratio.png", f"Event-day move vs normal day - {tag}")
    plot_paths(prices, events, f"{a.out}/paths.png", tag)
    print(f"== {tag} ==\n\nVolatility vs normal days:\n{vc.to_string(index=False)}\n\nFOMC day-0 by outcome:\n{fomc}")


if __name__ == "__main__":
    main()
