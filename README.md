ESC/POS virtual network printer 
----------

This is a very simple container-based ESC/POS network printer, that transforms the printed material in HTML pages and makes them avaliable in a web interface.

## Quick start

This project requires:
- A Docker installation (kubernetes should work, but is untested.)

To install from source:

```bash
wget --show-progress https://github.com/gilbertfl/escpos-netprinter/archive/refs/heads/master.zip
unzip master.zip 
cd escpos-netprinter-master
docker build -t escpos-netprinter:beta .
docker run -d -p 5000:5000/tcp -p 9100:9100/tcp escpos-netprinter:beta
```


