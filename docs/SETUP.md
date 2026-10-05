# Setup

Written for **macOS** (tested on macOS 26.5, Apple Silicon). Linux works the same way. On Windows, use the same `python` commands (no `make` needed) from PowerShell with Docker Desktop.

## 1. Install the tools

| Tool | Why | Check it |
|---|---|---|
| **Docker Desktop** | Runs Freqtrade in a container, so nothing trading-related is installed on your Mac | `docker info` prints a server version |
| **Python 3.10+** | Runs the task runner (`scripts/lab.py`, standard library only, nothing to pip install) | `python3 --version` |
| **git** | Version control (comes with Xcode Command Line Tools) | `git --version` |

Docker Desktop must be **running** (whale icon in the menu bar, "Engine running") before any lab command.

Docker Desktop settings that are enough for this lab: **4+ CPUs, 6+ GB memory, 20 GB disk** (Settings → Resources). Hyperopt uses every CPU you give it.

## 2. First-time setup

```bash
cd ~/Desktop/crypto-strategy
python3 scripts/lab.py setup
```

What `setup` does:
- checks Python, Docker and Docker Compose
- creates `user_data/{data,backtest_results,hyperopt_results,logs,db,walkforward}` (all git-ignored)
- creates `.env` from `.env.example` with a random FreqUI password and JWT secret (git-ignored, file mode 600)
- turns on the git pre-commit hook (`git config core.hooksPath scripts/hooks`)
- runs the safety check
- pulls the pinned image `freqtradeorg/freqtrade:2026.9@sha256:989aff56…` (about 1.3 GB on disk) and prints its version

## 3. Download price data

```bash
python3 scripts/lab.py download
```

- **What:** BTC, ETH, SOL, BNB, XRP against USDT, spot, on **5m, 15m, 1h and 4h** candles from **2023-05-01** to now. The first 5 months before the in-sample start (2023-10-01) are warm-up only: 600 warm-up candles on 4h need 100 days. It also downloads **BTC/USDT daily from 2022-01-01**, which is only used to label market regimes (a 200-day average needs 200 days of history first).
- **Where:** `user_data/data/binance/*.feather` (about 50 MB, git-ignored).
- **How long:** about 1 minute. Freqtrade pulls Binance's bulk public files from `data.binance.vision`, no API key needed.
- **Topping up:** run the same command again. Pass 1 (`--prepend`) extends files back to the start date if needed; pass 2 fetches only candles newer than what you already have.
- When the download finishes, it automatically runs the **data check**.

### Data check

```bash
python3 scripts/lab.py data-check
```

For each pair × timeframe it reports the first and last candle, missing candles, the longest gap, duplicates and "impossible" candles (for example a high below the close). The result is saved to `results/checks/data_check.md`.

**It fails if:**
- data starts after 2023-05-01
- coverage is under 98%
- any gap is longer than 24 hours
- there are duplicate timestamps or impossible candles

It **warns** if the last candle is more than 3 days old.

### Market regimes

```bash
python3 scripts/lab.py regimes
```

Picks a **bull**, a **bear** and a **sideways** 90-day window **inside each split**: in-sample for development, out-of-sample for the final check only. It saves them to `results/regimes.json`, so backtests can use `--period bull-is` and so on. Windows are judged on the equal-weight 5-coin basket, because that's what the strategies trade. The full method and the month-by-month table are in `results/checks/regimes.md`.

## Troubleshooting

### Docker
| Symptom | Fix |
|---|---|
| `Docker is installed but not running` / `Cannot connect to the Docker daemon` | Open Docker Desktop and wait for "Engine running". |
| `service "safety" didn't complete successfully: exit 1` | The safety check failed inside Docker. See why with `docker compose logs safety`, or run `python3 scripts/lab.py safety`. Fix the config; don't bypass the check. |
| Very slow backtests / hyperopt | Give Docker more CPUs and memory (Settings → Resources). |
| `no space left on device` | `docker system prune` removes old containers and images. The pinned image is pulled again by `setup`. |
| Permission errors writing `user_data/` | Docker Desktop on macOS maps file ownership automatically. On Linux, run `sudo chown -R 1000:1000 user_data results` (the container user is `ftuser`, uid 1000). |

### Data download
| Symptom | Fix |
|---|---|
| `download from binance failed` or HTTP **451 / 403** errors (region block) | Use the fallback: `python3 scripts/lab.py download --exchange bybit`. The `exchange-bybit.json` override switches the data source. Later commands pick the exchange you have data for automatically, or set `LAB_EXCHANGE=bybit`. |
| Bybit also fails | `--exchange okx` is the second fallback. **Note:** on 2026-10-06 `www.okx.com` didn't even resolve (DNS failure) from this network in Pakistan, while Binance and Bybit worked. A VPN or another DNS server might help, but check local rules first. |
| `data check failed: coverage …` or `gap of …h` | Usually a temporary exchange outage, or a partial download that was interrupted. Re-run `download`. If a real exchange outage left a gap, it shows the same way every time. Note it in `docs/DECISIONS.md` instead of hiding it. |
| `starts …, needed from 2023-05-01` | The pair wasn't listed yet on that exchange, or the download was cut short. Re-run `download`. |
| `stale: last candle …` (WARN) | Just run `download` again to top up. |
| Want to start over | Delete `user_data/data/<exchange>/` and run `download`. |

## Current data (downloaded 2026-10-06 from Binance)

| Timeframe | Candles per pair | Range | Missing | Longest gap |
|---|---:|---|---:|---:|
| 5m | 361,139 | 2023-05-01 → 2026-10-05 | 0 | 0h |
| 15m | 120,379 | 2023-05-01 → 2026-10-05 | 0 | 0h |
| 1h | 30,094 | 2023-05-01 → 2026-10-05 | 0 | 0h |
| 4h | 7,523 | 2023-05-01 → 2026-10-05 | 0 | 0h |
| 1d (BTC only) | 1,738 | 2022-01-01 → 2026-10-04 | 0 | 0h |

- **All 5 pairs passed:** 100% coverage, no duplicates, no impossible candles and no zero-volume filler candles. Binance's candles needed no repairs.
- **Data size:** 63 MB.
- **Full report:** `results/checks/data_check.md`.
- **The check really does fail on bad data.** As a one-off test, a copy of the 1h data was corrupted on purpose: 2 days deleted from ETH, a duplicate added to SOL, a BTC candle made impossible. The check flagged all three and exited with code 1.

**Network check from Pakistan (2026-10-06):**
- `api.binance.com` and `data.binance.vision` work, so Binance is used.
- `api.bybit.com` works, and a real test download through `exchange-bybit.json` succeeded, so Bybit is a working fallback.
- `www.okx.com` doesn't resolve (DNS failure), so OKX isn't usable from this connection.
