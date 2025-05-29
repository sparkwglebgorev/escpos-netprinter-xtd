import socket
import argparse

#This test script verifies escpos-netprinter responds all-clear to DLE DC4 requests that need them.

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
    # Send DLE DC4 <n=1> - Generate pulse
    s.sendall(b'\x10\x14\x01\x01\x01')
    assert True, "Generate pulse should return nothing"
    
    # Send DLE DC4 <n=2> - Execute power-off sequence
    s.sendall(b'\x10\x14\x02\x01\x08')
    data = s.recv(3)
    assert data == b'\x3B\x30\x00', "Printer did not confirm power-off"
    
    # Send DLE DC4 <n=3> - Sound buzzer
    s.sendall(b'\x10\x14\x03\x00\x02\x03\x04\x05')  #Stop sounding the buzzer 2 times
    assert True, "Sound buzzer should return nothing"

    #Send DLE EOT <n=8> Clear buffer(s)
    s.sendall(b'\x10\x14\x08\x01\x03\x14\x01\x06\x02\x08')
    data = s.recv(3)
    assert data == b'\x37\x25\x00', "Printer did not finish buffer clear"

    #DLE EOT <n=7> Transmit specified status in real time
    
    # Send DLE EOT <n=7><m=1>  basic ASB status
    s.sendall(b'\x10\x14\x07\x01')  
    data = s.recv(4)
    assert data == b'\x00\x00\x00\x00', "Printer returned an error: {data}"  
    
    # Send DLE EOT <n=7><m=2> extended ASB status
    s.sendall(b'\x10\x14\x07\x02')  
    data = s.recv(4)
    assert data == b'\x39\x00\x40\x00', "Printer returned an error: {data}"  
    
    # Send DLE EOT <n=7><m=4> offline response
    s.sendall(b'\x10\x14\x07\x04')  
    data = s.recv(3)
    assert data == b'\x37\x23\x00', "Printer returned an offline cause, or something else: {data}"    
    
    # Send DLE EOT <n=7><m=5> battery status
    s.sendall(b'\x10\x14\x07\x05')  
    data = s.recv(1)
    assert data == b'\x01', "Printer returned something unexpected: {data}"       
    
    #Send a printable string for this receipt.
    s.sendall(b'Test status DLE DC4 - complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    print("Test finished without exceptions")

print(f"Received {data!r}")