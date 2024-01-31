---
date: 2024-01-29
publishdate: 2024-01-29
title: DuckDB as a REST API with Named Pipes
summary: How to use named pipes to turn DuckDB into a RESTful API
tags: ["Engineering"]
---

One of the more interesting features of Scratch Data is we let you treat
your DuckDB instance as a RESTful API.

We'd written a bunch of code to  query DuckDB, buffer the results, and convert to
JSON - something particularly cumbersome in Go. However, with named
pipes, we figured out a trick to have DuckDB handle all of this for us.

## Before: Creating JSON from Scratch in Go

The first iteration of performing queries was cumbersome. The first step was 
to get a list of columns:

``` go
rows, _ := db.Query("DESCRIBE SELECT * FROM t")

for rows.Next() {
  rows.Scan(&columnName, ...)
  columnNames = append(columnNames, columnName)
}
```

Then we used DuckDB's [to_json()](https://duckdb.org/docs/extensions/json.html#json-creation-functions) 
function as a shortcut to translate from their data types to JSON:

``` go
rows, _ = db.Query("SELECT to_json(COLUMNS(*)) FROM (SELECT * FROM t)")
```

Finally, we stitched it all together. Using some magic from this
10-year-old Golang mailing list [thread](https://groups.google.com/g/golang-nuts/c/-9h9UwrsX7Q)
the code looked something like this:

``` go
pointers := make([]interface{}, len(cols))
container := make([]*string, len(cols))

for i, _ := range pointers {
  pointers[i] = &container[i]
}

hasNext := rows.Next()
for hasNext {
  err := rows.Scan(pointers...)
}

// Create JSON by combining the columnNames and our data
```

This worked but was cumbersome - DuckDB, after all, 
[already knows](https://duckdb.org/docs/guides/import/json_export.html) how to create JSON.
How could we get DuckDB to output that data not to a file on disk, but to an HTTP socket?

## Named Pipes to the Rescue!

I noticed that DuckDB does have the ability to [write to stdout](https://duckdb.org/docs/api/cli/overview.html#reading-from-stdin-and-writing-to-stdout).

The syntax looks like this:

``` sql
COPY (SELECT * FROM t) TO '/dev/stdout' WITH (FORMAT 'json', ARRAY true)
```

Does this also work with named pipes? It does! Here was a quick CLI test:

``` bash
$ mkfifo p.pipe
$ echo "COPY (SELECT * FROM t) TO './p.pipe' (FORMAT 'json', ARRAY true)" | duckdb
```

This process blocks until the pipe is read. Running `cat p.pipe` worked as expected. Now to wire it up
to our Go program:


``` go
func QueryHandler(w http.ResponseWriter, r *http.Request) {
  // Have DuckDB write to our pipe. This will block until data is read, so run
  // it in a separate goroutine
  go func() {
    db.Exec("COPY (SELECT * FROM t) TO 'p.pipe' (FORMAT JSON, ARRAY true)")
  }()

  // Open pipe for reading
  pipe, _ := os.OpenFile("p.pipe", os.O_CREATE|os.O_RDONLY, os.ModeNamedPipe)

  // Copy data directly from pipe (where duckdb is writing) to HTTP handler
  io.Copy(w, pipe)
}
```

Magic in only 3 lines of glue code!

## Conclusion

DuckDB continously delights, as its support for pipes really simplifies our JSON code.
One of the fun things about building this software is we get to pull 
all our Linux tricks out of the bag. If you have any comments or feedback, I'd love to hear them!
