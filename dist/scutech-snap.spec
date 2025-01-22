# debbuild doesn't define _usrsrc yet
%if "%{_vendor}" == "debbuild"
%global _usrsrc %{_prefix}/src
%endif

# Location to install kernel module sources
%global _kmod_src_root %{_usrsrc}/%{name}-%{version}

# Location for systemd shutdown script
%global _systemd_shutdown /lib/systemd/system-shutdown

# All sane distributions use dracut now, so here are dracut paths for it
%if 0%{?rhel} > 0 && 0%{?rhel} < 7
%global _dracut_modules_root %{_datadir}/dracut/modules.d
%else
%global _dracut_modules_root %{_prefix}/lib/dracut/modules.d
%endif

# RHEL 5 and openSUSE 13.1 and older use mkinitrd instead of dracut
%if 0%{?rhel} == 5 || 0%{?suse_version} > 0 && 0%{?suse_version} < 1315
%global _mkinitrd_scripts_root /lib/mkinitrd/scripts
%endif

# Debian and Ubuntu use initramfs-tools instead of dracut.. for now
%if 0%{?debian} || 0%{?ubuntu}
%global _initramfs_tools_root %{_datadir}/initramfs-tools
%endif

# SUSE hasn't yet reassigned _sharedstatedir to /var/lib, so we force it
# Likewise, RHEL/CentOS 5 doesn't have this fixed either, so we force it there too.
# Debian/Ubuntu doesn't set it there, so we force it for them too
%if 0%{?suse_version} || 0%{?rhel} == 5 || 0%{?debian} || 0%{?ubuntu}
%global _sharedstatedir %{_var}/lib
%endif

# On Debian/Ubuntu systems, /bin/sh usually points to /bin/dash,
# and we need it to be /bin/bash, so we set it here.
%if "%{_vendor}" == "debbuild"
%global _buildshell /bin/bash
%endif

# Set up the correct DKMS module name, per Debian convention for Debian/Ubuntu,
# and use the other name, per convention on all other distros.
%if "%{_vendor}" == "debbuild"
%global dkmsname %{name}-dkms
%else
%global dkmsname dkms-%{name}
%endif

# SUSE Linux does not define the dist tag,
# so we must define it manually
%if "%{_vendor}" == "suse"
%global dist .suse%{?suse_version}

# If SLE 11, redefine it to use SLE prefix
%if 0%{?suse_version} == 1110
%global dist .sle11
%endif

# Return the appropriate tags for SLE 12 and openSUSE 42.1
%if 0%{?suse_version} == 1315
%if 0%{?is_opensuse}
%global dist .suse4200
%else
%global dist .sle12
%endif
%endif

# Return the appropriate tags for SLE 15 and openSUSE 15.0
%if 0%{?suse_version} == 1500
%if 0%{?is_opensuse}
%global dist .suse1500
%else
%global dist .sle15
%endif
%endif

%endif

%if "%{_vendor}" != "debbuild"
%global rpm_dkms_opt 1
%endif

# Set the libdir correctly for Debian/Ubuntu systems
%if "%{_vendor}" == "debbuild"
%global _libdir %{_prefix}/lib/%(%{__dpkg_architecture} -qDEB_HOST_MULTIARCH)
%endif

# Set up library package names properly
%global libprefix libscutech-snap
%global libsover 1

%if "%{_vendor}" == "debbuild"
%global devsuffix dev
%else
%global devsuffix devel
%endif

%if 0%{?fedora} || 0%{?rhel}
%global libname %{libprefix}
%else
%global libname %{libprefix}%{libsover}
%endif

%global devname %{libprefix}-%{devsuffix}

# For local build stuff, disabled by default
%bcond_with devmode


Name:            scutech-snap
Version:         0.1
Release:         1%{?dist}
Summary:         Kernel module and utilities for enabling low-level live backups
Vendor:          Scutech Software, Inc.
%if "%{_vendor}" == "debbuild"
Packager:        Scutech Software
Group:           kernel
License:         GPL-2.0
%else
%if 0%{?suse_version}
Group:           System/Kernel
License:         GPL-2.0
%else
Group:           System Environment/Kernel
License:         GPLv2
%endif
%endif

URL:             https://github.com/scutech/scutech-snap
Source0:         %{name}.tar.gz

# BuildRequires:   gcc
# BuildRequires:   make
# BuildRequires:   rsync

# Some targets (like EL5) expect a buildroot definition
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
The Scutech-Snap is a kernel module that enables
live image snapshots through block devices.

