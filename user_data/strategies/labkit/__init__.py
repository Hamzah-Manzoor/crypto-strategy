"""Shared code for lab strategies.

Lives in a sub-package on purpose: Freqtrade only scans the top level of
user_data/strategies/ for strategy classes, so nothing in here is ever listed
or run as a strategy. Strategy files import it with `from labkit... import ...`.
"""
