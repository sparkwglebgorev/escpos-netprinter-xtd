#!/bin/bash
# This is a script to test the lpd backend with whole receipts
lp -d lpd_escpos ../receipt-with-logo.bin
lp -d lpd_escpos ../receipt-with-qrcode.bin