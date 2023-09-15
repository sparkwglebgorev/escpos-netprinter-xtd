from flask import Flask, send_file
from web import receipt_view
from os import getenv
import subprocess
from subprocess import CompletedProcess
from pathlib import PurePath
import random, socket, threading

#Network esc-pos printer service
def launchPrintServer():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        HOST = getenv('FLASK_RUN_HOST', '0.0.0.0')  #The print service will respond to the same adresses as Flask
        PORT = getenv('PRINTER_PORT', '9100')  #A printer should always listen to port 9100, but the Epson printers can be configured so also will we.
        s.bind((HOST, int(PORT)))  
        s.listen(1)  #Accept only one connection at a time.

        while True:  #Recevoir des connexions, une à la fois, pour l'éternité.  
            """ NOTE: On a volontairement pris la version bloquante pour s'assurer que chaque reçu va être sauvegardé puis converti avant d'en accepter un autre.
                NOTE:  il est possible que ce soit le comportement attendu de n'accepter qu'une connection à la fois.  Voir p.6 de la spécification d'un module Ethernet
                         à l'adresse suivante:  https://files.cyberdata.net/assets/010748/ETHERNET_IV_Product_Guide_Rev_D.pdf
                TODO:  peut-être implémenter certains codes de statut plus tard.  Voir l'APG Epson section "Processing the Data Received from the Printer"
             """
            print('waiting for connection')
            conn, addr = s.accept()
            with conn:
                print (f"Adress connected: {addr}", flush=True)
                binfile = open("reception.bin", "wb")

                while True:
                    data = conn.recv(1024)  # receive 1024 bytes (or less)
                    if not data:  #Quand on a reçu le signal de fin de transmission
                        binfile.close()  #Écrire le fichier et le fermer
                        break  #puis fermer la réception
                    else:
                        #Écrire les données reçues dans le fichier.
                        binfile.write(data)

                conn.sendall(b"Virtual printer: All done!")  #A enlever plus tard?  On dit au client qu'on a fini.
                conn.close()
                print ("Data received, client disconnected.", flush=True)
                
                #TODO:  traiter le fichier reception.bin pour en faire un HTML, plus possiblement informer Flask?
                recu:CompletedProcess = subprocess.run(["php", "esc2html.php", "reception.bin"], capture_output=True, text=True )
                if recu.returncode != 0:
                    print(f"Error while converting receipt: {recu.returncode}")
                    print("Error output:")
                    print(recu.stderr, flush=True)
                
                else:
                    #Si la conversion s'est bien passée, on devrait avoir le HTML

                    print (f"Receipt received")
                    #print(recu.stdout, flush=True)
                    try:
                        nouveauRecu = open(PurePath('web', 'receipts', 'myreceipt.html'), mode='wt')
                        #Écrire le reçu dans le fichier.
                        nouveauRecu.write(recu.stdout)
                        nouveauRecu.close()

                    except OSError as err:
                        print("File creation error:", err.errno, flush=True)
                    
                    

app = Flask(__name__)

@app.route("/")
def hello_world():

    #TODO: faire une interface qui présente tous les reçus qu'on a gardé.

    return "<p>Hello, World FLG!</p>"

@app.route("/recu")
def show_receipt():
    return send_file(PurePath('web', 'receipts', 'myreceipt.html'))

if __name__ == "__main__":
    #Lancer le service d'impression TCP
    t = threading.Thread(target=launchPrintServer)
    t.daemon = True
    t.start()
    print (f"Print port open", flush=True)

    #Lancer l'application Flask
    host = getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = getenv('FLASK_RUN_PORT', '5000')
    debugmode = getenv('FLASK_RUN_DEBUG', "false")
    if debugmode == 'True': 
        startDebug:bool = True
    else:
        startDebug:bool = False

    app.run(host=host, port=int(port), debug=startDebug, use_reloader=False) #On empêche le reloader parce qu'il repart "main" au complet et le service d'imprimante n'est pas conçu pour ça.