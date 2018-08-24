# (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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

import os
from time import sleep
import re
from pytest import mark

TOPOLOGY = """
#               +-------+
# +-------+     |       |
# |  sw1  <----->  hsw1 |
# +-------+     |       |
#               +-------+

# Nodes
[type=openswitch name="Switch 1"] sw1
[type=oobmhost name="Host 1"] h1

# Ports
[force_name=oobm] sw1:sp1

# Links
sw1:sp1 -- h1:if01
"""

# This class member is used for retaining
# IPv4 and it's subnet mask which is obtained from DHCP server.
dhcp_ipv4_submask = ''

# DHCP dhclient is currently not running on VSI image due to
# dhclient_apparmor_profile [/etc/apparmor.d/sbin.dhclient] file,
# which is present on running host machine[VM].
# The Profile files will declare access rules to allow access to
# linux system resources. Implicitly the access is denied
# when there is no matching rule in the profile.
# If we want to run docker instance with dhclient on such a
# host machine, we have to disable the dhclient_apparmor_profile file
# and enable it once testcase execution is finished.


def disable_dhclient_profile():
    if os.path.isfile("/etc/apparmor.d/sbin.dhclient") is True:
        os.system("sudo ln -s /etc/apparmor.d/sbin.dhclient "
                  "  /etc/apparmor.d/disable/")
        os.system('sudo apparmor_parser -R /etc/apparmor.d/sbin.dhclient')


def enable_dhclient_profile():
    if os.path.isfile("/etc/apparmor.d/sbin.dhclient") is True:
        os.system('sudo rm /etc/apparmor.d/disable/sbin.dhclient')
        os.system('sudo apparmor_parser -r /etc/apparmor.d/sbin.dhclient')


# When we run this test file with multiple instance,there is a chance of
# asynchronously enabling and disabling dhclient_profile file on the
# running system.
# To avoid asynchronous issue, the count variable is used to maintain
# the number of mgmt-intf test file execution instance in a temp file.
# whenever the count reaches zero, the profile file is enabled again.
def file_read_for_mgmt_instance_count():
    file_fd = open('mgmt_sys_var', 'r')
    count = file_fd.read()
    count = re.search('\d+', count)
    num = int(count.group(0))
    file_fd.close()
    return num


def file_write_for_mgmt_instance_count(count_number):
    file_fd = open('mgmt_sys_var', 'w+')
    file_fd.write(str(count_number))
    file_fd.close()


def setup_net():
    if os.path.exists('mgmt_sys_var') is False:
        file_write_for_mgmt_instance_count(0)
    else:
        count = file_read_for_mgmt_instance_count()
        num = count + 1
        file_write_for_mgmt_instance_count(num)
    disable_dhclient_profile()


# Static IP configuration check
def static_ip_config_check(sw1, conf_ip):
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        if conf_ip in output:
            cnt2 = 15
            while cnt2:
                output = sw1("ip addr show dev eth0", shell="bash")
                output += sw1("echo", shell="bash")
                if conf_ip in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert conf_ip in output


# Static IP unconfiguration check
def static_ip_unconfigure_check(sw1, conf_ip):
    eth0 = sw1.ports["sp1"]
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        if conf_ip not in output:
            cnt2 = 15
            while cnt2:
                output = sw1("ip addr show dev {eth0}".format(**locals()),
                             shell="bash")
                output += sw1("echo", shell="bash")
                if conf_ip not in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert conf_ip not in output


# Default IPv4 configuration check
def default_ipv4_configure_check(sw1, def_ip):
    sw1("end")
    output = sw1(" ")
    output_show = ''
    cnt = 15
    while cnt:
        output_show = sw1("show interface mgmt")
        output += sw1(" ")
        temp = re.findall("Default gateway IPv4\s+: " + def_ip, output_show)
        if temp:
            cnt2 = 15
            while cnt2:
                output = sw1("ip route show", shell="bash")
                output += sw1("echo", shell="bash")
                if def_ip in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert "Default gateway IPv4\t\t: " + def_ip in output_show
    assert def_ip in output


# DHCP client started on management interface.
def dhclient_started_on_mgmt_intf_ipv4(sw1):
    cnt = 15
    while cnt:
        output = sw1("systemctl status dhclient@eth0.service", shell="bash")
        output_temp = re.search(r'running', output, re.M | re.I)
        if output_temp is not None:
            if output_temp.group() == 'running':
                break
        else:
            cnt -= 1
            sleep(1)
    assert 'running' in output


# Mgmt Interface updated during bootup.
def mgmt_intf_updated_during_bootup(sw1):
    output = sw1("ovs-vsctl list system", shell="bash")
    output += sw1("echo", shell="bash")
    assert 'name="eth0"' in output


# Enter the management interface context.
def mgmt_intf_context_enter(sw1):
    output = sw1("configure terminal")
    assert 'Unknown command' not in output
    output = sw1("interface mgmt")
    assert 'Unknown command' not in output


# Set mode as DHCP.
def dhcp_mode_set_on_mgmt_intf(sw1):
    global dhcp_ipv4_submask
    sw1("ip dhcp")
    output = sw1(" ")
    cnt = 15
    tmp = []
    while cnt:
        output = sw1("do show interface mgmt")
        output += sw1(" ")
        tmp = re.findall("IPv4 address/subnet-mask\s+: \d+.\d+.\d+."
                         "\d+/.\d+", output)
        if tmp:
            break
        else:
            sleep(1)
            cnt -= 1
    dhcp_ipv4_submask = re.findall("\d+.\d+.\d+.\d+/.\d+",
                                   tmp[0])[0].split("/")
    assert 'dhcp' in output
    output = sw1("systemctl status dhclient@eth0.service", shell="bash")
    output_temp = re.search(r'running', output, re.M | re.I)
    if output_temp is None:
        assert 'running' in output


# Add Default gateway in DHCP mode.
def config_default_gateway_ipv4_dhcp_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("default-gateway 172.17.0.1")
    assert 'Configurations not allowed in dhcp mode' in output
    output = sw1(" ")
    output = sw1("do show interface mgmt")
    temp = re.findall("Default gateway IPv4\s+: .*\n", output)
    assert temp[0] in output


# Add DNS Server 1 in DHCP mode.
def config_primary_ipv4_dns_dhcp_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("nameserver 10.10.10.1")
    assert 'Configurations not allowed in dhcp mode' in output
    output = sw1(" ")
    output = sw1("echo", shell="bash")
    output = sw1("show interface mgmt")
    assert '10.10.10.1' not in output


