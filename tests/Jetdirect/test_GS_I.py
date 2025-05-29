import socket
import argparse

#This test script verifies escpos-netprinter responds to GS I requests.

#get printer host and port from command line
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='IP adress or hostname of the printer', default='localhost')
parser.add_argument('--port', help='Port of the printer', default=9100)
args = parser.parse_args()

HOST = args.host  #The IP adress or hostname of the printer
PORT = args.port  #A printer should always listen to port 9100, but the Epson printers can be configured so also will we.

print(f"Request sent to: {HOST}:{PORT}")

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
        
    print("Test start")
    # Send GS I <n=1> - paper sensor status
    s.sendall(b'\x1D\x49\x01')
    data:bytes = s.recv(1)
    assert data == b'\x01', f"Printer returned unexpected model ID <n=1> :{data}"
    
    # Send GS I <n=49> - paper sensor status
    s.sendall(b'\x1D\x49\x31')
    data = s.recv(1)
    assert data == b'\x01', f"Printer returned unexpected model ID <n=49> :{data}"

    # Send GS I <n=2> Type ID
    s.sendall(b'\x1D\x49\x02')
    data = s.recv(1)
    assert data == b'\x02', f"Printer returned unexpected type ID <n=2> :{data}"

    # Send GS I <n=50> Type ID
    s.sendall(b'\x1D\x49\x32')
    data = s.recv(1)
    assert data == b'\x02', f"Printer returned unexpected type ID <n=50> :{data}"

    # Send GS I <n=3> Type information
    s.sendall(b'\x1D\x49\x03')
    data = s.recv(1)
    assert data == b'\x23', f"Printer returned unexpected version ID <n=3> :{data}"
    
    # Send GS I <n=51> Transmits ink status
    s.sendall(b'\x1D\x49\x33')
    data = s.recv(1)
    assert data == b'\x23', f"Printer returned unexpected version ID <n=51> :{data}"
    
    # Send GS I <n=33> Transmits printer type information - supported functions
    s.sendall(b'\x1D\x49\x21')
    data = receive_to_null(s)
    assert data == b'\x3D\x02\x40\x40\x00', f"Printer returned unexpected printer type <n=33> :{data}"
 
    # Send GS I <n=35> Transmits printer type information - supported functions
    s.sendall(b'\x1D\x49\x23')
    data = receive_to_null(s)
    assert data == b'\x3D\x01\x01\x01\x00', f"Printer returned unexpected printer type info <n=35> :{data}"
        
    # Send GS I <n=96> Transmits printer type information - supported functions
    s.sendall(b'\x1D\x49\x60')
    data = receive_to_null(s)
    assert data == b'\x3D\x01\x01\x01\x00', f"Printer returned unexpected printer type info <n=96> :{data}"
    
    # Send GS I <n=110> Transmits printer type information - supported functions
    s.sendall(b'\x1D\x49\x6E')
    data = receive_to_null(s)
    assert data == b'\x3D\x01\x01\x01\x00', f"Printer returned unexpected printer type info <n=110> :{data}"

    # Send GS I <n=65> Transmits printer firmware version
    s.sendall(b'\x1D\x49\x41')
    data = receive_to_null(s)
    assert data == b'\x5F' + b'release 2.3' + b'\x00', f"Printer returned unexpected firmware version <n=65> :{data}"
    
    # Send GS I <n=66> Transmits printer maker name
    s.sendall(b'\x1D\x49\x42')
    data = receive_to_null(s)
    assert data == (b'\x5F' + b'ESCPOS-netprinter' + b'\x00'), f"Printer returned unexpected firmware version <n=66> :{data}"
    
    # Send GS I <n=67> Transmits printer model name
    s.sendall(b'\x1D\x49\x43')
    data = receive_to_null(s)
    assert data == (b'\x5F' + b'ESCPOS-netprinter' + b'\x00'), f"Printer returned unexpected model name <n=67> :{data}"
    
    # Send GS I <n=68> Transmits printer serial number
    s.sendall(b'\x1D\x49\x44')
    data = receive_to_null(s)
    assert data == (b'\x5F' +b'netprinter_1' + b'\x00'), f"Printer returned unexpected serial number <n=68> :{data}"    

    # Send GS I <n=69> Transmits font language for specific countries
    s.sendall(b'\x1D\x49\x45')
    data = receive_to_null(s)
    assert data == (b'\x5F' + b'PC850 Multilingual' + b'\x00'), f"Printer returned unexpected code page <n=69> :{data}"    
    
    # Send GS I <n=111> Transmits model specific information (Printer info B)
    s.sendall(b'\x1D\x49\x6F')
    data = receive_to_null(s)
    assert data == (b'\x5F' + b'Netprinter' + b'\x00'), f"Printer returned unexpected printer info B <n=111> :{data}"    

    # Send GS I <n=112> Transmits model specific information (Printer info B)
    s.sendall(b'\x1D\x49\x70')
    data = receive_to_null(s)
    assert data == (b'\x5F' + b'Netprinter' + b'\x00'), f"Printer returned unexpected printer info B <n=112> :{data}"    

    
    #Send a printable string for this receipt.
    s.sendall(b'Test status GS I - complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    print("Test finished without exceptions")
    

print(f"Received {data!r}")