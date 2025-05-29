import socket, select
import argparse
import re

#This test script verifies escpos-netprinter responds correctly to FS g requests.

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
    # Test FS g 1 Write to NV user memory
    
    s.sendall(b'\x1cg1') #FS g 1
    s.sendall(b'\x00')  #m=0
    s.sendall(b'\x0f\x0f\x0f\x0f')     #Address in memory to store data in - 4 bytes - not important (still, not 0000 just to prevent overwriting a real printer's boot bytes)
    s.sendall(b'\x05')  #nL
    s.sendall(b'\x00')  #nH
    s.sendall(b'\x00'*5) #5 bytes of data, as announced with nL and nH
    
    #Check that nothing is returned by the printer.
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS g 1: {avaliable_read[0].recv(1024)}"

    # Test FS g 2 Read from NV user memory
    
    s.sendall(b'\x1cg2') #FS g 2
    s.sendall(b'\x00')  #m=0
    s.sendall(b'\x0f\x0f\x0f\x0f')     #Address in memory to read data from - 4 bytes - not important 
    s.sendall(b'\x05')  #nL
    s.sendall(b'\x00')  #nH

    #We asked for 5 bytes (nL + nH*256), sent as header-to-null.  Let's check what we get back with a regex
    fs_g_2_regex = re.compile(b'\x5f(\S+?)\x00') 
    
    #Let's try to get those 5 bytes, and a little more.
    s.settimeout(1)
    response_fs_g_2:bytes = s.recv(10) 
    s.setblocking(True)
    
    matched = fs_g_2_regex.match(response_fs_g_2)
    
    assert matched is not None, f"Printer did not respond with the right format to FS g 2. Received this : {response_fs_g_2}"
    assert len(matched.group(1)) < 6, f"Printer returned too much data for FS g 2. Received: {response_fs_g_2}"
    
    
    #Send a printable string for this receipt.
    s.sendall(b'Test status FS g - complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    
print("part 1 finished.")
print(f"Received {data!r}")

print("Test finished without exceptions")

