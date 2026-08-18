# Categorization FAQ

Questions the Finance Platform team gets asked most often. Started during the
v1 rollout and added to since; some answers are older than others.

### Why did my expense end up in the wrong category?

Almost always evaluation order. Rules are checked one after another and the
first one that matches wins, so a merchant that could plausibly belong to two
categories lands in whichever rule runs first.

### What order are the rules evaluated in?

Rule modules are evaluated alphabetically by module name: `meals`, `office`,
`subscriptions`, `travel`. That ordering was chosen so it would stay stable
when new modules were added without anyone having to maintain a list by hand.

### What happens to an expense that matches nothing?

It gets the category `other` and is excluded from the monthly report totals so
it cannot distort the category percentages. Ask an analyst to add a keyword if
you see the same merchant fall through twice.

### Why is my Uber Eats order showing up as travel?

Because `travel` is evaluated before `meals` and both match on the `uber`
prefix. Put the words "team lunch" or "client dinner" in the memo and the meal
rule will pick it up instead.

### How are refunds handled?

A negative amount is treated as a credit. It is categorized as `refund` and
never reaches the rule modules, so a refunded flight does not net out against
the travel total; it appears as its own line in the report.

### Are amounts stored as dollars or cents?

Dollars, as a float, in `Expense.amount`. Round to two decimal places before
comparing two amounts, since float arithmetic will occasionally give you
`48.899999999999999`.

### Does the memo field affect categorization?

Yes. Each rule module has a small list of memo phrases it also matches on, such
as "team lunch" for meals or "annual license" for subscriptions. The memo is
only consulted after the merchant keywords fail to match.

### Can I add a keyword without a deploy?

Yes. Edit `ledgerline/rules_table.json` and the nightly job will pick it up on
its next run. Code changes are only needed for a brand new category.

### Why do merchant names look mangled in the report?

They are not mangled, they are raw. The card processor prefixes merchants with
its own routing string (`SQ *`, `TST*`) and appends store numbers. The engine
strips all of that internally before matching, but the report prints the
original string so you can search for it in the card portal.

### Who owns category policy?

Finance owns which categories exist and what belongs in them. The Finance
Platform team owns the code. If you disagree with a categorization, raise it
with finance first; do not just add a keyword.
