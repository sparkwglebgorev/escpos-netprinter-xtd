import socket, select
import argparse
import re

#This test script verifies escpos-netprinter responds correctly to ESC u and ESC v requests.

#get printer host and port from command line
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='IP adress or hostname of the printer', default='localhost')
parser.add_argument('--port', help='Port of the printer', default=9100)
args = parser.parse_args()

HOST = args.host  #The IP adress or hostname of the printer
PORT = args.port  #A printer should always listen to port 9100, but the Epson printers can be configured so also will we.

print(f"Test ESC SP on: {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test start")
    # Test ESC SP Transmit peripheral device status
    # n=0
    s.sendall(b'Hello, printer.  This has no right-side spacing.\n')
    s.sendall(b'\x1b\x20' + int.to_bytes(128))
    s.sendall(b'This now has a right-side spacing of 128\n')
    
    #Send a printable string for this receipt.
    s.send(b'Test ESC SP complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

print("Test finished without exceptions")

print(f"Received {data!r}")