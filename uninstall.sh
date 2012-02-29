#!/bin/sh

# File: uninstall.sh
#
# Version 0.1
# by AJ
#
# the uninstall script for timeslider

INSTFOUND=0

for IDIR in\
	'/usr/local/lib64/nautilus/extensions-2.0/python'\
	'/usr/local/lib/nautilus/extensions-2.0/python'\
	'/usr/lib64/nautilus/extensions-2.0/python'\
	'/usr/lib/nautilus/extensions-2.0/python'\
	"$HOME/.nautilus/python-extensions"
do
	if [ -f "$IDIR/timeslider.py" ]
	then
		INSTFOUND=1
		rm -f "$IDIR/timeslider.py" >/dev/null 2>&1
		rm -f "$IDIR/timeslider.glade" >/dev/null 2>&1
    
		if [ $? -ne 0 ]
		then
			echo "Unable to delete $IDIR/timeslider.*"
		else
			echo "$IDIR/timeslider.* is removed."
		fi
	fi
done

if [ $INSTFOUND -eq 0 ]
then
	echo 'No Timeslider installation is found.'
fi
