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

### Use the prebuilt container 

A prebuilt container of this project is avaliable on [Docker Hub](https://hub.docker.com/repository/docker/gilbertfl/escpos-netprinter).   

To run the prebuilt container:
```bash
docker run -d  \
    -p 515:515/tcp \
    -p 80:80/tcp   \
    -p 9100:9100/tcp \
    --mount source=receiptVolume,target=/home/escpos-emu/web \
    gilbertfl/escpos-netprinter:3.1
```
### Once started
Once started, the container will accept prints by JetDirect on the default port(9100) and by lpd on the default port(515).   You can access all received receipts with the web application at port 80.  

Version 3.1 is capable of dealing with all status requests from POS systems as described in the Epson APG.

## Working on the code

### Building from source

To install v3.1 from source:

```bash
wget --show-progress https://github.com/gilbertfl/escpos-netprinter/archive/refs/tags/3.1.zip
unzip 3.1.zip 
cd escpos-netprinter-3.1
docker build -t escpos-netprinter:3.1 .
```

To run the resulting container:
```bash
docker run -d  \
    -p 515:515/tcp \
    -p 80:80/tcp   \
    -p 9100:9100/tcp \
    --mount source=receiptVolume,target=/home/escpos-emu/web \
    escpos-netprinter:3.1
```

### Debugging 
Two interfaces have been made avaliable to help debugging.

There is also a general environment flag that make the Docker logs more verbose:  set ```ESCPOS_DEBUG=True``` (case-sensitive)
```bash
docker run -d  \
    -p 515:515/tcp \
    -p 80:80/tcp   \
    -p 9100:9100/tcp \
    --mount source=receiptVolume,target=/home/escpos-emu/web \
    --env ESCPOS_DEBUG=True  \
    escpos-netprinter:3.1
```

If you have problems with the CUPS interface, you can add port 631 to access the CUPS administrator interface.   The CUPS administrative username is `cupsadmin` and the password is `123456`;  you can change that in the dockerfile or at runtime inside the administrator interface.
```bash
docker run -d  \
    -p 515:515/tcp \
    -p 80:80/tcp   \
    -p 9100:9100/tcp \
    -p 631:631/tcp
    --mount source=receiptVolume,target=/home/escpos-emu/web \
    escpos-netprinter:3.1
```

## Known issues
While version 3.1 is no longer a beta version, it has known defects:
- It still uses the Flask development server, so it is unsafe for public networks.
- While it works with simple drivers, for example the one for the MUNBYN ITPP047 printers, the [Epson utilities](https://download.epson-biz.com/modules/pos/) refuse to speak to it.

