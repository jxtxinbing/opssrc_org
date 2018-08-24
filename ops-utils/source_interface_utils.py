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

VRF_TABLE = "VRF"
DEFAULT_VRF_NAME = "vrf_default"

SOURCE_INTERFACE_ALL_PROTOCOL = "all"

def get_protocol_source(idl, protocol_type, vrf_name):
    '''
        Get the source interface configured for the input protocol type and vrf.
        If the protocol type is not configured, return the source interface corresponding
        to "all" protocol type
    '''
    source_ip = None
    source_interface = None

    source_ip, source_interface = get_configured_protocol_source(idl, protocol_type, vrf_name)

    if source_ip is None and source_interface is None:
        source_ip, source_interface = get_configured_protocol_source(idl, SOURCE_INTERFACE_ALL_PROTOCOL, vrf_name)

    return source_ip, source_interface

def get_configured_protocol_source(idl, protocol_type, vrf_name):
    '''
        Get the source interface configured for the input protocol type and vrf.
        IP address is given priority over interface name.
    '''
    for ovs_rec in idl.tables[VRF_TABLE].rows.itervalues():
        if ovs_rec.name == vrf_name:
            ip = ovs_rec.source_ip
            for key, value in ovs_rec.source_ip.iteritems():
                if key == protocol_type:
                    if len(value) != 0:
                        return value, None

            source_interface = ovs_rec.source_interface
            for key, value in ovs_rec.source_interface.iteritems():
                if key == protocol_type:
                    return None, value.name

    return None, None