%package -n %{libname}
Summary:         Library for communicating with %{name} kernel module
%if "%{_vendor}" == "debbuild"
Group:           libs
License:         LGPL-2.1+
%else
%if 0%{?suse_version}
Group:           System/Libraries
License:         LGPL-2.1+
%else
Group:           System Environment/Libraries
License:         LGPLv2+
%endif
%endif

%description -n %{libname}
The library for communicating with the %{name} kernel module.


%package -n %{devname}
Summary:         Files for developing applications to use %{name}.
%if "%{_vendor}" == "debbuild"
Group:           libdevel
License:         LGPL-2.1+
%else
%if 0%{?suse_version}
Group:           Development/Libraries/C and C++
License:         LGPL-2.1+
%else
Group:           Development/Libraries
License:         LGPLv2+
%endif
%endif
Requires:        %{libname}%{?_isa} = %{version}-%{release}

%description -n %{devname}
This package provides the files necessary to develop applications
to use %{name}.


%package utils
Summary:         Utilities for using %{name} kernel module
%if "%{_vendor}" == "debbuild"
Group:           admin
%else
%if 0%{?suse_version}
Group:           System/Kernel
%else
Group:           System Environment/Kernel
%endif
%endif
Requires:        %{dkmsname} = %{version}-%{release}
Requires:        %{libname}%{?_isa} = %{version}-%{release}
%if 0%{?fedora} > 21 || 0%{?rhel} >= 8 || 0%{?suse_version} > 1320 || 0%{?debian} || 0%{?ubuntu}
Recommends:      bash-completion
%endif

%description utils
Utilities for %{name} to use the kernel module.


%package -n %{dkmsname}
Summary:         Kernel module source for %{name} managed by DKMS
%if "%{_vendor}" == "debbuild"
Group:           kernel
%else
%if 0%{?suse_version}
Group:           Development/Sources
%else
Group:           System Environment/Kernel
%endif
%endif

%if 0%{?rhel} != 5 && 0%{?suse_version} != 1110
# noarch subpackages aren't supported in EL5 and SLE11
BuildArch:       noarch
%endif

%if 0%{?debian}
%if ( "%{_arch}" != "x86_64" && "%{_arch}" != "amd64" ) && ( %{debian} >= 11 )

# By default, on arm64, Debian 11 is provided with the kernel with
# some symbols absent AND with without a System.map file. This makes
# the scutech-snap driver work without sys_call_table hooking support.
#
# As a compromise solution, we install linux-image-$(uname -r)-dbg
# to make it work properly. This package adds System.map and makes
# it possible to fetch the address of the system call table
#
# It is also true for Debian12, but it needs to be checked for Debian13
# when it is released
#
# Please refer to https://github.com/scutech/devboxes/pull/230
Requires:        linux-image-%(uname -r)-dbg
%endif
%endif

%if 0%{?rhel} >= 6 || 0%{?fedora} >= 23 || 0%{?suse_version} >= 1315
Requires(preun): dkms >= 2.3
Requires:        dkms >= 2.3
Requires(post):  dkms >= 2.3
%else
Requires(preun): dkms
Requires:        dkms
Requires(post):  dkms
%endif

%if 0%{?rhel}
# Ensure perl is actually installed for builds to work
# This issue mainly affects EL6, but it doesn't hurt to
# be cautious and just require it across the EL releases.
Requires:        perl
%endif

# Dependencies for actually building the kmod
Requires:        make

%if "%{_vendor}" != "debbuild"
%if 0%{?rhel} >= 6 || 0%{?suse_version} >= 1210 || 0%{?fedora}
# With RPM 4.9.0 and newer, it's possible to give transaction
# hints to ensure some kind of ordering for transactions using
# the OrderWithRequires statement.
# More info: http://rpm.org/wiki/Releases/4.9.0#package-building

# This was also backported to RHEL/CentOS 6' RPM, see RH#760793.
# Link: https://bugzilla.redhat.com/760793

# We can use this to ensure that if kernel-devel/kernel-syms is
# in the same transaction as the DKMS module upgrade, it will be
# installed first before processing the kernel module, ensuring
# that DKMS will be able to successfully build against the new
# kernel being installed.
#
# Upd: Left as it is for SLES and changed to Requires
# statement for RHEL/CentOS and Fedora due to problem in DKMS.
# It installs kernel-debug-devel instead of kernel-devel if no
# kernel-devel package has been already installed. See more
# here https://github.com/elastio/elastio-snap/issues/12 and
# here https://bugzilla.redhat.com/1228897
# This change ensures installation of the kernel-devel, not
# kernel-debug-devel if both dkms and kernel module are installed
# in one transaction. The installation order is preserved.
%if 0%{?rhel} || 0%{?fedora}
Requires: kernel-devel
%endif

