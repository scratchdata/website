---
date: 2024-03-11
publishdate: 2024-03-11
title: Debugging a Golang Bug with Non-Blocking Reads
summary: We found a bug when doing non-blocking IO in Go. Here's our workaround.
tags: ["Engineering"]
---

One of the ways we stream data from databases to the end-user is with a named pipe. 
Specifically, [we do this](/blog/duckdb-as-json-api) with DuckDB to stream JSON-formatted
results directly to the user. In the process of building this, we discovered a bug in how
Go handles reading data from pipes.

## The Original Code

The original code for reading data looks like this. First we create a named pipe:

``` bash
$ mkfifo p.pipe
```

And then we generate data and pass it to the pipe. Instead of DuckDB, I'll use a simpler
example to write data:

``` go
import "os"

go func() {
    pipe, _ := os.OpenFile("p.pipe", os.O_WRONLY|os.O_APPEND, os.ModeNamedPipe)
    for range 5 {
        pipe.WriteString("Hello")
        time.Sleep(1000 * time.Millisecond)
    }
    err := pipe.Close()
}()

pipe, err := os.OpenFile("p.pipe", os.O_RDONLY|syscall.O_NONBLOCK, os.ModeNamedPipe)
buf := make([]byte, 65536)
for {
    n, err := pipe.Read(buf)
}
```

You'll notice a few things:

- `time.Sleep()` This lets us simulate a slow writer - perhaps a slow query or network connection.
- `O_NONBLOCK` It's possible that our writer never successfully
  opens the file for writing - perhaps due to an error elsewhere. If this happens,
  our reader will block indefinitely waiting for data. Non-blocking IO lets us 
  coordinate with the writer.

## The Bug

The expected behavior is that the `for {}` loop runs infinitely. However, *on my M1 Mac*, this 
is not the case. The code blocks on `pipe.Read()`. If you're on a Mac, you can try the full program
in [this gist](https://gist.github.com/poundifdef/76377b75b15826baccab83cd501d0c85).

What's strange is that this code *does* work:

1. On Linux
2. If we remove `time.Sleep()` from the writer!

After testing and coming up with the simplest reproducible example, I filed a 
[bug report](https://github.com/golang/go/issues/66239). Much to my surprise, someone identified the
issue and wrote a patch the same day. There a lot of information in the ticket. The root causes are:

1. Go's implementation on darwin uses kqueue() to do non-blocking reads, however, named pipes
   were excluded from part of that logic.
2. There was a race condition where, if the writer does not close before the reader reads all data, then
   we skip the logic to poll.

   Hopefully a fix will come out in go 1.23.

## The Workaround

Go's os.File interface is a wrapper around underlying syscalls. What if we made
those syscalls directly? We can do exactly that with the `syscall` package. Our revised
reader looks like this:

``` go
import "syscall"

pipe, err := syscall.Open("p.pipe", os.O_RDONLY|syscall.O_NONBLOCK, 0666)
// pipe, err := os.OpenFile("p.pipe", os.O_RDONLY|syscall.O_NONBLOCK, os.ModeNamedPipe)
buf := make([]byte, 65536)
for {
    n, err := syscall.Read(pipe, buf)
    // n, err := pipe.Read(buf)
}
```

This works! Our for-loop no longer blocks due to this bug. We have to do a little more
bookkeeping ourselves but the logic is identical to before.

You can see the full solution we implemented [here](https://github.com/scratchdata/scratchdata/blob/7c1a0fcd0e202126c581924c3bee2b1b2b10335d/pkg/destinations/duckdb/query.go#L14). Feedback welcome!

## Conclusion

We're building software to let builders use analytical databases without the plumbing.
We're doing a lot of fun systems-y kinds of things in Go. If this is interesting to you
then [let's talk](https://q29ksuefpvm.typeform.com/to/baKR3j0p#source=go_nonblocking_pipes_bug)!