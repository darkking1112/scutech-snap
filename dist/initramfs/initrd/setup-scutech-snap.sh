#!/bin/bash
#%stage: block

# we need a directory to mount the root filesystem in
# when the boot-scutech-snap.sh script runs so it can run reload

export MOUNTROOT=$tmp_mnt/etc/scutech/dla/mnt
echo "scutech-snap dlad install making mountpoint directory $MOUNTROOT" > /dev/kmsg
mkdir -p $MOUNTROOT
cp /var/lib/scutech/dla/reload $tmp_mnt/sbin/scutech_reload

mkdir -p $tmp_mnt/usr/bin
mkdir -p $tmp_mnt/usr/sbin
