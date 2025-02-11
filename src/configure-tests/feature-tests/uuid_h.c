// SPDX-License-Identifier: GPL-2.0-only

/*
 * Copyright (C) 2017 Datto Inc.
 * Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
 */

#include "includes.h"
MODULE_LICENSE("GPL");
#include <linux/uuid.h>

static inline void dummy(void){
	generate_random_uuid(NULL);
}
