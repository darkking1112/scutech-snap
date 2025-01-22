/* SPDX-License-Identifier: LGPL-2.1-or-later */

/*
 * Copyright (C) 2015 Datto Inc.
 * Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
 */

#ifndef LIBSCUTECH_SNAP_H_
#define LIBSCUTECH_SNAP_H_

#include "scutech-snap.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

int scutech_snap_setup_snapshot(unsigned int minor, char *bdev, char *cow, unsigned long fallocated_space, unsigned long cache_size, bool ignore_snap_errors);

int scutech_snap_reload_snapshot(unsigned int minor, char *bdev, char *cow, unsigned long cache_size, bool ignore_snap_errors);

int scutech_snap_reload_incremental(unsigned int minor, char *bdev, char *cow, unsigned long cache_size, bool ignore_snap_errors);

int scutech_snap_destroy(unsigned int minor);

int scutech_snap_transition_incremental(unsigned int minor);

int scutech_snap_transition_snapshot(unsigned int minor, char *cow, unsigned long fallocated_space);

int scutech_snap_reconfigure(unsigned int minor, unsigned long cache_size);

int scutech_snap_info(unsigned int minor, struct scutech_snap_info *info);

/**
 * Get the first available minor.
 *
 * @returns non-negative number if minor is available, otherwise -1
 */
int scutech_snap_get_free_minor(void);

#ifdef __cplusplus
}
#endif

#endif /* LIBSCUTECH_SNAP_H_ */
