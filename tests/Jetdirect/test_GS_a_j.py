import socket, select
import argparse
import re

#This test script verifies escpos-netprinter responds correctly to GS a and GS j requests.

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
    # Test GS a <n=0> disable Automatic Status Back (ASB)
    
    s.sendall(b'\x1da') #GS a
    s.sendall(b'\x00')  #n=0 - disable ASB
    #Check that nothing is returned by the printer.
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to GS a <n=0>: {avaliable_read[0].recv(1024)}"


    # Test GS a <n!=0> enable Automatic Status Back (ASB)
    s.settimeout(1)
    for n in range(1,255):
        s.sendall(b'\x1da') #GS a
        s.sendall(int.to_bytes(n))  #n!=0 - enable ASB
        
        #Check that we get an ASB response.  These are always 4 bytes.  Let's try to get a little more.
        response_ASB:bytes = s.recv(5) 
        assert len(response_ASB) < 5, f"Printer returned too much data to GS a. Received: {response_ASB}"
    s.setblocking(True)
    
    # Test GS j <n=0> disable Automatic Status Back (ASB) for ink
    
    s.sendall(b'\x1dj') #GS a
    s.sendall(b'\x00')  #n=0 - disable ASB
    #Check that nothing is returned by the printer.
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to GS a <n=0>: {avaliable_read[0].recv(1024)}"

    # Test GS j <n!=0> enable Automatic Status Back (ASB) for ink
    # We have to check 2 things:  1) the response is in the expected format, and 2) the status itself is 2 bytes long
    # Let's use a regex
    ASB_regex = re.compile(b'\x35(\S\S)\x00')
    
    s.settimeout(1)
    for n in range(1,255):
        s.sendall(b'\x1dj') #GS a
        s.sendall(int.to_bytes(n))  #n!=0 - enable ASB
        
        #Check that we get an ASB header-to-null response.  These are always 4 bytes including the header and null.  Let's try to get a little more.
        response_ASB:bytes = s.recv(5) 
        matched = ASB_regex.match(response_ASB)
        
        assert matched is not None, f"Printer did not respond with the right format to GS j <n={n}>. Received this : {response_ASB}"
    s.setblocking(True)
    
    #Send a printable string for this receipt.
    s.sendall(b'Test status GS a and GS j - complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    
print("part 1 finished.")
print(f"Received {data!r}")

print("Test finished without exceptions")

