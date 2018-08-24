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
 * Source file for set fan speed functions.
 ***************************************************************************/

#include <string.h>

#include "fanspeed.h"

/* the order of these strings must match the fanspeed enum values */
static const char *fanspeed_string[] =
{
    "slow",
    "normal",
    "medium",
    "fast",
    "max"
};

/* convert override string to fanspeed enum */
enum fanspeed
fan_speed_string_to_enum(const char *name)
{
    size_t i;

    if (name == NULL) {
        return(FAND_SPEED_NONE);
    }

    for (i = 0; i < sizeof(fanspeed_string)/sizeof(const char *); i++) {
        if (strcmp(fanspeed_string[i], name) == 0) {
            return(i);
        }
    }

    return(FAND_SPEED_NONE);
}

const char *
fan_speed_enum_to_string(enum fanspeed fan_speed)
{
    if (fan_speed >= 0 &&
            (unsigned int)fan_speed < sizeof(fanspeed_string)/sizeof(char *)) {
        return(fanspeed_string[fan_speed]);
    }

    return(fanspeed_string[FAND_SPEED_NORMAL]);
}
