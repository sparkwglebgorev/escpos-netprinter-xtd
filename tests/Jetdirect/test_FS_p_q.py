import socket, select
import argparse
import re

#This test script verifies escpos-netprinter responds correctly to FS p and FS q requests (NV images).

#get printer host and port from command line
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='IP adress or hostname of the printer', default='localhost')
parser.add_argument('--port', help='Port of the printer', default=9100)
args = parser.parse_args()

HOST = args.host  #The IP adress or hostname of the printer
PORT = args.port  #A printer should always listen to port 9100, but the Epson printers can be configured so also will we.

print(f"Request status to: {HOST}:{PORT}")

#Utility method to read "Header to null"
def receive_to_null(s:socket.socket) -> bytes:
    #Read "Header to null"
    data:bytes = b''
      
    try:
        s.settimeout(10) #We will set a timeout in case the printer stops before sending \x00
        while True:
            chunk:bytes = s.recv(1)
            if not chunk: 
                break
            data = data + chunk
            if b'\x00' in chunk: 
                break
    except TimeoutError as original :
        # Communication stopped before we received the null termination
        raise AssertionError(f"Expected a null-terminated response, got {data} instead.") from original
    finally:
        s.setblocking(True) #Returns to blocking IO
        
    return data

 
   
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    
    print("Test start")
    # Test FS q Define NV bit image (obsolete command)
    
    s.sendall(b'\x1cq') #FS q
    s.sendall(b'\x01')  #n=1  - we send one image
    s.sendall(b'\x05')  #xL = 5
    s.sendall(b'\x00')  #xH
    s.sendall(b'\x01')  #yL = 1
    s.sendall(b'\x00')  #yH
    s.sendall(b'\x00'*5*8) #5*8 bytes of data, as announced with xL, xH, yL, yH (5 + 0*256)*(1 + 0*256)*8
    
    #Check that nothing is returned by the printer.
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS q: {avaliable_read[0].recv(1024)}"

    # Test FS p Read from NV user memory
    
    s.sendall(b'\x1cp') #FS p
    s.sendall(b'\x01')  #n=1 print image 1
    s.sendall(b'\x00')  #m=0 scale x1
 
    #Check that nothing is returned by the printer.
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS p: {avaliable_read[0].recv(1024)}"
    
      #Send a printable string for this receipt.
    s.sendall(b'Test status FS p and FS q - complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    
print(f"Received {data!r}")

print("Test finished without exceptions")

