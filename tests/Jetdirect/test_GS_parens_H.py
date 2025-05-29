import socket, select
import argparse
import re

#This test script verifies escpos-netprinter responds correctly to GS ( E requests.

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
        s.settimeout(1) #We will set a timeout in case the printer stops before sending \x00
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

def send_gs_parens_h_function(s:socket.socket, pL:bytes, pH:bytes, fn:int, data:bytes) -> None:
    s.sendall(b'\x1d\x28\x48') #GS ( H
    s.sendall(pL)
    s.sendall(pH)
    s.sendall(int.to_bytes(fn))
    s.sendall(data)
    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    
    print("Test start")
    # Test GS ( H <fn=48> Specifies the process ID response
    send_gs_parens_h_function(s, b'\x06', b'\x00', 48,  b'\x30\x301234')
    fn48_response = receive_to_null(s)
    assert fn48_response == b'\x37\x22' + b'1234'+ b'\x00', f"Printer returned unexpected data to GS ( H <fn=48>: {fn48_response}"

    # Test GS ( H <fn=49> Specifies the offline response
    
    #This regex checks that the response has the right format
    response_regex = re.compile(b'\x37\x23(\S{0,10})\x00')
    
    for d in [b'\x00', b'\x01', b'\x02', b'\x48', b'\x49', b'\x50']:
        send_gs_parens_h_function(s, b'\x02', b'\x00', 49,  b'\x30'+d)  #TODO:  check the pL - the specification demands \x03 but there are only 2 bytes after fn.
        fn49_response = receive_to_null(s)
        
        assert len(fn49_response) < 14, f"Printer returned too much data to GS ( H <fn=48> <d={d}>: {fn49_response}"
        
        # Extract the condition and the config from the response
        matched = response_regex.match(fn49_response)
        assert matched is not None, f"Printer did not respond with the right format to GS ( H <fn=48> <d={d}>: {fn49_response}"
    
    #Fermons la première partie du test.
    #Send a printable string for this receipt.
    s.sendall(b'Test GS ( H complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    

print("Test finished without exceptions")

print(f"Received {data!r}")