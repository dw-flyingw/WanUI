#!/bin/bash
# A simple Ralph Wiggum loop
MAX_ITERATIONS=10
ITERATION=1

while [ $ITERATION -le $MAX_ITERATIONS ]; do
  echo "🔥 Ralph Iteration: $ITERATION"
  
  # Run Claude in 'print' mode with auto-permissions
  claude -p "Review the task in plan.md and complete the next step. If finished, say 'DONE'." --dangerously-skip-permissions
  
  # Optional: Check if Claude said it was finished
  # (Requires piping output to a file to grep, or just let it run the full count)
  
  ((ITERATION++))
done
