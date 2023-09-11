#On part de l'image Debian de php
FROM php:8.1-cli

#On va utiliser l'utilitaire "install-php-extensions" au lieu de PECL car il marche mieux.
ADD https://github.com/mlocati/docker-php-extension-installer/releases/latest/download/install-php-extensions /usr/local/bin/
RUN chmod +x /usr/local/bin/install-php-extensions
RUN install-php-extensions imagick @composer mbstring

#Note:  utiliser "." au lieu de * permet de garder la structure et envoyer tous les sous-répertoires
ADD . /home/escpos-emu/
WORKDIR /home/escpos-emu/

#Installation de Flask et Flask-socketio
RUN apt-get update
RUN apt-get install -y python3-flask-socketio

RUN composer install

EXPOSE 5000
CMD [ "python3", "miniflask.py"]
#ENTRYPOINT [ "/bin/bash" ]