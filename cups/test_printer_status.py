import socket
import argparse

#This test script verifies a JetDirect protocol printer responds to DLE EOT requests.

#get printer host and port from command line
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='IP adress or hostname of the printer', default='localhost')
parser.add_argument('--port', help='Port of the printer', default=9100)
args = parser.parse_args()

HOST = args.host  #The IP adress or hostname of the printer
PORT = args.port  #A printer should always listen to port 9100, but the Epson printers can be configured so also will we.

print(f"Request status to: {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    s.sendall(b'\x10\x04\x01')
    data = s.recv(2)
    print(f"Printer status: received {data!r}\n")

    s.sendall(b'\x10\x04\x04')
    data = s.recv(2)
    print(f"Paper status: received {data!r}\n")

    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

print(f"Received {data!r}")