from flask import Flask, send_file, render_template
from os import getenv, listdir
from os.path import splitext
import subprocess
from subprocess import CompletedProcess
from pathlib import PurePath
from lxml import html, etree
from datetime import datetime
from zoneinfo import ZoneInfo
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
    timeout = 30  #On abandonne une réception après 30 secondes.
    
    # Receive the print data and dump it in a file.
    def handle(self):
        print (f"Address connected: {self.client_address}", flush=True)
        binfile = open("reception.bin", "wb")

        #Lire tout jusqu'à ce qu'on ait EOF 
        indata:bytes = b''
        try:
            indata = self.rfile.read()
     
        except TimeoutError:
            print("Timeout while reading")
            if len(indata) > 0:
                print(f"{len(indata)} bytes received.")
                print(indata, flush=True)
            else: 
                print("Nothing received!")
                
        else:
            print(f"{len(indata)} bytes received.", flush=True)
            #Écrire les données reçues dans le fichier.
            binfile.write(indata)

            #Quand on a reçu le signal de fin de transmission
            binfile.close()  #Écrire le fichier et le fermer

            self.wfile.write(b"Virtual printer: All done!")  #A enlever plus tard?  On dit au client qu'on a fini.
            self.wfile.flush()

            print ("Data received, ACK sent.", flush=True)
            
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

            recuConvert:etree.ElementTree  = html.fromstring(recu.stdout)

            theHead:etree.Element = recuConvert.head
            newTitle = etree.Element("title")
            newTitle.text = "Reçu imprimé le {}".format(heureRecept.strftime('%d %b %Y @ %X%Z'))
            theHead.append(newTitle)

            #print(etree.tostring(theHead), flush=True)

            try:
                nouveauRecu = open(PurePath('web', 'receipts', 'receipt{}.html'.format(heureRecept.strftime('%Y%b%d_%X%Z'))), mode='wt')
                #Écrire le reçu dans le fichier.
                nouveauRecu.write(html.tostring(recuConvert).decode())
                nouveauRecu.close()

            except OSError as err:
                print("File creation error:", err.errno, flush=True)
                        
                    

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
    

def launchPrintServer(printServ:ESCPOSServer):
    #Recevoir des connexions, une à la fois, pour l'éternité.  
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
        t = threading.Thread(target=launchPrintServer, args=[printServer])
        t.daemon = True
        t.start()
    
        #Lancer l'application Flask
        if debugmode == 'True': 
            startDebug:bool = True
        else:
            startDebug:bool = False

        app.run(host=host, port=int(port), debug=startDebug, use_reloader=False) #On empêche le reloader parce qu'il repart "main" au complet et le service d'imprimante n'est pas conçu pour ça.