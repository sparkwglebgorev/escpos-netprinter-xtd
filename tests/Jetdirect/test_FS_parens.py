import socket, select
import argparse
import re

#This test script verifies escpos-netprinter responds correctly to FS ( requests, especially FS ( e.

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

#Utility method to send the requests
def send_fs_parens_e_function(s:socket.socket, pL:bytes, pH:bytes, data:bytes) -> None:
    s.sendall(b'\x1c\x28\x65') #FS ( e
    s.sendall(pL)
    s.sendall(pH)
    s.sendall(data)
  
   
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    
    print("Test start")
    # Test FS ( e <n=0>
    send_fs_parens_e_function(s, b'\x02', b'\x00', int.to_bytes(51)+int.to_bytes(0))
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( e <n=0>: {avaliable_read[0].recv(1024)}"

    # Test FS ( e <n != 0>
    # We have to check 2 things:  1) the response includes the status we expect, and 2) the status itself is 1 byte long
    # Let's use a regex
    response_regex = re.compile(b'\x39(\S)\x40\x00')
    
    for n in range(1,255):
        send_fs_parens_e_function(s, b'\x02', b'\x00', int.to_bytes(51)+int.to_bytes(n))
        response:bytes = s.recv(4)
        matched:bytes = response_regex.match(response)
        
        assert matched is not None, f"Printer did not respond with the right format to FS ( e <n={n}> : {response}"
        assert matched.group(1) == b'\x00', f"Printer did not send the expected response to FS ( e <n={n}>: {response}"

print("part 1 finished.")
print(f"Received {data!r}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
    s2.connect((HOST, int(PORT)))

    #Ask for each FS ( subfunction possible    
    
    function:bytes = b''
    
    for function in [b'A', b'C']: # FS ( A, FS ( C 
        #Check that no response is received from the printer
        s2.sendall(b'\x1c\x28') #FS (
        s2.sendall(function)  
        s2.sendall(int.to_bytes(3))     #pL
        s2.sendall(int.to_bytes(0))     #pH
        s2.sendall(b'a'*3)   #Send the announced 4 bytes
        
        avaliable_read, _, _ = select.select([s2], [], [], 1)
        assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( {function}: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( E functions, except 61
    for fn in 60, 62, 63, 64, 65:
        #Check that no response is received from the printer
        s2.sendall(b'\x1c\x28E') #FS ( E
        s2.sendall(int.to_bytes(4))
        s2.sendall(int.to_bytes(0))
        s2.sendall(int.to_bytes(fn))
        s2.sendall(b'a'*4)   #Send the announced 4 bytes
        avaliable_read, _, _ = select.select([s2], [], [], 1)
        assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( E <fn={fn}>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( E function 61 <c=48>  Values for top logo printing 
    s2.sendall(b'\x1c\x28E') #FS ( E
    s2.sendall(int.to_bytes(3))
    s2.sendall(int.to_bytes(0))
    s2.sendall(int.to_bytes(61))
    s2.sendall(b'\x02')   #Send m
    s2.sendall(int.to_bytes(48))
    
    response_fn51_48:bytes = s2.recv(5)
    assert len(response_fn51_48) == 5, f"Printer returned unexpected response to FS ( E <fn=61> <c=48> :{response_fn51_48}"

    #Test FS ( E function 61 <c=49> Values for bottom logo printing
    s2.sendall(b'\x1c\x28E') #FS ( E
    s2.sendall(int.to_bytes(3))
    s2.sendall(int.to_bytes(0))
    s2.sendall(int.to_bytes(61))
    s2.sendall(b'\x02')   #Send m
    s2.sendall(int.to_bytes(49))
    
    response_fn51_49:bytes = s2.recv(4)
    assert len(response_fn51_49) == 4, f"Printer returned unexpected response to FS ( E <fn=61> <c=49> :{response_fn51_49}"

    #Send a printable string for this receipt.
    s2.sendall(b'Test status GS ( E - part 2 complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s2.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s2.recv(1024)
    
print("part 2 finished.")
print(f"Received {data!r}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s3:
    s3.connect((HOST, int(PORT)))   
    
    #Test FS ( E function 61 <c=50> Extended values for top/bottom logo printing
    s3.sendall(b'\x1c\x28E') #FS ( E
    s3.sendall(int.to_bytes(3))
    s3.sendall(int.to_bytes(0))
    s3.sendall(int.to_bytes(61))
    s3.sendall(b'\x02')   #Send m
    s3.sendall(int.to_bytes(50))
    
    #The maximum response length is 11.  Let's get a little more if it is there.
    s3.settimeout(1)
    response_fn51_50:bytes = s3.recv(14) 
    assert len(response_fn51_50) < 12, f"Printer returned too much data to FS ( E <fn=61> <c=50>. Received: {response_fn51_50}"
    s3.setblocking(True)
    
    #We want to verify two things:  1)that only pairs have been sent with m, and 2) the right number of them.
    # Let's use a regex
    extended_top_bottom_regex = re.compile(b'\x02(\S[\x30\x31]){1,5}')
    matched:bytes = extended_top_bottom_regex.match(response_fn51_50)
    assert matched is not None, f"Printer did not respond with the right format to FS ( E <fn=61> <c=50>. Received: {response_fn51_50}"
     
    #Test FS ( L <fn=33>    
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x0C\x00')  #pL = 12 pH=0
    s3.sendall(b'\x21')     #fn=33
    s3.sendall(b'0')        #sm=0 No reference (do not use layout)
    s3.sendall(b'0\x3b')    #sa=0 Does not specify the distance from the print reference to the next print reference
    s3.sendall(b'\x3b'*4)   #sb, sc, sd, se are omitted
    s3.sendall(b'800\x3b')  #se paper width is 80mm (unit=0.1mm)
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=33>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=65>  <m=48>
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(b'\x41')     #fn=65
    s3.sendall(int.to_bytes(48))  #m=48  Feeds paper to the label peeling position
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=65>  <m=48>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=65>  <m=49>
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(b'\x41')     #fn=65
    s3.sendall(int.to_bytes(49))  #m=49  Feeds paper to the label peeling position
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=65>  <m=49>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=66>  <m=48>
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(b'\x42')     #fn=66
    s3.sendall(int.to_bytes(48))  #m=48  Feeds paper to the cutting position
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=66>  <m=48>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=66>  <m=49>
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(b'\x42')     #fn=66
    s3.sendall(int.to_bytes(49))  #m=49  Feeds paper to the cutting position
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=66>  <m=49>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=67>  <m=48>
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(b'\x43')     #fn=67
    s3.sendall(int.to_bytes(48))  #m=48  Feeds paper to the starting position
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=67>  <m=48>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=67>  <m=49>
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(b'\x43')     #fn=67
    s3.sendall(int.to_bytes(49))  #m=49  Feeds paper to the starting position
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=67>  <m=49>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=67>  <m=50>
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(b'\x43')     #fn=67
    s3.sendall(int.to_bytes(50))  #m=49  Feeds paper to the starting position on the current label
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=67>  <m=49>: {avaliable_read[0].recv(1024)}"
    
    #Test FS ( L <fn=80> Paper layout error special margin setting
    s3.sendall(b'\x1c\x28L') #FS ( L
    s3.sendall(b'\x02\x00')  #pL = 2 pH=0
    s3.sendall(int.to_bytes(80))     #fn=80  NOTE: the documentation says b'\x43' but we test 80 just in case since it has already been tested.
    s3.sendall(int.to_bytes(100))    #We set a vertical margin of 10mm (unit=0.1mm)
    
    #Check that no response is returned by the printer 
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected response to FS ( L <fn=67>  <m=49>: {avaliable_read[0].recv(1024)}"
    
    #Send a printable string for this receipt.
    s3.sendall(b'Test status GS ( E - part 3 complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s3.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s3.recv(1024)
    
print("Test finished without exceptions")

print(f"Received {data!r}")