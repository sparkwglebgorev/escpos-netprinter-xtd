from flask import Flask, send_file, render_template
from os import getenv, listdir
from os.path import splitext
import subprocess
from subprocess import CompletedProcess
from pathlib import PurePath
from lxml import html, etree
from datetime import datetime
from zoneinfo import ZoneInfo
import shutil

import socket, threading 
import socketserver


#Network ESC/pos printer server
class ESCPOSServer(socketserver.TCPServer):

    def handle_timeout(self) -> None:
        print ('Print service timeout!', flush=True)
        return super().handle_timeout()



#Network ESC/pos printer request handling
class ESCPOSHandler(socketserver.StreamRequestHandler):
    
    """
        TODO:  peut-être implémenter certains codes de statut plus tard.  Voir l'APG Epson section "Processing the Data Received from the Printer"
    """
    timeout = 10  #On abandonne une réception après 10 secondes - un compromis pour assurer que tout passe sans se bourrer de connections zombies.
    
    # Receive the print data and dump it in a file.
    def handle(self):
        print (f"Address connected: {self.client_address}", flush=True)
        binfile = open("reception.bin", "wb")

        #Read everything until we get EOF 
        indata:bytes = b''
        try:
            indata = self.rfile.read()
     
        except TimeoutError:
            print("Timeout while reading")
            self.connection.close()
            if len(indata) > 0:
                print(f"{len(indata)} bytes received.")
                print(indata, flush=True)
            else: 
                print("Nothing received!", flush=True)
            
                
        else:
            print(f"{len(indata)} bytes received.", flush=True)
            #Écrire les données reçues dans le fichier.
            binfile.write(indata)

            #Quand on a reçu le signal de fin de transmission
            binfile.close()  #Écrire le fichier et le fermer

            self.wfile.write(b"ESCPOS-netprinter: All done!")  #A enlever plus tard?  On dit au client qu'on a fini.
            self.wfile.flush()
            self.connection.close()

            print ("Data received, signature sent.", flush=True)
            
            #traiter le fichier reception.bin pour en faire un HTML
            self.print_toHTML("reception.bin")

    #Convertir l'impression recue en HTML et la rendre disponible à Flask
    def print_toHTML(self, binfilename:str):

        print("Impression de ", binfilename)
        recu:CompletedProcess = subprocess.run(["php", "esc2html.php", binfilename], capture_output=True, text=True )
        if recu.returncode != 0:
            print(f"Error while converting receipt: {recu.returncode}")
            print("Error output:")
            print(recu.stderr, flush=True)
        
        else:
            #Si la conversion s'est bien passée, on devrait avoir le HTML
            print (f"Receipt decoded", flush=True)
            #print(recu.stdout, flush=True)

            heureRecept = datetime.now(tz=ZoneInfo("Canada/Eastern"))
            recuConvert = self.add_html_title(heureRecept, recu.stdout)

            #print(etree.tostring(theHead), flush=True)

            try:
                nouveauRecu = open(PurePath('web', 'receipts', 'receipt{}.html'.format(heureRecept.strftime('%Y%b%d_%X%Z'))), mode='wt')
                #Écrire le reçu dans le fichier.
                nouveauRecu.write(recuConvert)
                nouveauRecu.close()

            except OSError as err:
                print("File creation error:", err.errno, flush=True)

    def add_html_title(self,heureRecept:datetime, recu:str)->str:
        
        recuConvert:etree.ElementTree  = html.fromstring(recu)

        theHead:etree.Element = recuConvert.head
        newTitle = etree.Element("title")
        newTitle.text = "Reçu imprimé le {}".format(heureRecept.strftime('%d %b %Y @ %X%Z'))
        theHead.append(newTitle)

        return html.tostring(recuConvert).decode()
                        
                    

app = Flask(__name__)

@app.route("/")
def accueil():
    return render_template('accueil.html.j2', host=getenv('FLASK_RUN_HOST', '0.0.0.0'), 
                           port=getenv('PRINTER_PORT', '9100'), 
                            debug=getenv('FLASK_RUN_DEBUG', "false") )

@app.route("/recus")
def list_receipts():
    fichiers = listdir(PurePath('web', 'receipts'))
    noms = [ splitext(filename)[0] for filename in fichiers ]
    return render_template('receiptList.html.j2', receiptlist=noms)

@app.route("/recus/<string:filename>")
def show_receipt(filename):
    return send_file(PurePath('web', 'receipts', filename))

@app.route("/newReceipt")
def publish_receipt():
    """ Get the receipt from the CUPS temp directory and publish it in the web/receipts directory and add the corresponding log to our permanent logfile"""
    heureRecept = datetime.now(tz=ZoneInfo("Canada/Eastern"))
    #NOTE: on set dans cups-files.conf le répertoire TempDir:   
    #obtenir le répertoire temporaire de CUPS de cups-files.conf
    source_dir=PurePath('/var', 'spool', 'cups', 'tmp')
    
    # specify your source file and destination file paths
    source_file = source_dir.joinpath('esc2html.html')
    destination_dir = PurePath('web', 'receipts')

    # specify your new filename
    new_filename = 'receipt{}.html'.format(heureRecept.strftime('%Y%b%d_%X%Z'))

    # create the full destination path with the new filename
    destination_file = destination_dir / new_filename

    # use shutil.copy2() to copy the file
    shutil.copy2(source_file, destination_file)

    #Load the log from /var/spool/cups/tmp/esc2html_log and append it in web/tmp/esc2html_log
    log = open(PurePath('web','tmp', 'esc2html_log'), mode='at')
    source_log = open(source_dir.joinpath('esc2html_log'), mode='rt')
    log.write(source_log.read())
    log.close()
    #remove the contents from the source log
    source_log.close()
    source_log = open(source_dir.joinpath('esc2html_log'), mode='wt')
    source_log.write('')
    source_log.close()

    #send an http acknowledgement
    return "OK"

    

def launchPrintServer(printServ:ESCPOSServer):
    #Recevoir des connexions, une à la fois, pour l'éternité.  Émule le protocle HP JetDirect
    """ NOTE: On a volontairement pris la version bloquante pour s'assurer que chaque reçu va être sauvegardé puis converti avant d'en accepter un autre.
        NOTE:  il est possible que ce soit le comportement attendu de n'accepter qu'une connection à la fois.  Voir p.6 de la spécification d'un module Ethernet
                à l'adresse suivante:  https://files.cyberdata.net/assets/010748/ETHERNET_IV_Product_Guide_Rev_D.pdf  """
    print (f"Printer port open", flush=True)
    printServ.serve_forever()


if __name__ == "__main__":

    #Obtenir les variables d'environnement
    host = getenv('FLASK_RUN_HOST', '0.0.0.0')  #By default, listen to all source addresses
    port = getenv('FLASK_RUN_PORT', '5000')
    debugmode = getenv('FLASK_RUN_DEBUG', "false")
    printPort = getenv('PRINTER_PORT', '9100')

    #Lancer le service d'impression TCP
    with ESCPOSServer((host, int(printPort)), ESCPOSHandler) as printServer:
        # t = threading.Thread(target=launchPrintServer, args=[printServer])
        # t.daemon = True
        # t.start()
    
        #Lancer l'application Flask
        if debugmode == 'True': 
            startDebug:bool = True
        else:
            startDebug:bool = False

        app.run(host=host, port=int(port), debug=startDebug, use_reloader=False) #On empêche le reloader parce qu'il repart "main" au complet et le service d'imprimante n'est pas conçue pour ça.