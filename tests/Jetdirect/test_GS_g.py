import socket
import argparse

#This test script verifies escpos-netprinter responds correctly to GS g requests.

#get printer host and port from command line
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='IP adress or hostname of the printer', default='localhost')
parser.add_argument('--port', help='Port of the printer', default=9100)
args = parser.parse_args()

HOST = args.host  #The IP adress or hostname of the printer
PORT = args.port  #A printer should always listen to port 9100, but the Epson printers can be configured so also will we.

print(f"Request status to: {HOST}:{PORT}")

#Utility method to read "Header to null"
def receive_to_null(s:socket) -> bytes:
    #Read "Header to null"
    data:bytes = b''
    while True:
        chunk:bytes = s.recv(1)
        if not chunk: 
            break
        data = data + chunk
        if b'\x00' in chunk: 
            break
    return data


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    # Both GS r status return only one byte
    
    print("Test start")
    # Send GS g 2 - read maintenance counter
    s.sendall(b'\x1D\x67\x32\x00\x10\x00')
    data = receive_to_null(s)
    assert data == b'\x5F\x01\x00', f"Printer returned unexpected counter value: {data}"
        
    #Send a printable string for this receipt.
    s.sendall(b'Test status GS g - complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    print("Test finished without exceptions")

print(f"Received {data!r}")