%if 0%{?suse_version}
OrderWithRequires: kernel-syms
%endif

%endif
%endif

%description -n %{dkmsname}
Kernel module sources for %{name} for DKMS to
automatically build and install for each kernel.


%prep
%if ! %{with devmode}
%setup -q
%else
%setup -q -n %{name}
%endif


%build
export CFLAGS="%{optflags}"
make application
make utils
# Not needs to be installed: we expect the
# user to generate it during the build
rm -f src/kernel-config.h


%install
# Install library
mkdir -p %{buildroot}%{_libdir}/pkgconfig
install -p -m 0755 lib/libscutech-snap.so.%{libsover} %{buildroot}%{_libdir}/
ln -sf libscutech-snap.so.%{libsover} %{buildroot}%{_libdir}/libscutech-snap.so
install -p -m 0644 dist/libscutech-snap.pc.in %{buildroot}%{_libdir}/pkgconfig/libscutech-snap.pc
mkdir -p %{buildroot}%{_includedir}/scutech-snap
install -p -m 0644 lib/libscutech-snap.h %{buildroot}%{_includedir}/scutech-snap/libscutech-snap.h
install -p -m 0644 src/scutech-snap.h %{buildroot}%{_includedir}/scutech-snap/scutech-snap.h

sed -e "s:@prefix@:%{_prefix}:g" \
    -e "s:@libdir@:%{_libdir}:g" \
    -e "s:@includedir@:%{_includedir}/scutech-snap:g" \
    -e "s:@PACKAGE_VERSION@:%{version}:g" \
    -i %{buildroot}%{_libdir}/pkgconfig/libscutech-snap.pc


# Generate symbols for library package (Debian/Ubuntu only)
%if "%{_vendor}" == "debbuild"
mkdir -p %{buildroot}/%{libname}/DEBIAN
dpkg-gensymbols -P%{buildroot} -p%{libname} -v%{version}-%{release} -e%{buildroot}%{_libdir}/%{libprefix}.so.%{?!libsover:0}%{?libsover} -e%{buildroot}%{_libdir}/%{libprefix}.so.%{?!libsover:0}%{?libsover}.* -O%{buildroot}/%{libname}/DEBIAN/symbols
%endif

# Install utilities and man pages
mkdir -p %{buildroot}%{_bindir}
install -p -m 0755 app/elioctl %{buildroot}%{_bindir}/elioctl
mkdir -p %{buildroot}%{_sysconfdir}/bash_completion.d
install -p -m 0755 app/bash_completion.d/elioctl %{buildroot}%{_sysconfdir}/bash_completion.d/
mkdir -p %{buildroot}%{_mandir}/man8
install -p -m 0644 doc/elioctl.8 %{buildroot}%{_mandir}/man8/elioctl.8
install -p -m 0755 utils/update-img %{buildroot}%{_bindir}/update-img
install -p -m 0644 doc/update-img.8 %{buildroot}%{_mandir}/man8/update-img.8

# Install kmod sources
mkdir -p %{buildroot}%{_kmod_src_root}
rsync -av src/ %{buildroot}%{_kmod_src_root}

# Install DKMS configuration
install -m 0644 dist/scutech-snap-dkms-conf %{buildroot}%{_kmod_src_root}/dkms.conf
sed -i "s/@MODULE_VERSION@/%{version}/g" %{buildroot}%{_kmod_src_root}/dkms.conf

# Install modern modprobe stuff
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -m 0644 dist/scutech-snap-modprobe-conf %{buildroot}%{_sysconfdir}/modules-load.d/%{name}.conf

# Legacy automatic module loader for RHEL 5/6
%if 0%{?rhel} && 0%{?rhel} < 7
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig/modules
install -m 0755 dist/scutech-snap-sysconfig-modules %{buildroot}%{_sysconfdir}/sysconfig/modules/scutech-snap.modules
%endif

# We only need the hook with older distros
%if 0%{?rhel} == 5 || (0%{?suse_version} && 0%{?suse_version} < 1315) || (0%{?fedora} && 0%{?fedora} < 23)
# Install the kernel hook to enforce scutech-snap rebuilds
mkdir -p %{buildroot}%{_sysconfdir}/kernel/postinst.d
install -m 755 dist/kernel.postinst.d/50-scutech-snap %{buildroot}%{_sysconfdir}/kernel/postinst.d/50-scutech-snap
%endif

# RHEL/CentOS 5 will not have the initramfs scripts because its mkinitrd doesn't support scripts
%if 0%{?rhel} != 5

