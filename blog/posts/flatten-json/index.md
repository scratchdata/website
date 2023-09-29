---
date: 2023-09-29
publishdate: 2023-09-29
title: Flattening and Denormalizing JSON
summary: How to denormalize JSON to make it SQL-friendly
tags: ["Engineering"]
---

JSON data is not friendly to relational databases. While many DBs support 
JSON extraction - most DBs, from SQLite to Postgres have JSON functions - you often
end up doing table scans to parse this data. With OLAP databases,
you gain the most efficiency when value is in its own column. Let's talk about
how to denormalize JSON.

## Denormalizing nested items

Start with this structure:

``` json
{
  "name": "John Doe",
  "age": 21,
  "courses": [
    {"courseName": "Mathematics", "grades": [88, 90, 94]},
    {"courseName": "Physics", "grades": [92, 85, 100]}
  ]
}
```

The goal is to represent this data in a table without any sort of nested structure.
The tricky part is how to deal with arrays.

## Option 1: Separate Column per Array Element

The most common approach is to create a new column for every array element.
In our case, we have a single row to represent this object. We end up with
columns names like `courses_1_grades_0` to represent `courses[1].grades[0]`.

I personally find this confusing - after all, now I need a new column every time
there is a new array element - but you can infer, from column names, the structure
of data. This also lets you use a mongo-like syntax for fetching data from specific
array elements.

```
| courses_1_grades_0 | name     | courses_0_courseName | courses_0_grades_2 | courses_1_courseName | courses_1_grades_1 | age | courses_0_grades_0 | courses_0_grades_1 | courses_1_grades_2 |
|--------------------|----------|----------------------|--------------------|----------------------|--------------------|-----|--------------------|--------------------|--------------------|
| 92                 | John Doe | Mathematics          | 94                 | Physics              | 85                 | 21  | 88                 | 90                 | 100                |
```

The algorithm to do this is pretty simple:

``` python
def flatten(j, path=None):
  if path is None:
      path = []
  if isinstance(j, dict):
      for k, v in j.items():
          f(v, path+[k])
  elif isinstance(j, list):
      for i, item in enumerate(j):
          f(item, path+[i])
  else:
      print(path, j)
```

## Option 2: Denormalize each array element to separate row

This is my preferred approach for storing denormalized JSON. In this case, we 
take the cartesian product of the parent and child arrays (`courses` and `grades`)
to have one row per line. While we do repeat data (`age`, `courseName`, and `name`),
this is not a problem in OLAP databases where we don't physically repeat each
value on disk.

```
| age | courses_courseName | courses_grades | name     |
|-----|--------------------|----------------|----------|
| 21  | Mathematics        | 88             | John Doe |
| 21  | Mathematics        | 90             | John Doe |
| 21  | Mathematics        | 94             | John Doe |
| 21  | Physics            | 92             | John Doe |
| 21  | Physics            | 85             | John Doe |
| 21  | Physics            | 100            | John Doe |
```

This also makes it easy to use normal SQL queries. To get a student's 
grade we can do this:

``` sql
SELECT courses_courseName, AVG(courses_grades) FROM students GROUP BY courses.courseName
```

This can create slightly more complicated queries as we need to avoid calculating
the average age multiple times for the same student:

``` sql
SELECT AVG(DISTINCT_AGE) as AVG_AGE
FROM (
    SELECT DISTINCT name, age as DISTINCT_AGE
    FROM students
)
```

Here's an algorithm to do this in Python. Many thanks to my friend
[Francis](https://www.linkedin.com/in/francis-sirizzotti-b649b135/) who 
helped me get a working implementation!


``` python
def parse(obj, path = None):
  if path is None:
    path = []
  if isinstance(obj, list):
    return [p for i in obj  for p in parse(i, path) ]
  if isinstance(obj, dict):
    return cross_product([parse(v, path + [k]) for k, v in obj.items()])
  return [{tuple(path): obj}]

def cross_product(dicts):
  if len(dicts) == 0:
    return [{}]
  return [ {**lhs, **rhs} for lhs in dicts[0] for rhs in cross_product(dicts[1:])]
```

## Support in ScratchDB

**We support both of these ways to denormalize JSON**. By default, we do option 1,
creating new columns for each array element. This is the least surprising to users,
as it ensures there is exactly 1 row of ouptut per row of input.

However, if you supply `?flatten=explode` as a parameter when inserting data, 
we will use option 2 and "explode" the input into all combinations of all
nested array elements.

## What is ScratchDB?

[ScratchDB](https://github.com/scratchdata/ScratchDB) is an open-source 
data warehouse. It completely simplifies the process of ingesting data and
managing Clickhouse servers.

You can send any JSON you want and we automatically create tables based on
what you've sent.

ScratchDB is aimed at making it easy to do the simplest thing: capture data to analyze 
later. Managing JSON is one of the many ways we smoothen the developer experience
of analyzing data.