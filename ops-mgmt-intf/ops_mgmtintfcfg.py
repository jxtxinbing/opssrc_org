#!/usr/bin/env python
# (c) Copyright [2015-2016] Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import errno
import os
import sys
import select
import struct
import socket
from time import sleep
import re
import ovs.dirs
import ovs.daemon
import ovs.db.idl
import ovs.unixctl
import ovs.unixctl.server
import argparse
import ovs.vlog
import commands
import dhcp_options
from socket import inet_ntoa
from struct import pack

from pyroute2 import IPRoute
from pyroute2.netlink import NetlinkError
from pyroute2.netlink.rtnl.ifinfmsg import ifinfmsg
from pyroute2.netlink.rtnl.ifaddrmsg import ifaddrmsg
from pyroute2.netlink.rtnl import RTM_NEWADDR
from pyroute2.netlink.rtnl import RTM_GETADDR
from pyroute2.netlink.rtnl import RTM_DELADDR
from pyroute2.netlink.rtnl import RTM_NEWLINK
from pyroute2.netlink.rtnl import RTM_GETLINK
from pyroute2.netlink.rtnl import RTM_DELLINK

RECV_BUFFER = 4096
SYSTEM_TABLE = "System"
DNS_FILE = "/etc/resolv.conf"
DEFAULT_DNS_1 = '8.8.4.4'
DEFAULT_DNS_2 = '8.8.8.8'
DEFAULT_IPV4 = '0.0.0.0'

DEF_DB = 'unix:/var/run/openvswitch/db.sock'
OVS_SCHEMA = '/usr/share/openvswitch/vswitch.ovsschema'

# Anything that starts with 127.0.0 will be taken as loopback address.
LOOPBACK_ADDR = "127.0.0"
# Wait 2 seconds for the DHCP client to restart.
RESTART_WAIT_TIME = 1

MGMT_INTF_NULL_VAL = 'null'
MGMT_INTF_NAMESERVER_STR_LEN = 11
mgmt_interface_name = MGMT_INTF_NULL_VAL
RTMGRP_LINK = 1
RTMGRP_IPV4_IFADDR = 0x10
RTMGRP_IPV6_IFADDR = 0x100
IFA_F_DADFAILED = 0x08
IFA_F_TENTATIVE = 0x40
SO_BINDTODEVICE = 11
RTNL_GROUPS = RTMGRP_LINK | RTMGRP_IPV4_IFADDR | RTMGRP_IPV6_IFADDR


MGMT_INTF_KEY_NAME = "name"
MGMT_INTF_KEY_MODE = "mode"
MGMT_INTF_KEY_IP = "ip"
MGMT_INTF_KEY_SUBNET = "subnet_mask"
MGMT_INTF_KEY_DEF_GW = "default_gateway"
MGMT_INTF_KEY_DNS1 = "dns_server_1"
MGMT_INTF_KEY_DNS2 = "dns_server_2"
MGMT_INTF_MODE_DHCP = "dhcp"
MGMT_INTF_MODE_STATIC = "static"
MGMT_INTF_KEY_IPV6 = "ipv6"
MGMT_INTF_KEY_DEF_GW_V6 = "default_gateway_v6"
MGMT_INTF_KEY_IPV6_LINK_LOCAL = "ipv6_linklocal"
MGMT_INTF_KEY_LINK_STATE = "link_state"
MGMT_INTF_KEY_HOSTNAME = "hostname"
MGMT_INTF_KEY_DHCP_HOSTNAME = "dhcp_hostname"
MGMT_INTF_KEY_DOMAIN_NAME = "domain_name"
MGMT_INTF_KEY_DHCP_DOMAIN_NAME = "dhcp_domain_name"
MGMT_INTF_DEFAULT_HOSTNAME = "switch"
MGMT_INTF_DEFAULT_DOMAIN_NAME = ""

AF_INET = 2
RT_TABLE_MAIN = 254
#IPv6 Macros
DEFAULT_IPV6 = "::"
#Ipv6 family
AF_INET6 = 10
#IPv6 scope macros
SCOPE_IPV6_GLOBAL = 0
SCOPE_IPV6_LINK_LOCAL = 253

# Program control.
exiting = False

mode_val = MGMT_INTF_MODE_DHCP

#Logging.
vlog = ovs.vlog.Vlog("mgmtintfcfg")


def mgmt_intf_is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # Not a valid address.
        return False

    return True


def mgmt_intf_is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # Not a valid address.
        return False
    return True


def mgmt_intf_unixctl_exit(conn, unused_argv, unused_aux):
    global exiting

    exiting = True
    conn.reply(None)


# Funtion to get interface name by using interface index number.
def mgmt_intf_get_interface_name(index):
    nl = IPRoute()
    try:
        msg = nl.get_links(index)[0]
        ifname = msg.get_attr('IFLA_IFNAME')
    except Exception:
        ifname = None
    nl.close()
    return ifname