# Install initramfs stuff
mkdir -p %{buildroot}%{_sharedstatedir}/scutech/dla
install -m 755 dist/initramfs/reload %{buildroot}%{_sharedstatedir}/scutech/dla/reload

# Debian/Ubuntu use initramfs-tools
%if 0%{?debian} || 0%{?ubuntu}
mkdir -p %{buildroot}%{_initramfs_tools_root}
mkdir -p %{buildroot}%{_initramfs_tools_root}/hooks
mkdir -p %{buildroot}%{_initramfs_tools_root}/scripts/init-premount
install -m 755 dist/initramfs/initramfs-tools/hooks/scutech-snap %{buildroot}%{_initramfs_tools_root}/hooks/scutech-snap
install -m 755 dist/initramfs/initramfs-tools/scripts/scutech-snap %{buildroot}%{_initramfs_tools_root}/scripts/init-premount/scutech-snap
%else
# openSUSE 13.1 and older use mkinitrd
%if 0%{?suse_version} > 0 && 0%{?suse_version} < 1315
mkdir -p %{buildroot}%{_mkinitrd_scripts_root}
install -m 755 dist/initramfs/initrd/boot-scutech-snap.sh %{buildroot}%{_mkinitrd_scripts_root}/boot-scutech-snap.sh
install -m 755 dist/initramfs/initrd/setup-scutech-snap.sh %{buildroot}%{_mkinitrd_scripts_root}/setup-scutech-snap.sh
%else
mkdir -p %{buildroot}%{_dracut_modules_root}/90scutech-snap
install -m 755 dist/initramfs/dracut/scutech-snap.sh %{buildroot}%{_dracut_modules_root}/90scutech-snap/scutech-snap.sh
install -m 755 dist/initramfs/dracut/module-setup.sh %{buildroot}%{_dracut_modules_root}/90scutech-snap/module-setup.sh
install -m 755 dist/initramfs/dracut/install %{buildroot}%{_dracut_modules_root}/90scutech-snap/install
%endif
%endif
%endif

# Install systemd shutdown script
mkdir -p %{buildroot}%{_systemd_shutdown}
install -m 755 dist/system-shutdown/umount_rootfs.shutdown %{buildroot}%{_systemd_shutdown}/umount_rootfs.shutdown

# Get rid of git artifacts
find %{buildroot} -name "*.git*" -print0 | xargs -0 rm -rfv

%preun -n %{dkmsname}

%if "%{_vendor}" == "debbuild"
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
%else
if [ $1 -eq 0 ]; then
%endif
    if lsmod | grep -q $(echo %{name} | tr '-' '_') ; then
        modprobe -r %{name} || :
    fi
fi

if dkms status -m %{name} -v %{version} | grep -q %{name} ; then
    dkms remove -m %{name} -v %{version} --all %{?rpm_dkms_opt:--rpm_safe_upgrade}
fi

%post -n %{dkmsname}

rmmod %{name} &> /dev/null || :

%if "%{_vendor}" == "debbuild"
if [ "$1" = "configure" ]; then
%else
if [ "$1" -ge "1" ]; then
%endif
    if [ -f /usr/lib/dkms/common.postinst ]; then
        /usr/lib/dkms/common.postinst %{name} %{version} || exit $?
    fi
# It was always necessary for "%{_vendor}" == "debbuild" and now necessary for CentOS/Fedora and any distro with
# DKMS version starting from 2.8.8. Now DKMS has a parameter '--modprobe-on-install' for the 'dkms install' command.
# But /usr/lib/dkms/common.postinst script doesn't offer this parameter. So, modprobing it manually.
modinfo %{name} &> /dev/null && modprobe %{name} || :
fi


%post utils
%if 0%{?rhel} != 5
# Generate initramfs
if type "dracut" &> /dev/null; then
    echo "Configuring dracut, please wait..."
    dracut -f || :
elif type "mkinitrd" &> /dev/null; then
    echo "Configuring initrd, please wait..."
    mkinitrd || :
elif type "update-initramfs" &> /dev/null; then
    echo "Configuring initramfs, please wait..."
    update-initramfs -u || :
fi
sleep 1 || :
%endif


%postun utils
%if 0%{?rhel} != 5
%if 0%{?debian} || 0%{?ubuntu}
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
%else
if [ $1 -eq 0 ]; then
%endif

        if type "dracut" &> /dev/null; then
                echo "Configuring dracut, please wait..."
                dracut -f || :
        elif type "mkinitrd" &> /dev/null; then
                echo "Configuring initrd, please wait..."
                mkinitrd || :
        elif type "update-initramfs" &> /dev/null; then
                echo "Configuring initramfs, please wait..."
                update-initramfs -u || :
        fi
