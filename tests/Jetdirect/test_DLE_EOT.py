import socket
import argparse

#This test script verifies escpos-netprinter responds all-clear to DLE EOT requests.

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
    # All DLE EOT return only one byte
    
    print("Test start")
    # Send DLE EOT <n=1> - printer status
    s.sendall(b'\x10\x04\x01')
    data = s.recv(1)
    assert data == b'\x16', "Printer returned a non-clear status"

    #Send DLE EOT <n=2> Transmit offline cause status
    s.sendall(b'\x10\x04\x02')
    data = s.recv(1)
    assert data == b'\x12', "Printer returned an offline cause"

    #Send DLE EOT <n=3> Transmit Error cause status
    s.sendall(b'\x10\x04\x03')  
    data = s.recv(1)
    assert data == b'\x12', "Printer returned an error"  # Check for error response
    
    #Send the DLE eot <n=4> Transmit Roll paper sensor status
    s.sendall(b'\x10\x04\x04')
    data = s.recv(1)
    assert data == b'\x12', "Printer returned an error"
    
    #Send the DLE EOT <n=7><a=1> Transmit ink status A
    s.sendall(b'\x10\x04\x07\x01')
    data = s.recv(1)
    assert data == b'\x12', "Printer returned ink status problem"
    
    #Send the DLE EOT <n=7><a=2> Transmit ink status B
    s.sendall(b'\x10\x04\x07\x02')
    data = s.recv(1)
    assert data == b'\x12', "Printer returned ink status problem"

    #Send the DLE EOT <n=8><a=3> Transmit peeler status B
    s.sendall(b'\x10\x04\x08\x03')
    data = s.recv(1)
    assert data == b'\x12', "Printer returned peeler status problem"

    #Send the DLE EOT <n=18><a=1> Transmit interface status
    s.sendall(b'\x10\x04\x18\x01')
    data = s.recv(1)
    assert data == b'\x10', "Printer returned multiple interfaces enabled, or something else"
    
    #Send the DLE EOT <n=18><a=2> Transmit DM-D status
    s.sendall(b'\x10\x04\x18\x02')
    data = s.recv(1)
    assert data == b'\x10', "Printer returned DM-D BUSY, or something else"
    
    #Send a printable string for this receipt.
    s.sendall(b'Test status DLE EOT - complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    print("Test finished without exceptions")

print(f"Received {data!r}")