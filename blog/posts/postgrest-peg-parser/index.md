---
date: 2024-02-02
publishdate: 2024-02-02
title: PEG Parsers and PostgREST
summary: How we're bringing PostgREST's ease of use to other databases
tags: ["Engineering"]
---

**tl;dr** We're bringing the magic of [PostgREST](https://postgrest.org) to analytical 
databases. Here's how we're doing it.

PostgREST is an program that lets you treat your Postgres database
as a RESTful API. It's so powerful that it backs [Supabase](https://supabase.com).

What if we could use this for any database? What if we could access Clickhouse 
or BigQuery using REST? We've been working on building exactly that and 
learning a lot about grammars in the process.

## PostgREST Query Syntax

Postgres has a pretty intuive [syntax](https://postgrest.org/en/stable/references/api/tables_views.html)
for querying tables. For example, a query of the form `GET /people?age=gt.40 HTTP/1.1`
translates to `SELECT * FROM people WHERE age > 40`. All we needed to do was parse this query format. Easy, right?

## Parsing the PostgREST Query Syntax

It took a few iterations to make it work. Our first attempt used regex.

### regex: now we have Two Problems

``` go
pattern := `^(?P<field>[A-Za-z0-9]+)(?P<not>\.[a-z]+)?\.(?P<operator>[A-Za-z]+)(?P<modifier>\([A-Za-z]+\))?\.(?P<operand>.*)$`
```

It took a lot of effort to come up with that since we weren't very familiar with Perl regex syntax.
This became cumbersome as we tried to implement more and more features of Postgrest so 
we looked for alternatives.

### Clues from the PostgREST Source

I contacted [Joe Nelson](https://github.com/begriffs), the creator of PostgREST to ask for help, and he gave me some clues 
in the code itself. He pointed me to the grammer used in the [source](https://github.com/PostgREST/postgrest/blob/b2095a8ef601f4540f46e148ac038014720ea462/src/PostgREST/ApiRequest/QueryParams.hs) itself, 
which uses a Parsec parser combinator grammar.
This was helpful in giving me something to refer to - but my lack of Haskell, Parsec,
or parsers kept me from doing a direct translation.

But still, I could start to intuit some structure. For example, the following snippet
let me feel my way around how I might think parse a SQL "IN" statement:

``` haskell
pIn = In <$> (try (string "in" *> pDelimiter) *> pListVal)
``` 
Reading this like English, it seems like we're looking for the word "in",
followed by a delimiter, followed by some sort of list of values. This intuitively
matches what I'd expect in SQL and the Postgrest documentation.

### A round peg in a round hole

I knew there were tools like `yacc` and `lex` that were used for parsing things,
but I'd never tried them myself. Google also turned up `peg` parsers which seemed
promising. After a fumbling a bit with tutorials and experiments, I landed on [peg](https://en.wikipedia.org/wiki/Parsing_expression_grammar) as an ideal solution.

Here was my first crack at defining a grammar to parse the string `age=gt.40`:

``` txt
//         age    =  gt      .   40
Filter <- [a-z]+ '=' [a-z]+ '.' [a-z0-9]+ END
```

This literally translates to "A Filter is defined as a sequence of 
characters (age), followed by an equals sign,
followed by another sequence of characters (gt) followed by another sequence of letters and numbers (40)"

Then I refactored:

``` txt
Filter <- ColumnName '=' Predicate END

Predicate <- Operator '.' Operand

ColumnName <- String 
Operator <- String 
Operand <- String 

String <- [a-z0-9]+
END <- !.
```

With a passable grammar in hand, the next step is to write a Go program to 
parse it. There are a lot of options for this (more below) and at the moment
I've chosen [pointlander/peg](https://github.com/pointlander/peg). 

The first step is to use the library's command-line tool to generate a parser
from the grammar.

``` bash
$ peg filter.peg
```

This outputs `filter.peg.go` which we can use as follows:

``` go
expression := "age=gt.40"
filter := &Postgrest{Buffer: expression}
filter.Init()
filter.Parse()
filter.PrintSyntaxTree()
```

And here is the output:

``` text
Filter "age=gt.40"
 ColumnName "age"
  String "age"
 Predicate "gt.40"
  Operator "gt"
   String "gt"
  Operand "40"
   String "40"
```

Now that we have a useful data structure, we can construct SQL. That will be a post for
another day, but you can imagine an algorithm to traverse this tree and translate.

## The Result

The larger pull request, still in progress, is [here](https://github.com/scratchdata/ScratchDB/pull/96/files#diff-f966727801de111e3f6c8d750eaf476efd9178a5c19a0366cdaf496f6b70fcb4) and that file in particular 
shows the full grammar. It does not parse *everything* that postgrest supports, but now we have a pretty
clear path to do so. The current work, in progress, is to translate the syntax tree to SQL.

Here's a taste of what the .peg grammar looks like:

``` text
QueryString <- QueryParam? ('&' QueryParam)* END

QueryParam <- Limit / Offset / Order / Select / LogicalQuery / Filter

Select <- 'select' '=' SelectOptions
SelectOptions <- SelectOption (',' SelectOption)*
SelectOption <- Renamed ':' (SelectCount / SelectColumn) '::' Cast
              / Renamed ':' (SelectCount / SelectColumn)
              / (SelectCount / SelectColumn) '::' Cast
              / (SelectCount / SelectColumn)

// ...and so on...
```

## Resources

In go, I found popular libraries that deal with peg:

- [pointlander/peg](https://github.com/pointlander/peg)
- [mna/pigeon](https://github.com/mna/pigeon)

And another library which is useful for parsing (not peg-specific). This one
is particularly interesting because it lets you bind data directly to go 
structs:

- [alecthomas/participle](https://github.com/alecthomas/participle)

## Acknowledgements

I emailed a lot of people who are building parsers for help.

- [Joe Nelson](https://github.com/begriffs), creator of PostgREST
- [Alec Thomas](https://github.com/alecthomas), who was kind enough to implement a first iteration using his participle library
- [Lucas Bremgartner](https://github.com/breml), the pigeon maintainer

## Conclusion

We're building really interesting things at Scratch Data and trying to bring
all of the great tools from the traditional database world into analytical 
DBs. If you want to preview Postgrest on your own data, let me know!
And if you want to contribute,
I'd love to talk to people who have more experience with grammars to help make sure
we're building this the right way.