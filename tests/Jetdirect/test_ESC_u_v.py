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

print(f"Request status to: {HOST}:{PORT}")

    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    
    print("Test start")
    # Test ESC u Transmit peripheral device status
    # n=0
    s.sendall(b'\x1b\x75' + int.to_bytes(0))
    fn0_response = s.recv(1)
    assert fn0_response == b'\x00', f"Printer returned unexpected data to ESC u <n=0>: {fn0_response}"

    # Test ESC u Transmit peripheral device status
    # n=48
    s.sendall(b'\x1b\x75'+int.to_bytes(48))
    fn48_response = s.recv(1)
    assert fn48_response == b'\x00', f"Printer returned unexpected data to ESC u <n=48>: {fn48_response}"

    #Send a printable string for this receipt.
    s.send(b'Test ESC u complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
    s2.connect((HOST, int(PORT)))
    
    print("Test start")
    # Test ESC v Transmit paper sensor status
    s2.sendall(b'\x1b\x76')
    response = s2.recv(1)
    assert response == b'\x00', f"Printer returned unexpected data to ESC v: {response}"

    #Send a printable string for this receipt.
    s2.send(b'Test ESC v complete.\n')
    
    s2.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s2.recv(1024)

print("Test finished without exceptions")

print(f"Received {data!r}")