# Add DNS Server 2 in DHCP mode.
def config_secondary_ipv4_dns_dhcp_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("nameserver 10.10.10.1 10.10.10.2")
    assert 'Configurations not allowed in dhcp mode' in output
    output = sw1(" ")
    output = sw1("echo", shell="bash")
    sw1("end")
    output = sw1("show interface mgmt")
    output += sw1("echo", shell="bash")
    assert '10.10.10.2' not in output


# Add DNS Server 2 through dhclient in DHCP mode.
def invalid_test_config_secondary_ipv4_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None 10.10.10.2 10.10.10.4 None", shell="bash")
    output = sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
        temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
        if temp and temp2:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '10.10.10.2' in output and \
           '10.10.10.4' in output


# Add DNS Server 1 through dhclient in DHCP mode.
def config_primary_ipv4_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None 10.10.10.5 None None", shell="bash")
    output = sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 10.10.10.5", output)
        if temp:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '10.10.10.5' in output


# Modify DNS Server 1 & 2 through dhclient in DHCP mode.
def reconfig_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None 10.10.10.2 10.10.10.4 None", shell="bash")
    output = sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
        temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
        if temp and temp2:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '10.10.10.2' in output and \
           '10.10.10.4' in output


# Remove primary and secondary DNS through dhclient in DHCP mode.
def remove_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None None None None", shell="bash")
    output = sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
        temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
        if temp and temp2:
            sleep(1)
            cnt -= 1
        else:
            break
    assert '10.10.10.2' not in output and \
           '10.10.10.4' not in output


# Add DNS Server 2 through dhclient in DHCP mode.
def config_secondary_ipv4_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None 10.10.10.2 10.10.10.4 None", shell="bash")
    output = sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
        temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
        if temp and temp2:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '10.10.10.2' in output and \
           '10.10.10.4' in output


# Static IP config when mode is static.
def config_ipv4_on_mgmt_intf_static_mode(sw1):
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    conf_ipv4 = ipv4_static+"/" + dhcp_ipv4_submask[1]
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)


# Reconfigure Sattic IP when mode is static.
def reconfig_ipv4_on_mgmt_intf_static_mode(sw1):
    ipv4_static = re.sub('\d+$', '129', dhcp_ipv4_submask[0])
    conf_ipv4 = ipv4_static+"/" + dhcp_ipv4_submask[1]
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)


# Add Default gateway in Static mode.
def config_ipv4_default_gateway_static_mode(sw1):
    ipv4_default = re.sub('\d+$', '130', dhcp_ipv4_submask[0])
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("default-gateway " + ipv4_default)
    default_ipv4_configure_check(sw1, ipv4_default)


# Remove Default gateway in static mode.
def unconfig_ipv4_default_gateway_static_mode(sw1):
    ipv4_default = re.sub('\d+$', '130', dhcp_ipv4_submask[0])
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("no default-gateway " + ipv4_default)
    cnt = 15
    while cnt:
        output = sw1("do show interface mgmt")
        output += sw1(" ")
        temp = re.findall("Default gateway IPv4\s+: " + ipv4_default, output)
        if temp:
            sleep(1)
            cnt -= 1
        else:
            break
    assert "Default gateway IPv4\t\t: \n" in output

    cnt2 = 15
    while cnt2:
        output = sw1("ip route show", shell="bash")
        output += sw1("echo", shell="bash")
        if ipv4_default not in output:
            break
        else:
            cnt2 -= 1
            sleep(1)
    assert ipv4_default not in output


# Add IPv6 Default gateway in static mode when IPV4 configured.
def config_ipv6_default_gateway_ipv4_is_set_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("default-gateway 2001:db8:0:1::128")
    assert 'IP should be configured first' in output


# Add DNS Server 1 in static mode.
def config_primary_ipv4_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("nameserver 10.10.10.5")
    output = sw1(" ")
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 10.10.10.5", output)
        if temp:
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.5' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 10.10.10.5' in output


# Add another primary DNS server.
def reconfig_primary_ipv4_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("nameserver 10.10.10.20")
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 10.10.10.20", output)
        if temp:
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.20' in output and\
                   'nameserver 10.10.10.1' not in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 10.10.10.20' in output
    assert 'nameserver 10.10.10.1' not in output


# Remove primary dns in static mode.
def remove_primary_ipv4_dns_static_mode(sw1):
    sleep(15)
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("no nameserver 10.10.10.20")
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        if 'Primary Nameserver\s+: 10.10.10.20' not in output:
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.20' not in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 10.10.10.20' not in output


# Configure Secondary DNS Server in static mode.
def config_secondary_ipv4_dns_static_mode(sw1):
    sleep(15)
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("nameserver 10.10.10.4 10.10.10.5")
    sleep(2)
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
           re.findall("Secondary Nameserver\s+: 10.10.10.5", output):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.5' in output\
                   and 'nameserver 10.10.10.4' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 10.10.10.5' in output
    assert 'nameserver 10.10.10.4' in output


# Reconfigure Secondary DNS Server in static mode.
def reconfig_secondary_ipv4_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("nameserver 10.10.10.4 10.10.10.20")
    output = sw1(" ")
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
           re.findall("Secondary Nameserver\s+: 10.10.10.20", output):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.4' in output and \
                   'nameserver 10.10.10.5' not in output and \
                   'nameserver 10.10.10.20' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 10.10.10.4' in output
    assert 'nameserver 10.10.10.5' not in output
    assert 'nameserver 10.10.10.20' in output


# Remove Secondary DNS ipv4 in static mode.
def unconfig_secondary_ipv4_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("no nameserver  10.10.10.4 10.10.10.20")
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
           re.findall("Secondary Nameserver\s+: 10.10.10.20", output):
            sleep(1)
            cnt -= 1
        else:
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.20' not in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
    assert 'nameserver 10.10.10.20' not in output


