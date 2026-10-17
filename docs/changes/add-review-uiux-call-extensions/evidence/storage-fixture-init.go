package main
import (
 "fmt"
 "os"
 "strconv"
 engine "github.com/stenhigh/prifly/internal/runtime"
)
func main() {
 if len(os.Args)!=3 {panic("new owned fixture authority path and finite bytes required")}
 budget,err:=strconv.ParseInt(os.Args[2],10,64);if err!=nil {panic(err)}
 if _,err:=os.Stat(os.Args[1]);!os.IsNotExist(err) {panic("fixture path must not exist")}
 if err:=engine.InitProjectWithStorageBudget(os.Args[1],budget);err!=nil {panic(err)}
 fmt.Println("created a new isolated fixture authority with finite budget",budget)
}
