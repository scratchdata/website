---
date: 2024-04-18
publishdate: 2024-04-18
title: Sync Data with your Customers' Warehouse
summary: Scratch Data lets you push and pull data to your customers' warehouse.
tags: ["Launches"]
---

Stripe has an enterprise [feature](https://stripe.com/data-pipeline) where they will, for
the low, low price of $0.03 per transaction, copy your financial data from
your hard-earned sales in your own database. Otherwise you have to figure out how to do 
it yourself from their dashbaord.

Enterprises are willing to pay for this because they already have a dashboard that has
all their other business numbers and would rather pay an engineer to write LookML rather
than give anyone a Stripe login.

What if you could also sell this to your enterprise customers? Now you can.
**Scratch Data lets you connect to your customers' data warehouse.**

## How do I connect to my customers' database?

It is absurdly simple.

1. Send your customer a private URL that lets them fill in their DB connection details.
2. Use Scratch Data's API to safely stream data to and from their database.
3. ???
4. Profit.

Here's what it looks like:

![Set up external connection](setup_connection.gif)

## How do I move data into their database?

There are two ways to do it. You can copy data directly from your own DB without 
exposing any of the underlying tables or you can stream in real time.

### How do I copy data from one database to another?

To copy data from your own DB to a customer's, make the following API call:

```
$ curl -X POST "/api/data/copy?api_key=x" \
    --data '{"query": "select * from events", "destination_id": 3, "destination_table": "events"}'
```

We will run the query against your DB, automatically create tables in your customer's database, and
and batch insert the rows. All of this runs in the background.

### How do I stream data to a data warehouse?

If you want to stream data in realtime to your customer's warehouse, all you need is REST:

```
$ curl -X POST "/api/data/insert/events?api_key=x" \
    --data '{"user": "alice", "event": "click"}'
```

### How do I query data from their warehouse?

If you want to move data from the external database to your own, you can use the same `/copy` endpoint. 
You can also make queries like so:

```
curl -G "/api/data/query" \
     --data-urlencode="api_key=x" \
     --data-urlencode="query=select * from events" 
```

## Conclusion

Scratch Data makes it incredibly easy to build applications on top of 
your warehouse. We think this is a huge unlock for folks with demanding
enterprise clients. [Check us out!](https://app.scratchdata.com?source=sync-data-with-customers)