# Set Invalid IP on mgmt-intf.
def config_invalid_ipv4_on_mgmt_intf(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("ip static 0.0.0.0/24")
    assert 'Invalid IPv4 or IPv6 address' in output


# Set Multicast IP on mgmt-intf.
def config_multicast_ipv4_on_mgmt_intf(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("ip static 224.0.0.1/16")
    assert 'Invalid IPv4 or IPv6 address' in output


# Set broadcast IP on mgmt-intf.
def config_broadcast_ipv4_on_mgmt_intf(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("ip static 192.168.0.255/24")
    assert 'Invalid IPv4 or IPv6 address' in output


# Set loopback IP on mgmt-intf.
def config_loopback_ipv4_on_mgmt_intf(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("ip static 127.0.0.1/24")
    assert 'Invalid IPv4 or IPv6 address' in output


# Add Default Invalid gateway IP in static mode
def config_invalid_default_gateway_ipv4_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("default-gateway 0.0.0.0")
    assert 'Invalid IPv4 or IPv6 address' in output


# Add multicast ip as default gateway in static mode.
def config_multicast_ipv4_default_gateway_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("default-gateway 224.0.0.1")
    assert 'Invalid IPv4 or IPv6 address' in output


# Add broadcast ip as default gateway ip in static mode.
def config_broadcast_ipv4_default_gateway_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("default-gateway 192.168.0.255")
    assert 'Invalid IPv4 or IPv6 address' in output


# Add loopback address as default gateway ip in static mode
def config_loopback_ipv4_default_gateway_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("default-gateway 127.0.0.1")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure an invalid IP address as primary DNS.
def config_invalid_primary_ipv4_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("nameserver 0.0.0.0")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure a multicast address as primary DNS.
def config_multicast_ipv4_primary_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("nameserver 224.0.0.1")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure a broadcast address as primary DNS.
def config_broadcast_ipv4_primary_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("nameserver 192.168.0.255")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure a loopback address as primary DNS.
def config_loopback_primary_ipv4_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("nameserver 127.0.0.1")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure an invalid IP as secondary DNS.
def config_invalid_ipv4_secondary_dns_static_mode(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    output = sw1("nameserver 10.10.10.1 0.0.0.0")
    assert 'Invalid IPv4 or IPv6 address' in output


# Change mode from static to dhcp.
def change_mode_from_static_to_dhcp_ipv4(sw1):
    sw1("end")
    sw1("config t")
    sw1("interface mgmt")
    sw1("ip dhcp")
    output = sw1(" ")
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        output += sw1("echo", shell="bash")
        if 'dhcp' in output:
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'dhcp' in output


# Test if IP got from DHCP is set.
def ipv4_got_after_populated_ipv4_config(sw1):
    sleep(5)
    # Populate values as though populated from DHCP.
    sw1("ifconfig eth0 172.17.0.100 netmask 255.255.255.0", shell="bash")
    sw1("route add default gw 172.17.0.1 eth0", shell="bash")
    sw1("echo nameserver 1.1.1.1  > /etc/resolv.conf", shell="bash")
    sw1("echo nameserver 2.2.2.2 >> /etc/resolv.conf", shell="bash")

    out = sw1("ip addr show dev eth0", shell="bash")
    temp = re.findall("inet\s+\d+.\d+.\d+.\d+/\d+", out)
    host_ip_address = re.findall("\d+.\d+.\d+.\d+/\d+", temp[0])
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        output += sw1("echo", shell="bash")
        if host_ip_address[0] in output:
            break
        else:
            sleep(1)
            cnt -= 1
    assert host_ip_address[0] in output


# Test if Default gateway got from DHCP is set.
def ipv4_default_gateway_got_after_populated_ipv4_config(sw1):
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        output += sw1("echo", shell="bash")
        if '172.17.0.1' in output:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '172.17.0.1' in output


# Test if DNS server got from DHCP is set.
def dns_ipv4_got_after_populated_ipv4_config(sw1):
    output = sw1("cat /etc/resolv.conf", shell="bash")
    temp = re.findall("nameserver\s+.*\nnameserver\s+.*", output)
    assert temp[0] in output


# Add Default gateway IPV6 in DHCP mode.
def config_default_gateway_ipv6_dhcp_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    sleep(30)
    sw1("default-gateway 2001:db8:0:1::128")
    output = sw1(" ")
    output = sw1("do show interface mgmt")
    assert '2001:db8:0:1::128' not in output


# Add IPV6 DNS Server 1 in DHCP mode.
def config_primary_ipv6_dns_dhcp_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 2001:db8:0:1::128")
    output = sw1(" ")
    output = sw1("echo", shell="bash")
    sw1("end")
    output = sw1("show interface mgmt")
    assert '2001:db8:0:1::128' not in output


# Add IPV6 DNS Server 2 in DHCP mode.
def config_secondary_ipv6_dns_dhcp_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 2001:db8:0:1::106 2001:db8:0:1::128")
    output = sw1(" ")
    output = sw1("echo", shell="bash")
    sw1("end")
    output = sw1("show interface mgmt")
    output += sw1("echo", shell="bash")
    assert '2001:db8:0:1::128' not in output


# config IPv6 DNS Server 2 through dhclient in DHCP mode.
def config_secondary_ipv6_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None 2001:470:35:270::1  2001:470:35:270::2 None",
        shell="bash")
    output = sw1(" ")
    sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 2001:470:35:270::1",
                          output)
        temp2 = re.findall("Secondary Nameserver\s+: 2001:470:35:270::2",
                           output)
        if temp and temp2:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '2001:470:35:270::1' in output and \
           '2001:470:35:270::2' in output


# Config IPv6 DNS Server 1 through dhclient in DHCP mode.
def config_primary_ipv6_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None 2001:470:35:270::1 None None", shell="bash")
    output = sw1(" ")
    sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 2001:470:35:270::1",
                          output)
        if temp:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '2001:470:35:270::1' in output


# reconfig IPv6 DNS Server 2 & 1 through dhclient in DHCP mode.
def reconfig_ipv6_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None 2001:470:35:270::5  2001:470:35:270::6 None",
        shell="bash")
    output = sw1(" ")
    sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 2001:470:35:270::5",
                          output)
        temp2 = re.findall("Secondary Nameserver\s+: 2001:470:35:270::6",
                           output)
        if temp and temp2:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '2001:470:35:270::5' in output and \
           '2001:470:35:270::6' in output


