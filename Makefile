# Short aliases for the task runner. Every target forwards to scripts/lab.py:
#   make setup                       == python3 scripts/lab.py setup
#   make backtest ARGS="--period oos" == python3 scripts/lab.py backtest --period oos
# scripts/lab.py is the real tool (it also works where `make` is missing).
PY ?= python3

.PHONY: help
help:
	@$(PY) scripts/lab.py --help

# Stop make from trying to "rebuild" the Makefile through the catch-all rule below.
Makefile: ;

%:
	@$(PY) scripts/lab.py $@ $(ARGS)
