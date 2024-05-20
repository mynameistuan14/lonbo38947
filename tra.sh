#!/bin/bash

command="./mineral-linux mine"

while true; do
  $command 2>&1 |
  while IFS= read -r line; do
    echo "$line"
    if echo "$line" | grep -q "EInsufficientDifficulty"; then
      echo "Specific string found in the output. Terminating and re-executing the command."

      child_pid=$(pgrep -f "$command")

      kill "$child_pid"

      break
    fi
  done

  sleep 1
done