# Remove IPV6 primary and secondary DNS through dhclient in DHCP mode.
def remove_primary_secondary_ipv6_dns_by_dhclient_dhcp_mode(sw1):
    sw1("dhcp_options None None None None", shell="bash")
    output = sw1(" ")
    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        temp = re.findall("Primary Nameserver\s+: 2001:470:35:270::5",
                          output)
        temp2 = re.findall("Secondary Nameserver\s+: 2001:470:35:270::6",
                           output)
        if temp and temp2:
            sleep(1)
            cnt -= 1
        else:
            break
    assert '2001:470:35:270::5' not in output and \
           '2001:470:35:270::6' not in output


# Static IPV6 config when mode is static.
def config_ipv6_on_mgmt_intf_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static 2001:db8:0:1::156/64")
    static_ip_config_check(sw1, "2001:db8:0:1::156/64")


# Set the IPV6 again.
def reconfig_ipv6_on_mgmt_intf_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static 2001:db8:0:1::157/64")
    static_ip_config_check(sw1, "2001:db8:0:1::157/64")


# Set Invalid IPV6 on mgmt-intf.
def config_invalid_ipv6_on_mgmt_intf(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("ip static ::")
    assert 'Unknown command' in output


# Test to verify Multicast IPV6 on mgmt-intf.
def config_multicast_ipv6_on_mgmt_intf(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("ip static ff01:db8:0:1::101/64")
    assert 'Invalid IPv4 or IPv6 address' in output


# Test to verify link-local IPV6 on mgmt-intf.
def config_link_local_ipv6_on_mgmt_intf(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("ip static fe80::5484:7aff:fefe:9799/64")
    assert 'Invalid IPv4 or IPv6 address' in output


# Test to verify loopback IPV6 on mgmt-intf
def config_loopback_ipv6_on_mgmt_intf(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("ip static ::1")
    assert 'Unknown command' in output


# Default gateway should be reachable. Otherwise test case will fail.
# Add Default gateway in Static mode.
def config_ipv6_default_gateway_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("default-gateway 2001:db8:0:1::128")
    output = sw1("end")
    output = sw1("show running-config")
    assert 'default-gateway 2001:db8:0:1::128' in output


# Add IPV4 Default gateway in static mode when IPV6 configured.
def config_ipv4_default_gateway_ipv6_is_set_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("default-gateway 192.168.1.2")
    assert 'IP should be configured first' in output


# Add Default Invalid gateway IPV6 in static mode.
def config_invalid_default_gateway_ipv6_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("default-gateway ::")
    assert 'Invalid IPv4 or IPv6 address' in output


# Add Deafult  multicast gateway ipv6 in static mode.
def config_multicast_ipv6_default_gateway_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("default-gateway ff01:db8:0:1::101")
    assert 'Invalid IPv4 or IPv6 address' in output


# Add Default link-local  gateway ipv6 in static mode.
def config_default_link_local_ipv6_gateway_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("default-gateway fe80::5484:7aff:fefe:9799")
    assert 'Invalid IPv4 or IPv6 address' in output


# Add Default loopback gateway ipv6 in static mode.
def config_loopback_ipv6_default_gateway_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("default-gateway ::1")
    assert 'Invalid IPv4 or IPv6 address' in output


# Remove Default gateway in static mode.
def unconfig_ipv6_default_gateway_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("no default-gateway 2001:db8:0:1::128")
    output = sw1("end")
    output = sw1("show running-config")
    assert 'default-gateway 2001:db8:0:1::128' not in output


# Configure an invalid IPV6 for primary DNS.
def config_invalid_primary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver ::")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure an multicast for primary DNS.
def config_multicast_ipv6_primary_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver ff01:db8:0:1::101")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure a link-local for primary DNS.
def config_link_local_ipv6_primary_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver fe80::5484:7aff:fefe:9799")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure a loopback for primary DNS.
def config_loopback_primary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver ::1")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure an invalid IP for secondary DNS.
def config_invalid_ipv6_secondary_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver 2001:db8:0:1::144 ::")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure an multicast for secondary DNS.
def config_multicast_ipv6_secondary_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver 2001:db8:0:1::144 ff01:db8:0:1::101")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure a link-local for secondary DNS.
def config_link_local_ipv6_secondary_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver 2001:db8:0:1::144 fe80::5484:7aff:fefe:9799")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure a loopback for secondary DNS.
def config_loopback_ipv6_secondary_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver 2001:db8:0:1::144 ::1")
    assert 'Invalid IPv4 or IPv6 address' in output


# Configure primary and secondary DNS as same.
def config_same_ipv6_primary_secondary_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver 2001:db8:0:1::144 2001:db8:0:1::144")
    assert 'Duplicate value entered' in output


# Add DNS Server 1 in static mode.
def config_primary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 2001:db8:0:1::144")
    output = sw1(" ")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall("Primary Nameserver\s+: 2001:db8:0:1::144",
                      output_show):
            cnt2 = 100
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::144' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 2001:db8:0:1::144' in output


# Add another DNS server 1.
def reconfig_primary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 2001:db8:0:1::154")
    output = sw1(" ")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall("Primary Nameserver\s+: 2001:db8:0:1::154",
                      output_show):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::154' in output \
                   and 'nameserver 2001:db8:0:1::144' not in output:
                    break
                else:
                    cnt -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 2001:db8:0:1::154' in output
    assert 'nameserver 2001:db8:0:1::144' not in output


# Remove DNS server 1.
def remove_primary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("no nameserver 2001:db8:0:1::154")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall('Primary Nameserver\s+: 2001:db8:0:1::154',
                      output_show):
            sleep(1)
            cnt -= 1
        else:
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::154' not in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
    assert 'nameserver 2001:db8:0:1::154' not in output


# Add DNS Server 2 in static mode.
def config_secondary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver 2001:db8:0:1::150 2001:db8:0:1::156")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
           output_show) and re.findall("Secondary Nameserver\s+: 2001:"
                                       "db8:0:1::156", output_show):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::156' in output and \
                   'nameserver 2001:db8:0:1::150' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 2001:db8:0:1::156' in output
    assert 'nameserver 2001:db8:0:1::150' in output


# Add another DNS server 2.
def reconfig_secondary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 2001:db8:0:1::150 2001:db8:0:1::154")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output = sw1(" ")
        if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
                      output_show) and \
           re.findall("Secondary Nameserver\s+: 2001:db8:0:1::154",
                      output_show):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::150' in output and \
                   'nameserver 2001:db8:0:1::156' not in output and \
                   'nameserver 2001:db8:0:1::154' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert 'nameserver 2001:db8:0:1::150' in output
    assert 'nameserver 2001:db8:0:1::156' not in output
    assert 'nameserver 2001:db8:0:1::154' in output


# Remove DNS server 2.
def unconfig_secondary_ipv6_dns_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("no nameserver  2001:db8:0:1::150 2001:db8:0:1::154")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
                      output_show) and \
           re.findall("Secondary Nameserver\s+: 2001:db8:0:1::154",
                      output_show):
            sleep(1)
            cnt -= 1
        else:
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::154' not in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
    assert 'nameserver 2001:db8:0:1::154' not in output


# Change mode from static to dhcp.
def change_mode_from_static_to_dhcp_ipv6(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    output = sw1(" ")
    sleep(15)
    output = ''
    output = sw1("do show interface mgmt")
    output += sw1(" ")
    assert 'dhcp' in output
    output = sw1("ovs-vsctl list system", shell="bash")
    output += sw1("echo", shell="bash")
    assert 'ipv6_linklocal' in output
    assert 'dns-server-1' not in output
    assert 'dns-server-2' not in output


# Test if IPV6  got from DHCP is set.
def ipv6_got_after_populated_ipv6_config(sw1):
    sleep(5)
    sw1("ip -6 addr add 2001:db8:0:1::150/64 dev eth0", shell="bash")
    sw1("ip -6 route add default via 2001:db8:0:1::128", shell="bash")
    sw1("echo nameserver 1.1.1.1  > /etc/resolv.conf", shell="bash")
    sw1("echo nameserver 2.2.2.2 >> /etc/resolv.conf", shell="bash")

    output = sw1("ip -6 addr show dev eth0", shell="bash")
    output = sw1("cat /etc/resolv.conf", shell="bash")

    cnt = 15
    sw1("end")
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1(" ")
        if re.findall("IPv6 address/prefix\s+: 2001:db8:0:1::150/64",
                      output):
            break
        else:
            sleep(1)
            cnt -= 1
    assert "IPv6 address/prefix\t\t: 2001:db8:0:1::150/64" in output


# Test if Default gateway got from DHCP is set.
def ipv6_default_gateway_got_after_populated_ipv6_config(sw1):
    sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1(" ")
        if "Default gateway IPv6\t\t: 2001:db8:0:1::128" not in output:
            sleep(1)
            cnt -= 1
        else:
            break
    assert "Default gateway IPv6\t\t: 2001:db8:0:1::128" in output


# Tests to verify 'no ip static .. ' to remove static Ips
# Verify to remove static IPv4 . Mode should be changed to 'dhcp'
def remove_ipv4_on_mgmt_intf_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    sw1("ip dhcp")
    sleep(15)
    conf_ipv4 = ipv4_static+"/" + dhcp_ipv4_submask[1]
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("no ip static " + conf_ipv4)
    static_ip_unconfigure_check(sw1, conf_ipv4)
    sw1("end")
    show_output = sw1("show interface mgmt")
    assert 'dhcp' in show_output


# Verify to remove static IPv4 with static Ipv6. Mode should not changed
def remove_ipv4_on_mgmt_intf_with_ipv6(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static 2001:db8:0:1::156/64")
    static_ip_config_check(sw1, "2001:db8:0:1::156/64")
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    conf_ipv4 = ipv4_static+"/" + dhcp_ipv4_submask[1]
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("no ip static " + conf_ipv4)
    static_ip_unconfigure_check(sw1, conf_ipv4)
    sw1("end")
    show_output = sw1("show interface mgmt")
    assert 'static' in show_output


# Verify to remove static IPv4 with default gw. Should not be removed
def remove_ipv4_on_mgmt_intf_with_def_gw(sw1):
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    ipv4_default = re.sub('\d+$', '130', dhcp_ipv4_submask[0])
    conf_ipv4 = ipv4_static + "/" + dhcp_ipv4_submask[1]
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("default-gateway " + ipv4_default)
    default_ipv4_configure_check(sw1, ipv4_default)
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    cmd_output = sw1("no ip static " + conf_ipv4)
    assert "Remove all IPv4 related info (Default gateway/DNS address)"
    " before removing the IP address from this interface" in cmd_output


# Verify to remove static IPv4 with name server. Should not be removed
def remove_ipv4_on_mgmt_intf_with_nameserver(sw1):
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    conf_ipv4 = ipv4_static+"/" + dhcp_ipv4_submask[1]
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 10.10.10.4 10.10.10.20")
    output = sw1(" ")
    sw1("end")
    cnt = 15
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        output += sw1("echo", shell="bash")
        if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
           re.findall("Secondary Nameserver\s+: 10.10.10.20", output):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.4' in output and \
                   'nameserver 10.10.10.5' not in output and \
                   'nameserver 10.10.10.20' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert '10.10.10.4' in output
    assert '10.10.10.5' not in output
    assert '10.10.10.20' in output
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    cmd_output = sw1("no ip static " + conf_ipv4)
    assert "Remove all IPv4 related info (Default gateway/DNS address)"
    " before removing the IP address from this interface" in cmd_output


# verify to remove static Ipv4 with mixed name server should not be removed
def remove_ipv4_on_mgmt_intf_with_nameserver_ipv6(sw1):
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    conf_ipv4 = ipv4_static+"/" + dhcp_ipv4_submask[1]
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 2001:db8:0:1::128 10.10.10.30")
    sw1("end")
    cnt = 15
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall("Primary Nameserver\s+: 2001:db8:0:1::128",
           output_show) and re.findall("Secondary Nameserver\s+: "
                                       "10.10.10.30", output_show):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::128' in output and \
                   'nameserver 10.10.10.30' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert '2001:db8:0:1::128' in output
    assert '10.10.10.30' in output

    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    cmd_output = sw1("no ip static " + conf_ipv4)
    assert "Remove all IPv4 related info (Default gateway/DNS address)"
    " before removing the IP address from this interface" in cmd_output


# Verify to remove static IPv6. Mode should be changed to DHCP
def remove_ipv6_on_mgmt_intf_static_mode(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    sw1(" ")
    sleep(15)
    sw1("ip static 2001:db8:0:1::156/64")
    static_ip_config_check(sw1, "2001:db8:0:1::156/64")
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("no ip static 2001:db8:0:1::156/64")
    static_ip_unconfigure_check(sw1, "2001:db8:0:1::156/64")
    sw1("end")
    show_output = sw1("show interface mgmt")
    assert 'dhcp' in show_output


# Verify to remove static Ipv6 with static Ipv4. Mode should not be changed
def remove_ipv6_on_mgmt_intf_with_ipv4(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static 2001:db8:0:1::156/64")
    static_ip_config_check(sw1, "2001:db8:0:1::156/64")
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    conf_ipv4 = ipv4_static+"/" + dhcp_ipv4_submask[1]
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static " + conf_ipv4)
    static_ip_config_check(sw1, conf_ipv4)
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("no ip static 2001:db8:0:1::156/64")
    static_ip_unconfigure_check(sw1, "2001:db8:0:1::156/64")
    sw1("end")
    show_output = sw1("show interface mgmt")
    assert 'static' in show_output


# Verify to remove Ipv6 with default gw. Should not be allowed
def remove_ipv6_on_mgmt_intf_with_def_gw(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static 2001:db8:0:1::156/64")
    static_ip_config_check(sw1, "2001:db8:0:1::156/64")
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("default-gateway 2001:db8:0:1::128")
    output = sw1(" ")
    sw1("end")
    cnt = 30
    while cnt:
        output = sw1("show interface mgmt")
        output += sw1("echo", shell="bash")
        output += sw1("echo", shell="bash")
        if '2001:db8:0:1::128' in output:
            break
        else:
            sleep(1)
            cnt -= 1
    assert '2001:db8:0:1::128' in output
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    cmd_output = sw1("no ip static 2001:db8:0:1::156/64")
    cmd_output += sw1(" ")
    assert "Remove all IPv6 related info (Default gateway/DNS address)"
    " before removing the IP address from this interface." in cmd_output


# Verify to remove IPv6 with name server. Should not be allowed
def remove_ipv6_on_mgmt_intf_with_nameserver(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static 2001:db8:0:1::156/64")
    static_ip_config_check(sw1, "2001:db8:0:1::156/64")
    output = sw1(" ")
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    output = sw1("nameserver 2001:db8:0:1::150 2001:db8:0:1::156")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
           output_show) and re.findall("Secondary Nameserver\s+: 2001:"
                                       "db8:0:1::156", output_show):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 2001:db8:0:1::156' in output and \
                   'nameserver 2001:db8:0:1::150' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert '2001:db8:0:1::156' in output
    assert '2001:db8:0:1::150' in output
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    cmd_output = sw1("no ip static 2001:db8:0:1::156/64")
    cmd_output += sw1(" ")
    assert "Remove all IPv6 related info (Default gateway/DNS address)"
    " before removing the IP address from this interface." in cmd_output


# Verify to remove IPv6 with mixed name server. Should not be allowed
def remove_ipv6_on_mgmt_intf_with_nameserver_ipv4(sw1):
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("ip static 2001:db8:0:1::156/64")
    static_ip_config_check(sw1, "2001:db8:0:1::156/64")
    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    sw1("nameserver 10.10.10.20 2001:db8:0:1::130")
    cnt = 15
    sw1("end")
    while cnt:
        output_show = sw1("show interface mgmt")
        output_show += sw1(" ")
        if re.findall("Primary Nameserver\s+: 10.10.10.20",
           output_show) and re.findall("Secondary Nameserver\s+: 2001:"
                                       "db8:0:1::130", output_show):
            cnt2 = 15
            while cnt2:
                output = sw1("cat /etc/resolv.conf", shell="bash")
                output += sw1("echo", shell="bash")
                if 'nameserver 10.10.10.20' in output and \
                   'nameserver 2001:db8:0:1::130' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert '10.10.10.20' in output
    assert '2001:db8:0:1::130' in output

    sw1("end")
    sw1("configure terminal")
    sw1("interface mgmt")
    cmd_output = sw1("no ip static 2001:db8:0:1::156/64")
    assert "Remove all IPv6 related info (Default gateway/DNS address)"
    " before removing the IP address from this interface." in cmd_output


# Verify to configure system hostname through CLI
def config_set_hostname_from_cli(sw1):
    sleep(15)
    sw1("end")
    sw1("config terminal")
    sleep(15)
    sw1("hostname cli")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        hostname = sw1("ovs-vsctl get system . hostname",
                       shell="bash").rstrip('\r\n')
        output = sw1("uname -n", shell="bash")
        if "hostname=cli" in cmd_output and \
           hostname == "cli" and \
           "cli" in output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'hostname=cli' in cmd_output and \
           hostname == 'cli' and 'cli' in output
    sw1._shells['vtysh']._prompt = (
        '(^|\n)cli(\\([\\-a-zA-Z0-9]*\\))?#'
    )


# Verify to unconfigure system hostname through CLI
def config_no_hostname_from_cli(sw1):
    sw1._shells['vtysh']._prompt = (
        '(^|\n)cli(\\([\\-a-zA-Z0-9]*\\))?#'
    )

    sw1("end")
    sw1("config terminal")
    sw1("no hostname")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        hostname = sw1("ovs-vsctl get system . hostname",
                       shell="bash").rstrip('\r\n')
        output = sw1("uname -n", shell="bash")
        if "hostname=switch" in cmd_output and \
           hostname == "" and \
           "switch" in output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'hostname=switch' in cmd_output and \
           hostname == '""' and 'switch' in output
    sw1._shells['vtysh']._prompt = (
        '(^|\n)switch(\\([\\-a-zA-Z0-9]*\\))?#'
    )


# Verify to check system hostname defaults to switch
def default_system_hostname(sw1):
    sw1._shells['vtysh']._prompt = (
        '(^|\n)switch(\\([\\-a-zA-Z0-9]*\\))?#'
    )
    sw1("end")
    sw1("config terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    sleep(2)
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        hostname = sw1("ovs-vsctl get system . hostname",
                       shell="bash").rstrip('\r\n')
        output = sw1("uname -n", shell="bash")
        if "hostname=switch" in cmd_output and \
           hostname == '""' and \
           "switch" in output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'hostname=switch' in cmd_output and \
           hostname == '""' and 'switch' in output


# Verify to set hostname through dhclient
def set_hostname_by_dhclient(sw1):
    sw1("dhcp_options dhcp-new None None None", shell="bash")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        hostname = sw1("ovs-vsctl get system . hostname",
                       shell="bash").rstrip('\r\n')
        output = sw1("uname -n", shell="bash")
        if "dhcp_hostname=dhcp-new" in cmd_output and \
           "hostname=dhcp-new" in cmd_output and \
           hostname == '""' and "dhcp-new" in output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'dhcp_hostname=dhcp-new' in cmd_output and \
           'hostname=dhcp-new' in cmd_output and \
           hostname == '""' and 'dhcp-new' in output
    sw1._shells['vtysh']._prompt = (
        '(^|\n)dhcp-new(\\([\\-a-zA-Z0-9]*\\))?#'
    )


# Verify to remove hostname through dhclient
def remove_dhcp_hostname_by_dhclient(sw1):
    sw1._shells['vtysh']._prompt = (
        '(^|\n)dhcp-new(\\([\\-a-zA-Z0-9]*\\))?#'
    )
    sw1("end")
    sw1("config terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    sleep(2)
    sw1("dhcp_options None None None None", shell="bash")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        hostname = sw1("ovs-vsctl get system . hostname",
                       shell="bash").rstrip('\r\n')
        output = sw1("uname -n", shell="bash")
        if "dhcp_hostname=" not in cmd_output and \
           "hostname=switch" in cmd_output and \
           hostname == '""' and "switch" in output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'dhcp_hostname=' not in cmd_output and \
           hostname == '""' and 'switch' in output
    sw1._shells['vtysh']._prompt = (
        '(^|\n)switch(\\([\\-a-zA-Z0-9]*\\))?#'
    )


# Verify to configure system domainname through CLI
def config_set_domainname_from_cli(sw1):
    sw1._shells['vtysh']._prompt = (
        '(^|\n)switch(\\([\\-a-zA-Z0-9]*\\))?#'
    )
    sw1("end")
    sw1("config terminal")
    sw1("domain-name cli")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        domainname = sw1("ovs-vsctl get system . domain_name",
                         shell="bash").rstrip('\r\n')
        resolve_output = sw1("cat /etc/resolv.conf", shell="bash")
        if "domain_name=cli" in cmd_output and \
           domainname == "cli" and \
           "domain cli" in resolve_output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'domain_name=cli' in cmd_output and \
           domainname == 'cli' and "domain cli" in resolve_output


# Verify to unconfigure system domainname through CLI
def config_no_domainname_from_cli(sw1):
    sw1("end")
    sw1("config terminal")
    sw1("domain-name cli")
    sw1("no domain-name")
    cnt = 15
    while cnt:
        sw1("ovs-vsctl list system", shell="bash")
        domainname = sw1("ovs-vsctl get system . domain_name",
                         shell="bash").rstrip('\r\n')
        resolve_output = sw1("cat /etc/resolv.conf", shell="bash")
        if domainname == '""' and \
           "domain cli" not in resolve_output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert "domain cli" not in resolve_output and domainname == '""'


# Verify to set domainname through dhclient
def set_domainname_by_dhclient(sw1):
    sw1("end")
    sw1("config terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    sleep(2)
    sw1("dhcp_options None None None new_dom", shell="bash")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        domainname = sw1("ovs-vsctl get system . domain_name",
                         shell="bash").rstrip('\r\n')
        if "dhcp_hostname=new_dom" in cmd_output and \
           "domain_name=new_dom" in cmd_output and domainname == '""':
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'dhcp_domain_name=new_dom' in cmd_output and \
           'domain_name=new_dom' in cmd_output and domainname == '""'


# Verify to remove domainname through dhclient
def remove_dhcp_domainname_by_dhclient(sw1):
    sw1("end")
    sw1("config terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    sleep(2)
    sw1("dhcp_options None None None None", shell="bash")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        domainname = sw1("ovs-vsctl get system . domain_name",
                         shell="bash").rstrip('\r\n')
        if "dhcp_domain_name" not in cmd_output and domainname == '""':
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'dhcp_domain_name' not in cmd_output and domainname == '""'


# Extra cleanup if test fails in middle.
def mgmt_intf_cleanup(sw1):
    output = sw1("ip netns exec swns ip addr show dev 1", shell="bash")
    if 'inet' in output:
        sw1("ip netns exec swns ip address flush dev 1", shell="bash")


@mark.gate
def test_ct_mgmt_intf(topology, step):

    setup_net()

    sw1 = topology.get('sw1')

    hsw1 = topology.get('h1')

    assert sw1 is not None

    assert hsw1 is not None

    hsw1("echo -e \"option domain-name-servers 10.10.10.4, 10.10.10.5;\n"
         "option routers 172.17.0.1;\noption routers 172.17.0.1;\n"
         "subnet 172.17.0.0 netmask 255.255.255.0 {\n"
         "range 172.17.0.10 172.17.0.100;\n"
         "option domain-name-servers 10.10.10.4, 10.10.10.5;\n}\" >> "
         "/etc/dhcp/dhcpd.conf")

    hsw1("ifconfig eth1 172.17.0.15 netmask 255.255.255.0")

    hsw1("sudo service isc-dhcp-server start")

    # mgmt intf tests.
    step("\n########## Test to configure Management "
         "interface with DHCP IPV4 ##########\n")

    # mgmt-intf service started without disabling dhclient profile on
    # running VM.Due to that we disabled the dhclient profile by setup_net
    # function and restarting the mgmt-intf service.
    sw1("systemctl restart mgmt-intf", shell="bash")

    dhclient_started_on_mgmt_intf_ipv4(sw1)

    mgmt_intf_updated_during_bootup(sw1)

    mgmt_intf_context_enter(sw1)

    dhcp_mode_set_on_mgmt_intf(sw1)

    config_default_gateway_ipv4_dhcp_mode(sw1)

    config_primary_ipv4_dns_dhcp_mode(sw1)

    config_secondary_ipv4_dns_dhcp_mode(sw1)

    config_secondary_ipv4_dns_by_dhclient_dhcp_mode(sw1)

    config_primary_ipv4_dns_by_dhclient_dhcp_mode(sw1)

    reconfig_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(sw1)

    remove_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(sw1)

    step("\n########## Test to configure Management "
         "interface with static IPV4 ##########\n")
    config_ipv4_on_mgmt_intf_static_mode(sw1)

    reconfig_ipv4_on_mgmt_intf_static_mode(sw1)

    config_ipv4_default_gateway_static_mode(sw1)

    unconfig_ipv4_default_gateway_static_mode(sw1)

    config_ipv6_default_gateway_ipv4_is_set_static_mode(sw1)

    config_primary_ipv4_dns_static_mode(sw1)

    reconfig_primary_ipv4_dns_static_mode(sw1)

    remove_primary_ipv4_dns_static_mode(sw1)

    config_secondary_ipv4_dns_static_mode(sw1)

    reconfig_secondary_ipv4_dns_static_mode(sw1)

    unconfig_secondary_ipv4_dns_static_mode(sw1)

    config_invalid_ipv4_on_mgmt_intf(sw1)

    config_multicast_ipv4_on_mgmt_intf(sw1)

    config_broadcast_ipv4_on_mgmt_intf(sw1)

    config_loopback_ipv4_on_mgmt_intf(sw1)

    config_invalid_default_gateway_ipv4_static_mode(sw1)

    config_multicast_ipv4_default_gateway_static_mode(sw1)

    config_broadcast_ipv4_default_gateway_static_mode(sw1)

    config_loopback_ipv4_default_gateway_static_mode(sw1)

    config_invalid_primary_ipv4_dns_static_mode(sw1)

    config_multicast_ipv4_primary_dns_static_mode(sw1)

    config_broadcast_ipv4_primary_dns_static_mode(sw1)

    config_loopback_primary_ipv4_dns_static_mode(sw1)

    config_invalid_ipv4_secondary_dns_static_mode(sw1)

    change_mode_from_static_to_dhcp_ipv4(sw1)

    ipv4_got_after_populated_ipv4_config(sw1)

    ipv4_default_gateway_got_after_populated_ipv4_config(sw1)

    step("\n########## Test to configure Management "
         "interface with Dhcp IPV6 ##########\n")
    config_default_gateway_ipv6_dhcp_mode(sw1)

    config_primary_ipv6_dns_dhcp_mode(sw1)

    config_secondary_ipv6_dns_dhcp_mode(sw1)

    config_secondary_ipv6_dns_by_dhclient_dhcp_mode(sw1)

    config_primary_ipv6_dns_by_dhclient_dhcp_mode(sw1)

    reconfig_ipv6_dns_by_dhclient_dhcp_mode(sw1)

    remove_primary_secondary_ipv6_dns_by_dhclient_dhcp_mode(sw1)

    step("\n########## Test to configure Management "
         "interface with static IPV6 ##########\n")
    config_ipv6_on_mgmt_intf_static_mode(sw1)

    reconfig_ipv6_on_mgmt_intf_static_mode(sw1)

    config_invalid_ipv6_on_mgmt_intf(sw1)

    config_multicast_ipv6_on_mgmt_intf(sw1)

    config_link_local_ipv6_on_mgmt_intf(sw1)

    config_loopback_ipv6_on_mgmt_intf(sw1)

    config_ipv6_default_gateway_static_mode(sw1)

    config_ipv4_default_gateway_ipv6_is_set_static_mode(sw1)

    config_invalid_default_gateway_ipv6_static_mode(sw1)

    config_multicast_ipv6_default_gateway_static_mode(sw1)

    config_default_link_local_ipv6_gateway_static_mode(sw1)

    config_loopback_ipv6_default_gateway_static_mode(sw1)

    unconfig_ipv6_default_gateway_static_mode(sw1)

    config_invalid_primary_ipv6_dns_static_mode(sw1)

    config_multicast_ipv6_primary_dns_static_mode(sw1)

    config_link_local_ipv6_primary_dns_static_mode(sw1)

    config_loopback_primary_ipv6_dns_static_mode(sw1)

    config_invalid_ipv6_secondary_dns_static_mode(sw1)

    config_multicast_ipv6_secondary_dns_static_mode(sw1)

    config_link_local_ipv6_secondary_dns_static_mode(sw1)

    config_loopback_ipv6_secondary_dns_static_mode(sw1)

    config_same_ipv6_primary_secondary_dns_static_mode(sw1)

    config_primary_ipv6_dns_static_mode(sw1)

    reconfig_primary_ipv6_dns_static_mode(sw1)

    remove_primary_ipv6_dns_static_mode(sw1)

    config_secondary_ipv6_dns_static_mode(sw1)

    reconfig_secondary_ipv6_dns_static_mode(sw1)

    unconfig_secondary_ipv6_dns_static_mode(sw1)

    change_mode_from_static_to_dhcp_ipv6(sw1)

    ipv6_got_after_populated_ipv6_config(sw1)

    ipv6_default_gateway_got_after_populated_ipv6_config(sw1)

    step("\n########## Test to remove static IPv4 on management "
         "interface ##########\n")
    remove_ipv4_on_mgmt_intf_static_mode(sw1)

    remove_ipv4_on_mgmt_intf_with_ipv6(sw1)

    remove_ipv4_on_mgmt_intf_with_def_gw(sw1)

    remove_ipv4_on_mgmt_intf_with_nameserver(sw1)

    remove_ipv4_on_mgmt_intf_with_nameserver_ipv6(sw1)

    step("\n########## Test to remove static IPv6 on management "
         "interface ##########\n")
    remove_ipv6_on_mgmt_intf_static_mode(sw1)

    remove_ipv6_on_mgmt_intf_with_ipv4(sw1)

    remove_ipv6_on_mgmt_intf_with_def_gw(sw1)

    remove_ipv6_on_mgmt_intf_with_nameserver(sw1)

    remove_ipv6_on_mgmt_intf_with_nameserver_ipv4(sw1)

    step("\n########## Test to configure System Hostname "
         " ##########\n")
    config_set_hostname_from_cli(sw1)

    config_no_hostname_from_cli(sw1)

    default_system_hostname(sw1)

    set_hostname_by_dhclient(sw1)

    remove_dhcp_hostname_by_dhclient(sw1)

    step("\n########## Test to configure System Domainname "
         " ##########\n")
    config_set_domainname_from_cli(sw1)

    config_no_domainname_from_cli(sw1)

    set_domainname_by_dhclient(sw1)

    remove_dhcp_domainname_by_dhclient(sw1)

    mgmt_intf_cleanup(sw1)

    enable = False

    if os.path.exists('mgmt_sys_var') is True:
        num = file_read_for_mgmt_instance_count()
        if num == 0:
            enable = True
        else:
            num = num - 1
            file_write_for_mgmt_instance_count(num)

    # Enabling dhclient.profile on VM.
    if enable is True:
        enable_dhclient_profile()
        os.system('rm mgmt_sys_var')
