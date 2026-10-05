# Decisions

Short log of key decisions and why. Newest at the bottom. Format: **date: decision.** Why.

---

**2026-10-06: Use Freqtrade as the engine.**
- It's mature, open source and Python. It has backtesting, hyperopt (auto-tuning), dry-run, lookahead/recursive bias checks and a web UI (FreqUI) built in.
- Writing our own engine would mean spending time on plumbing instead of strategy quality.

**2026-10-06: Run everything through Docker Compose.**
- Same engine on every machine, nothing to install except Docker, and the Python on the Mac stays untouched.
- Each paper-trading bot is its own container.

**2026-10-06: Pin `freqtradeorg/freqtrade:2026.9` by tag *and* digest (`sha256:989aff56…`).**
- 2026.9 was the latest stable release (29 Sep 2026) and has an arm64 build for Apple Silicon.
- A tag can be re-pushed. The digest can't, so the engine never changes under us.
- Upgrading means a deliberate change logged here, followed by a reference backtest.

**2026-10-06: Binance spot data, with Bybit then OKX as fallbacks.**
- Binance has the deepest liquidity and longest public history for these pairs.
- If downloads fail (for example a region block), override configs `exchange-bybit.json` / `exchange-okx.json` switch the data source without editing `base.json`.

**2026-10-06: Static whitelist BTC, ETH, SOL, BNB, XRP / USDT.**
- They're liquid, so a backtest at "candle open" prices is not far from reality.
- The list is static so results are repeatable. A dynamic "top volume" list changes every day, so a backtest couldn't be re-run with the same pairs.

**2026-10-06: Spot only, long only, no leverage.**
- Keeps the risk simple to reason about while we learn what works.
- Futures add funding fees, liquidations and shorting rules.

**2026-10-06: Fee 0.1% per side in every run, plus a 0.15% stress run.**
- 0.1% is Binance's standard spot fee without discounts.
- Freqtrade doesn't simulate slippage (getting a worse price than expected), so the 0.15% stress run stands in for it.

**2026-10-06: Market orders, priced from the "other" side of the order book.**
- A backtest assumes you buy at the candle's price.
- Market orders in dry-run behave closest to that assumption, so paper results and backtests are comparable.

**2026-10-06: Equal split of the wallet, 5 open trades max (`stake_amount: unlimited`).**
- Starting wallet is 1000 USDT. Each new trade gets an equal share of the free balance, so profits compound.
- With 5 pairs and 5 slots, no pair is ever starved. The buy-and-hold baseline naturally becomes "20% in each coin".

**2026-10-06: The FreqUI API block lives only in the per-bot dry-run configs; its secrets live only in `.env`.**
- Freqtrade 2026.9 requires `jwt_secret_key` to be 32+ characters whenever an `api_server` block exists.
- Keeping the block out of `base.json` means backtests don't need it. The bots get username, password and JWT secret from `.env` through `FREQTRADE__API_SERVER__*` variables.

**2026-10-06: Three layers of safety checks.**
1. `lab.py` runs `safety_check.py` before starting anything.
2. The compose `safety` service runs it inside Docker, and every Freqtrade service depends on it. So even a raw `docker compose run` refuses to start.
3. The git pre-commit hook runs it and blocks data, logs, DBs and `.env`.
- Bots will also run `trade --dry-run`, which makes Freqtrade itself strip exchange secrets and simulate trades.

**2026-10-06: Host scripts use the Python standard library only.**
- Nothing to pip install on the Mac.
- Anything that needs pandas runs inside the Freqtrade container, which already has it.

**2026-10-06: Hyperopt never auto-exports parameters next to the strategy (`disableparamexport`).**
- Freqtrade silently loads `<Strategy>.json` if it sits next to a strategy file. Then two backtests of the "same" strategy can use different settings without anyone noticing.
- Tuned params go into a new versioned class instead (`EmaTrendV2`), so the code always shows exactly what ran.