# Function to add IP and netmask.
def mgmt_intf_add_ip(mgmt_intf, ip_val, prefixlen):

    # Input validation.
    if ip_val == DEFAULT_IPV4 or prefixlen == 0:
        vlog.err("Trying to add NULL IP")
        return False

    ip = DEFAULT_IPV4
    prefix = 0

    try:
        ipr = IPRoute()
        # lookup interface by name.
        dev = ipr.link_lookup(ifname=mgmt_intf)[0]

        # Get the IP configured and check if the IP we are trying to configure
        # is already present.
        ip_list = [x.get_attr('IFA_ADDRESS')
                   for x in ipr.get_addr(label=mgmt_intf, family=AF_INET)]
        if ip_list:
            ip = ip_list[0]
        prefix_list = [x['prefixlen']
                       for x in ipr.get_addr(label=mgmt_intf, family=AF_INET)]
        if prefix_list:
            prefix = prefix_list[0]

        # If same IP already configured then do nothing.
        if ip == ip_val and prefixlen == prefix:
            ipr.close()
            return True
        elif ip != DEFAULT_IPV4 and prefix != 0:
            ipr.addr('delete', dev, address=ip, mask=prefix)

        # Add IP to the interface.
        ipr.addr('add', dev, address=ip_val, mask=prefixlen)
        ipr.close()

    except NetlinkError as e:
        vlog.err("Adding IP %s/%s on Mgmt Interface %s failed with code %d"
                 % (ip_val, prefixlen, mgmt_intf, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    vlog.info("Configured IP %s/%s on Mgmt Interface %s"
              % (ip_val, prefixlen, mgmt_intf))
    return True


# Function to remove statically configured IP and subnet mask.
def mgmt_intf_remove_ip(mgmt_intf, ip_val, prefixlen):

    ip = DEFAULT_IPV4
    prefix = 0

    try:
        ipr = IPRoute()
        # Get the configured IP and see if the IP we are trying to
        # remove is present.
        ip_list = [x.get_attr('IFA_ADDRESS')
                   for x in ipr.get_addr(label=mgmt_intf, family=AF_INET)]
        if ip_list:
            ip = ip_list[0]
            prefix_list = [x['prefixlen']
                           for x in
                           ipr.get_addr(label=mgmt_intf, family=AF_INET)]
            if prefix_list:
                prefix = prefix_list[0]
        else:
            # No IP is available on the interface.
            # So there is nothing to remove.
            ipr.close()
            return True

        # If the IP we are trying to remove not present,
        # then nothing to remove.
        if ip_val != DEFAULT_IPV4 and ip != ip_val and prefixlen != prefix:
            ipr.close()
            return True

        # Incase of flush, the input will be default ip.
        # In this case, clear the IP that is available.
        if ip_val == DEFAULT_IPV4 and ip != DEFAULT_IPV4:
            ip_val = ip
            prefixlen = prefix

        # lookup interface by name.
        dev = ipr.link_lookup(ifname=mgmt_intf)[0]
        # Remove the IP.
        ipr.addr('delete', dev, address=ip_val, mask=int(prefixlen))
        ipr.close()
    except NetlinkError as e:
        vlog.err("Removing IP %s/%s on Mgmt Interface %s failed with code %d"
                 % (ip_val, prefixlen, mgmt_intf, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    vlog.info("Removed IP %s/%s on Mgmt Interface %s"
              % (ip_val, prefixlen, mgmt_intf))
    return True


# Function to configure default gateway.
def mgmt_intf_add_def_gw(def_gw):

    cfg_gw = DEFAULT_IPV4
    # Input validation.
    if def_gw == DEFAULT_IPV4:
        return False

    try:
        ipr = IPRoute()
        # Get the existing default routes if any.
        if ipr.get_default_routes(table=RT_TABLE_MAIN, family=AF_INET):
            gw_list = [x.get_attr('RTA_GATEWAY')
                       for x in ipr.get_default_routes(table=RT_TABLE_MAIN,
                                                       family=AF_INET)]
            if gw_list:
                cfg_gw = gw_list[0]
                # If default route is already present then nothing to do.
        if cfg_gw == def_gw:
            ipr.close()
            return True
        elif cfg_gw != DEFAULT_IPV4:
            ipr.route('delete', gateway=cfg_gw)

        # Configure the default gateway.
        ipr.route('add', gateway=def_gw)
        ipr.close()
    except NetlinkError as e:
        vlog.err("Adding default gw %s on mgmt interface failed with code %d"
                 % (def_gw, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    vlog.info("Configured default gateway %s on Mgmt Interface" % def_gw)
    return True


# Function to remove configured default gateway.
def mgmt_intf_remove_def_gw(def_gw):

    cfg_gw = DEFAULT_IPV4

    try:
        ipr = IPRoute()
        # Get the configured gateway.
        if ipr.get_default_routes(table=RT_TABLE_MAIN, family=AF_INET):
            gw_list = [x.get_attr('RTA_GATEWAY')
                       for x in ipr.get_default_routes(table=RT_TABLE_MAIN,
                                                       family=AF_INET)]
            if gw_list:
                cfg_gw = gw_list[0]
            else:
                # There is not default gateway to remove. So return.
                ipr.close()
                return True

        # Gateway does not exists. So nothing to remove.
        if def_gw != DEFAULT_IPV4 and cfg_gw != def_gw:
            ipr.close()
            return True

        # Incase of flush, the input will be default gateway.
        # In this case, remove the default gateway that is available.
        if def_gw == DEFAULT_IPV4:
            def_gw = cfg_gw

        # If gateway available, then delete
        if def_gw != DEFAULT_IPV4:
            # Remove the default gateway.
            ipr.route('delete', gateway=def_gw)

        ipr.close()
    except NetlinkError as e:
        vlog.err("Removing default gw %s from mgmt interface failed.Code = %d"
                 % (def_gw, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    vlog.info("Removed default gateway %s on Mgmt Interface" % def_gw)
    return True


# Function to remove all the parameters that were configured
# statically from cache and OVSDB.
def mgmt_intf_clear_static_val(mgmt_intf):
    # No need to check the return value here.
    # If value is not present to remove these calls may fail,
    # which is ok in this case.
    mgmt_intf_remove_ip(mgmt_intf, DEFAULT_IPV4, 0)
    mgmt_intf_remove_def_gw(DEFAULT_IPV4)
    vlog.info("Cleared all statically configured values on mgmt interface")


# Update the OVSDB with the updated values.
def mgmt_intf_clear_status_col(idl):

    ovs_rec = {}
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            break

    data = {}

    txn = ovs.db.idl.Transaction(idl)

    setattr(ovs_rec, "mgmt_intf_status", data)

    status = txn.commit_block()
    if status != "success" and status != "unchanged":
        vlog.err("Clearing status column from ovsdb failed with status %s"
                 % (status))

        return False

    return True


# Function to update the resolved conf file with the values statically
# configured by the user.
def mgmt_intf_update_dns_conf(dns_1, dns_2, domain):

    cmd = ""
    if dns_1 != DEFAULT_IPV4:
        cmd = "DNS= %s" % (dns_1)
    if dns_2 != DEFAULT_IPV4:
        cmd += " %s" % (dns_2)
    try:
        cmd = ""
        if dns_1 != DEFAULT_IPV4:
            cmd = "nameserver %s\n" % (dns_1)
        if dns_2 != DEFAULT_IPV4:
            cmd += "nameserver %s\n" % (dns_2)
        if (domain != MGMT_INTF_DEFAULT_DOMAIN_NAME) and \
           (domain != MGMT_INTF_NULL_VAL):
            cmd += "domain %s\n" % (domain)
        fd = open(DNS_FILE, 'w')
        fd.write(cmd)
        fd.close()
    except IOError:
        vlog.err("File operation failed for file " + DNS_FILE)
        return False

    return True


# Function to clear the entries populated by DHCP client
def mgmt_intf_clear_dhcp_val(mgmt_intf):
    '''
    #Direct flushing with following APIs are not working.
    ipr.flush_addr(label=mgmt_intf)
    ipr.flush_routes(label=mgmt_intf)
    '''
    # Removing the DHCP populated IP address and default gateway.
    try:
        ipr = IPRoute()
        if ipr.get_addr(label=mgmt_intf):
            ip_list = [x.get_attr('IFA_ADDRESS')
                       for x in ipr.get_addr(label=mgmt_intf)]
            if ip_list:
                ip = ip_list[0]
                prefix_list = [x['prefixlen']
                               for x in ipr.get_addr(label=mgmt_intf)]
                if prefix_list:
                    prefix = prefix_list[0]

                    # lookup interface by name.
                    dev = ipr.link_lookup(ifname=mgmt_intf)[0]
                    ipr.addr('delete', dev, address=ip, mask=prefix)

        if ipr.get_default_routes(table=RT_TABLE_MAIN):
            gw_list = [x.get_attr('RTA_GATEWAY')
                       for x in ipr.get_default_routes(table=RT_TABLE_MAIN)]
            if gw_list:
                cfg_gw = gw_list[0]
                # Remove the default gateway.
                ipr.route('delete', gateway=cfg_gw)
        ipr.close()
    except NetlinkError as e:
        vlog.err("Removing DHCP populated values failed with code %d" % e.code)
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    return True


# Function to start the DHCP client on the management interface.
def mgmt_intf_start_dhcp_client(idl):

    mgmt_intf = get_mgmt_interface_name(idl)

    # Check the management interface status
    try:
        ip = IPRoute()
        state = ip.get_links(
            ip.link_lookup(ifname=mgmt_intf))[0].get_attr('IFLA_OPERSTATE')
        ip.close()
    except NetlinkError as e:
        vlog.err("Getting Management interface status failed with code %d"
                 % e.code)
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    # Update the link state.
    mgmt_intf_update_link_state(idl, state)

    if state == 'DOWN':
        return False

    # Start IPv4 DHCP client.
    dhcp_str = "systemctl start dhclient@" + mgmt_intf + ".service"
    os.system(dhcp_str)
    vlog.info("Started dhcp v4 client on interface " + mgmt_intf)
    #Before starting dhclient6 we need to check if DAD is complete
    try:
        ipr = IPRoute()
        dev = ipr.link_lookup(ifname=mgmt_intf)[0]
        cnt = 0
        while True:
            dhcp_flags_list = [x['flags']
                               for x in ipr.get_addr(index=dev,
                                                     family=AF_INET6)]
            dhcp_flags = dhcp_flags_list[0]
            vlog.dbg("flag status %d " % (dhcp_flags))
            cnt += 1
            sleep(1)
            if (dhcp_flags & IFA_F_TENTATIVE) != IFA_F_TENTATIVE or \
               (cnt > 10):
                break
        ipr.close()
    except NetlinkError as e:
        vlog.err("Getting flag info failed with code %d" % e.code)
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))

    # Start IPv6 DHCP client.
    dhcp_str = "systemctl start dhclient6@" + mgmt_intf + ".service"
    os.system(dhcp_str)
    vlog.info("Started dhcp v6 client on interface " + mgmt_intf)

    return True


# Function to stop the DHCP client.
def mgmt_intf_stop_dhcp_client(mgmt_intf):

    # Check if the DHCP client is running.
    dhcp_str = "systemctl status dhclient@" + mgmt_intf + ".service"
    status, output = commands.getstatusoutput(dhcp_str)
    if not status:
        if "running" in output:
            # No need to check for IPv6 status, as we start both and
            # stop both together.
            # Stop the IPv4 dhcp client.
            dhcp_str = "systemctl stop dhclient@" + mgmt_intf + ".service"
            os.system(dhcp_str)
            vlog.info("Stopped dhcp v4 client on interface " + mgmt_intf)

            # Stop the IPv6 dhcp client.
            dhcp_str = "systemctl stop dhclient6@" + mgmt_intf + ".service"
            os.system(dhcp_str)
            vlog.info("Stopped dhcp v6 client on interface " + mgmt_intf)

            sleep(RESTART_WAIT_TIME)


# Function to clean up the dhcp settings
def mgmt_intf_dhcp_cleanup(idl, mgmt_intf):
    # Stop DHCP client.
    mgmt_intf_stop_dhcp_client(mgmt_intf)

    # Remove entries populated by DHCP.
    mgmt_intf_clear_dhcp_val(mgmt_intf)

    # Remove any default DNS server Ips populated by DNS daemon.
    dhcp_options.mgmt_intf_clear_dns_conf()

    # Clear status column
    mgmt_intf_clear_status_col(idl)


# Function to process the mode transition from static to dhcp
def mgmt_intf_dhcp_mode_handler(idl, mgmt_intf):
    # Flush out the statically configured values if any.
    mgmt_intf_clear_static_val(mgmt_intf)

    dhcp_options.mgmt_intf_clear_dns_conf()

    # Start the DHCP client
    mgmt_intf_start_dhcp_client(idl)

    # Clear status column
    mgmt_intf_clear_status_col(idl)


# Function to add IPv6 and prefix
def mgmt_intf_add_ipv6(mgmt_intf, ipv6_addr, ipv6_prefix):

    # Input validation
    if ipv6_addr == DEFAULT_IPV6 or ipv6_prefix == 0:
        vlog.err("IPv6: Trying to add NULL IP")
        return False

    try:
        ipr = IPRoute()

        # lookup interface by name
        dev = ipr.link_lookup(ifname=mgmt_intf)[0]
        # Get the configured IP and see if the IP is present.
        ip_list = [x.get_attr('IFA_ADDRESS')
                   for x in ipr.get_addr(index=dev, family=AF_INET6,
                                         scope=SCOPE_IPV6_GLOBAL)]
        prefix_list = [x['prefixlen']
                       for x in ipr.get_addr(index=dev, family=AF_INET6,
                                             scope=SCOPE_IPV6_GLOBAL)]
        ind = 0
        for ip in ip_list:
            if ip == ipv6_addr and ipv6_prefix == prefix_list[ind]:
                ipr.close()
                return True
            ind = ind + 1

        # Add IP to the interface
        ipr.addr('add', dev, address=ipv6_addr, mask=ipv6_prefix)

        # Get the configured IP and see if the IP is present.
        ip_list = [x.get_attr('IFA_ADDRESS')
                   for x in ipr.get_addr(index=dev, family=AF_INET6,
                                         scope=SCOPE_IPV6_GLOBAL)]
        if ip_list:
            ip = ip_list[0]
        prefix_list = [x['prefixlen']
                       for x in ipr.get_addr(index=dev, family=AF_INET6,
                                             scope=SCOPE_IPV6_GLOBAL)]
        if prefix_list:
            prefix = prefix_list[0]

        ipr.close()

        # If IP configs are updated properly then update the DB status column
        if ip == ipv6_addr and ipv6_prefix == prefix:
            vlog.info("Configure static Ipv6 address %s/%s: success"
                      % (ipv6_addr, ipv6_prefix))
            return True
        else:
            vlog.err("Configure static Ipv6 address %s/%s: failed"
                     % (ipv6_addr, ipv6_prefix))
            return False

    except NetlinkError as e:
        vlog.err("Adding Ipv6 %s/%s on Mgmt Interface %s failed with code=%d"
                 % (ipv6_addr, ipv6_prefix, mgmt_intf, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    return True


# Function to remove statically configured IP and subnet mask
def mgmt_intf_remove_ipv6(mgmt_intf):
    try:
        ipr = IPRoute()
        # lookup interface by name
        dev = ipr.link_lookup(ifname=mgmt_intf)[0]
        # Get configured IP and see if IP we are trying to remove is present.
        ip_list = [x.get_attr('IFA_ADDRESS')
                   for x in ipr.get_addr(index=dev, family=AF_INET6,
                                         scope=SCOPE_IPV6_GLOBAL)]
        prefix_list = [x['prefixlen']
                       for x in ipr.get_addr(index=dev, family=AF_INET6,
                                             scope=SCOPE_IPV6_GLOBAL)]
        ind = 0
        for ip in ip_list:
            ipr.addr('delete', dev, address=ip, mask=prefix_list[ind])
            ind = ind + 1

        ipr.close()

    except NetlinkError as e:
        vlog.err("Remove Ipv6 Mgmt Interface %s failed with error code=%d"
                 % (mgmt_intf, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    return True


# Function to configure default gateway
def mgmt_intf_add_def_gw_ipv6(def_gw_ipv6):

    cfg_gw_ipv6 = DEFAULT_IPV6
    # Input validation
    if def_gw_ipv6 == DEFAULT_IPV6:
        return False

    try:
        ipr = IPRoute()
        # Get the existing default routes if any
        if ipr.get_default_routes(family=AF_INET6):
            gw_list = [x.get_attr('RTA_GATEWAY')
                       for x in ipr.get_default_routes(family=AF_INET6)]
            if gw_list:
                cfg_gw_ipv6 = gw_list[0]
                # If default route is already present then nothing to do
        if cfg_gw_ipv6 == def_gw_ipv6:
            ipr.close()
            return True

        # Delete the already existing one.
        if cfg_gw_ipv6 != DEFAULT_IPV6:
            ipr.route('delete', gateway=cfg_gw_ipv6, family=AF_INET6)

        # Configure the default gateway
        ipr.route('add', gateway=def_gw_ipv6, family=AF_INET6)

        if ipr.get_default_routes(family=AF_INET6):
            gw_list = [x.get_attr('RTA_GATEWAY')
                       for x in ipr.get_default_routes(family=AF_INET6)]
            if gw_list:
                cfg_gw_ipv6 = gw_list[0]

        ipr.close()
        # If default route is configured then update the DB status column
        if cfg_gw_ipv6 == def_gw_ipv6:
            vlog.info("Configure IPv6 default gateway %s: success"
                      % def_gw_ipv6)
        else:
            vlog.info("Configure IPv6 default gateway %s: failed"
                      % def_gw_ipv6)
            return False

    except NetlinkError as e:
        vlog.err("Adding Ipv6 default gw %s on Mgmt Interface failed. Code=%d"
                 % (def_gw_ipv6, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    return True


# Function to remove configured default gateway
def mgmt_intf_remove_def_gw_ipv6(def_gw_ipv6):

    if def_gw_ipv6 == DEFAULT_IPV6:
        return False

    cfg_gw_ipv6 = DEFAULT_IPV6

    try:
        ipr = IPRoute()
        # Get the configured gateway
        if ipr.get_default_routes(family=AF_INET6):
            gw_list = [x.get_attr('RTA_GATEWAY')
                       for x in ipr.get_default_routes(family=AF_INET6)]
            if gw_list:
                cfg_gw_ipv6 = gw_list[0]
        # Gateway does not exist. So nothing to remove
        if cfg_gw_ipv6 != def_gw_ipv6:
            ipr.close()
            return True
        # Remove the default gateway
        ipr.route('delete', gateway=def_gw_ipv6, family=AF_INET6)
        ipr.close()
    except NetlinkError as e:
        vlog.err("Removing Ipv6 default gw %s on Mgmt Interface failed.Code=%d"
                 % (def_gw_ipv6, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    return True


# Function to clear the IPv6 values.
def mgmt_intf_clear_ipv6_param(mgmt_intf, def_gw_ipv6):
    mgmt_intf_remove_ipv6(mgmt_intf)
    mgmt_intf_remove_def_gw_ipv6(def_gw_ipv6)

    return True


def mgmgt_intf_precheck_ip(mode_val, value, prev_ip):
    if mode_val != MGMT_INTF_MODE_STATIC:
        return False

    # Check if the address is valid
    if not mgmt_intf_is_valid_ipv4_address(value):
        vlog.err("Management interface: Trying to configure "
                 "Invalid IP address %s" % value)
        return False

    # Get the previously configured IP if any and check
    # if we are trying to update the same value.
    if prev_ip == value:
        return False

    return True


def mgmt_intf_precheck_subnet(mode_val, value, cfg_ip):
    if mode_val != MGMT_INTF_MODE_STATIC:
        return False

    # Check if the address is valid
    if int(value) < 1 or int(value) > 31:
        vlog.err("Management interface: Trying to configure "
                 "invalid subnet %s" % value)
        return False

    # If the configured IP is not valid then continue.
    # This will happen in ip remove case.
    if cfg_ip == DEFAULT_IPV4:
        return False

    # If value is 0.0.0.0 then the handling is already done in
    # IP handler.
    if value == DEFAULT_IPV4:
        return False

    return True


def mgmt_intf_precheck_ipv6(mode_val, value, prev_ip):
    if mode_val != MGMT_INTF_MODE_STATIC:
        return False

    if value != DEFAULT_IPV6:
        # Check if the address is valid
        offset = value.find('/')
        ipv6_addr = value[0:offset]
        if not mgmt_intf_is_valid_ipv6_address(ipv6_addr):
            vlog.err("Management interface: Trying to configure "
                     "invalid IPv6 address %s" % value)
            return False

    if prev_ip == value:
        return False

    return True


def mgmt_intf_precheck_gw(mode_val, value, prev_gw):
    if mode_val != MGMT_INTF_MODE_STATIC:
        return False

    # Check if the address is valid
    if not mgmt_intf_is_valid_ipv4_address(value):
        vlog.err("Management interface: Trying to configure "
                 "invalid gateway IP address %s" % value)
        return False

    if prev_gw == value:
        return False

    return True


def mgmt_intf_precheck_gwv6(mode_val, value, prev_gw):
    if mode_val != MGMT_INTF_MODE_STATIC:
        return False

    if value != DEFAULT_IPV6:
        # Check if the address is valid
        if not mgmt_intf_is_valid_ipv6_address(value):
            vlog.err("Management interface: Trying to configure "
                     "invalid gateway IP address %s" % value)
            return False

    if prev_gw == value:
        return False

    return True


def mgmt_intf_precheck_dns(mode_val, value, prev_dns):
    if mode_val != MGMT_INTF_MODE_STATIC:
        return False

    # Check if the address is valid
    if (value != DEFAULT_IPV6) and not mgmt_intf_is_valid_ipv4_address(value) \
            and not mgmt_intf_is_valid_ipv6_address(value):
        vlog.err("Management interface: Trying to configure "
                 "invalid nameserver IP address %s" % value)
        return False

    # Get the previously configured dns2 if any and
    # check if we are trying to update the same value.
    if prev_dns == value:
        return False

    return True


# Function to fetch row and handle the configurations.
# Only modified variables are handled.
def mgmt_intf_cfg_update(idl):
    global mode_val
    mgmt_intf = MGMT_INTF_NULL_VAL

    status_data = {}
    status_col_updt_reqd = False
    hostname = MGMT_INTF_DEFAULT_HOSTNAME
    domainname = MGMT_INTF_DEFAULT_DOMAIN_NAME
    new_mode = mode_val
    # Retrieve the data from status table
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.hostname:
            hostname = ovs_rec.hostname
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status
        if ovs_rec.domain_name:
            if ovs_rec.domain_name[0] != MGMT_INTF_DEFAULT_DOMAIN_NAME:
                domainname = ovs_rec.domain_name[0]
        if ovs_rec.mgmt_intf:
            new_mode = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_MODE,
                                             MGMT_INTF_NULL_VAL)
            if (new_mode == MGMT_INTF_NULL_VAL):
                new_mode = mode_val

    status_hostname = status_data.get(MGMT_INTF_KEY_HOSTNAME,
                                      MGMT_INTF_NULL_VAL)
    dhcp_hostname = status_data.get(MGMT_INTF_KEY_DHCP_HOSTNAME,
                                    MGMT_INTF_NULL_VAL)
    status_domainname = status_data.get(MGMT_INTF_KEY_DOMAIN_NAME,
                                        MGMT_INTF_NULL_VAL)
    dhcp_domainname = status_data.get(MGMT_INTF_KEY_DHCP_DOMAIN_NAME,
                                      MGMT_INTF_NULL_VAL)
    if new_mode == MGMT_INTF_MODE_STATIC:
        if dhcp_domainname != MGMT_INTF_NULL_VAL:
            del status_data[MGMT_INTF_KEY_DHCP_DOMAIN_NAME]
            dhcp_domainname = MGMT_INTF_NULL_VAL
            status_col_updt_reqd = True
        if dhcp_hostname != MGMT_INTF_NULL_VAL:
            del status_data[MGMT_INTF_KEY_DHCP_HOSTNAME]
            dhcp_hostname = MGMT_INTF_NULL_VAL
            status_col_updt_reqd = True

    if (hostname == MGMT_INTF_DEFAULT_HOSTNAME) and \
       (dhcp_hostname != MGMT_INTF_NULL_VAL):
        hostname = dhcp_hostname

    # Pick domainname from dhcp domainname
    if (domainname == MGMT_INTF_DEFAULT_DOMAIN_NAME) and \
       (dhcp_domainname != MGMT_INTF_NULL_VAL):
        domainname = dhcp_domainname

    # Set hostname status to value updated by CLI
    if hostname != status_hostname:
        status_data[MGMT_INTF_KEY_HOSTNAME] = hostname
        status_col_updt_reqd = True

    # Set domainname status based on the domainname configured
    if domainname != status_domainname:
        status_data[MGMT_INTF_KEY_DOMAIN_NAME] = domainname
        status_col_updt_reqd = True

    if status_col_updt_reqd:
        os.system("hostname " + hostname)

    # domain name should be added if configured manually
    # Add domainname entry in resolv.conf
    dns_1 = status_data.get(MGMT_INTF_KEY_DNS1, DEFAULT_IPV4)
    dns_2 = status_data.get(MGMT_INTF_KEY_DNS2, DEFAULT_IPV4)
    mgmt_intf_update_dns_conf(dns_1, dns_2, domainname)

    cfg_ip = DEFAULT_IPV4
    dns1 = DEFAULT_IPV4

    # Retrieve the mode and interface from config table
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf:
            mgmt_intf = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_NAME,
                                              MGMT_INTF_NULL_VAL)

            #---------------  MODE HANDLER ------------------------------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_MODE,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                # Mode configuration did not change. So nothing to update.
                if value != mode_val:
                    # If mode is static:
                    #   Stop the dhcp client (if it was running)
                    #   Clear the values from status column
                    if value == MGMT_INTF_MODE_STATIC:
                        # Link local will not be retrieved again.
                        # So preserve it across mode change.
                        ipv6_link_local = \
                            status_data.get(MGMT_INTF_KEY_IPV6_LINK_LOCAL,
                                            DEFAULT_IPV6)
                        link_state = \
                            status_data.get(MGMT_INTF_KEY_LINK_STATE,
                                            MGMT_INTF_NULL_VAL)
                        hostname = \
                            status_data.get(MGMT_INTF_KEY_HOSTNAME,
                                            MGMT_INTF_NULL_VAL)
                        dhcp_hostname = \
                            status_data.get(MGMT_INTF_KEY_DHCP_HOSTNAME,
                                            MGMT_INTF_NULL_VAL)
                        domainname = \
                            status_data.get(MGMT_INTF_KEY_DOMAIN_NAME,
                                            MGMT_INTF_NULL_VAL)
                        dhcp_domainname = \
                            status_data.get(MGMT_INTF_KEY_DHCP_DOMAIN_NAME,
                                            MGMT_INTF_NULL_VAL)

                        mgmt_intf_clear_ipv6_param(mgmt_intf,
                                                   status_data.get(
                                                       MGMT_INTF_KEY_DEF_GW_V6,
                                                       DEFAULT_IPV6))
                        mgmt_intf_dhcp_cleanup(idl, mgmt_intf)
                        #The system configured domain name should be updated
                        mgmt_intf_update_dns_conf(DEFAULT_IPV4,
                                                  DEFAULT_IPV4, domainname)
                        status_data = {}
                        if ipv6_link_local != DEFAULT_IPV6:
                            status_data[MGMT_INTF_KEY_IPV6_LINK_LOCAL] = \
                                ipv6_link_local
                            status_col_updt_reqd = True

                        if link_state != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_LINK_STATE] = \
                                link_state
                            status_col_updt_reqd = True

                        if hostname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_HOSTNAME] = \
                                hostname
                            status_col_updt_reqd = True

                        if dhcp_hostname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_DHCP_HOSTNAME] = \
                                dhcp_hostname
                            status_col_updt_reqd = True

                        if domainname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_DOMAIN_NAME] = \
                                domainname
                            status_col_updt_reqd = True

                        if dhcp_domainname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_DHCP_DOMAIN_NAME] = \
                                dhcp_domainname
                            status_col_updt_reqd = True

                    else:
                        # Mode is DHCP
                        # Link local will not be retrieved again.
                        # So preserve it across mode change.
                        ipv6_link_local = \
                            status_data.get(MGMT_INTF_KEY_IPV6_LINK_LOCAL,
                                            DEFAULT_IPV6)
                        link_state = \
                            status_data.get(MGMT_INTF_KEY_LINK_STATE,
                                            MGMT_INTF_NULL_VAL)
                        hostname = \
                            status_data.get(MGMT_INTF_KEY_HOSTNAME,
                                            MGMT_INTF_NULL_VAL)
                        dhcp_hostname = \
                            status_data.get(MGMT_INTF_KEY_DHCP_HOSTNAME,
                                            MGMT_INTF_NULL_VAL)
                        domainname = \
                            status_data.get(MGMT_INTF_KEY_DOMAIN_NAME,
                                            MGMT_INTF_NULL_VAL)
                        dhcp_domainname = \
                            status_data.get(MGMT_INTF_KEY_DHCP_DOMAIN_NAME,
                                            MGMT_INTF_NULL_VAL)

                        mgmt_intf_clear_ipv6_param(mgmt_intf,
                                                   status_data.get(
                                                       MGMT_INTF_KEY_DEF_GW_V6,
                                                       DEFAULT_IPV6))
                        mgmt_intf_dhcp_mode_handler(idl, mgmt_intf)

                        status_data = {}
                        if ipv6_link_local != DEFAULT_IPV6:
                            status_data[MGMT_INTF_KEY_IPV6_LINK_LOCAL] = \
                                ipv6_link_local
                            status_col_updt_reqd = True

                        if link_state != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_LINK_STATE] = \
                                link_state
                            status_col_updt_reqd = True

                        if hostname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_HOSTNAME] = \
                                hostname
                            status_col_updt_reqd = True

                        if dhcp_hostname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_DHCP_HOSTNAME] = \
                                dhcp_hostname
                            status_col_updt_reqd = True

                        if domainname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_DOMAIN_NAME] = \
                                domainname
                            status_col_updt_reqd = True

                        if dhcp_domainname != MGMT_INTF_NULL_VAL:
                            status_data[MGMT_INTF_KEY_DHCP_DOMAIN_NAME] = \
                                dhcp_domainname
                            status_col_updt_reqd = True

                    mode_val = value

            #-------------------------IP HANDLER ----------------------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_IP,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                prev_ip = status_data.get(MGMT_INTF_KEY_IP, DEFAULT_IPV4)
                # Check if the validation passes.
                if mgmgt_intf_precheck_ip(mode_val, value, prev_ip):
                    # If any IP was previously configured and the user tries
                    # to configure another one now, then delete the old IP
                    if prev_ip != DEFAULT_IPV4:
                        prev_subnet = status_data.get(MGMT_INTF_KEY_SUBNET,
                                                      DEFAULT_IPV4)
                        if prev_subnet != DEFAULT_IPV4:
                            mgmt_intf_remove_ip(mgmt_intf, prev_ip,
                                                prev_subnet)
                        else:
                            # IP was there but subnet not found.
                            # So remove the ip.
                            del status_data[MGMT_INTF_KEY_IP]
                            status_col_updt_reqd = True

                    if value == DEFAULT_IPV4:
                        # Previously configured IP is removed in above
                        # condition.
                        # So only update status column here.
                        del status_data[MGMT_INTF_KEY_IP]
                        del status_data[MGMT_INTF_KEY_SUBNET]
                        status_col_updt_reqd = True

                    # Update this value to be added when subnet key is
                    # processed.
                    cfg_ip = value
            #-------------------------SUBNET HANDLER -------------------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_SUBNET,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                # If the configured IP is not valid then continue.
                # This will happen in ip remove case.
                if cfg_ip == DEFAULT_IPV4:
                    # Check if only subnet has changed.
                    cfg_ip = status_data.get(MGMT_INTF_KEY_IP, DEFAULT_IPV4)

                if mgmt_intf_precheck_subnet(mode_val, value, cfg_ip):
                    # If adding IP fails then ip will not be updated in status
                    # column so that it will be retried again.
                    if mgmt_intf_add_ip(mgmt_intf, cfg_ip, int(value)):
                        status_data[MGMT_INTF_KEY_IP] = cfg_ip
                        status_data[MGMT_INTF_KEY_SUBNET] = value
                        status_col_updt_reqd = True

            #-------------------------IPv6 HANDLER ---------------------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_IPV6,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                # Get the previously configured IPv6 if any and
                # check if we are trying to update the same value.
                prev_ip = status_data.get(MGMT_INTF_KEY_IPV6, DEFAULT_IPV6)
                temp = re.match("^.+\d+", prev_ip)
                if temp:
                    prev_ip = temp.group(0)
                if mgmt_intf_precheck_ipv6(mode_val, value, prev_ip):
                    if prev_ip != DEFAULT_IPV6:
                        # If IPv6 is set again the previous value has to be
                        # removed before the new one is set.
                        mgmt_intf_remove_ipv6(mgmt_intf)
                        del status_data[MGMT_INTF_KEY_IPV6]
                        status_col_updt_reqd = True

                    if value != DEFAULT_IPV6:
                        offset = value.find('/')
                        ipv6_addr = value[0:offset]
                        ipv6_prefix = int(value[offset+1:len(value)])
                        if mgmt_intf_add_ipv6(mgmt_intf, ipv6_addr,
                                              ipv6_prefix):
                            status_data[MGMT_INTF_KEY_IPV6] = value
                            status_col_updt_reqd = True

            #-------------------------DEFAULT GATEWAY HANDLER -----------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_DEF_GW,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                # Get the previously configured gw if any and check if we
                # are trying to update the same value.
                prev_gw = status_data.get(MGMT_INTF_KEY_DEF_GW, DEFAULT_IPV4)
                if mgmt_intf_precheck_gw(mode_val, value, prev_gw):
                    # If any gw was previously configured and the user tries
                    # to configure another one now, then delete the old gw.
                    if prev_gw != DEFAULT_IPV4:
                        mgmt_intf_remove_def_gw(prev_gw)

                    # No default-gateway case.
                    if value == DEFAULT_IPV4:
                        # Previously configured gw is removed in above
                        # condition. So only update status column here.
                        del status_data[MGMT_INTF_KEY_DEF_GW]
                        status_col_updt_reqd = True
                    else:
                        # If adding default gateway fails then default gateway
                        # will not be updated in status column, so that it
                        # will be retried again.
                        if mgmt_intf_add_def_gw(value):
                            status_data[MGMT_INTF_KEY_DEF_GW] = value
                            status_col_updt_reqd = True

            #---------------DEFAULT GATEWAY HANDLER IPV6----------------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_DEF_GW_V6,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                # Get the previously configured gw if any and check
                # if we are trying to update the same value.
                prev_gw = status_data.get(MGMT_INTF_KEY_DEF_GW_V6,
                                          DEFAULT_IPV6)
                if mgmt_intf_precheck_gwv6(mode_val, value, prev_gw):
                    if value != DEFAULT_IPV6:
                        if prev_gw != DEFAULT_IPV6:
                            mgmt_intf_remove_def_gw_ipv6(prev_gw)
                            del status_data[MGMT_INTF_KEY_DEF_GW_V6]

                        if mgmt_intf_add_def_gw_ipv6(value):
                            status_data[MGMT_INTF_KEY_DEF_GW_V6] = value
                            status_col_updt_reqd = True
                    else:
                        mgmt_intf_remove_def_gw_ipv6(prev_gw)
                        if prev_gw != DEFAULT_IPV6:
                            del status_data[MGMT_INTF_KEY_DEF_GW_V6]
                            status_col_updt_reqd = True

            #------------------PRIMARY DNS HANDLER ----------------------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_DNS1,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                # Get the previously configured dns1 if any and check if
                # we are trying to update the same value.
                prev_dns = status_data.get(MGMT_INTF_KEY_DNS1, DEFAULT_IPV4)

                if mgmt_intf_precheck_dns(mode_val, value, prev_dns):
                    # If any dns1 was previously configured and the user tries
                    # to configure another one now, then delete the old dns1
                    if prev_dns != DEFAULT_IPV4:
                        # We cannot configure secondary without primary.
                        # So flush the dns values
                        mgmt_intf_update_dns_conf(DEFAULT_IPV4, DEFAULT_IPV4,
                                                  domainname)
                    # no nameserver <ip-addr case>.
                    if (value == DEFAULT_IPV4) or (value == DEFAULT_IPV6):
                        '''
                          Previously configured dns1 is removed here.
                          Sometimes when the daemon restarts again the
                          dns value might not be present. So check
                          and then remove
                        '''
                        if status_data.get(MGMT_INTF_KEY_DNS1, DEFAULT_IPV4) \
                                != DEFAULT_IPV4:
                            del status_data[MGMT_INTF_KEY_DNS1]
                            status_col_updt_reqd = True
                    else:
                        # If adding dns1 fails then dns1 will not be updated in
                        # status column, so that it will be retried again.
                        if mgmt_intf_update_dns_conf(value, DEFAULT_IPV4,
                                                     domainname):
                            status_data[MGMT_INTF_KEY_DNS1] = value
                            status_col_updt_reqd = True

            #--------------------SECONDARY DNS HANDLER ------------------------
            value = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_DNS2,
                                          MGMT_INTF_NULL_VAL)
            if value != MGMT_INTF_NULL_VAL:
                dns2 = status_data.get(MGMT_INTF_KEY_DNS2, DEFAULT_IPV4)
                dns1 = status_data.get(MGMT_INTF_KEY_DNS1, DEFAULT_IPV4)
                prev_dns = status_data.get(MGMT_INTF_KEY_DNS2, DEFAULT_IPV4)
                if mgmt_intf_precheck_dns(mode_val, value, prev_dns):
                    # no nameserver <dns1-ip-addr> <dns2-ip-addr> case.
                    if ((value == DEFAULT_IPV4) or (value == DEFAULT_IPV6)) \
                            and (dns2 != DEFAULT_IPV4):
                        mgmt_intf_update_dns_conf(DEFAULT_IPV4, DEFAULT_IPV4,
                                                  domainname)
                        '''
                         DNS1 would have been deleted already in DNS1 handler.
                         So delete DNS2 alone here.
                        '''
                        del status_data[MGMT_INTF_KEY_DNS2]
                        status_col_updt_reqd = True
                    else:
                        # Secondary cannot be configured without primary.
                        # So if primary DNS is not present,
                        # then dont update secondary DNS too.
                        if dns1 != DEFAULT_IPV4:
                            # Delete old one and then configure new one.
                            if prev_dns != DEFAULT_IPV4:
                                # Remove the previous dns2 alone
                                mgmt_intf_update_dns_conf(dns1, DEFAULT_IPV4,
                                                          domainname)

                            # If adding dns1 fails then dns1 will not be
                            # updated in status column, so that it will be
                            # retried again.
                            if mgmt_intf_update_dns_conf(dns1, value,
                                                         domainname):
                                status_data[MGMT_INTF_KEY_DNS2] = value
                                status_col_updt_reqd = True
        else:
            continue

    if (status_col_updt_reqd):
        txn = ovs.db.idl.Transaction(idl)

        setattr(ovs_rec, "mgmt_intf_status", status_data)

        status = txn.commit_block()

        if status != "success" and status != "unchanged":
            # The difference in values between mgmt_intf and mgmt_intf_status
            # will help us debug which updated failed.
            vlog.err("Updating status column failed with status %s" % (status))
            return False

    return True


def mgmt_intf_get_status(idl):

    ipv6_link_local = DEFAULT_IPV6
    link_state = MGMT_INTF_NULL_VAL
    hostname = MGMT_INTF_NULL_VAL
    dhcp_hostname = MGMT_INTF_NULL_VAL
    domainname = MGMT_INTF_NULL_VAL
    dhcp_domainname = MGMT_INTF_NULL_VAL

    # Get the cuurent values from status column
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status
            ipv6_link_local = status_data.get(MGMT_INTF_KEY_IPV6_LINK_LOCAL,
                                              DEFAULT_IPV6)
            link_state = status_data.get(MGMT_INTF_KEY_LINK_STATE,
                                         MGMT_INTF_NULL_VAL)
            hostname = status_data.get(MGMT_INTF_KEY_HOSTNAME,
                                       MGMT_INTF_NULL_VAL)
            dhcp_hostname = status_data.get(MGMT_INTF_KEY_DHCP_HOSTNAME,
                                            MGMT_INTF_NULL_VAL)
            domainname = status_data.get(MGMT_INTF_KEY_DOMAIN_NAME,
                                         MGMT_INTF_NULL_VAL)
            dhcp_domainname = status_data.get(MGMT_INTF_KEY_DHCP_DOMAIN_NAME,
                                              MGMT_INTF_NULL_VAL)

    return (ipv6_link_local, link_state, hostname,
            dhcp_hostname, domainname, dhcp_domainname)


# Function to update the values populated by DHCP client to ovsdb.
def mgmt_intf_update_dhcp_param(idl):

    mgmt_intf = MGMT_INTF_NULL_VAL

    # Retrieve the mode and interface from config table
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf:
            mgmt_intf = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_NAME,
                                              MGMT_INTF_NULL_VAL)

    if mgmt_intf == MGMT_INTF_NULL_VAL:
        vlog.err("Could not update DHCP values. "
                 "Management Interface was not available.")
        return False

    # If mode is not dhcp then dont update anything.
    if mode_val != MGMT_INTF_MODE_DHCP:
        return True

    # Initialize the values to be used.
    data = {}
    is_updt = False
    dhcp_ip = DEFAULT_IPV4
    ovsdb_ip = DEFAULT_IPV4
    dhcp_gw = DEFAULT_IPV4
    ovsdb_gw = DEFAULT_IPV4

    status_data = {}
    # Get the current values from status column
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status

    try:
        ipr = IPRoute()
        if ipr.get_addr(label=mgmt_intf, family=AF_INET):
            dhcp_ip_list = [x.get_attr('IFA_ADDRESS')
                            for x in ipr.get_addr(label=mgmt_intf,
                                                  family=AF_INET)]
            if not dhcp_ip_list:
                # Mode is DHCP but no IP.
                ipr.close()
                return True

            # Get the first IP address.
            # We handle only one IP address currently.
            dhcp_ip = dhcp_ip_list[0]
            # update the ovsdb only if the already existing value is
            # different from the dhcp populated value.
            ovsdb_ip = status_data.get(MGMT_INTF_KEY_IP, DEFAULT_IPV4)
            if (dhcp_ip != ovsdb_ip) and (dhcp_ip != DEFAULT_IPV4):
                dhcp_prefix_list = [x['prefixlen']
                                    for x in ipr.get_addr(label=mgmt_intf,
                                                          family=AF_INET)]
                if not dhcp_prefix_list:
                # Mode is DHCP but no IP.
                    ipr.close()
                    return True

                dhcp_prefix = dhcp_prefix_list[0]
                is_updt = True
        else:
            ipr = IPRoute()
            # lookup interface by name
            dev = ipr.link_lookup(ifname=mgmt_intf)[0]
            #update IPv6 global address in DB
            is_ip = ipr.get_addr(index=dev,
                                 family=AF_INET6, scope=SCOPE_IPV6_GLOBAL)
            if is_ip:
                dhcp_ip_list = [x.get_attr('IFA_ADDRESS')
                                for x in ipr.get_addr(index=dev,
                                                      family=AF_INET6,
                                                      scope=SCOPE_IPV6_GLOBAL)]
                if dhcp_ip_list:
                    dhcp_ip = dhcp_ip_list[0]
                if not dhcp_ip:
                    newdata = ""
                    fd = open(DNS_FILE, 'w')
                    fd.write(newdata)
                    fd.close()
            ipr.close()

        if ipr.get_default_routes(table=RT_TABLE_MAIN, family=AF_INET):
            dhcp_gw = [x.get_attr('RTA_GATEWAY')
                       for x in ipr.get_default_routes(table=RT_TABLE_MAIN,
                                                       family=AF_INET)][0]
            # update the ovsdb only if the already existing value is different
            # from the dhcp populated value.
            ovsdb_gw = status_data.get(MGMT_INTF_KEY_DEF_GW, DEFAULT_IPV4)
            if (dhcp_gw != ovsdb_gw) and (dhcp_gw != DEFAULT_IPV4):
                is_updt = True

        ipr.close()
    except NetlinkError as e:
        vlog.err("Updating IP and gateway from DHCP failed with code %d"
                 % e.code)
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False
    if is_updt:
        retry_count = 50
        while retry_count > 0:
            txn = ovs.db.idl.Transaction(idl)
            for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
                if ovs_rec.mgmt_intf_status:
                    data = ovs_rec.mgmt_intf_status
                    break
            ovs_rec.verify("mgmt_intf_status")
            if (dhcp_ip != ovsdb_ip) and (dhcp_ip != DEFAULT_IPV4):
                data[MGMT_INTF_KEY_IP] = dhcp_ip
                data[MGMT_INTF_KEY_SUBNET] = str(dhcp_prefix)
            if (dhcp_gw != ovsdb_gw) and (dhcp_gw != DEFAULT_IPV4):
                data[MGMT_INTF_KEY_DEF_GW] = dhcp_gw
            for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
                if ovs_rec.mgmt_intf:
                    break

            setattr(ovs_rec, "mgmt_intf_status", data)
            status = txn.commit_block()
            if status == "try again":
                vlog.info("ovsdb not in syn.Hence retrying the transaction")
                retry_count = retry_count - 1
                continue
            if status != "success" and status != "unchanged":
                vlog.err("Updating ovsdb for dhcp param failed with status %s"
                         % (status))
                return False
            else:
                break
    return True


# Function to update the values populated by DHCP client to ovsdb
def mgmt_intf_update_dhcp_param_ipv6(idl):

    mgmt_intf = MGMT_INTF_NULL_VAL

    # Retrieve the mode and interface from config table
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf:
            mgmt_intf = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_NAME,
                                              MGMT_INTF_NULL_VAL)

    if mgmt_intf == MGMT_INTF_NULL_VAL:
        vlog.err("Could not update DHCP values. "
                 "Management Interface was not available.")
        return False

    # If mode is not dhcp then dont update anything.
    if mode_val != MGMT_INTF_MODE_DHCP:
        return True

    # Initialize the values to be used.
    is_updt = False

    status_data = {}
    # Get the cuurent values from status column
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status

    dhcp_ipv6 = status_data.get(MGMT_INTF_KEY_IPV6, DEFAULT_IPV6)
    dhcp_gw_ipv6 = status_data.get(MGMT_INTF_KEY_DEF_GW_V6, DEFAULT_IPV6)

    try:
        ipr = IPRoute()
        # lookup interface by name
        dev = ipr.link_lookup(ifname=mgmt_intf)[0]
        #update IPv6 global address in DB
        if ipr.get_addr(index=dev, family=AF_INET6, scope=SCOPE_IPV6_GLOBAL):
            dhcp_ip_list = [x.get_attr('IFA_ADDRESS')
                            for x in ipr.get_addr(index=dev, family=AF_INET6,
                                                  scope=SCOPE_IPV6_GLOBAL)]
            if not dhcp_ip_list:
                # Mode is DHCP but no IP.
                # Resolved might write back the default values.
                # So flush the DNS file
                flush_dns_file()
                return True

            dhcp_ip = dhcp_ip_list[0]
            dhcp_prefix_list = [x['prefixlen']
                                for x in ipr.get_addr(index=dev,
                                                      family=AF_INET6,
                                                      scope=SCOPE_IPV6_GLOBAL)]
            dhcp_flags_list = [x['flags']
                               for x in ipr.get_addr(index=dev,
                                                     family=AF_INET6,
                                                     scope=SCOPE_IPV6_GLOBAL)]
            dhcp_prefix = dhcp_prefix_list[0]
            dhcp_addr_prefix = dhcp_ip + "/" + str(dhcp_prefix)
            # Update the ovsdb only if the already existing value is
            # different from the dhcp populated value.
            flags_string = ""
            if (dhcp_ipv6 != dhcp_addr_prefix) and \
                    (dhcp_addr_prefix != DEFAULT_IPV6):
                if (dhcp_flags_list[0] & IFA_F_DADFAILED) == IFA_F_DADFAILED:
                    flags_string = " ["+"duplicate"+"]"
                    vlog.info("Configuring %s address failed due to DAD "
                              "Failure" % (dhcp_addr_prefix))
                    dhcp_addr_prefix = dhcp_addr_prefix+flags_string

                dhcp_ipv6 = dhcp_addr_prefix
                is_updt = True

        #Update default-gateway-ipv6
        if ipr.get_default_routes(family=AF_INET6):
            cfg_gw_ipv6 = [x.get_attr('RTA_GATEWAY')
                           for x in ipr.get_default_routes(family=AF_INET6)][0]
            # Update the ovsdb only if the already existing value is
            # different from the dhcp populated value.
            if (dhcp_gw_ipv6 != cfg_gw_ipv6) and (cfg_gw_ipv6 != DEFAULT_IPV6):
                dhcp_gw_ipv6 = cfg_gw_ipv6
                is_updt = True

        ipr.close()

    except NetlinkError as e:
        vlog.err("Updating DHCP Ipv6 values on Mgmt Interface %s "
                 "failed with error code=%d" % (mgmt_intf, e.code))
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        return False

    if is_updt:
        txn = ovs.db.idl.Transaction(idl)

        for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
                data = ovs_rec.mgmt_intf_status
                break

        if dhcp_ipv6 != DEFAULT_IPV6:
            data[MGMT_INTF_KEY_IPV6] = dhcp_ipv6

        if dhcp_gw_ipv6 != DEFAULT_IPV6:
            data[MGMT_INTF_KEY_DEF_GW_V6] = dhcp_gw_ipv6

        setattr(ovs_rec, "mgmt_intf_status", data)
        status = txn.commit_block()
        if status != "success" and status != "unchanged":
            vlog.err("Updating ovsdb for ipv6 parameter populated from dhcp "
                     "failed with status %s" % (status))
            return False

    return True


