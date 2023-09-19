ESC/POS virtual network printer 
----------

This is a very simple container-based ESC/POS network printer, that transforms the printed material in HTML pages and makes them avaliable in a web interface.

## Quick start

This project requires:
- A Docker installation (kubernetes should work, but is untested.)

To install from source:

```bash
wget --show-progress https://github.com/gilbertfl/escpos-netprinter/archive/refs/heads/moveToSocketServer.zip
unzip master.zip 
cd escpos-netprinter-master
docker build -t escpos-netprinter:beta .
```

To run the resulting container:
```bash
docker run -d --rm --cpus 1.8 -p 5000:5000/tcp -p 9100:9100/tcp escpos-netprinter:beta
```
It should now accept prints on the default port(9100), and you can visualize it with the web application at port 5000.  I have put a CPU usage limit as a safety, because it completely locked up my two-core PhotonOS host twice.

## Known issues
This is very deep beta software for now, so it has known major defects:
- There seems to be an infinite loop which eats up CPU time somewhere, but it's location is unknown.
- It still uses the Flask development server, so it is unsafe for public networks.