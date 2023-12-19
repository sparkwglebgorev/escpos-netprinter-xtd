#!/bin/bash

# Start CUPS
/usr/sbin/cupsd

# Start Flask
python3 ${FLASK_APP}