# Update IPv6 link local address in DB status column
def mgmt_intf_update_ipv6_linklocal(idl):

    is_updt = False

    status_data = {}
    # Get the cuurent values from status column
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status
        if ovs_rec.mgmt_intf:
            mgmt_intf = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_NAME,
                                              MGMT_INTF_NULL_VAL)

    ipv6_link_local = status_data.get(MGMT_INTF_KEY_IPV6_LINK_LOCAL,
                                      DEFAULT_IPV6)

    try:
        ipr = IPRoute()
        # lookup interface by name
        dev = ipr.link_lookup(ifname=mgmt_intf)[0]

        # Update link local address in DB
        if ipr.get_addr(index=dev,
                        family=AF_INET6, scope=SCOPE_IPV6_LINK_LOCAL):
            dhcp_ip_list = [x.get_attr('IFA_ADDRESS')
                            for x in ipr.get_addr(index=dev, family=AF_INET6,
                                                  scope=SCOPE_IPV6_LINK_LOCAL)]

            dhcp_ip = dhcp_ip_list[0]
            dhcp_prefix_list = [x['prefixlen']
                                for x in
                                ipr.get_addr(index=dev,
                                             family=AF_INET6,
                                             scope=SCOPE_IPV6_LINK_LOCAL)]
            dhcp_prefix = dhcp_prefix_list[0]
            ipv6_link = dhcp_ip + "/" + str(dhcp_prefix)
            # Update the ovsdb only if the already existing value is
            # different from the dhcp populated value.
            if (ipv6_link_local != ipv6_link) and (ipv6_link != DEFAULT_IPV6):
                ipv6_link_local = ipv6_link
                is_updt = True

        ipr.close()
    except NetlinkError as e:
        vlog.err("Updating Ipv6 link local on Mgmt Interface failed "
                 "with error code=%d", e.code)
        ipr.close()
        return False
    except:
        vlog.err("Unexpected error:" + str(sys.exc_info()[0]))
        ipr.close()
        return False

    if is_updt:
        txn = ovs.db.idl.Transaction(idl)

        for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
                data = ovs_rec.mgmt_intf_status
                break

        data[MGMT_INTF_KEY_IPV6_LINK_LOCAL] = ipv6_link_local

        setattr(ovs_rec, "mgmt_intf_status", data)
        status = txn.commit_block()
        if status != "success" and status != "unchanged":
            vlog.err("Updating ovsdb for ipv6 link local failed with status %s"
                     % (status))
            return False

    return True


