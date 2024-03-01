---
date: 2024-03-01
publishdate: 2024-03-01
title: Building a Scalable Accounting Ledger
summary: How to use an analytics database to build a ledger that can handle millions of rows.
tags: ["Engineering"]
---

A number of [blog](https://beancount.github.io/docs/the_double_entry_counting_method.html#double-entry-bookkeeping) [posts](https://www.moderntreasury.com/journal/accounting-for-developers-part-i) have come to light explaining the basics of double-entry accounting for developers. I aim to share a simple - and elegant, I think - database schema for recording and tabulating ledger entries.

Engineers tend to hand-wave over accounting terminology, dispensing with terms like “debit” and “credit” - after all, why not just use positive and negative numbers? I think this leads to confusing results. Take this example from ledger-cli’s [documentation](https://www.ledger-cli.org/3.0/doc/ledger3.html#Stating-where-money-goes):

> "When you look at the balance totals for your ledger, you may be surprised to see that Expenses are a positive figure, and Income is a negative figure. It may take some getting used to, but…"

I understand the argument: since the normal balance for income is credit, and ledger-cli represents credits as negative numbers, then income would be show as negative. But this is not consistent at all with how financial statements are prepared.

So let’s design a system which can be easily modeled in a database and consistent with how actual accounting is done.

## Database Choice Matters

If you're building an application with millions of transactions, you'll inevitably
find that calling SUM() on these columns is plain old slow. One way to solve this is
to pre-aggregate data, perhaps by day, and store it in a separate table. This can be
done in the application, materialized views, or triggers.

Another option is to use a column-oriented database like Clickhouse. That's what we've chosen here:
we prefer to keep the data model simple and use the technology to process data quickkly rather
than complicate how data gets inserted.

## The Chart of Accounts

The first thing we want to define is our list of accounts. Our accounts table has 3 columns:

- **Name**. The name of the account (Assets, Liabilities, etc)
- **Number**. Often, accounts are assigned a number hierarchy. For example: 100 Assets, 101 Cash, 106 Accounts Receivable, etc. The useful thing here is we can roll up the value of sub-accounts by using place value. We’ll get to an example later.
- **Normal balance**. In our schema, we define `1` for credit and `-1` as debit. The user never sees this! But it is convenient for arithmetic.

Here’s our table, using SQLite:

``` sql
CREATE TABLE "accounts" (
    "name"      TEXT,
    "number"    INTEGER,
    "normal"    INTEGER
)
```

And we’ll populate it with some accounts:

| name               | number | normal |
|--------------------|--------|--------|
| Assets             | 100    | 1      |
| Cash               | 110    | 1      |
| Merchandise        | 120    | 1      |
| Liabilities        | 200    | -1     |
| Deferred Revenue   | 210    | -1     |
| Revenues           | 300    | -1     |
| Expenses           | 400    | 1      |
| Cost of Goods Sold | 410    | 1      |
| Equity             | 500    | -1     |
| Capital            | 510    | -1     |

Note that Cash and Merchandise roll up into Assets (likewise for other sub-accounts.) All Asset accounts are in the “100” range. This is [typical](https://www.accountingtools.com/articles/chart-of-accounts-numbering.html) for how firms set up their chart of accounts.

This schema is already useful! Just based on knowing our accounts and their normal balances, we can derive the accounting equation:

``` sql
SELECT
  group_concat(name , ' + ') AS expression
FROM accounts
GROUP BY normal;
```

| expression                                                   |
|--------------------------------------------------------------|
| Liabilities + Revenues + Equity + Deferred Revenue + Capital |
| Assets + Expenses + Cash + Merchandise + Cost of Goods Sold  |

Each line is one side of the equation. This is a rather, erm, comprehensive rendition of that equation. We can just get the high-level accounts by selecting those which are divisible by 100. The arithmetic is pretty nifty, and lets us roll up data as granularly as we like.

``` sql
SELECT group_concat(name, ' + ') AS expression
FROM accounts
WHERE number % 100 = 0
GROUP BY normal;
```

| expression                      |
|---------------------------------|
| Liabilities + Revenues + Equity |
| Assets + Expenses               |

Much better! With a little more SQL we can output the equation itself:

``` sql
select 
  max(left_side) || ' = ' || max(right_side) as equation 
from 
  (
    select 
      group_concat(
        case when normal == 1 then name end, ' + '
      ) as left_side, 
      group_concat(
        case when normal == -1 then name end, ' + '
      ) as right_side 
    from 
      accounts 
    where 
      number % 100 == 0 
    group by 
      normal
  );
```

## Transactions

Now that we have a workable chart of accounts, let’s add transactions. Our transactions table is straightforward.

``` sql
CREATE TABLE "transactions"
  (
     "id"        INTEGER, 
     "date"      TEXT,
     "amount"    REAL,
     "account"   INTEGER,
     "direction" INTEGER
  ) 
``` 

- **Transaction ID**. This will identify all single-entry items (debits+credits) which make up a single transaction.
- **Date**. The transaction date.
- **Amount**. The dollar amount for the transaction. This is usually a positive number - we do not use negative numbers to represent credits, there is a separate column for that.)
- **Account**. This is the account number (ie, 110 for Cash) for this transaction’s line item.
- **Direction**. We choose `1` for debit and `-1` for credit, as before. This is a handy convention for arithmetic.

### Example Transactions

For our example, we’ll record a number of ledger entries to show an opening account balance, buying inventory, and then selling the inventory to a customer. This post won’t go into the accounting explanation for each transaction (stay tuned!) but shows how to use this data to do basic queries.

<script src="https://snippets.journalize.io/snippets/js/59f9f5a426ec.js"></script>

In our DB, we add the following rows:

| id | date       | amount | account | direction |
|----|------------|--------|---------|-----------|
| 0  | 2022-01-01 | 500.0  | 110     | 1         |
| 0  | 2022-01-01 | 500.0  | 510     | -1        |
| 1  | 2022-01-01 | 100.0  | 120     | 1         |
| 1  | 2022-01-01 | 100.0  | 110     | -1        |
| 2  | 2022-02-01 | 15.0   | 110     | 1         |
| 2  | 2022-02-01 | 15.0   | 210     | -1        |
| 3  | 2022-02-05 | 15.0   | 210     | 1         |
| 3  | 2022-02-05 | 15.0   | 300     | -1        |
| 4  | 2022-02-05 | 3.0    | 410     | 1         |
| 4  | 2022-02-05 | 3.0    | 120     | -1        |

Note there are multiple rows with the same ID. This is because both rows are part of the same transaction - the entirety of that transaction must have debits = credits.

Breaking down transaction `0`:

- The amount is for $500.
- The first line is a debit, denoted as `direction=1`. The account is Cash, as the account number `110` matches with our accounts table. Because Cash shares the same prefix as “Assets” then this transaction rolls up to the “Assets” account.
- The second line is a credit, denoted as `direction=-1`. Similarly, the account number `510` is Capital, which is an Equity account.

## Querying Transactions

Now that we have a full set of ledger entries, let’s run some SQL queries! These are all surprisingly understandable - dare I say elegant. The schema preserves the norms of accounting, the DB operations are cheap, and the output is consistent with any standard accounting statement.

### JOIN Transactions with Account details

This is a basic query to show transaction and account information.

``` sql
select
  *
from
  transactions
  left join accounts on transactions.account = accounts.number;
```

| id | date       | amount | account | direction | name               | number | normal |
|----|------------|--------|---------|-----------|--------------------|--------|--------|
| 2  | 2022-02-01 | 15.0   | 110     | 1         | Cash               | 110    | 1      |
| 2  | 2022-02-01 | 15.0   | 210     | -1        | Deferred Revenue   | 210    | -1     |
| 3  | 2022-02-05 | 15.0   | 210     | 1         | Deferred Revenue   | 210    | -1     |
| 3  | 2022-02-05 | 15.0   | 300     | -1        | Revenues           | 300    | -1     |
| 1  | 2022-01-01 | 100.0  | 110     | -1        | Cash               | 110    | 1      |
| 1  | 2022-01-01 | 100.0  | 120     | 1         | Merchandise        | 120    | 1      |
| 4  | 2022-02-05 | 3.0    | 120     | -1        | Merchandise        | 120    | 1      |
| 4  | 2022-02-05 | 3.0    | 410     | 1         | Cost of Goods Sold | 410    | 1      |
| 0  | 2022-01-01 | 500.0  | 510     | -1        | Capital            | 510    | -1     |
| 0  | 2022-01-01 | 500.0  | 110     | 1         | Cash               | 110    | 1      |

### Verifying debits = credits

This query helps us verify that, overall, debits and credits match.

``` sql
select
  sum(case when direction == 1 then amount end) as DR,
  sum(case when direction == -1 then amount end) as CR
from
  transactions;
```

| DR    | CR    |
|-------|-------|
| 633.0 | 633.0 |

Debits and credits should sum to 0. We can verify this like so:


``` sql
select
  sum(direction * amount)
from
  transactions;
```

| sum(direction * amount) |
|-------------------------|
| 0.0                     |

What if we want to find transactions where debits and credits don’t match? 

``` sql
select
  id,
  sum(direction * amount) as s
from
  transactions
group by
  id
having
  s != 0;
```

### Balances

Putting together a balance sheet is easy:

``` sql
select
  (account) as a,
  name,
  sum(amount * direction * normal) as balance
from
  transactions
  left join accounts on a = accounts.number
group by
  name
order by
  a,
  name;
```

| a   | name               | balance |
|-----|--------------------|---------|
| 110 | Cash               | 415.0   |
| 120 | Merchandise        | 97.0    |
| 210 | Deferred Revenue   | 0.0     |
| 300 | Revenues           | 15.0    |
| 410 | Cost of Goods Sold | 3.0     |
| 510 | Capital            | 500.0   |

The most important part of this query is `SUM(amount * direction * normal)`. This ensures we are correctly increasing and decreasing our balances, and ensures the balance is positive.

What if we want a report with the sub-accounts rolled into the main ones? We can use arithmetic to find the parent account number.

``` sql
select
  ((account / 100) * 100) as a,
  name,
  sum(amount * direction * normal) as balance
from
  transactions
  left join accounts on a = accounts.number
group by
  name
order by
  a,
  name;
```

| a   | name        | balance |
|-----|-------------|---------|
| 100 | Assets      | 512.0   |
| 200 | Liabilities | 0.0     |
| 300 | Revenues    | 15.0    |
| 400 | Expenses    | 3.0     |
| 500 | Equity      | 500.0   |


Here, we've rolled up Cash and Merchandise under Assets.

Finally, here’s how we can display all transactions in a human-readable way:

``` sql
select
  id,
  date,
  name,
  case when direction == 1 then amount end as DR,
  case when direction == -1 then amount end as CR
from
  transactions
  left join accounts on account = accounts.number
order by
  id,
  date,
  CR,
  DR;
```

| id | date       | name               | DR    | CR    |
|----|------------|--------------------|-------|-------|
| 0  | 2022-01-01 | Cash               | 500.0 |       |
| 0  | 2022-01-01 | Capital            |       | 500.0 |
| 1  | 2022-01-01 | Merchandise        | 100.0 |       |
| 1  | 2022-01-01 | Cash               |       | 100.0 |
| 2  | 2022-02-01 | Cash               | 15.0  |       |
| 2  | 2022-02-01 | Deferred Revenue   |       | 15.0  |
| 3  | 2022-02-05 | Deferred Revenue   | 15.0  |       |
| 3  | 2022-02-05 | Revenues           |       | 15.0  |
| 4  | 2022-02-05 | Cost of Goods Sold | 3.0   |       |
| 4  | 2022-02-05 | Merchandise        |       | 3.0   |

## Streaming with Scratch Data

Finally, one can ask: how do we get all of this data into our database? If using a 
data warehouse (Clickhouse, Snowflake, etc) then it's impossible to do individual 
INSERT statements every time a transaction happens. You end up setting up a nightly 
bulk load process.

What if you could stream journal entries in as transactions happen in real time? You could
have up-to-the-minute balance sheets. Thankfully, Scratch Data makes this really easy.

You can stream data to Scratch and we will automatically collect it, create database
schemas, and safely batch insert.

### Streaming Stripe and Shopify Data

Stripe and Shopify have webhooks to track every transaction. With our
API endpoints, you can set Scratch Data as a webhook destination and every
transaction will stream into the database in real time. Check out our blog
posts for [Stripe](/blog/stripe-data-ingest/) and [Shopfiy](/blog/shopify-data-ingest/) as examples.


### Streaming From Code

If you want to stream data from code - perhaps you have your own webhook, or
application code - this is really easy too! Here's what the JSON would look like:

``` json
{
    "date": "2022-01-01",
    "amount": 500.00,
    "account": 110,
    "direction": 1
}
```

And then POST it:

``` bash
$ curl -X POST "https://api.scratchdata.com/data?table=transactions" \
    --json '{"amount": 500.00 ...}'
```

From here, data can be streamed to your application (if you're building a 
user-facing dashboard) or as an Excel file.

## Conclusion

This is hopefully a starting point on how to design a ledgering system
which has a high chance of producing data that can be used by your finance
team using correct terminology.

If you want to learn more about how we can help you build such a system, please
[reach out](https://q29ksuefpvm.typeform.com/to/baKR3j0p#source=building_a_ledger)!
