# Macro Event Impact Study

How do markets react to scheduled macro events? This project measures the reaction of
equities (SPY), long bonds (TLT), the US dollar (UUP) and gold (GLD) to
**FOMC rate decisions** (14:00 New York) and **US jobs reports / NFP** (08:30 New York).

## Questions answered
1. Is the event-day move bigger than a normal day's move? (ratio + Mann-Whitney test)
2. What happens over the following 1 and 5 trading days: does the move continue or reverse?
3. Do hikes, holds and cuts produce different reactions?
4. Minutes after release: how far has the market moved after 5 / 15 / 30 / 60 minutes? (5-min data)

## Run
    pip install -r requirements.txt
    python run_study.py --demo                      # synthetic data, offline
    python run_study.py --start 2022-12-01 --end 2025-01-31   # real daily data
    python run_study.py --intraday SPY              # 5-min reaction, events in last ~60 days only

Outputs go to `output/` (CSV tables + `vol_ratio.png`, `paths.png`).

## Files
- `events.csv` - event dates. FOMC dates and rate changes are filled in for 2023-24; NFP dates for 2024. **Verify NFP dates against the BLS schedule** and extend as you like.
- `data.py` - data loading (yfinance) and a synthetic generator.
- `analysis.py` - event returns, volatility comparison, FOMC by outcome, intraday reaction.
- `run_study.py` - runs everything and saves charts.

## Method notes (write these up in your own words)
- Reaction = close of day before the event -> close k days after. Both release times fall inside day 0.
- Baseline = every other trading day in the sample, including other event types' days (small contamination; a good thing to mention).
- Hike/hold/cut is the *outcome*, not the *surprise*. Markets move on the gap vs. expectations. To improve it, add NFP actual vs consensus or fed funds futures-implied odds to `events.csv` and split on that.
- Small samples (12-16 events): treat results as indicative, and say so.
- Yahoo only gives ~60 days of 5-min bars; for older events use a broker or paid 1-min export with the same function.
- `--demo` data has volatility injected by construction; never present it as a finding.

## Extension ideas
Add US CPI, ECB decisions, a VIX column, or EUR/USD and Bund futures; regress reactions on surprise size.
