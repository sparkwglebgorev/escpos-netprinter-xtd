#!/bin/bash

# Start CUPS
/usr/sbin/cupsd
lpadmin -p lpd_escpos -v $DEVICE_URI -E -o printer-is-shared=true

# Start Flask
python3 ${FLASK_APP}
