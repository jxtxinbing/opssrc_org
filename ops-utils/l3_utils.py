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

def  get_mgmt_ip(idl):
    '''
       This function gets the ip address of the management interface
    '''
    mgmt_ip = None

    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status and ovs_rec.mgmt_intf_status is not None:
            for key, value in ovs_rec.mgmt_intf_status.iteritems():
                if key == "ip":
                    mgmt_ip = value

    return mgmt_ip

def extract_ip(ip):
    '''
       This function extracts the ip address from [u'x.x.x.x/y'] format
    '''
    tmp = str(ip).split('\'')
    tmp = tmp[1].split('/')
    ip = tmp[0]

    return ip

def get_lowest_secondary_ip(ovs_rec):
    '''
       This function returns the lowest secondary ipv4 address from the Port row
    '''

    secondary_ips = []

    for ip in ovs_rec.ip4_address_secondary:
        secondary_ips.append(ip)

    for i in range(len(secondary_ips)):
        secondary_ips[i] = "%3s.%3s.%3s.%3s" % tuple(secondary_ips[i].split("."))

    secondary_ips.sort()

    for i in range(len(secondary_ips)):
        secondary_ips[i] = secondary_ips[i].replace(" ", "")

    tmp = str(secondary_ips[0]).split('/')
    return tmp[0]


def get_ip_from_interface(idl, source_interface):
    '''
       This function returns the ip address configured on the interface.

       If primary address is configured, it returns the primary address.
       Otherwise, the lowest secondary ip address is returned.
    '''
    ip = None

    for ovs_rec in idl.tables[PORT_TABLE].rows.itervalues():
        if ovs_rec.name == source_interface:
            ip = ovs_rec.ip4_address
            if len(ip) == 0:
                ip = get_lowest_secondary_ip(ovs_rec)
            else:
                ip = extract_ip(ip)

    return ip
