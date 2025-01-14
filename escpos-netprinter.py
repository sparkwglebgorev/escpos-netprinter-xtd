import os
from flask import Flask, redirect, render_template, request, url_for
from os import getenv
from io import BufferedWriter
import csv
import subprocess
from subprocess import CompletedProcess
from pathlib import PurePath
from lxml import html, etree
from datetime import datetime
from zoneinfo import ZoneInfo

import threading 
import socketserver


#Network ESC/pos printer server
class ESCPOSServer(socketserver.TCPServer):

    def handle_timeout(self) -> None:
        print ('Print service timeout!', flush=True)
        return super().handle_timeout()



#Network ESC/pos printer request handling
class ESCPOSHandler(socketserver.StreamRequestHandler):
    
    """
        Voir l'APG Epson section "Processing the Data Received from the Printer"
    """
    timeout = 10  #On abandonne une réception après 10 secondes - un compromis pour assurer que tout passe sans se bourrer de connections zombies.
    netprinter_debugmode = "false"
    
    # Receive the print data and dump it in a file.
    def handle(self):
        print (f"Address connected: {self.client_address}", flush=True)
        self.netprinter_debugmode = getenv('ESCPOS_DEBUG', "false")
        bin_filename = PurePath('web', 'tmp', "reception.bin")
        with open(bin_filename, "wb") as binfile:

            #Read everything until we get EOF, and keep everything in a receive buffer
            receive_buffer:bytes = b''

            try:
                # Implement the "Real-time command processing" block described in the Epson APG.
                # How:  Skim the received data byte by byte to respond to status checks as they come.   
                # We are making this as simple as possible so we do not slow down the print:  
                #   1)  watch for ESC/POS commands that could lead to a status request               
                #   2)  If this byte is none of those, send it forward without further processing
                #   3)  If this byte is a candidate command:
                #       a) Check a second byte for a status request
                #       b) if the second byte does not indicate a status request, send the two bytes forward without further processing
                #       c) if the second byte indicates a status request, reply appropriately then send all processed data bytes forward
                
                while (indata_statuscheck := self.rfile.read(1)):
                    match indata_statuscheck:
                        case b'\x10' | b'\x1D' :  # DLE or GS
                            #This is potentially a status request.
                            indata_statuscheck = indata_statuscheck + self.rfile.read(1) #Get the second command byte

                            match indata_statuscheck:
                                case b'\x10\x04':
                                    # Respond to DLE EOT status requests
                                    dle_eot_data:bytes = self.respond_dle_eot()
                                    indata_statuscheck = indata_statuscheck + dle_eot_data #append the DLE EOT bytes to the processed bytes
                                    if self.netprinter_debugmode == True:
                                        print(f"DLE EOT received containing {len(indata_statuscheck)} bytes", flush=True)

                                case b'\x10\x14':
                                    # Respond to DLE DC4 <fn=7> 
                                    dle_dc4_data: bytes = self.respond_dle_dc4()
                                    indata_statuscheck = indata_statuscheck + dle_dc4_data
                                    if self.netprinter_debugmode == True:
                                        print(f"DLE EOT received containing {len(indata_statuscheck)} bytes", flush=True)

                                case b'\x1D\x72':
                                    #Respond to GS r status requests
                                    gs_r_data:bytes = self.respond_gs_r()
                                    indata_statuscheck = indata_statuscheck + gs_r_data
                                    if self.netprinter_debugmode == True:
                                        print(f"GS r received containing {len(indata_statuscheck)} bytes", flush=True)

                                case b'\x1D\x49':
                                    # Respond to GS I printer ID request
                                    gs_i_data:bytes = self.respond_gs_i()
                                    indata_statuscheck = indata_statuscheck + gs_i_data
                                    if self.netprinter_debugmode == True:
                                        print(f"GS i received containing {len(indata_statuscheck)} bytes", flush=True)

                                case b'\x1D\x67':
                                    # Respond to GS g <fn=2> maintenance counter request
                                    gs_g2_data:bytes = self.respond_gs_g()
                                    indata_statuscheck = indata_statuscheck + gs_g2_data
                                    if self.netprinter_debugmode == True:
                                        print(f"GS g received containing {len(indata_statuscheck)} bytes", flush=True)
                                
                                case b'\x1D\x28':
                                    # Respond to GS ( E and GS ( H requests
                                    gs_parens_data:bytes = self.respond_gs_parens()
                                    indata_statuscheck = indata_statuscheck + gs_parens_data
                                    if self.netprinter_debugmode == True:
                                        print(f"GS ( received containing {len(indata_statuscheck)} bytes", flush=True)

                                case _:
                                    #This is not a status request
                                    if self.netprinter_debugmode == True:
                                        print(f"Almost-status bytes: {indata_statuscheck}", flush=True)
                        case b'\x1C':  #FS
                            indata_statuscheck = indata_statuscheck + self.rfile.read(1) #Get the second command byte
                            match indata_statuscheck:
                                case b'\x1C\x28':
                                    #This a FS ( request
                                    fs_parens_data:bytes = self.respond_fs_parens()
                                    indata_statuscheck = indata_statuscheck + fs_parens_data
                                    if self.netprinter_debugmode == True:
                                        print(f"FS ( received containing {len(indata_statuscheck)} bytes", flush=True)

                                case b'\x1C\x26' | b'\x1C\x2E':
                                    #Subrequests with zero argument bytes
                                    pass
                                
                                case b'\x1C\x21' | b'\x1C\x2D' | b'\x1C\x43'| b'\x1C\x57':
                                    #Subrequests with one argument byte
                                    #Munch on it and pass it on
                                    indata_statuscheck = indata_statuscheck + self.rfile.read(1)
                                
                                case b'\x1C\x3F' | b'\x1C\x53' | b'\x1C\x70':
                                    #Subrequests with 2 argument bytes
                                    #Munch on em and pass it on
                                    indata_statuscheck = indata_statuscheck + self.rfile.read(2)

                                case b'\x1C\x32':
                                    #TODO: FS 2 command has c1 c2 then k bits (arbitrarily decided by the printer??)
                                    pass

                                case b'\x1C\x67':
                                    #TODO: FS g 1 has m then 4 a bytes then nl, ng then (nL + nH × 256) data bytes
                                    #TODO: FS g 2 has m then 4 a bytes then nl, ng.  sends back "header to NUL"
                                    pass

                                case b'\x1C\x71':
                                    #TODO: FS q has n then a ton of bytes.   I just can't.
                                    pass

                                case _:
                                    if self.netprinter_debugmode == 'True':
                                        print("Unknown FS request received: " + indata_statuscheck, flush=True)
                        case _:
                            #This byte is uninteresting data for this block's purposes, no processing necessary.
                            pass

                    #Append the processed byte(s) to the receive buffer
                    receive_buffer = receive_buffer + indata_statuscheck

        
            except TimeoutError:
                print("Timeout while reading")
                self.connection.close()
                if len(receive_buffer) > 0:
                    print(f"{len(receive_buffer)} bytes received.")
                    if self.netprinter_debugmode == 'True':
                        print("-----start of data-----\n", flush=True)
                        print(receive_buffer, flush=True)
                        print("\n-----end of data-----", flush=True)
                else: 
                    print("No data received!", flush=True)
                
                    
            else:
                #Quand on a reçu le signal de fin de transmission
                print(f"{len(receive_buffer)} bytes received.", flush=True)

                if self.netprinter_debugmode == 'True':
                    print("-----start of data-----\n", flush=True)
                    print(receive_buffer, flush=True)
                    print("\n-----end of data-----", flush=True)

                #Écrire les données reçues dans le fichier.
                if len(receive_buffer) > 0:
                    binfile.write(receive_buffer)
                    binfile.close()  #Écrire le fichier et le fermer
                    #traiter le fichier reception.bin pour en faire un HTML
                    self.print_toHTML(binfile, bin_filename)
                elif self.netprinter_debugmode == 'True':
                        print("No data received: nothing will be printed.", flush=True)

        #The binfile should auto-close here.

        self.wfile.write(b"ESCPOS-netprinter: All done!")  #A enlever plus tard?  On dit au client qu'on a fini.
        self.wfile.flush()
        self.connection.close()

        print ("Data received, signature sent.", flush=True)

    def respond_dle_dc4(self) -> bytes:
        #Consume a DLE DC4 request and respond to <fn=7>
        if self.netprinter_debugmode == 'True': 
            print("DLE DC4 request", flush=True)
        next_in:bytes = self.rfile.read(1)  #Get the first byte
        match next_in:
            case b'\x07':
                # Respond to a real-time ASB request
                m:bytes = self.rfile.read(1)
                match m:
                    case b'\x01':
                        #Transmit the 4 bytes of the all-clear ASB status like GS a
                        self.wfile.write(b'\x00\x00\x00\x00')
                        self.wfile.flush()
                        if self.netprinter_debugmode == 'True':
                            print("4-byte ASB status sent", flush=True) 
                    
                    case b'\x02':
                        #Transmit the 4 bytes of the all-clear extended ASB status like FS ( e 
                        self.send_extended_ASB_OK()
                    
                    case b'\x04':
                        #Transmit the offline response like GS ( H <f=49>
                        #TODO: The spec is not very clear on how to respond since GS ( h is a configuration request
                        pass

                    case _:
                        if self.netprinter_debugmode == 'True':
                            print("Unknown DLE DC4 <fn=7> request received: " + m, flush=True)

                next_in = next_in + m

            case _:
                #This request is about something else, nothing to do.
                if self.netprinter_debugmode == 'True':
                    print("Non-status DLE DC4 request received: " + next_in, flush=True)
        return next_in

    def respond_fs_parens(self) -> bytes:
        #Consume and process one FS ( request
        if self.netprinter_debugmode == 'True': 
            print("FS ( request", flush=True)
        next_in:bytes = self.rfile.read1(1)  #The n is at most 1 byte
        match next_in:
            case b'\x65':  # e
                # Enable/disable Automatic Status Back (ASB) for optional functions (extended status)
                #  First, get the next bytes
                pL:bytes = self.rfile.read(1) # Get pL byte 
                pH:bytes = self.rfile.read(1) # Get pH byte
                m:bytes = self.rfile.read(1) # Get m byte
                n:bytes = self.rfile.read(1) # Get n byte
                next_in = next_in + pL + pH + m + n # Send these bytes forward in all cases

                match n:
                    case b'\x00':
                        #Request disable ASB:  nothing to return
                        pass
                    case _:
                        #Enabling any status (specifying n != 0) starts extended ASB
                        self.send_extended_ASB_OK() 

            case b'\x41'| b'\x43' | b'\x45' | b'\x4C': # A, C or E :  
                # These are not relevant functions, so we consume those bytes and send them forward.
                # These all include pl, ph, fn and some bytes.  
                # pL and pH specify the number of bytes following fn as (pL + (pH × 256)). 

                #  First, get the size and fn bytes
                pL:int = int.from_bytes(self.rfile.read(1), "big") # Get pL value 
                pH:int = int.from_bytes(self.rfile.read(1), "big") # Get pH value
                fn:bytes = self.rfile.read(1) # Get fn byte
                next_in = next_in + pL + pH + fn

                num_bytes:int = pL + (pH * 256) # Range:  1 - 65535
                if num_bytes == 0:
                    print("Error:  zero-byte-long argument specified", flush=True)
                
                next_in = next_in + self.rfile.read(num_bytes) # Send these bytes forward in all cases

            case _:
                if self.netprinter_debugmode == 'True':
                    print("Unknown FS ( request received: " + next_in, flush=True)

        return next_in

    def send_extended_ASB_OK(self):
        #Return all-clear extended ASB status (\x00)
        self.wfile.write(b'\x39\x00\x40\x00')  
        self.wfile.flush()
        if self.netprinter_debugmode == 'True':
            print("4-byte extended ASB status sent", flush=True)

    def respond_gs_g(self) -> bytes:
        #Consume a GS G request and respond to <fn=2>
        if self.netprinter_debugmode == 'True': 
            print("GS g request", flush=True)
        next_in:bytes = self.rfile.read(2)  #Get the 2 and m bytes
        match next_in:
            case b'\x32\x00': 
                #Respond to GS g 2 with a constant number
                #TODO: someday implement counters in case some client checks their progress
                next_in = next_in + self.rfile.read(2)  #Get 2 more bytes (nL and nH)
                self.wfile.write(b'\x5F\x01\x00') #Send one(1) for all counters
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("4-byte extended ASB status sent", flush=True) 

            case _:
                if self.netprinter_debugmode == 'True':
                    print("Non-status GS g request received: " + next_in, flush=True)

        return next_in

    def respond_gs_i(self) -> bytes:
        #Consume and process one GS i request

        #First, define inner helper functions
        def send_gs_i_printer_info_A(contents:bytes) -> None:
            #Helper to respond with Printer Info A
            self.wfile.write(b'\x3D') #Header
            self.wfile.write(contents[:80])  # Max 80 bytes here, so send only that slice
            self.wfile.write(b'\x00') #NUL
            self.wfile.flush()
    
        def send_gs_i_printer_info_B(contents:bytes) -> None:
            #Helper to respond with Printer Info B
            self.wfile.write(b'\x5F') #Header
            self.wfile.write(contents[:80])  # Max 80 bytes here, so send only that slice
            self.wfile.write(b'\x00') #NUL
            self.wfile.flush()

        # Let's do this
        if self.netprinter_debugmode == 'True': 
            print("GS i request", flush=True)
        next_in:bytes = self.rfile.read1(1)  #The n is at most 1 byte
        match next_in:
            case b'\x01' | b'\x31':  #1 or 49
                #Transmit some printer model ID byte
                self.wfile.write(b'\x01') #TODO: choose a model ID
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Printer model ID byte sent", flush=True)   
            
            case b'\x02' | b'\x32': # 2 or 50
                #Transmit Printer type ID
                self.wfile.write(b'\x02') # No multi-byte chars, autocutter installed, no DM-D
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Printer type ID byte sent", flush=True)   

            case b'\x03' | b'\x33': # 3 or 51
                #Transmit some version ID byte
                self.wfile.write(b'\x01') #TODO: choose a version ID
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Printer version ID byte sent", flush=True)   

            case b'\x21':  # 33
                #Transmit printer type information - supported functions
                # We send a 3-byte all-clear response
                first_byte = b'\x02' # No multi-byte chars, autocutter installed, no DM-D
                second_byte = b'\x40' #Fixed
                third_byte = b'\x40'  #No peeler.
                send_gs_i_printer_info_A(next_in + first_byte + second_byte + third_byte)
                if self.netprinter_debugmode == 'True':
                    print("Printer supported functions sent", flush=True)                 

            case b'\x41': # 65
                #Transmit printer firmware version
                send_gs_i_printer_info_B(b'netprinter_1')  #TODO: choose a version number
                if self.netprinter_debugmode == 'True':
                    print("Printer firmware version sent", flush=True) 

            case b'\x42' | b'\x43':  # 66 or 67
                #Transmit maker name or model name - could be different but not important.
                send_gs_i_printer_info_B(b'ESCPOS-netprinter')
                if self.netprinter_debugmode == 'True':
                    print("Printer maker or model name sent", flush=True) 
          
            case b'\x44': # 68
                #Transmit printer serial number
                send_gs_i_printer_info_B(b'netprinter_1')
                if self.netprinter_debugmode == 'True':
                    print("Printer serial sent", flush=True) 

            case b'\x45': # 69
                #Transmit printer font of language
                # TODO: we send an empty response but testing is needed
                send_gs_i_printer_info_B(b'')
                if self.netprinter_debugmode == 'True':
                    print("Empty language sent", flush=True) 

            case _:
                if self.netprinter_debugmode == 'True':
                    print("Unknown GS i request received: " + next_in, flush=True)

        return next_in

    def respond_gs_r(self) -> bytes:
        #Consume and process one GS r request
        if self.netprinter_debugmode == 'True': 
            print("GS r request", flush=True)
        next_in:bytes = self.rfile.read1(1)  #The n is at most 1 byte
        match next_in:
            case b'\x01':  #n=1
                #Send paper status adequate and present
                self.wfile.write(b'\x00')
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Paper status sent", flush=True) 
            case b'\x31':  #n=49
                #Send paper status adequate and present (alternate)
                self.wfile.write(b'\x00')
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Paper status sent", flush=True) 
            case b'\x02':  #n=2
                #Send drawer kick-out connector status
                self.wfile.write(b'\x00')
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Drawer kick-out status sent", flush=True) 
            case b'\x32':  #n=50
                #Send drawer kick-out connector status (alternate)
                self.wfile.write(b'\x00')
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Drawer kick-out status sent", flush=True) 
            case b'\x04':  #n=4
                #Send ink status adequate
                self.wfile.write(b'\x00')
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Ink status sent", flush=True) 
            case b'\x34':  #n=52
                #Send ink status adequate
                self.wfile.write(b'\x00')
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Ink status sent", flush=True)
            case _:
                if self.netprinter_debugmode == 'True':
                    print("Unknown GS r request received: " + next_in, flush=True)
        return next_in
    
    def respond_gs_parens(self) -> bytes:
        #Consume and process one GS ( request

        next_in:bytes = self.rfile.read(1) #Start by getting the next byte
        match next_in:
            case b'\x45': #E
                #Set user setup command
                pL:bytes = self.rfile.read(1) # Get pL byte 
                pH:bytes = self.rfile.read(1) # Get pH byte
                fn:bytes = self.rfile.read(1) # Get fn byte
                next_in = next_in + pL + pH + fn # Send these bytes forward in all cases
                match fn:
                    case b'\x01':
                        # Respond to user setting mode start request
                        next_in = next_in + self.rfile.read(2) #read d1 and d2
                        self.wfile.write(b'\x37\x20\x00')  # Respond OK
                        self.wfile.flush()
                        if self.netprinter_debugmode == 'True':
                            print("Mode change notice sent", flush=True)

                    case b'\x04':
                        # Respond with settings of the memory switches
                        a:bytes = self.rfile.read(1)  #read a
                        next_in = next_in + a
                        match a:
                            case b'\x01':
                                # Respond with: Power-on notice disabled, Receive buffer large, busy when buffer full, 
                                #               receive error ignored, auto line-feed disabled, DM-D not connected,
                                #               RS-232 pins 6 and 25 not used.
                                response:bytes = b'\x30\x30\x31\x31\x30\x30\x30\x30'
                                self.wfile.write(b'\x37\x21' + response + b'\x00') 
                                self.wfile.flush()
                                if self.netprinter_debugmode == 'True':
                                    print("Msw1 switches sent", flush=True)
                            case b'\x02':
                                # Respond with: Autocutter enabled and chinese character code GB2312.
                                response:bytes = b'\x31\x31\x31\x30\x30\x30\x30\x30'
                                self.wfile.write(b'\x37\x21' + response + b'\x00') 
                                self.wfile.flush()
                                if self.netprinter_debugmode == 'True':
                                    print("Msw2 switches sent", flush=True)
                            case _:
                                if self.netprinter_debugmode == 'True':
                                    print("Unknown switch set requested", flush=True)

                    case b'\x06': #6
                        """ TODO: This one has a LOT of info to return.  TBD later.
                        a:bytes = self.rfile.read(1)  #read a
                        next_in = next_in + a
                         match a:
                            case b'\x01':
                                #Memory capacity
                                response:bytes = b''
                                self.wfile.write(b'\x37\x27' + a + b'\x1F' + response + b'\x00') 
                                self.wfile.flush()
                                if self.netprinter_debugmode == 'True':
                                    print("Customized setting {a} sent", flush=True) """
                        pass

                    case b'\x0C': # 12
                        """TODO: this one is for serial flow control.  Probably never happens over Ethernet"""
                        pass

                    case b'\x0E':  #14
                        """TODO: this one is for Bluetooth interface config.  Probably never happens over Ethernet"""
                        pass

                    case b'\x10':  #16
                        """TODO: this one is for USB interface config.  Probably never happens over Ethernet"""
                        pass

                    case b'\x32':  #50
                        # Transmit the paper layout information
                        n:bytes = self.rfile.read(1)  #read n
                        next_in = next_in + n
                        match n:
                            case b'\x40' | b'\x50':  #64 (set) or 80(actual)
                                #Setting values - only useful for labels so not used
                                separator = b'\x1F'
                                sa = b'48' #Paper layout is not used
                                sb = b'' #Value omitted
                                sc = b'' #Value omitted
                                sd = b'' #Value omitted
                                se = b'' #Value omitted
                                se = b'' #Value omitted
                                response:bytes = sa +separator+ sb +separator+ sc +separator+ sd +separator+ se
                                self.wfile.write(b'\x37\x39' + n + b'\x1F' + response + b'\x00') 
                                self.wfile.flush()
                                if self.netprinter_debugmode == 'True':
                                    print("Paper layout sent", flush=True)
                            case _:
                                if self.netprinter_debugmode == 'True':
                                    print("Unknown paper layout info request: " + next_in, flush=True)

                    case b'\x64':  #100:
                        #Transmit internal buzzer patterns
                        a:bytes = self.rfile.read(1)  #read a, the desired pattern
                        next_in = next_in + a

                        # Extracted from the Epson docs:
                        # [n m1 t1 m2 t2 m3 t3 m4 t4 m5 t5 m6 t6] (13 bytes) is processed as one sound pattern. 
                        # When the setting of "Duration time" is (t = 0), it is 1-byte data of "0" [Hex = 30h / Decimal = 48].
                        # When the setting of "Duration time" is (t = 100), it is 3-byte data of "100" [Hex = 31h, 30h, 30h / Decimal = 49, 48, 48].
                        # NOTE: there is no mention in the spec for the m fields, so I will assume it's the same as t:  char-to-hex.

                        # Our pattern will be "silence for 0 seconds, 6 times"
                        pattern = b'000000000000' 
                        self.wfile.write(a + pattern + b'\x00')  #The data has to be sent "Header to NUL" with a as a header.
                        self.wfile.flush()
                        if self.netprinter_debugmode == 'True':
                            print("Buzzer pattern sent", flush=True)

                    case _:
                        #Any other functions that do not transmit data back
                        if self.netprinter_debugmode == 'True':
                            print("No-response-needed GS ( E command received: " + next_in + pL + pH + fn, flush=True)
               
            case b'\x48': #H
                #TODO: Transmission + response or status
                pass

            case _:
                if self.netprinter_debugmode == 'True':
                    print("Non-status GS ( request received: " + next_in, flush=True)
        
        return next_in


    def respond_dle_eot(self) -> bytes:
        # Consume and process one DLE EOT command and return the processed bytes
        if self.netprinter_debugmode == 'True':
            print("DLE EOT request", flush=True)
        next_in:bytes = self.rfile.read1(1)  #The ops are 1 or 2 bytes, check the first
        match next_in:
            case b'\x01':
                # Send printer status OK
                self.wfile.write(b'\x16') 
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Printer status sent", flush=True)
            case b'\x04':
                # Send roll paper status "present and adequate"
                self.wfile.write(b'\x12') 
                self.wfile.flush()
                if self.netprinter_debugmode == 'True':
                    print("Paper status sent", flush=True)   
            case _:
                #2 byte ops are not relevant for this project, so we ignore them after consuming the second byte -> NOTE: this could block the print.
                next_in = next_in + self.rfile.read(1)  #NOTE: this will block if there are no more bytes in the stream.
        return next_in
            
            

    #Convertir l'impression recue en HTML et la rendre disponible à Flask
    # Implémente les blocs "Main processing" et "Mechanism" de l'APG Epson.
    def print_toHTML(self, binfile:BufferedWriter, bin_filename:PurePath):

        print("Printing ", binfile.name)
        try:
            if self.netprinter_debugmode == 'True':
                recu:CompletedProcess = subprocess.run(["php", "esc2html.php", "--debug", bin_filename.as_posix()], capture_output=True, text=True, check=True)
            else:
                recu:CompletedProcess = subprocess.run(["php", "esc2html.php", bin_filename.as_posix()], capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError as err:
            print(f"Error while converting receipt: {err.returncode}")
            # append the error output to the log file
            with open(PurePath('web','tmp', 'esc2html_log'), mode='at') as log:
                log.write(f"Error while converting a JetDirect print: {err.returncode}")
                log.write(datetime.now(tz=ZoneInfo("Canada/Eastern")).strftime('%Y%b%d %X.%f %Z'))
                log.write(err.stderr)
                log.close()
            
            print("Error output:")
            print(err.stderr, flush=True)
        
        else:
            #Si la conversion s'est bien passée, on devrait avoir le HTML
            print (f"Receipt decoded", flush=True)
            with open(PurePath('web','tmp', 'esc2html_log'), mode='at') as log:
                log.write("Successful JetDirect print\n")
                log.write(datetime.now(tz=ZoneInfo("Canada/Eastern")).strftime('%Y%b%d %X.%f %Z\n\n'))
                log.write(recu.stderr)
                log.close()
            #print(recu.stdout, flush=True)

            #Ajouter un titre au reçu
            heureRecept = datetime.now(tz=ZoneInfo("Canada/Eastern"))
            recuConvert = self.add_html_title(heureRecept, recu.stdout)

            #print(etree.tostring(theHead), flush=True)

            try:
                #Créer un nouveau fichier avec le nom du reçu
                html_filename = 'receipt{}.html'.format(heureRecept.strftime('%Y%b%d_%X.%f%Z'))
                with open(PurePath('web', 'receipts', html_filename), mode='wt') as nouveauRecu:
                    #Écrire le reçu dans le fichier.
                    nouveauRecu.write(recuConvert)
                    nouveauRecu.close()
                    #Ajouter le reçu à la liste des reçus
                    self.add_receipt_to_directory(html_filename)

            except OSError as err:
                print("File creation error:", err.errno, flush=True)

    @staticmethod
    def add_html_title(heureRecept:datetime, recu:str, self=None)->str:
        """ Ajouter un titre au reçu """
        recuConvert:etree.ElementTree  = html.fromstring(recu)

        theHead:etree.Element = recuConvert.head
        newTitle = etree.Element("title")
        newTitle.text = "Reçu imprimé le {}".format(heureRecept.strftime('%d %b %Y @ %X%Z'))
        theHead.append(newTitle)

        return html.tostring(recuConvert).decode()
    
    @staticmethod
    def add_receipt_to_directory(new_filename: str, self=None) -> None:
        # Add an entry in the reference file with the new filename and an unique ID.
        # Open the CSV file in read mode to count the existing rows
        try:
            with open(PurePath('web', 'receipt_list.csv'), mode='r') as fileDirectory:
                reader = csv.reader(fileDirectory)
                # Count the number of rows, starting from 1 (to include the header)
                next_fileID = sum(1 for row in reader) + 1
                fileDirectory.close()
        except FileNotFoundError:
            # Create the CSV file with the headers
            with open(PurePath('web', 'receipt_list.csv'), mode='w', newline='') as fileDirectory:
                writer = csv.writer(fileDirectory)
                writer.writerow(['next_fileID', 'filename'])
                fileDirectory.close()
            next_fileID = 1  # If the file does not exist, start IDs is 1
        # Now, id holds the next sequential ID

        # Open the CSV file in append mode to add a new row
        with open(PurePath('web', 'receipt_list.csv'), mode='a', newline='') as fileDirectory:
            writer = csv.writer(fileDirectory)
            # Append a new line to the CSV file with the new ID and filename
            writer.writerow([next_fileID, new_filename])    
               

app = Flask(__name__)

@app.route("/")
def accueil():
    return render_template('accueil.html.j2', host = request.host.split(':')[0], 
                           jetDirectPort=getenv('PRINTER_PORT', '9100'),
                            debug=getenv('FLASK_RUN_DEBUG', "false") )

@app.route("/recus")
def list_receipts():
    """ List all the receipts available """
    try:
        with open(PurePath('web', 'receipt_list.csv'), mode='r') as fileDirectory:
            # Skip the header and get all the filenames in a list
            reader = csv.reader(fileDirectory)
            noms = list()
            for row in reader:
                if row[0] == 'next_fileID':
                    continue # Skip the header
                else:
                    # Add the file id and filename to the list
                    noms.append([row[0], row[1]])
            # Since the file is found, render the template with the list of filenames
            # in reverse chronological order (most recent at the top)
            noms.reverse()
            return render_template('receiptList.html.j2', receiptlist=noms)
    except FileNotFoundError:
        return redirect(url_for('accueil'))
    

@app.route("/recus/<int:fileID>")
def show_receipt(fileID:int):
    """ Show the receipt with the given ID """
    # Open the CSV file in read mode
    with open(PurePath('web', 'receipt_list.csv'), mode='r') as fileDirectory:
        reader = csv.reader(fileDirectory)
        # Find the row with the given ID
        for row in reader:
            if row[0] == 'next_fileID':
                continue # Skip the header
            elif int(row[0]) == fileID:
                filename = row[1]
                break
        else:
            # If the ID is not found, return a 404 error
            return "Not found", 404
        
        # If the ID is found, open the html rendering of the receipt and add the footer from templates/footer.html
        with open(PurePath('web', 'receipts', filename), mode='rt') as receipt:
            receipt_html = receipt.read()   # Read the file content
            receipt_html = receipt_html.replace('<body>', '<body style="display: flex;flex-direction: column;min-height: 100vh;"><div id="page" style="flex-grow: 1;">')
            receipt_html = receipt_html.replace('</body>', '</div>' + render_template('footer.html') + '</body>')  # Append the footer
            return receipt_html
    

@app.route("/newReceipt")
def publish_receipt_from_CUPS():
    """ Get the receipt from the CUPS temp directory and publish it in the web/receipts directory and add the corresponding log to our permanent logfile"""
    heureRecept = datetime.now(tz=ZoneInfo("Canada/Eastern"))
    #NOTE: on set dans cups-files.conf le répertoire TempDir:   
    #Extraire le répertoire temporaire de CUPS de cups-files.conf
    source_dir=PurePath('/var', 'spool', 'cups', 'tmp')
    
    # Get the source filename from the environment variable and create the full path
    source_filename = os.environ['DEST_FILENAME']
    source_file = source_dir.joinpath(source_filename)

    # specify the destination filename
    new_filename = 'receipt{}.html'.format(heureRecept.strftime('%Y%b%d_%X.%f%Z'))

    # Create the full destination path with the new filename
    destination_file = PurePath('web', 'receipts', new_filename)

    # Read the source file, add the title and write it in the destination file
    with open(source_file, mode='rt') as receipt:
        receipt_html = receipt.read()
        receipt_html = ESCPOSHandler.add_html_title(heureRecept, receipt_html)
        with open(destination_file, mode='wt') as newReceipt:
            newReceipt.write(receipt_html)
            newReceipt.close()

    # Add the new receipt to the directory
    ESCPOSHandler.add_receipt_to_directory(new_filename)

    #Load the log file from /var/spool/cups/tmp/ and append it in web/tmp/esc2html_log
    logfile_filename = os.environ['LOG_FILENAME']
    # print(logfile_filename)
    log = open(PurePath('web','tmp', 'esc2html_log'), mode='wt')
    source_log = open(source_dir.joinpath(logfile_filename), mode='rt')
    log.write(f"CUPS print received at {datetime.now(tz=ZoneInfo('Canada/Eastern')).strftime('%Y%b%d %X.%f %Z')}\n")
    log.write(source_log.read())
    log.close()
    source_log.close()

    #send an http acknowledgement
    return "OK"


def launchPrintServer(printServ:ESCPOSServer):
    #Recevoir des connexions, une à la fois, pour l'éternité.  Émule le protocle HP JetDirect
    """ NOTE: On a volontairement pris la version bloquante pour s'assurer que chaque reçu va être sauvegardé puis converti avant d'en accepter un autre.
        NOTE:  il est possible que ce soit le comportement attendu de n'accepter qu'une connection à la fois.  Voir p.6 de la spécification d'un module Ethernet
                à l'adresse suivante:  https://files.cyberdata.net/assets/010748/ETHERNET_IV_Product_Guide_Rev_D.pdf  """
    print (f"JetDirect port open", flush=True)
    printServ.serve_forever()


if __name__ == "__main__":

    #Obtenir les variables d'environnement
    host = getenv('FLASK_RUN_HOST', '0.0.0.0')  #By default, listen to all source addresses
    port = getenv('FLASK_RUN_PORT', '5000')
    flask_debugmode = getenv('FLASK_RUN_DEBUG', "false")
    printPort = getenv('PRINTER_PORT', '9100')

    print("Starting ESCPOS-netprinter", flush=True)

    #Lancer le service d'impression TCP
    with ESCPOSServer((host, int(printPort)), ESCPOSHandler) as printServer:
        t = threading.Thread(target=launchPrintServer, args=[printServer])
        t.daemon = True
        t.start()
    
        #Lancer l'application Flask
        if flask_debugmode == 'True': 
            startDebug:bool = True
        else:
            startDebug:bool = False

        app.run(host=host, port=int(port), debug=startDebug, use_reloader=False) #On empêche le reloader parce qu'il repart "main" au complet et le service d'imprimante n'est pas conçue pour ça.