# Function to clear values when address delete message is received.
def mgmt_intf_address_delete_hdlr(idl, ipv6_link_local,
                                  link_state, hostname, dhcp_hostname,
                                  domainname, dhcp_domainname):
    status_data = {}
    updt_status = False

    # Clear status column
    mgmt_intf_clear_status_col(idl)

    if ipv6_link_local != DEFAULT_IPV6:
        status_data[MGMT_INTF_KEY_IPV6_LINK_LOCAL] = ipv6_link_local
        updt_status = True

    if link_state != MGMT_INTF_NULL_VAL:
        status_data[MGMT_INTF_KEY_LINK_STATE] = link_state
        updt_status = True

    if hostname != MGMT_INTF_NULL_VAL:
        status_data[MGMT_INTF_KEY_HOSTNAME] = hostname
        updt_status = True

    if dhcp_hostname != MGMT_INTF_NULL_VAL:
        status_data[MGMT_INTF_KEY_DHCP_HOSTNAME] = dhcp_hostname
        updt_status = True

    if domainname != MGMT_INTF_NULL_VAL:
        status_data[MGMT_INTF_KEY_DOMAIN_NAME] = domainname
        updt_status = True

    if dhcp_domainname != MGMT_INTF_NULL_VAL:
        status_data[MGMT_INTF_KEY_DHCP_DOMAIN_NAME] = dhcp_domainname
        updt_status = True

    if updt_status:

        for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
            if ovs_rec.mgmt_intf_status:
                break

        txn = ovs.db.idl.Transaction(idl)

        setattr(ovs_rec, "mgmt_intf_status", status_data)

        status = txn.commit_block()

        if status != "success" and status != "unchanged":
            # The difference in values between mgmt_intf and mgmt_intf_status
            # will help us debug which updated failed.
            vlog.err("Updating status column failed in address delete "
                     "with status %s" % (status))


