package main
import ("flag"; "fmt"; "os")
func main() {
 file := flag.String("file", "", "input file")
 flag.Parse()
 if *file == "" { fmt.Fprintln(os.Stderr, "required: -file"); os.Exit(2) }
 stat, err := os.Stat(*file)
 if err != nil { fmt.Fprintln(os.Stderr, err); os.Exit(2) }
 fmt.Println(stat.Size())
}
