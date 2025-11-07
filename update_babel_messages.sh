#!/bin/bash
# This script creates messages.pot from the project files, then updates the existing translations with any new texts

pybabel extract -F babel.cfg --copyright-holder="Francois-Leonard Gilbert" --project="escpos-netprinter" --msgid-bugs-address="github.com/gilbertfl/escpos-netprinter/issues" --version="3.2" -o translations/messages.pot .
pybabel update -i translations/messages.pot -d translations