# Function to update the state on the mgmt interface physical link.
def mgmt_intf_update_link_state(idl, state):
    status_data = {}

    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status
            break

    status_data[MGMT_INTF_KEY_LINK_STATE] = state
    txn = ovs.db.idl.Transaction(idl)

    setattr(ovs_rec, "mgmt_intf_status", status_data)

    status = txn.commit_block()

    if status != "success" and status != "unchanged":
    # The difference in values between mgmt_intf and mgmt_intf_status
    # will help us debug which updated failed.
        vlog.err("Updating status column failed in link state update "
                 "with status %s" % (status))


# Function to handle DAD event for ipv6
def mgmt_intf_dad_event_handler(idl, ip_addr, flags):
    status_data = {}
    flag_str = ""
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status
            break
    if ((flags & IFA_F_DADFAILED) == IFA_F_DADFAILED):
        flag_str = " [" + "duplicate" + "]"
    status_data[MGMT_INTF_KEY_IPV6] = ip_addr+flag_str
    vlog.info("Configuring %s address on management interface "
              "failed due to DAD Failure" % (ip_addr))
    txn = ovs.db.idl.Transaction(idl)
    setattr(ovs_rec, "mgmt_intf_status", status_data)

    status = txn.commit_block()
    if status != "success" and status != "unchanged":
    # will help us debug which updated failed.
        vlog.err("Updating status column failed in DAD event handler "
                 "with status %s" % (status))
        return False
    return True


