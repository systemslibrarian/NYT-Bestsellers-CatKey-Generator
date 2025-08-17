#!/bin/bash
# Runner for NYT-to-Library-CatKey-Generator.py

set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

python3 NYT-to-Library-CatKey-Generator.py
