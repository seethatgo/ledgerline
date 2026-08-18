"""Rule modules.

Every module in this package exposes the same two names:

    CATEGORY_NAME    the category string this module assigns
    matches(expense) True when the expense belongs to that category

Adding a module here does nothing on its own; it also has to be listed in
RULE_MODULES in ledgerline/engine.py.
"""
