
/* Feature Mapping Header file
 * Copyright (C) 2016 Hewlett Packard Enterprise Development LP
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * File: feature_mapping.h
 *
 * Purpose: header file for feature_mapping.c
 */

#ifndef __FEATURE_MAPPING_H
#define __FEATURE_MAPPING_H

#define FEATURE_MAPPING_CONF  \
    "/etc/openswitch/supportability/ops_featuremapping.yaml"
#define FEATURE_SIZE           30
#define FEATURE_DESC_SIZE     100
#define DIAG_DUMP_FEATURE_FLAG "y"

typedef enum  diagdump_enable {
    DISABLE = 0,
    ENABLE = 1
} diag_enable;

struct daemon {
   char* name;
   diag_enable diag_flag; /* daemon supports diag-dump feature flag*/
   struct daemon* next;
};

struct feature {
   char* name;
   char* desc;
   struct daemon*   p_daemon;
   /* Enable this flag if any one daemon supports diag-dump feature.
      Disable this flag If all the daemons doesnot support diag-dump.
      This flag useful to know whether this feature supports diag-dump */
   diag_enable diag_flag;
   struct feature*   next;
};

enum  {
   VALUE,
   FEATURE_NAME,
   FEATURE_DESC,
   DAEMON,
   DAEMON_NAME,
   DIAGDUMP_FLAG,
   MAX_NUM_KEYS
} ;


struct feature* get_feature_mapping(void);

#endif  /* __FEATURE_MAPPING_H */