fi
%endif

%post -n %{libname}
/sbin/ldconfig

%postun -n %{libname}
/sbin/ldconfig


%clean
# EL5 and SLE 11 require this section
rm -rf %{buildroot}


%files utils
%if 0%{?suse_version}
%defattr(-,root,root,-)
%endif
%{_bindir}/elioctl
%{_bindir}/update-img
%{_sysconfdir}/bash_completion.d/elioctl
%{_mandir}/man8/elioctl.8*
%{_mandir}/man8/update-img.8*
# Initramfs scripts for all but RHEL 5
%if 0%{?rhel} != 5
%dir %{_sharedstatedir}/scutech/dla
%{_sharedstatedir}/scutech/dla/reload
%if 0%{?debian} || 0%{?ubuntu}
%{_initramfs_tools_root}/hooks/scutech-snap
%{_initramfs_tools_root}/scripts/init-premount/scutech-snap
%else
%if 0%{?suse_version} > 0 && 0%{?suse_version} < 1315
%{_mkinitrd_scripts_root}/boot-scutech-snap.sh
%{_mkinitrd_scripts_root}/setup-scutech-snap.sh
%else
%dir %{_dracut_modules_root}/90scutech-snap
%{_dracut_modules_root}/90scutech-snap/scutech-snap.sh
%{_dracut_modules_root}/90scutech-snap/module-setup.sh
%{_dracut_modules_root}/90scutech-snap/install
%endif
%endif
%endif
# Install systemd shutdown script
%{_systemd_shutdown}/umount_rootfs.shutdown

%doc README.md doc/STRUCTURE.md
%if "%{_vendor}" == "redhat"
%{!?_licensedir:%global license %doc}
%license COPYING* LICENSING.md
%else
%if "%{_vendor}" == "debbuild"
%license dist/copyright
%else
%doc COPYING* LICENSING.md
%endif
%endif

%files -n %{libname}
%if 0%{?suse_version}
%defattr(-,root,root,-)
%endif
%{_libdir}/libscutech-snap.so.%{libsover}
%if "%{_vendor}" == "redhat"
%{!?_licensedir:%global license %doc}
%license COPYING* LICENSING.md
%else
%if "%{_vendor}" == "debbuild"
%license dist/copyright
%else
%doc COPYING* LICENSING.md
%endif
%endif

%files -n %{devname}
%if 0%{?suse_version}
%defattr(-,root,root,-)
%endif
%{_libdir}/libscutech-snap.so
%{_libdir}/pkgconfig/libscutech-snap.pc
%{_includedir}/scutech-snap/
%if "%{_vendor}" == "redhat"
%{!?_licensedir:%global license %doc}
%license COPYING* LICENSING.md
%else
%if "%{_vendor}" == "debbuild"
%license dist/copyright
%else
%doc COPYING* LICENSING.md
%endif
%endif

%files -n %{dkmsname}
%if 0%{?suse_version}
%defattr(-,root,root,-)
%endif
%if 0%{?rhel} == 5 && 0%{?rhel} == 6 && 0%{?suse_version} == 1110
# RHEL/CentOS 5/6 and SLE 11 don't support this at all
%exclude %{_sysconfdir}/modules-load.d/scutech-snap.conf
%else
%config %{_sysconfdir}/modules-load.d/scutech-snap.conf
%endif
%if 0%{?rhel} && 0%{?rhel} < 7
%config %{_sysconfdir}/sysconfig/modules/scutech-snap.modules
%endif
%dir %{_kmod_src_root}
%{_kmod_src_root}/Makefile
%{_kmod_src_root}/configure-tests
%{_kmod_src_root}/main.c
%{_kmod_src_root}/scutech-snap.h
%{_kmod_src_root}/nl_debug.c
%{_kmod_src_root}/nl_debug.h
%{_kmod_src_root}/dkms.conf
%{_kmod_src_root}/genconfig.sh
%{_kmod_src_root}/includes.h
%exclude %dir %{_kmod_src_root}/configure-tests/feature-tests/build
%if 0%{?rhel} == 5 || (0%{?suse_version} && 0%{?suse_version} < 1315) || (0%{?fedora} && 0%{?fedora} < 23)
%dir %{_sysconfdir}/kernel/postinst.d
%{_sysconfdir}/kernel/postinst.d/50-scutech-snap
%endif
%doc README.md
%if "%{_vendor}" == "redhat"
%{!?_licensedir:%global license %doc}
%license COPYING* LICENSING.md
%else
%if "%{_vendor}" == "debbuild"
%license dist/copyright
%else
%doc COPYING* LICENSING.md
%endif
%endif
