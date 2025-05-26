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
def send_gs_parens_e_function(s:socket.socket, pL:bytes, pH:bytes, fn:int, data:bytes) -> None:
    s.sendall(b'\x1D\x28\x45') #GS ( E
    s.sendall(pL)
    s.sendall(pH)
    s.sendall(int.to_bytes(fn))
    s.sendall(data)
   
data:bytes = b''   
    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))
    
    print("Test start")
    # Test GS ( E <fn=1>
    send_gs_parens_e_function(s, b'\x03', b'\x00', 1, b'IN')
    fn1_response = receive_to_null(s)
    assert fn1_response == b'\x37\x20\x00', f"Printer returned unexpected counter value: {fn1_response}"

    # Test GS ( E <fn=2>
    send_gs_parens_e_function(s, b'\x04', b'\x00', 2, b'OUT')
    #Check that nothing has been returned - this method requires that we set a timeout on the socket
    try:
        s.settimeout(1)  # We activate a 1s timeout on socket operations.  This will let us check if no data is returned on a test.
        fn2_response = s.recv(1)
        assert len(fn2_response) == 0, f"Printer returned unexpected data to GS ( E <fn=2>: {fn2_response}"
    except TimeoutError:
        # s.recv() timed out, so the printer returned no data -> this test is successful.
        pass
    finally:
        # Return the socket to it's original blocking IO state.
        s.setblocking(True)

    # Test GS ( E <fn=3>
    send_gs_parens_e_function(s, b'\x0A', b'\x00', 3, b'\x01\x32\x32\x32\x32\x32\x32\x32\x31')
    #Check that nothing has been returned - works for all sockets, even without timeouts
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=3>: {avaliable_read[0].recv(1024)}"

    # Test GS ( E <fn=4> <a=1> read msw1 switches
    send_gs_parens_e_function(s, b'\x02', b'\x00', 4, b'\x01')
    fn4_a1_response = receive_to_null(s)
    assert fn4_a1_response == (b'\x37\x21'+ b'\x30\x30\x31\x31\x30\x30\x30\x30' +b'\x00'), f"Printer returned unexpected msw1 state : {fn4_a1_response}"
    
    # Test GS ( E <fn=4> <a=2> read msw2 switches
    send_gs_parens_e_function(s, b'\x02', b'\x00', 4, b'\x02')
    fn4_a2_response = receive_to_null(s)
    assert fn4_a2_response == (b'\x37\x21'+ b'\x31\x31\x31\x30\x30\x30\x30\x30' +b'\x00'), f"Printer returned unexpected msw2 state : {fn4_a2_response}"


    # Test GS ( E <fn=5> set customized setting values
    send_gs_parens_e_function(s, b'\x04', b'\x00', 5, b'\x03\x06\x00')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=5>: {avaliable_read[0].recv(1024)}"
    
    #Fermons la première partie du test.
    #Send a printable string for this receipt.
    s.sendall(b'Test status GS ( E - part 1 complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)
    
print("part 1 finished.")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
    s2.connect((HOST, int(PORT)))

    #Ask for each GS ( e <fn=6>  customized value
    for a in [1,2,3, 5,6,7,8,9,10,11,12,13,14, 20,21,22, 70,71,73, 97,98, 100,101,102,103,104,105,106, 111,112,113, 116]:
        send_gs_parens_e_function(s2, b'\x02', b'\x00', 6, int.to_bytes(a))
        fn6_data = receive_to_null(s2)
        assert (len(fn6_data) > 5 and len(fn6_data) < 13 ), f"Printer returned unexepected data to GS ( <fn=6> <a={a}> : {fn6_data}"            

    # Test GS ( E <fn=7> Copy the user-defined page
    send_gs_parens_e_function(s2, b'\x04', b'\x00', 7, b'\x10\x30\x31')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s2], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=7>: {avaliable_read[0].recv(1024)}"
   
    # Test GS ( E <fn=8> Define the data (column format) for the character code page
    # This command has a length between 5 and 65535.  Let's do 5.
    send_gs_parens_e_function(s2, b'\x05', b'\x00', 8, b'\x01\x08\x08\x08\x08')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s2], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=8>: {avaliable_read[0].recv(1024)}"  
    
    # Test GS ( E <fn=9> Define the data (raster format) for the character code page
    # This command has a length between 5 and 65535.  Let's do 5.
    send_gs_parens_e_function(s2, b'\x05', b'\x00', 9, b'\x01\x09\x09\x09\x09')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s2], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=9>: {avaliable_read[0].recv(1024)}"      
    
    # Test GS ( E <fn=10> Delete the data for the character code page
    send_gs_parens_e_function(s2, b'\x03', b'\x00', 10, b'\x80\x81')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s2], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=10>: {avaliable_read[0].recv(1024)}"  
    
    # Test GS ( E <fn=11> Delete the data for the character code page
    # This command has a length between 3 and 65535.  Let's do 3.
    send_gs_parens_e_function(s2, b'\x06', b'\x00', 11, b'\x0119200')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s2], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=11>: {avaliable_read[0].recv(1024)}"  
    
    # Test GS ( E <fn=12> Transmit the configuration item for the serial interface
    # The spec demands a "Header to null" response.
    send_gs_parens_e_function(s2, b'\x02', b'\x00', 12, b'\x04')
    fn12_data = receive_to_null(s2)
    # We have to check 2 things:  1) the response includes the configuration we asked for, and 2) the config itself is between 1 and 5 bytes
    # Let's use a regex
    response_regex = re.compile(b'\x37\x33(\S)\x1f(\S{1,5})\x00')
    # Extract the condition and the config from the response
    condition:bytes = response_regex.match(fn12_data).group(1)
    config:bytes = response_regex.match(fn12_data).group(2)
    
    assert condition == b'4', f"Printer did not return the right condition to GS ( E <fn=12>: {condition}"
    assert config == b'19200', f"Printer did not return the expected baud rate to GS ( E <fn=12> <a=4>: {config}"
    
    # Test GS ( E <fn=13> Set the configuration item for the Bluetooth interface
    # This command has a length between 2 and 65535.  Let's do 2.
    send_gs_parens_e_function(s2, b'\x02', b'\x00', 13, b'a1')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s2], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=13>: {avaliable_read[0].recv(1024)}"  
    
    # Test GS ( E <fn=14> Transmit the configuration item for the Bluetooth interface 
    # The spec demands a "Header to null" response.
    send_gs_parens_e_function(s2, b'\x02', b'\x00', 14, b'\x31')
    fn14_data = receive_to_null(s2)
    # We have to check 2 things:  1) the response includes the configuration we asked for, and 2) the config itself is between 1 and 64 bytes
    # Let's use a regex
    response_regex = re.compile(b'\x37\x4a([\x30|\x31|\x49])(\S{1,64})\x00')
    # Extract the condition and the config from the response
    matched = response_regex.match(fn14_data)
    
    assert matched is not None, f"Printer did not respond with the right format to GS ( E <fn=14>: {fn14_data}"
    assert matched.group(1) == b'\x31', f"Printer did not respond with the condition sent to GS ( E <fn=14>: {fn14_data}"
    
    # Test GS ( E <fn=15> Set conditions for USB interface communication
    send_gs_parens_e_function(s2, b'\x03', b'\x00', 15, b'\x20\x30')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s2], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=15>: {avaliable_read[0].recv(1024)}"      
    
    #Send a printable string for this receipt.
    s2.sendall(b'Test status GS ( E - part 2 complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s2.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s2.recv(1024)
    
print("part 2 finished.")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s3:
    s3.connect((HOST, int(PORT)))    
    
    # Test GS ( E <fn=16> Set conditions for USB interface communication
    send_gs_parens_e_function(s3, b'\x02', b'\x00', 16, b'\x01')
    #Check that at least one byte has been returned
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) > 0, f"Printer did not respond any data to GS ( E <fn=16>"    
    # We need to ingest whatever has been sent back so the next test works
    avaliable_read[0].recv(1024)
    
    # Test GS ( E <fn=48> Delete the paper layout
    send_gs_parens_e_function(s3, b'\x04', b'\x00', 48, b'\x43\x4c\x52')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=48>: {avaliable_read[0].recv(1024)}"      

    # Test GS ( E <fn=49> Set the paper layout
    # The layout has 16 bytes
    send_gs_parens_e_function(s3, b'\x10', b'\x00', 49, b'\x01\3b\x01\3b\x01\3b\x01\3b\x01\3b\x01\3b\x01\3b\x01\3b')
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=49>: {avaliable_read[0].recv(1024)}"   
    
    # Test GS ( E <fn=50> Transmit the paper layout information
    # The spec demands a "Header to null" response.
    send_gs_parens_e_function(s3, b'\x02', b'\x00', 50, b'\x40')
    fn50_data = receive_to_null(s3)
    # We have to check 2 things:  1) the response includes the configuration we asked for, and 2) the config itself is 8 blocks separated by \x1F
    # Let's use a regex
    response_regex = re.compile(b'\x37\x39((64)|(80))\x1f\S{0,3}?\x1f(\S{0,5}?\x1f){7}\x00')  
    # Extract the condition and the config from the response
    matched = response_regex.match(fn50_data)
    #Check    
    assert matched is not None, f"Printer did not respond with the right format to GS ( E <fn=50>: {fn50_data}"
    assert matched.group(1) == b'64', f"Printer did not respond with the condition sent to GS ( E <fn=50>: {fn50_data}"   
 
    # Test GS ( E <fn=51> Set the control for label paper and paper with black marks
    # The layout has 45-72 bytes. Lets send 45
    send_gs_parens_e_function(s3, b'\x2d', b'\x00', 51, b'\x05'*40)
    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s3], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=51>: {avaliable_read[0].recv(1024)}"             

    #Send a printable string for this receipt.
    s3.sendall(b'Test status GS ( E - part 3 complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s3.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s3.recv(1024)

print("part 3 finished.")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s4:
    s4.connect((HOST, int(PORT)))    
    
    # Test GS ( E <fn=52> Transmit the control settings for label paper and paper with black marks
    #the control setting value can have 0-80 bytes, lets send 10
    control_setting:bytes = b'\x08'*10
    send_gs_parens_e_function(s4, b'\x10', b'\x00', 52, b'm\x3f\x75\x40\x1f' + control_setting + b'\x00') 
        
    #We should get a CAN here
    avaliable_read, _, _ = select.select([s4], [], [], 1)
    assert len(avaliable_read) > 0, f"Printer did not respond any data to GS ( E <fn=52>" 
    can:bytes = avaliable_read[0].recv(1)
    assert can == int.to_bytes(24), f"Printer returned unexpected data to GS ( E <fn=52>: {can}" 

    # Test GS ( E <fn=99> Set internal buzzer patterns
    # The buzzer pattern bank has 1-5041 patterns of 13 bytes. Let's send one pattern.
    buzz_pattern:bytes = b'011000000000'
    n:bytes = b'\x01'
    send_gs_parens_e_function(s4, b'\x0E', b'\x00', 99, n+buzz_pattern)

    #Check that nothing has been returned
    avaliable_read, _, _ = select.select([s4], [], [], 1)
    assert len(avaliable_read) == 0, f"Printer returned unexpected data to GS ( E <fn=99>: {avaliable_read[0].recv(1024)}"   

    #Send a printable string for this receipt.
    s4.sendall(b'Test status GS ( E - part 4 complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s4.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s4.recv(1024)
    
print("Part 4 finished")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s5:
    s5.connect((HOST, int(PORT)))    
    
    # Test GS ( E <fn=100> Transmit internal buzzer patterns
    send_gs_parens_e_function(s5, b'\x02', b'\x00', 100, b'\x01')
    
    fn100_response:bytes = receive_to_null(s5)
    assert len(fn100_response) == 14, f"Printer returned unexpected data to GS ( E <fn=100>: {fn100_response}"
    
    
    #Send a printable string for this receipt.
    s5.sendall(b'Test status GS ( E - part 4 complete.\n')
    #BUG:  check why this text does not appear in the receipts.   When executing esc2thml.php from the command line, it is there in the output.

    s5.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s5.recv(1024)
    
print("Part 5 finished")

print("Test finished without exceptions")

print(f"Received {data!r}")