import socket, select
import argparse

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
        s.settimeout(0.1) #We will set a timeout in case the printer stops before sending \x00
        while True:
            chunk:bytes = s.recv(1)
            if not chunk: 
                break
            data = data + chunk
            if b'\x00' in chunk: 
                break
    except TimeoutError as original :
        # The printer stopped before sending the null termination
        raise AssertionError(f"Expected a null-terminated response, got {data} instead.") from original
    finally:
        s.setblocking(True) #Returns to blocking IO
        
    return data

#Utility method to send the requests
def send_gs_parens_e_function(s:socket.socket, pL:bytes, pH:bytes, fn:int, data:bytes) -> None:
    s.sendall(b'\x1D\x28\x45') #GS ( E
    s.sendall(pL)
    s.sendall(pH)
    s.sendall(bytes([fn]))
    s.sendall(data)
    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    
    print("Test start")
    # Send GS ( E <fn=1>
    send_gs_parens_e_function(s, b'\x03', b'\x00', 1, b'IN')
    data = receive_to_null(s)
    assert data == b'\x37\x20\x00', f"Printer returned unexpected counter value: {data}"

    # Send GS ( E <fn=2>
    send_gs_parens_e_function(s, b'\x04', b'\x00', 2, b'OUT')
    #Check that nothing has been returned - requires that we set a timeout on the socket
    try:
        s.settimeout(1)  # We activate a 1s timeout on socket operations.  This will let us check if no data is returned on a test.
        data = s.recv(1)
        assert len(data) == 0, f"Printer returned unexpected data to GS ( E <fn=2>: {data}"
    except TimeoutError:
        # s.recv() timed out, so the printer returned no data -> this test is successful.
        pass
    finally:
        # Return the socket to it's original blocking IO state.
        s.setblocking(True)

    # Send GS ( E <fn=3>
    send_gs_parens_e_function(s, b'\x0A', b'\x00', 3, b'\x01\x32\x32\x32\x32\x32\x32\x32\x31')
    #Check that nothing has been returned - works for all sockets, even without timeouts
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=3>: {avaliable_read[0].recv(1)}"

    #TODO:  test all other functions
        
    #Send a printable string for this receipt.
    s.sendall(b'Test status GS ( E - complete.\n')

    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    print("Test finished without exceptions")

print(f"Received {data!r}")