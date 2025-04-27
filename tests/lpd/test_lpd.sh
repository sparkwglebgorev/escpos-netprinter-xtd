#!/bin/bash
# This is a script to test the lpd backend
lp -d lpd_escpos ../receipt-with-logo.bin
lp -d lpd_escpos ../receipt-with-qrcode.bin