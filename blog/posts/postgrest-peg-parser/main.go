package main

import "log"

func main() {
	expression := "age=gt.40"
	calc := &Postgrest{Buffer: expression}
	// calc := &Postgrest{}
	log.Println(calc.Init())
	log.Println(calc.Parse())
	calc.PrintSyntaxTree()
}
