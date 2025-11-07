#!/bin/bash
# This script creates a new locale for translation

# Argument validation check
if [ "$#" -ne 1 ]; then
    echo "This initializes a new locale for Flask-Babel"
    echo "Usage: $0 <language-isocode>"
    exit 1
fi

pybabel init -i translations/messages.pot -d translations -l ${1}