# Function to process mgmt_intf netlink event.
def mgmt_intf_process_netlink_events(idl,
                                     ifname,
                                     event,
                                     msg_type,
                                     flags,
                                     ip_addr):
    global mode_val

    status_data = {}

    # Get the current values from status column.
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.mgmt_intf_status:
            status_data = ovs_rec.mgmt_intf_status
        if ovs_rec.mgmt_intf:
            mgmt_intf = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_NAME,
                                              MGMT_INTF_NULL_VAL)

    if ifname != mgmt_intf:
        vlog.dbg("Received event %s with msg type %s from "
                 "non-management interface %s" % (event, msg_type, ifname))
        return

    vlog.info("Netlink event %s with message type %d received "
              "for management interface" % (event, msg_type))

    if (msg_type == RTM_NEWADDR) \
       and ((flags & IFA_F_DADFAILED) == IFA_F_DADFAILED):
        return mgmt_intf_dad_event_handler(idl, ip_addr, flags)

    if (event == 'DOWN') or (event == 'UP'):
        mgmt_intf_update_link_state(idl, event)

    if mode_val != MGMT_INTF_MODE_DHCP:
        return

    # Event is for management interface.
    if (event == 'DOWN') or (msg_type == RTM_DELLINK):
        mgmt_intf_dhcp_cleanup(idl, mgmt_intf)
        mgmt_intf_clear_ipv6_param(mgmt_intf,
                                   status_data.get(MGMT_INTF_KEY_DEF_GW_V6,
                                                   DEFAULT_IPV6))
        mgmt_intf_address_delete_hdlr(
            idl, status_data.get(MGMT_INTF_KEY_IPV6_LINK_LOCAL,
                                 DEFAULT_IPV6), event,
            status_data.get(MGMT_INTF_KEY_HOSTNAME, MGMT_INTF_NULL_VAL),
            MGMT_INTF_NULL_VAL,
            status_data.get(MGMT_INTF_KEY_DOMAIN_NAME, MGMT_INTF_NULL_VAL),
            MGMT_INTF_NULL_VAL)
        mgmt_intf_cfg_update(idl)
    elif (event == 'UP') or (msg_type == RTM_NEWLINK):
        mgmt_intf_start_dhcp_client(idl)

    elif (msg_type == RTM_NEWADDR):
        mgmt_intf_update_dhcp_param(idl)
        mgmt_intf_update_dhcp_param_ipv6(idl)
        mgmt_intf_update_ipv6_linklocal(idl)
    elif (msg_type == RTM_DELADDR):
        mgmt_intf_address_delete_hdlr(
            idl, status_data.get(MGMT_INTF_KEY_IPV6_LINK_LOCAL, DEFAULT_IPV6),
            status_data.get(MGMT_INTF_KEY_LINK_STATE, MGMT_INTF_NULL_VAL),
            status_data.get(MGMT_INTF_KEY_HOSTNAME, MGMT_INTF_NULL_VAL),
            MGMT_INTF_NULL_VAL,
            status_data.get(MGMT_INTF_KEY_DOMAIN_NAME, MGMT_INTF_NULL_VAL),
            MGMT_INTF_NULL_VAL)
        dhcp_options.mgmt_intf_clear_dns_conf()
        mgmt_intf_cfg_update(idl)


