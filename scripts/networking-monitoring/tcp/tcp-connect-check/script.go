package main

import (
 "encoding/json"
 "flag"
 "fmt"
 "net"
 "os"
 "time"
)
func main() {
 host := flag.String("host", "127.0.0.1", "host to connect to")
 port := flag.Int("port", 80, "single TCP port")
 timeout := flag.Duration("timeout", 3*time.Second, "dial timeout")
 flag.Parse()
 if *port < 1 || *port > 65535 || *timeout <= 0 {
  fmt.Fprintln(os.Stderr, "port must be 1..65535 and timeout must be positive")
  os.Exit(2)
 }
 started := time.Now()
 conn, err := net.DialTimeout("tcp", net.JoinHostPort(*host, fmt.Sprint(*port)), *timeout)
 if err == nil { conn.Close() }
 result := map[string]interface{}{"host": *host, "port": *port, "reachable": err == nil, "elapsed_ms": time.Since(started).Milliseconds()}
 if err != nil { result["error"] = err.Error() }
 json.NewEncoder(os.Stdout).Encode(result)
 if err != nil { os.Exit(1) }
}
