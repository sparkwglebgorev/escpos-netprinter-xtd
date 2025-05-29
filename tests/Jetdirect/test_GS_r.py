import socket
import argparse

#This test script verifies escpos-netprinter responds all-clear to GS r requests.

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
    # Both GS r status return only one byte
    
    print("Test start")
    # Send GS r <n=1> - paper sensor status
    s.sendall(b'\x1D\x72\x01')
    data = s.recv(1)
    assert data == b'\x00', "Printer returned a non-clear paper status <n=1>"
    
    # Send GS r <n=49> - paper sensor status
    s.sendall(b'\x1D\x72\x31')
    data = s.recv(1)
    assert data == b'\x00', "Printer returned a non-clear paper status <n=49>"

    #Send GS r <n=2> Drawer kick-out connector status
    s.sendall(b'\x1D\x72\x02')
    data = s.recv(1)
    assert data in [b'\x00', b'\x01'], "Printer returned unexpected kick-out status <n=2>"

    #Send GS r <n=50> Drawer kick-out connector status
    s.sendall(b'\x1D\x72\x32')
    data = s.recv(1)
    assert data in [b'\x00', b'\x01'], "Printer returned unexpected kick-out status <n=50>"

    #Send GS r <n=4> Transmits ink status
    s.sendall(b'\x1D\x72\x04')
    data = s.recv(1)
    assert data == b'\x00', "Printer returned non-clear ink status <n=4>"
    
    #Send GS r <n=52> Transmits ink status
    s.sendall(b'\x1D\x72\x34')
    data = s.recv(1)
    assert data == b'\x00', "Printer returned non-clear ink status <n=52>"
    
    #Send a printable string for this receipt.
    s.sendall(b'Test status GS r - complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    print("Test finished without exceptions")

print(f"Received {data!r}")