# Netlink event handler.
def netlink_event_handler(idl, nl_socket):
    try:
        data = nl_socket.recv(RECV_BUFFER)

    except socket.error, e:
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            return
        else:
            # Socket error occurred.
            vlog.err("Netlink socket recv error %s" % (e))
    else:
        # Netlink message received.
        if data:
            msg_len, msg_type, flags, seq, pid = struct.unpack("=LHHLL",
                                                               data[:16])
            # Handle only link/address change notifications.
            if msg_type in (RTM_NEWLINK, RTM_DELLINK):
                msg = ifinfmsg(data)
                msg.decode()
            elif msg_type in (RTM_NEWADDR, RTM_DELADDR):
                msg = ifaddrmsg(data)
                msg.decode()
            else:
                return

            # Get the Interface name from the event message.
            ifname = msg.get_attr('IFLA_IFNAME') \
                or mgmt_intf_get_interface_name(msg['index'])
            event = msg.get_attr('IFLA_OPERSTATE', '')
            flags = msg['flags']
            ip_addr = ""
            if msg_type in (RTM_NEWADDR, RTM_DELADDR):
                ip_addr = msg.get_attr('IFA_ADDRESS')
                pre_len = msg['prefixlen']
                ip_addr = ip_addr+"/"+str(pre_len)
            vlog.dbg("Netlink Events %s event %s "
                     "flags %s" % (ifname, event, flags))
            mgmt_intf_process_netlink_events(idl, ifname,
                                             event, msg_type, flags, ip_addr)


