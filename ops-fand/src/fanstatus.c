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
 * Source file for set fan status functions.
 ***************************************************************************/

#include <string.h>

#include "fanstatus.h"

/* the order of these strings must match the fanstatus enum values */
static const char *fanstatus_string[] =
{
    "uninitialized",
    "ok",
    "fault"
};

/* convert override string to fanstatus enum */
enum fanstatus
fan_status_string_to_enum(const char *name)
{
    size_t i;

    if (name == NULL) {
        return(FAND_STATUS_UNINITIALIZED);
    }

    for (i = 0; i < sizeof(fanstatus_string)/sizeof(const char *); i++) {
        if (strcmp(fanstatus_string[i], name) == 0) {
            return(i);
        }
    }

    return(FAND_STATUS_UNINITIALIZED);
}

const char *
fan_status_enum_to_string(enum fanstatus status)
{
    if ((unsigned int)status < (sizeof(fanstatus_string)/sizeof(const char *)))
        return(fanstatus_string[status]);
    return(fanstatus_string[FAND_STATUS_UNINITIALIZED]);
}
