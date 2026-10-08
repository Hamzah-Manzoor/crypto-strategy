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
| `Found orphan containers ([crypto-lab-bot-…])` warning | Harmless. The paper bots are defined in the second compose file (`docker-compose.bots.yml`), so commands that only load `docker-compose.yml` don't know them. **Don't add `--remove-orphans`**: it would delete the running bots (`bots up` would bring them back, with their paper trades kept). |
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

**Extra history (added 2026-10-07 for the quarterly re-tuning test):**
- **What:** 1h and 4h for all 5 pairs now go back to **2020-08-11** (SOL's Binance listing). 1h: 53,928 candles per pair, 99.96% coverage. 4h: 100% coverage.
- **Gaps:** 20 hours missing in the 1h files, from short Binance outages in 2020–2023. The longest is 4h, on 21 Dec 2020 and 13 Aug 2021. Freqtrade fills such gaps in backtests.
- **Report:** `results/checks/data_check_20200811_1h-4h.md`.
- **Command:** `python3 scripts/lab.py download --start 20200811 --timeframes 1h 4h`.

**Exam history (added 2026-10-08 for the Round 4 exam on 2019–2020):**
- **What:** 1h and 1d for BTC, ETH, BNB and XRP now go back to **2018-05-01**. XRP starts on its Binance listing, 2018-05-04.
- **Coverage:** 99.88%. The longest gap is 10h (short Binance outages). SOL has no data before 2020-08-11, so it isn't downloaded for this period.
- **Report:** `results/checks/data_check_20180605_1h-1d_BTC-ETH-BNB-XRP.md`. The check starts at 2018-06-05: the 200-day Bitcoin average needs that much history before 2019-01-01.
- **Command:** `python3 scripts/lab.py download --start 20180501 --timeframes 1h 1d --pairs BTC/USDT ETH/USDT BNB/USDT XRP/USDT`.
- **2019–2020 is protected test data** (`exam2019`): don't backtest on it outside the pre-registered exam.

- **All 5 pairs passed:** 100% coverage, no duplicates, no impossible candles and no zero-volume filler candles. Binance's candles needed no repairs.
- **Data size:** 63 MB.
- **Full report:** `results/checks/data_check.md`.
- **The check really does fail on bad data.** As a one-off test, a copy of the 1h data was corrupted on purpose: 2 days deleted from ETH, a duplicate added to SOL, a BTC candle made impossible. The check flagged all three and exited with code 1.

**Network check from Pakistan (2026-10-06):**
- `api.binance.com` and `data.binance.vision` work, so Binance is used.
- `api.bybit.com` works, and a real test download through `exchange-bybit.json` succeeded, so Bybit is a working fallback.
- `www.okx.com` doesn't resolve (DNS failure), so OKX isn't usable from this connection.

## Paper-trading bots (Phase 7)

Every bot is a **dry-run** Freqtrade: live Binance prices, a fake 1000 USDT wallet, no API keys. The list of bots lives in `user_data/configs/bots.json`:

| Bot | Strategy | FreqUI | Role |
|---|---|---|---|
| `ema-trend-v2` | `EmaTrendV2` | http://127.0.0.1:8081 | **watch list**: passed Stage 1, failed Stage 2, so it's *not* promoted |
| `buy-hold` | `BuyHoldV1` | http://127.0.0.1:8082 | baseline: buy & hold from the same start day |

```bash
python3 scripts/lab.py bots up        # safety check, generate configs, start, wait, show status
python3 scripts/lab.py bots status    # state, dry_run, open/closed trades, profit per bot
python3 scripts/lab.py bots logs      # last 50 log lines per bot (--tail N)
python3 scripts/lab.py bots down      # stop and remove the containers (databases are kept)
```

- **Add or remove a bot:** edit `bots.json` (name, strategy, port, status, reason), then run `bots up`. Generated files (`docker-compose.bots.yml`, `user_data/configs/dryrun/*.json`) are rewritten; never edit them by hand.
- **Own files per bot:** each bot keeps its own database `user_data/db/<bot>.sqlite` and log `user_data/logs/<bot>.log`, all git-ignored.
  - Paper trades survive restarts.
  - To restart a bot from a fresh wallet: `bots down <bot>`, delete its `.sqlite*` files, then `bots up <bot>`.
- **After a Mac restart:** bots come back with Docker Desktop (`restart: unless-stopped`). They reuse the container exactly as it was created, including its `--dry-run` flag. Any config change only takes effect through `bots up`, which runs the safety check again.

### FreqUI (the web dashboard)

1. Open http://127.0.0.1:8081.
2. Log in with `FREQTRADE__API_SERVER__USERNAME` and `FREQTRADE__API_SERVER__PASSWORD` from `.env` (`cat .env`).
3. To see all bots in one tab: in FreqUI, open the bot menu, choose **Add new bot**, and enter `http://127.0.0.1:8082` with the same login. Every bot already allows the others' addresses (`CORS_origins`).

The ports are bound to `127.0.0.1`, so FreqUI only opens on this Mac, not from your Wi-Fi network.

### Telegram alerts (optional, off by default)

1. In Telegram, talk to **@BotFather** and run `/newbot`. Keep the token it gives you.
2. Send any message to your new bot. Then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat.id`.
3. Create a file for **that one bot**. It's git-ignored, and the safety check still scans it.
   ```bash
   cat > .env.bot-ema-trend-v2 <<'X'
   FREQTRADE__TELEGRAM__ENABLED=true
   FREQTRADE__TELEGRAM__TOKEN=123456:ABC...
   FREQTRADE__TELEGRAM__CHAT_ID=987654321
   X
   chmod 600 .env.bot-ema-trend-v2
   ```
4. Run `python3 scripts/lab.py bots up ema-trend-v2`.

- **Use one Telegram bot (token) per Freqtrade bot.** Two programs reading the same token fight over its messages; Telegram answers "Conflict: terminated by other getUpdates request".
- **What was tested:** Freqtrade accepts these three variables, as confirmed by its config validation with a fake token.
- **Not tested end-to-end:** that needs your own Telegram token. After step 4, check `bots logs` for Telegram errors.
- **A Telegram token can't touch an exchange.** There are no exchange keys anywhere, so the worst a leaked token allows is reading and controlling a *paper* bot. Still keep it private.