# Get the management interface name from the ovsdb.
def get_mgmt_interface_name(idl):
    global mgmt_interface_name

    # During first time the management interface will not be available.
    # In that case retrieve the management interface from ovsdb.
    if mgmt_interface_name == MGMT_INTF_NULL_VAL:
        # Get the current values from status column
        for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
            if ovs_rec.mgmt_intf:
                mgmt_interface_name = ovs_rec.mgmt_intf.get(MGMT_INTF_KEY_NAME,
                                                            MGMT_INTF_NULL_VAL)

    if mgmt_interface_name == MGMT_INTF_NULL_VAL:
        vlog.err("Management Interface was not available.")

    return mgmt_interface_name


# This function is not called. But maintained for use during debugging.
def terminate():
    global exiting

    exiting = True
    return True


# Function to initialize dhcp parameters to ovsdb and start the dhclient.
def mgmt_intf_dhcp_initialize(idl):
    dhcp_options.mgmt_intf_clear_dns_conf()
    # Start the DHCP client. It is ok if it fails to start here,
    # since depending on the mode we might restart it again.
    mgmt_intf_start_dhcp_client(idl)
    mgmt_intf_cfg_update(idl)
    mgmt_intf_update_dhcp_param(idl)
    mgmt_intf_update_dhcp_param_ipv6(idl)
    mgmt_intf_update_ipv6_linklocal(idl)


# Function to wait till idl seq no has changed.
def mgmt_intf_run(idl, seqno):

    idl.run()

    if idl.change_seqno != seqno:
        mgmt_intf_cfg_update(idl)
        seqno = idl.change_seqno


#------------------ wait_for_config_complete() ----------------
def wait_for_config_complete(idl):

    system_is_configured = 0
    while True:
        idl.run()
        for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
            if ovs_rec.cur_cfg is not None and ovs_rec.cur_cfg != 0:
                system_is_configured = ovs_rec.cur_cfg
                break

        if(system_is_configured != 0):
            break

        poller = ovs.poller.Poller()
        idl.wait(poller)
        poller.block()


def mgmt_intf_initialize(idl):

    mgmt_intf = get_mgmt_interface_name(idl)

    # Bring the interface up
    try:
        ip = IPRoute()
        ip.link('set', index=ip.link_lookup(ifname=mgmt_intf)[0], state='up')
        ip.close()
    except NetlinkError as e:
        vlog.err("Failed to bring management interface up with code %d"
                 % e.code)
        return False


def main():
    global exiting

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', metavar="DATABASE",
                        help="A socket on which ovsdb-server is listening.",
                        dest='database')

    ovs.vlog.add_args(parser)
    ovs.daemon.add_args(parser)
    args = parser.parse_args()
    ovs.vlog.handle_args(args)
    ovs.daemon.handle_args(args)

    if args.database is None:
        remote = DEF_DB
    else:
        remote = args.database

    schema_helper = ovs.db.idl.SchemaHelper(location=OVS_SCHEMA)
    schema_helper.register_columns(SYSTEM_TABLE, ["cur_cfg"])
    schema_helper.register_columns(SYSTEM_TABLE, ["mgmt_intf"])
    schema_helper.register_columns(SYSTEM_TABLE, ["mgmt_intf_status"])
    schema_helper.register_columns(SYSTEM_TABLE, ["hostname"])
    schema_helper.register_columns(SYSTEM_TABLE, ["domain_name"])
    idl = ovs.db.idl.Idl(remote, schema_helper)

    ovs.daemon.daemonize()

    ovs.unixctl.command_register("exit", "", 0, 0,
                                 mgmt_intf_unixctl_exit, None)
    error, unixctl_server = ovs.unixctl.server.UnixctlServer.create(None)
    if error:
        ovs.util.ovs_fatal(error, "could not create unixctl server", vlog)

    seqno = idl.change_seqno  # Sequence number when we last processed the db.

    # Wait until the ovsdb sync up.
    while (seqno == idl.change_seqno):
        idl.run()
        if seqno == idl.change_seqno:
            poller = ovs.poller.Poller()
            idl.wait(poller)
            poller.block()

    wait_for_config_complete(idl)

    # Netlink Socket Creation.
    try:
        nl_socket = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW,
                                  socket.NETLINK_ROUTE)
        nl_socket.bind((os.getpid(),  RTNL_GROUPS))
        nl_socket.setsockopt(socket.SOL_SOCKET, SO_BINDTODEVICE,
                             get_mgmt_interface_name(idl))
        nl_socket.setblocking(False)
    except socket.error as msg:
        vlog.err("Management Interface netlink Socket Error: %s" % msg)
        sys.exit()

    mgmt_intf_initialize(idl)

    mgmt_intf_dhcp_initialize(idl)

    while not exiting:
        mgmt_intf_run(idl, seqno)
        seqno = idl.change_seqno

        unixctl_server.run()

        poller = ovs.poller.Poller()
        unixctl_server.wait(poller)
        poller.fd_wait(nl_socket, ovs.poller.POLLIN | ovs.poller.POLLHUP)
        idl.wait(poller)

        events_dict = {}
        # Use the poll function instead of poller.block() to get the events
        # and fd.
        try:
            try:
                events_dict = poller.poll.poll(poller.timeout)
                poller._Poller__log_wakeup(events_dict)
            except select.error, e:
                # Rate-limit.
                error, msg = e
                if error != errno.EINTR:
                    vlog.err("Management Interface poll: %s" % e[1])
        finally:
            poller._Poller__reset()

        # Netlink event handler.
        if events_dict:
            for fd, events in events_dict:
                if(nl_socket.fileno() == fd) \
                        and (events & ovs.poller.POLLIN):
                    netlink_event_handler(idl, nl_socket)
                if(nl_socket.fileno() == fd) \
                        and (events & ovs.poller.POLLHUP):
                    vlog.err("Management Interface netlink socket error HUP")
                    nl_socket.close()
                    sys.exit()
        if exiting:
            break

    # Daemon Exit.
    unixctl_server.close()
    idl.close()
    nl_socket.close()

    return

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally.
        raise
    except:
        vlog.exception("traceback")
        sys.exit(ovs.daemon.RESTART_EXIT_CODE)
