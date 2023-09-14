from flask import Flask
import random, socket, threading

#tcp server
HOST = ''  #Empty string accepts all origins
TCP_PORT = 9100

def launchServer():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, TCP_PORT))
        s.listen()

        while True:  #Recevoir des connexions, une à la fois, pour l'éternité.  
            """ NOTE: On a volontairement pris la version bloquante pour s'assurer que chaque reçu va être sauvegardé puis converti avant d'en accepter un autre.
                NOTE:  il est possible que ce soit le comportement attendu soit de n'accepter qu'une connection à la fois.  Voir p.6 de la spécification d'un module Ethernet
                         à l'adresse suivante:  https://files.cyberdata.net/assets/010748/ETHERNET_IV_Product_Guide_Rev_D.pdf
                TODO:  peut-être implémenter certains codes de statut plus tard.  Voir l'APG Epson section "Processing the Data Received from the Printer"
             """
            print('waiting for connection')
            conn, addr = s.accept()
            with conn:
                print (f"Adress connected: {addr}")
                binfile = open("reception.bin", "wb")

                while True:
                    data = conn.recv(1024)  # receive 1024 bytes (or less)
                    if not data:  #Quand tout a été reçu
                        binfile.close()  #Écrire le fichier et le fermer
                        break  #puis fermer la réception
                    else:
                        binfile.write(data)

                conn.sendall(b"All done!")  #A enlever plus tard?  On dit au client qu'on a fini.
                
                #TODO:  traiter le fichier reception.bin pour en faire un HTML, plus possiblement informer Flask?

                print (f"Receipt received", flush=True)





app = Flask(__name__)

@app.route("/")
def hello_world():

    #TODO: faire une interface qui présente tous les reçus qu'on a gardé.

    return "<p>Hello, World FLG!</p>"



if __name__ == "__main__":
    #Lancer le service TCP
    t = threading.Thread(target=launchServer)
    t.daemon = True
    t.start()

    #Lancer l'application Flask
    app.run(host='0.0.0.0', port=5000, debug=True)