import socket, select
import argparse
import re

#This test script verifies escpos-netprinter interprets the b'\xe9' character.

#get printer host and port from command line
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='IP adress or hostname of the printer', default='localhost')
parser.add_argument('--port', help='Port of the printer', default=9100)
args = parser.parse_args()

HOST = args.host  #The IP adress or hostname of the printer
PORT = args.port  #A printer should always listen to port 9100, but the Epson printers can be configured so also will we.

print(f"Test character encoding on: {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test start")
    # Test String encoded with é - our bad one
    
    s.sendall(b'Hello, printer.\n')
    
    s.sendall(b'\r\nMontr\xe9al (Qu\xe9bec)')
    
    #Send a printable string for this receipt.
    s.sendall(b'\n\nTest xE9 complete.\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test PC437")
    # Test character encoding with configuration
    
    s.sendall(b'Hello printer.\n')
    # select no encoding -> default PC437 applies
    s.sendall("Montréal (à Québec)".encode("cp437"))
    
    s.sendall(b'\n\nTest PC437 complete\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test PC850")
    # Test character encoding with configuration
    
    s.sendall(b'Hello printer.\n')
    s.sendall(b'\x1bt\x02') #send ESC t 2 (select PC850 encoding)
    s.sendall("Montréal (à Québec)".encode("cp850"))
    
    s.sendall(b'\n\nTest PC850 complete\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test PC863")
    # Test character encoding with configuration
    
    s.sendall(b'Hello printer.\n')
    s.sendall(b'\x1bt\x04') #send ESC t 4 (select PC863 encoding)
    
    s.sendall("Montréal (à Québec)".encode("cp863"))

    s.sendall(b'\n\nTest PC863 complete\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

"""  Python does not have the cp852 encoding.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test PC852")
    # Test character encoding with configuration
    
    s.sendall(b'Hello printer.\n')
    s.sendall(b'\x1bt\x12') #send ESC t 18 (select PC8652 encoding)
    s.sendall("Montréal (à Québec)".encode("cp852"))
    s.sendall(b'\n\nTest PC863 complete\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024) """

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test PC858")
    # Test character encoding with configuration
    
    s.sendall(b'Hello printer.\n')
    s.sendall(b'\x1bt\x13') #send ESC t 19 (select PC858 encoding)
    
    s.sendall("Montréal (à Québec)".encode("cp858"))

    s.sendall(b'\n\nTest PC858 complete\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test ISO8859-2")
    # Test character encoding with configuration
    
    s.sendall(b'Hello printer.\n')
    s.sendall(b'\x1bt\x27') #send ESC t 19 (select ISO8859-2 encoding)
    
    s.sendall("Montréal (ô Québec)".encode("iso8859-2"))

    s.sendall(b'\n\nTest ISO8859-2 complete\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, int(PORT)))

    print("Test mixed code pages")
    # Test character encoding with configuration
    
    s.sendall(b'Hello printer.\n')
    
    s.sendall(b'\x1bt\x00') #send ESC t 0 (select CP437 encoding)
    s.sendall("CP437 - Montréal (à Québec)\n".encode("cp437"))
    
    s.sendall(b'\x1bt\x02') #send ESC t 2 (select PC850 encoding)
    s.sendall("PC850 - Montréal (à Québec)\n".encode("cp850"))
    
    s.sendall(b'\x1bt\x04') #send ESC t 4 (select PC863 encoding)
    s.sendall("PC863 - Montréal (à Québec)\n".encode("cp863"))
    
    s.sendall(b'\x1bt\x13') #send ESC t 19 (select PC858 encoding)
    s.sendall("PC858 - Montréal (à Québec)\n".encode("cp858"))
    
    s.sendall(b'\x1bt\x27') #send ESC t 19 (select ISO8859-2 encoding)    
    s.sendall("ISO-8859-2 - Montréal (ô Québec)\n".encode("iso8859-2"))

    s.sendall(b'\n\nTest mixed code pages complete\n')
    
    s.shutdown(socket.SHUT_WR) #Indiquer qu'on a fini de transmettre, et qu'on est prêt à recevoir.
    data = s.recv(1024)

print("Test finished without exceptions")

print(f"Received {data!r}")