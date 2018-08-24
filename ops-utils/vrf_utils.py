#!/usr/bin/env python
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

SYSTEM_TABLE = "System"
PORT_TABLE = "Port"
VRF_TABLE = "VRF"

DEFAULT_VRF_NAME = "vrf_default"
SWITCH_NAMESPACE = "swns"
NAMESPACE_NAME_PREFIX = "VRF_"

def get_vrf_ns_from_name(idl, vrf_name):
    '''
       This function returns the namespace corresponding to the vrf.
    '''
    namespace = None

    for ovs_rec in idl.tables[VRF_TABLE].rows.itervalues():
         if ovs_rec.name == vrf_name:
                table_id = ovs_rec.table_id
                table_id = str(table_id).strip('[]')
                if table_id == '0':
                    namespace = SWITCH_NAMESPACE
                else:
                    namespace = NAMESPACE_NAME_PREFIX + str(table_id)

    return namespace
