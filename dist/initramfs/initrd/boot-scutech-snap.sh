#!/bin/bash
# we need the scutech-snap module and the elioctl binary in the initramfs
# blkid is already there but I just want to be extra sure. shmura.

#%stage: volumemanager
#%depends: lvm2
#%modules: scutech-snap
#%programs: /usr/bin/elioctl
#%programs: /sbin/lsmod
#%programs: /sbin/modprobe
#%programs: /sbin/blkid
#%programs: /usr/sbin/blkid
#%programs: /sbin/blockdev
#%programs: /usr/sbin/blockdev
#%programs: /bin/mount
#%programs: /usr/bin/mount
#%programs: /bin/umount
#%programs: /usr/bin/umount
#%programs: /bin/udevadm
#%programs: /usr/bin/udevadm

echo "scutech-snap dlad load_modules" > /dev/kmsg
# this is a function in linuxrc, modprobes scutech-snap for us.
load_modules

/sbin/modprobe --allow-unsupported scutech-snap

rbd="${root#block:}"
if [ -n "$rbd" ]; then
    case "$rbd" in
        LABEL=*)
            rbd="$(echo $rbd | sed 's,/,\\x2f,g')"
            rbd="/dev/disk/by-label/${rbd#LABEL=}"
            ;;
        UUID=*)
            rbd="/dev/disk/by-uuid/${rbd#UUID=}"
            ;;
        PARTLABEL=*)
            rbd="/dev/disk/by-partlabel/${rbd#PARTLABEL=}"
            ;;
        PARTUUID=*)
            rbd="/dev/disk/by-partuuid/${rbd#PARTUUID=}"
            ;;
    esac

    echo "scutech-snap: root block device = $rbd" > /dev/kmsg

    # Device might not be ready
    if [ ! -b "$rbd" ]; then
        udevadm settle
    fi

    # Kernel cmdline might not specify rootfstype
    [ -z "$rootfstype" ] && rootfstype=$(blkid -s TYPE -o value $rbd)

    echo "scutech-snap: mounting $rbd as $rootfstype" > /dev/kmsg
    blockdev --setro $rbd
    mount -t $fstype -o ro "$rbd" /etc/scutech/dla/mnt > /dev/kmsg
    udevadm settle

    if [ -x /sbin/scutech_reload ]; then
        /sbin/scutech_reload
    else
        echo "scutech-snap: error: cannot reload tracking data: missing /sbin/scutech_reload" > /dev/kmsg
    fi

    umount -f /etc/scutech/dla/mnt > /dev/kmsg
    blockdev --setrw $rbd
fi
