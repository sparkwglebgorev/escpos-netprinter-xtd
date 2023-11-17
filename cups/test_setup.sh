#!/bin/bash
shopt -s extglob
shopt -s nullglob  #Quand un patron ne retourne rien, ignorer la commande.  Pour continuer avec le patron lui-même, mettre "shopt -u nullglob"

cupsd
lpadmin -p test -v $DEVICE_URI -E
echo "Allo!"|lp -d test

x=0;
for FILE in /home/escpos-emu/web/receipts/* ; do
    echo "$FILE"
    ((x=x+1))
done

if [ "$x" = "0" ]; then 
    echo "ERREUR: Aucun fichier produit par l'impression"
    exit 1;
fi

#A partir d'ici, retirer l'imprimante-test ?