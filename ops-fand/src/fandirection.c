/*
 *  (c) Copyright 2015 Hewlett Packard Enterprise Development LP
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may
 *  not use this file except in compliance with the License. You may obtain
 *  a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 *  License for the specific language governing permissions and limitations
 *  under the License.
 */

/************************************************************************//**
 * @ingroup fand
 *
 * @file
 * Source file for set fan direction functions.
 ***************************************************************************/

#include <string.h>

#include "fandirection.h"

/* the order of these strings must match the fandirection enum values */
static const char *fandirection_string[] =
{
    "f2b",
    "b2f"
};

enum fandirection
fan_direction_string_to_enum(const char *name)
{
    size_t i;

    if (name == NULL) {
        return(FAND_DIRECTION_F2B);
    }

    for (i = 0; i < sizeof(fandirection_string)/sizeof(const char *); i++) {
        if (strcmp(fandirection_string[i], name) == 0) {
            return(i);
        }
    }

    return(FAND_DIRECTION_F2B);
}

const char *
fan_direction_enum_to_string(enum fandirection fan_direction)
{
    if (fan_direction >= 0 &&
            (unsigned int)fan_direction < sizeof(fandirection_string)/sizeof(char *)) {
        return(fandirection_string[fan_direction]);
    }

    return(fandirection_string[FAND_DIRECTION_F2B]);
}
