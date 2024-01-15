ESC/POS virtual network printer 
----------

This is a container-based ESC/POS network printer, that transforms the printed material in HTML pages and makes them avaliable in a web interface.

The printer emulates a 80mm roll of paper.

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
docker build -t escpos-netprinter:2.0-beta .
```

To run the resulting container:
```bash
docker run -d --rm --name escpos_netprinter -p 515:515/tcp -p 80:80/tcp -p 9100:9100/tcp escpos-netprinter:2.0-beta
```
It should now accept prints by JetDirect on the default port(9100) and by lpd on the default port(515), and you can visualize it with the web application at port 80.  
For debugging, you can add port 631 to access the CUPS interface.   The CUPS administrative username is `cupsadmin` and the password is `123456`.

As of version 2.0, this has been tested to work with a regular POS program without adapting it.

## Known issues
This is still beta software for now, so it has known major defects:
- It still uses the Flask development server, so it is unsafe for public networks.
- The conversion to HTML does not do QR codes correctly (see the 1.0-beta.2 release notes)
- While it works with simple drivers, for example for the MUNBYN ITPP047 printers, the [Epson utilities](https://download.epson-biz.com/modules/pos/) refuse to speak to it.

