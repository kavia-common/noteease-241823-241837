#!/bin/bash
cd /home/kavia/workspace/code-generation/noteease-241823-241837/notes_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

