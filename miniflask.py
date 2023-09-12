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
            print('waiting for connection')
            conn, addr = s.accept()
            with conn:
                print (f"Adress connected: {addr}")
                taille = 0
                while True:
                    data = conn.recv(1024)  # receive 1024 bytes (or less)
                    taille += 1
                    if not data:
                        break  #pour arrêter quand tout est reçu 
                    conn.sendall(b"All done!")
                print (f"Received {taille} packets", flush=True)





app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World FLG!</p>"

if __name__ == "__main__":
    #Lancer le service TCP
    t = threading.Thread(target=launchServer)
    t.daemon = True
    t.start()

    #Lancer l'application Flask
    app.run(host='0.0.0.0', port=5000, debug=True)