#!/bin/bash
#
# /usr/lib/cups/backend/esc2file
#
# (c) November 2023  Francois-Leonard Gilbert
#
# Derived from "2file" CUPS backend script from the KDE printing project
#  https://community.kde.org/Printing/Developer_Tools
#
# License: AGPL-3.0
#

backend=${0}
jobid=${1}
cupsuser=${2}
jobtitle=${3}
jobcopies=${4}
joboptions=${5}
jobfile=${6}

# the following messages should appear in /var/log/cups/error_log,
# depending on what "LogLevel" setting your cupsd.conf carries:
echo "INFO: backend=${backend}"       1>&2
echo "INFO: jobid=${jobid}"           1>&2
echo "INFO: cupsuser=${cupsuser}"     1>&2
echo "INFO: jobtitle=${jobtitle}"     1>&2
echo "INFO: jobcopies=${jobcopies}"   1>&2
echo "INFO: joboptions=${joboptions}" 1>&2
echo "INFO: jobfile=${jobfile}"       1>&2
echo "INFO: printtime=${printtime}"   1>&2
echo "DEBUG:   Executing as ${USER}"  1>&2
echo "NOTICE: processing Job ${jobid}" 1>&2

#echo "EMERG:  This is a \"emergency\" level log message" 1>&2
#echo "ALERT:  This is a \"alert\" level log message"     1>&2
#echo "CRIT:   This is a \"critical\" level log message"  1>&2
#echo "ERROR:  This is a \"error\" level log message"     1>&2
#echo "WARN:   This is a \"warn\" level log message"      1>&2
#echo "NOTICE: This is a \"notice\" level log message"    1>&2
#echo "INFO:   This is a \"info\" level log message"      1>&2
#echo "INFO:   This is a 2nd \"info\" level log message"  1>&2
#echo "INFO:   This is a 3rd \"info\" level log message"  1>&2
#echo "DEBUG:  This is a \"debug\" level log message"     1>&2
                                                                                                         

# We will read the output filename from the printers and set the debug mode from the $DEVICE_URI 
# environment variable that should look like "esc2file:/dest_filename.suffix/log_filename.suffix/isdebug"

# Extract the file names from the DEVICE_URI
FILENAMES=${DEVICE_URI#esc2file:/}
DEST_FILENAME=${FILENAMES%/*/*}
TEMP=${FILENAMES%/*}
LOG_FILENAME=${TEMP#*/}
# Extract the debug flag from the DEVICE_URI
ESCPOS_DEBUG=${FILENAMES##*/}

echo "DEBUG:  DEST_FILENAME=${DEST_FILENAME}" 1>&2
echo "DEBUG:  LOG_FILENAME=${LOG_FILENAME}" 1>&2
echo "esc2file - Debug mode: ${ESCPOS_DEBUG}" 1>${TMPDIR}/${LOG_FILENAME}

# Now do the real work:
case ${#} in
      0)
         # this case is for "backend discovery mode"
         echo "file esc2file \"ESCPOS-netprinter\" \"2file-style backend to print ESC-POS to HTML\""
         exit 0
         ;;
      5)
         # backend needs to read from stdin if number of arguments is 5
         # NOTE: the CUPS backend programming directives state that temporary files should be created in the directory specified by the "TMPDIR" environment variable
         echo "DEBUG:  Printing from stdin"     1>&2
         # read from stdin and write to receipt.bin
         cat - > ${TMPDIR}/receipt.bin
         if [ "$?" -ne "0" ]; 
         then
            echo "ERROR:   Cannot write to ${TMPDIR}/receipt.bin"  1>&2
            exit 51 #Send an error to CUPS to signal printing failure
         else 
            if [ "${ESCPOS_DEBUG}" == "True" ]; then
               /usr/local/bin/php /home/escpos-emu/esc2html.php --debug ${TMPDIR}/receipt.bin 1>${TMPDIR}/${DEST_FILENAME} 2>>${TMPDIR}/${LOG_FILENAME}
            else
               #/usr/local/bin/php /home/escpos-emu/esc2html.php ${TMPDIR}/receipt.bin 1>${TMPDIR}/esc2html.html 2>>${TMPDIR}/esc2html_log
               /usr/local/bin/php /home/escpos-emu/esc2html.php ${TMPDIR}/receipt.bin 1>${TMPDIR}/${DEST_FILENAME} 2>>${TMPDIR}/${LOG_FILENAME}
            fi
            if [ "$?" -ne "0" ]; then
               echo "ERROR:   Error $? while printing ${TMPDIR}/receipt.bin to ${TMPDIR}/${DEST_FILENAME}"  1>&2
               exit 52  #Send an error to CUPS to signal printing failure
            fi
         fi
         ;;
      6)
         # backend needs to read from file if number of arguments is 6
         echo "DEBUG:  Printing from file ${6}"     1>&2
         if [ "${ESCPOS_DEBUG}" == "True" ]; then
            /usr/local/bin/php /home/escpos-emu/esc2html.php --debug ${6} 1>${TMPDIR}/${DEST_FILENAME} 2>>${TMPDIR}/${LOG_FILENAME}
         else
            #/usr/local/bin/php /home/escpos-emu/esc2html.php ${6} 1>${TMPDIR}/esc2html.html 2>>${TMPDIR}/esc2html_log
            /usr/local/bin/php /home/escpos-emu/esc2html.php ${6} 1>${TMPDIR}/${DEST_FILENAME} 2>>${TMPDIR}/${LOG_FILENAME}
         fi
         if [ "$?" -ne "0" ]; then
            echo "ERROR:  Error $? while printing ${6} to ${TMPDIR}/${DEST_FILENAME}"  1>&2
            #echo "ERROR:  Error $? while printing ${6} to ${TMPDIR}/test.html"  1>&2
            exit 61 #Send an error to CUPS to signal printing failure
         fi
         #Call the web app to move the html file to the web directory
         response=$(/usr/bin/curl -s http://localhost:${FLASK_RUN_PORT}/newReceipt)
         if [ "$?" -eq "0" ]; then
            if echo "$response" | grep -q "OK"; then
               echo "DEBUG:  File copy returned OK" 1>&2
            else
               echo "ERROR:  File copy did not return OK" 1>&2
               exit 62 #Send an error to CUPS to signal printing failure
            fi
         else
            echo "ERROR:  Error $? while calling the web app to move ${TMPDIR}/${DEST_FILENAME} to the web directory"  1>&2
            exit 63 #Send an error to CUPS to signal printing failure
         fi
         ;;
      1|2|3|4|*)
         # these cases are unsupported
         echo " "
         echo " Usage: esc2file job-id user title copies options [file]"
         echo " "
         echo " (Install as CUPS backend in /usr/lib/cups/backend/esc2file)"
         echo " (Use as 'device URI' like \"esc2file:/dest_filename.suffix/log_filename.suffix\" for printer installation.)"
         exit 0
esac

echo  1>&2

# we reach this line only if we actually "printed something"
echo "NOTICE: processed Job ${jobid} to file ${TMPDIR}/${DEST_FILENAME}" 1>&2
echo "NOTICE: End of \"${0}\" run."                             1>&2
echo "NOTICE: ---------------------------------------------------" 1>&2
echo  1>&2
exit 0