#!/bin/sh

# File: install.sh
#
# version 0.1
# by AJ
#
# This is the install script for timeslider

for INSTDIR in\
  '/usr/local/lib64/nautilus/extensions-2.0/python' \
  '/usr/local/lib/nautilus/extensions-2.0/python' \
  '/usr/lib64/nautilus/extensions-2.0/python' \
  '/usr/lib/nautilus/extensions-2.0/python' \
  "$HOME/.nautilus/python-extensions"
  do

  # make the "$HOME/.nautilus/python-extensions" before we check it
  if [ $INSTDIR == "$HOME/.nautilus/python-extensions" ]
  then
	mkdir -p "$INSTDIR" >/dev/null 2>&1
  fi

  # Copy nautilusvim.py to it.
  if [ -d $INSTDIR ] && [ -w $INSTDIR ]
  then
	cp timeslider.py "$INSTDIR/"
	cp timeslider.glade "$INSTDIR/"
    	echo "Timeslider copied to $INSTDIR"
    	echo "Restart nautilus to complete the installation."
    	exit
   fi
   done

# Installation failed
echo "Failed to install timeslider. You may try to install it manually."
echo "Copy timeslider.py and timeslider.glade to ~/.nautilus/python-extensions/"
echo "restart nautilus and go to subvol which is under btrfs autosnap."
