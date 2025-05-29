#!/bin/bash
<<<<<<< HEAD
# This is a script to test the lpd backend with whole receipts
=======
# This is a script to test the lpd backend
>>>>>>> origin/1-deal-with-pre-print-requests-from-pos-systems
lp -d lpd_escpos ../receipt-with-logo.bin
lp -d lpd_escpos ../receipt-with-qrcode.bin