ESC/POS virtual network printer 
----------

This is a container-based ESC/POS network printer, that replaces paper rolls with HTML pages and a web interface.

The printer emulates a 80mm roll of paper.

![sample print](https://github.com/gilbertfl/escpos-netprinter/assets/83510612/8aefc8c5-01ab-45f3-a992-e2850bef70f6)

## Limits
This docker image is not to be exposed on a public network (see [known issues](#known-issues))

A print cannot last longer than 10 seconds.  This timeout could be changed at some point, or made configurable.

## Quick start

This project requires:
- A Docker installation (kubernetes should work, but is untested.)

To install from source:

```bash
wget --show-progress https://github.com/gilbertfl/escpos-netprinter/archive/refs/heads/master.zip
unzip master.zip 
cd escpos-netprinter-master
docker build -t escpos-netprinter:2.0 .
```

To run the resulting container:
```bash
docker run -d --rm --name escpos_netprinter -p 515:515/tcp -p 80:80/tcp -p 9100:9100/tcp escpos-netprinter:2.0
```
It should now accept prints by JetDirect on the default port(9100) and by lpd on the default port(515), and you can visualize it with the web application at port 80.  
For debugging, you can add port 631 to access the CUPS interface.   The CUPS administrative username is `cupsadmin` and the password is `123456`.

As of version 2.0, this has been tested to work with a regular POS program without adapting it.

## Known issues
While version 2.0 is no longer a beta version, it has known defects:
- It still uses the Flask development server, so it is unsafe for public networks.
- While it works with simple drivers, for example the one for the MUNBYN ITPP047 printers, the [Epson utilities](https://download.epson-biz.com/modules/pos/) refuse to speak to it.

