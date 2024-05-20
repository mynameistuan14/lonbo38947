#!/bin/bash

command="./titan-edge daemon start --init --url https://hk-locator.titannet.io:5000/rpc/v0"

while true; do
  $command 2>&1 |
  while IFS= read -r line; do
    echo "$line"
    if echo "$line" | grep -q "sendRequest"; then
      echo "Specific string found in the output. Terminating and re-executing the command."

      child_pid=$(pgrep -f "$command")

      kill "$child_pid"

      break
    fi
  done

  sleep 1
done
