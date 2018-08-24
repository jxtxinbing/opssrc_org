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
import os
import sys
import time
import re
from mininet.net import *
from mininet.topo import *
from mininet.node import *
from mininet.link import *
from mininet.cli import *
from mininet.log import *
from mininet.util import *
from subprocess import *
from opsvsi.docker import *
from opsvsi.opsvsitest import *
import select
import pytest


class mgmtIntfTests(OpsVsiTest):
    # This class member is used for retaining
    # IPv4 and it's subnet mask which is obtained from DHCP server.
    Dhcp_Ipv4_submask = ''

    # DHCP dhclient is currently not running on VSI image due to
    # dhclient_apparmor_profile [/etc/apparmor.d/sbin.dhclient] file,
    # which is present on running host machine[VM].
    # The Profile files will declare access rules to allow access to
    # linux system resources. Implicitly the access is denied
    # when there is no matching rule in the profile.
    # If we want to run docker instance with dhclient on such a
    # host machine, we have to disable the dhclient_apparmor_profile file
    # and enable it once testcase execution is finished.

    def disable_dhclient_profile(self):
        if os.path.isfile("/etc/apparmor.d/sbin.dhclient") is True:
            os.system("sudo ln -s /etc/apparmor.d/sbin.dhclient "
                      "  /etc/apparmor.d/disable/")
            os.system('sudo apparmor_parser -R /etc/apparmor.d/sbin.dhclient')

    def enable_dhclient_profile(self):
        if os.path.isfile("/etc/apparmor.d/sbin.dhclient") is True:
            os.system('sudo rm /etc/apparmor.d/disable/sbin.dhclient')
            os.system('sudo apparmor_parser -r /etc/apparmor.d/sbin.dhclient')

    # When we run this test file with multiple instance,there is a chance of
    # asynchronously enabling and disabling dhclient_profile file on the
    # running system.
    # To avoid asynchronous issue, the count variable is used to maintain
    # the number of mgmt-intf test file execution instance in a temp file.
    # whenever the count reaches zero, the profile file is enabled again.
    def file_read_for_mgmt_instance_count(self):
        file_fd = open('mgmt_sys_var', 'r')
        count = file_fd.read()
        count = re.search('\d+', count)
        num = int(count.group(0))
        file_fd.close()
        return num

    def file_write_for_mgmt_instance_count(self, count_number):
        file_fd = open('mgmt_sys_var', 'w+')
        file_fd.write(str(count_number))
        file_fd.close()

    def setupNet(self):
        if os.path.exists('mgmt_sys_var') is False:
            self.file_write_for_mgmt_instance_count(0)
        else:
            count = self.file_read_for_mgmt_instance_count()
            num = count + 1
            self.file_write_for_mgmt_instance_count(num)

        self.disable_dhclient_profile()

        # If you override this function, make sure to
        # either pass getNodeOpts() into hopts/sopts of the topology that
        # you build or into addHost/addSwitch calls.
        mgmt_topo = SingleSwitchTopo(k=0,
                                     hopts=self.getHostOpts(),
                                     sopts=self.getSwitchOpts())
        self.net = Mininet(topo=mgmt_topo,
                           switch=VsiOpenSwitch,
                           host=Host,
                           link=OpsVsiLink, controller=None,
                           build=True)

    # Static IP configuration check
    def static_ip_config_check(self, conf_ip):
        s1 = self.net.switches[0]
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            if conf_ip in output:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("ip addr show dev eth0")
                    output += s1.cmd("echo")
                    if conf_ip in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
            else:
                sleep(1)
                cnt -= 1
        assert conf_ip in output,\
            'Test to add static IP address in static mode failed'

    # Static IP unconfiguration check
    def static_ip_unconfigure_check(self, conf_ip):
        s1 = self.net.switches[0]
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            if conf_ip not in output:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("ip addr show dev eth0")
                    output += s1.cmd("echo")
                    if conf_ip not in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
            else:
                sleep(1)
                cnt -= 1
        assert conf_ip not in output,\
            'Test to Remove static IP address in static mode failed'

    # Default IPv4 configuration check
    def default_ipv4_configure_check(self, def_ip):
        s1 = self.net.switches[0]
        output = s1.cmdCLI(" ")
        output_show = ''
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output += s1.cmdCLI(" ")
            temp = re.findall("Default gateway IPv4\s+: "+def_ip, output_show)
            if temp:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("ip route show")
                    output += s1.cmd("echo")
                    if def_ip in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
            else:
                sleep(1)
                cnt -= 1
        assert "Default gateway IPv4\t\t: "+def_ip in output_show,\
               'Test to add default ipv4 gateway failed in show interface'
        assert def_ip in output,\
            "Test to add Default gateway in ip route failed"

    # DHCP client started on management interface.
    def dhclient_started_on_mgmt_intf_ipv4(self):
        s1 = self.net.switches[0]
        cnt = 15
        while cnt:
            output = s1.cmd("systemctl status dhclient@eth0.service")
            if output in 'running':
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'running' in output, "Test to verify dhcp client has"\
            " started failed"
        info('### Successfully verified dhcp client has started ###\n')

    # Mgmt Interface updated during bootup.
    def mgmt_intf_updated_during_bootup(self):
        s1 = self.net.switches[0]
        output = s1.ovscmd("ovs-vsctl list system")
        output += s1.cmd("echo")
        assert 'name=eth0' in output, "Test to mgmt interface has "\
            " updated from image.manifest file failed"
        info("### Successfully verified mgmt interface"
             " has updated from image.manifest file ###\n")

    # Enter the management interface context.
    def mgmt_intf_context_enter(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("configure terminal")
        assert 'Unknown command' not in output, "Test"\
            " to enter the management interface context failed"
        output = s1.cmdCLI("interface mgmt")
        assert 'Unknown command' not in output, "Test"\
            " to enter the management interface context failed"
        info("### Successfully verified enter into"
             " the management interface context ###\n")

    # Set mode as DHCP.
    def dhcp_mode_set_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip dhcp")
        output = s1.cmdCLI(" ")
        cnt = 15
        tmp = []
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmdCLI(" ")
            tmp = re.findall("IPv4 address/subnet-mask\s+: \d+.\d+.\d+."
                             "\d+/.\d+", output)
            if tmp:
                break
            else:
                sleep(1)
                cnt -= 1
        self.Dhcp_Ipv4_submask = re.findall("\d+.\d+.\d+.\d+/.\d+",
                                            tmp[0])[0].split("/")
        assert 'dhcp' in output, 'Test to set mode as DHCP failed'
        output = s1.cmd("systemctl status dhclient@eth0.service")
        assert 'running' in output, 'Test to set mode as DHCP failed'
        info('### Successfully configured DHCP mode ###\n')

    # Add Default gateway in DHCP mode.
    def config_default_gateway_ipv4_dhcp_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway 172.17.0.1")
        assert 'Configurations not allowed in dhcp mode'\
            in output, 'Test to add default gateway in DHCP mode failed'
        output = s1.cmdCLI(" ")
        output = s1.cmdCLI("do show interface mgmt")
        temp = re.findall("Default gateway IPv4\s+: .*\n", output)
        assert temp[0] in output, "Test to add default"\
            " gateway in DHCP mode failed"
        info("### Successfully verified configuration"
             " of Default gateway in DHCP mode ###\n")

    # Add DNS Server 1 in DHCP mode.
    def config_primary_ipv4_dns_dhcp_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 10.10.10.1")
        assert 'Configurations not allowed in dhcp mode'\
            in output, 'Test to add Primary DNS in DHCP mode failed'
        output = s1.cmdCLI(" ")
        output = s1.cmd("echo")
        output = s1.cmdCLI("do show interface mgmt")
        assert '10.10.10.1' not in output,\
               'Test to add Primary DNS in DHCP mode failed'
        info("### Successfully verified configuration"
             " of Primary DNS in DHCP mode ###\n")

    # Add DNS Server 2 in DHCP mode.
    def config_secondary_ipv4_dns_dhcp_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 10.10.10.1 10.10.10.2")
        assert 'Configurations not allowed in dhcp mode' in output,\
               'Test to add Secondary DNS in DHCP mode failed'
        output = s1.cmdCLI(" ")
        output = s1.cmd("echo")
        output = s1.cmdCLI("do show interface mgmt")
        output += s1.cmd("echo")
        assert '10.10.10.2' not in output,\
            'Test to add Secondary DNS in DHCP mode failed'
        info("### Successfully verified configuration"
             " of Secondary DNS in DHCP mode ###\n")

    # Add DNS Server 2 through dhclient in DHCP mode.
    def config_secondary_ipv4_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None 10.10.10.2 10.10.10.4 None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
            temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
            if temp and temp2:
                break
            else:
                sleep(1)
                cnt -= 1
        assert '10.10.10.2' in output and \
               '10.10.10.4' in output,\
               'Test to add IPV4 secondary DNS by dhclient failed'
        info("### Successfully configured IPV4 secondary DNS by "
             "dhclient in dhcp mode ###\n")

    # Add DNS Server 1 through dhclient in DHCP mode.
    def config_primary_ipv4_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None 10.10.10.5 None None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 10.10.10.5", output)
            if temp:
                break
            else:
                sleep(1)
                cnt -= 1
        assert '10.10.10.5' in output,\
               'Test to add IPV4 primary DNS by dhclient failed'
        info("### Successfully configured IPV4 primary DNS by "
             "dhclient in dhcp mode ###\n")

    # Modify DNS Server 1 & 2 through dhclient in DHCP mode.
    def reconfig_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None 10.10.10.2 10.10.10.4 None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
            temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
            if temp and temp2:
                break
            else:
                sleep(1)
                cnt -= 1
        assert '10.10.10.2' in output and \
               '10.10.10.4' in output,\
               'Test to reconfigure IPV4 DNS1 and DNS2 by dhclient failed'
        info("### Successfully reconfigured IPV4 primary and secondary DNS by "
             "dhclient in dhcp mode ###\n")

    # Remove primary and secondary DNS through dhclient in DHCP mode.
    def remove_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None None None None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
            temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
            if temp and temp2:
                sleep(1)
                cnt -= 1
            else:
                break
        assert '10.10.10.2' not in output and \
               '10.10.10.4' not in output,\
               'Test to remove IPV4 DNS1 and DNS2 by dhclient failed'
        info("### Successfully removed IPV4 primary and secondary DNS by "
             "dhclient in dhcp mode ###\n")

    # Add DNS Server 2 through dhclient in DHCP mode.
    def config_secondary_ipv4_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None 10.10.10.2 10.10.10.4 None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 10.10.10.2", output)
            temp2 = re.findall("Secondary Nameserver\s+: 10.10.10.4", output)
            if temp and temp2:
                break
            else:
                sleep(1)
                cnt -= 1
        assert '10.10.10.2' in output and \
               '10.10.10.4' in output,\
               'Test to add Secondary DNS by dhclient is failed'
        info("### Successfully configured Secondary DNS by "
             "dhclient in dhcp mode ###\n")

    # Static IP config when mode is static.
    def config_ipv4_on_mgmt_intf_static_mode(self):
        s1 = self.net.switches[0]
        IPV4_static = re.sub('\d+$', '128', self.Dhcp_Ipv4_submask[0])
        conf_ipv4 = IPV4_static+"/"+self.Dhcp_Ipv4_submask[1]
        s1.cmdCLI("ip static "+conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        info("### Successfully configured static"
             " IP address in static mode ###\n")

    # Reconfigure Sattic IP when mode is static.
    def reconfig_ipv4_on_mgmt_intf_static_mode(self):
        s1 = self.net.switches[0]
        IPV4_static = re.sub('\d+$', '129', self.Dhcp_Ipv4_submask[0])
        conf_ipv4 = IPV4_static+"/"+self.Dhcp_Ipv4_submask[1]
        s1.cmdCLI("ip static "+conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        info("### Successfully Reconfigured static"
             " IP address in static mode ###\n")

    # Add Default gateway in Static mode.
    def config_ipv4_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        IPV4_default = re.sub('\d+$', '130', self.Dhcp_Ipv4_submask[0])
        s1.cmdCLI("default-gateway "+IPV4_default)
        self.default_ipv4_configure_check(IPV4_default)
        info("### Successfully configured Default gateway"
             " in static mode ###\n")

    # Remove Default gateway in static mode.
    def unconfig_ipv4_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        IPV4_default = re.sub('\d+$', '130', self.Dhcp_Ipv4_submask[0])
        s1.cmdCLI("no default-gateway "+IPV4_default)
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmdCLI(" ")
            temp = re.findall("Default gateway IPv4\s+: "+IPV4_default, output)
            if temp:
                sleep(1)
                cnt -= 1
            else:
                break
        assert "Default gateway IPv4\t\t: \n"in output,\
               'Test to remove default gateway failed in show interface'
        cnt2 = 15
        while cnt2:
            output = s1.cmd("ip route show")
            output += s1.cmd("echo")
            if IPV4_default not in output:
                break
            else:
                cnt2 -= 1
                sleep(1)
        assert IPV4_default not in output,\
            'Test to remove default gateway failed in ip route'
        info('### Successfully Removed Default gateway in static mode ###\n')

    # Add IPv6 Default gateway in static mode when IPV4 configured.
    def config_ipv6_default_gateway_ipv4_is_set_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway 2001:db8:0:1::128")
        assert 'IP should be configured first' in output, \
               "Test to Add IPV6 default gateway when IPV4 "\
               "configured in static mode failed"
        info("### Successfully verified configuration of IPV6 "
             "default gateway when IPV4 is configured in static mode ###\n")

    # Add DNS Server 1 in static mode.
    def config_primary_ipv4_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 10.10.10.5")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 10.10.10.5", output)
            if temp:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
                    if 'nameserver 10.10.10.5' in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
            else:
                sleep(1)
                cnt -= 1
        assert 'nameserver 10.10.10.5' in output,\
               'Test to add Primary DNS failed'
        info('### Successfully configured Primary DNS in static mode ###\n')

    # Add another primary DNS server.
    def reconfig_primary_ipv4_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 10.10.10.20")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 10.10.10.20", output)
            if temp:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert 'nameserver 10.10.10.20' in output,\
               'Test to Reconfigure Primary DNS failed'
        assert 'nameserver 10.10.10.1' not in output,\
               'Test to Reconfigure Primary DNS failed'
        info('### Successfully Reconfigured Primary DNS in static mode ###\n')

    # Remove primary dns in static mode.
    def remove_primary_ipv4_dns_static_mode(self):
        sleep(15)
        s1 = self.net.switches[0]
        s1.cmdCLI("no nameserver 10.10.10.20")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            if 'Primary Nameserver\s+: 10.10.10.20' not in output:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
                    if 'nameserver 10.10.10.20' not in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
            else:
                sleep(1)
                cnt -= 1
        assert 'nameserver 10.10.10.20' not in output,\
               'Test to Remove Primary DNS failed'
        info('### Successfully Removed Primary DNS in static mode ###\n')

    # Configure Secondary DNS Server in static mode.
    def config_secondary_ipv4_dns_static_mode(self):
        sleep(15)
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 10.10.10.4 10.10.10.5")
        sleep(2)
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
               re.findall("Secondary Nameserver\s+: 10.10.10.5", output):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert 'nameserver 10.10.10.5' in output,\
               'Test to add Secondary DNS failed'
        assert 'nameserver 10.10.10.4' in output,\
               'Test to add Secondary DNS failed'
        info('### Successfully Configured Secondary DNS in static mode ###\n')

    # Reconfigure Secondary DNS Server in static mode.
    def reconfig_secondary_ipv4_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 10.10.10.4 10.10.10.20")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
               re.findall("Secondary Nameserver\s+: 10.10.10.20", output):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert 'nameserver 10.10.10.4' in output,\
               'Test to Reconfigure Secondary DNS failed'
        assert 'nameserver 10.10.10.5' not in output,\
               'Test to Reconfigure Secondary DNS failed'
        assert 'nameserver 10.10.10.20' in output,\
               'Test to Reconfigure Secondary DNS failed'
        info("### Successfully Reconfigured Secondary"
             " DNS in static mode ###\n")

    # Remove Secondary DNS ipv4 in static mode.
    def unconfig_secondary_ipv4_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("no nameserver  10.10.10.4 10.10.10.20")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
               re.findall("Secondary Nameserver\s+: 10.10.10.20", output):
                sleep(1)
                cnt -= 1
            else:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
                    if 'nameserver 10.10.10.20' not in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
        assert 'nameserver 10.10.10.20' not in output,\
               'Test to Remove Secondary DNS failed'
        info('### Successfully Removed Secondary DNS in static mode ###\n')

    # Set Invalid IP on mgmt-intf.
    def config_invalid_ipv4_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static 0.0.0.0/24")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to configure invalid static IP address failed'
        info("### Successfully verified configure"
             " of Invalid IP in static mode ###\n")

    # Set Multicast IP on mgmt-intf.
    def config_multicast_ipv4_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static 224.0.0.1/16")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to configure multicast IP address failed'
        info("### Successfully verified configure"
             " of multicast IP in static mode ###\n")

    # Set broadcast IP on mgmt-intf.
    def config_broadcast_ipv4_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static 192.168.0.255/24")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to configure broadcast IP address failed'
        info("### Successfully verified configure of"
             " broadcast IP in static mode ###\n")

    # Set loopback IP on mgmt-intf.
    def config_loopback_ipv4_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static 127.0.0.1/24")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to configure loopback IP address failed'
        info("### Successfully verified configure of"
             " loopback IP in static mode ###\n")

    # Add Default Invalid gateway IP in static mode
    def config_invalid_default_gateway_ipv4_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway 0.0.0.0")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add Invalid default gateway failed'
        info("### Successfully Verified configure of Invalid"
             " default gateway IP in static mode ###\n")

    # Add multicast ip as default gateway in static mode.
    def config_multicast_ipv4_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway 224.0.0.1")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add multicast default gateway failed'
        info("### Successfully Verified configure of multicast"
             " default gateway IP in static mode ###\n")

    # Add broadcast ip as default gateway ip in static mode.
    def config_broadcast_ipv4_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway 192.168.0.255")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add broadcast default gateway ip failed'
        info("### Successfully Verified configure of broadcast"
             " default gateway in static mode ###\n")

    # Add loopback address as default gateway ip in static mode
    def config_loopback_ipv4_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway 127.0.0.1")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add loopback default gateway ip failed'
        info("### Successfully Verified configure of "
             "loopback default gateway in static mode ###\n")

    # Configure an invalid IP address as primary DNS.
    def config_invalid_primary_ipv4_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 0.0.0.0")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add invalid Primary DNS failed'
        info("### Successfully Verified configure of invalid"
             " Primary DNS in static mode ###\n")

    # Configure a multicast address as primary DNS.
    def config_multicast_ipv4_primary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 224.0.0.1")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add multicast Primary DNS failed'
        info("### Successfully Verified configure of multicast"
             " Primary DNS in static mode ###\n")

    # Configure a broadcast address as primary DNS.
    def config_broadcast_ipv4_primary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 192.168.0.255")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add broadcast Primary DNS failed'
        info("### Successfully Verified configure of "
             "broadcast Primary DNS in static mode ###\n")

    # Configure a loopback address as primary DNS.
    def config_loopback_primary_ipv4_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 127.0.0.1")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add loopback Primary DNS failed'
        info("### Successfully Verified configure of"
             " loopback Primary DNS in static mode ###\n")

    # Configure an invalid IP as secondary DNS.
    def config_invalid_ipv4_secondary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 10.10.10.1 0.0.0.0")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               "Test to add invalid Secondary DNS failed"
        info("### Successfully Verified configure of"
             " invalid secondary DNS in static mode ###\n")

    # Change mode from static to dhcp.
    def change_mode_from_static_to_dhcp_ipv4(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip dhcp")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            output += s1.cmd("echo")
            if 'dhcp' in output:
                break
            else:
                sleep(1)
                cnt -= 1
        assert 'dhcp' in output,\
               'Test to change mode to DHCP from static failed'
        info('### Successfully changed the mode from static to DHCP ###\n')

    # Test if IP got from DHCP is set.
    def ipv4_got_after_populated_ipv4_config(self):
        s1 = self.net.switches[0]
        time.sleep(5)
        # Populate values as though populated from DHCP.
        s1.cmd("ifconfig eth0 172.17.0.100 netmask 255.255.255.0")
        s1.cmd("route add default gw 172.17.0.1 eth0")
        s1.cmd("echo nameserver 1.1.1.1  > /etc/resolv.conf")
        s1.cmd("echo nameserver 2.2.2.2 >> /etc/resolv.conf")

        out = s1.cmd("ip addr show dev eth0")
        temp = re.findall("inet\s+\d+.\d+.\d+.\d+/\d+", out)
        hostIpAddress = re.findall("\d+.\d+.\d+.\d+/\d+", temp[0])
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            output += s1.cmd("echo")
            if hostIpAddress[0] in output:
                break
            else:
                sleep(1)
                cnt -= 1
        assert hostIpAddress[0] in output, "Test to verify IP got after "\
            "changed the mode from static to dhcp failed"
        info("### Successfully got the IP after changed "
             "the mode from static to dhcp ###\n")

    # Test if Default gateway got from DHCP is set.
    def ipv4_default_gateway_got_after_populated_ipv4_config(self):
        s1 = self.net.switches[0]
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            output += s1.cmd("echo")
            if '172.17.0.1' in output:
                break
            else:
                sleep(1)
                cnt -= 1
        assert '172.17.0.1' in output, "Test to verify Default "\
            "gateway got after changed the mode from static to dhcp failed"
        info("### Successfully got Default gateway IP after changed the "
             "mode from static to dhcp ###\n")

    # Test if DNS server got from DHCP is set.
    def dns_ipv4_got_after_populated_ipv4_config(self):
        s1 = self.net.switches[0]
        output = s1.cmd("cat /etc/resolv.conf")
        temp = re.findall("nameserver\s+.*\nnameserver\s+.*", output)
        assert temp[0] in output,\
            "Test to verify DNS IP got after changed the mode"\
            " from static to dhcp failed"
        info("### Successfully got DNS IP after changed the "
             " mode from static to dhcp ###\n")

    # Add Default gateway IPV6 in DHCP mode.
    def config_default_gateway_ipv6_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("end")
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("interface mgmt")
        s1.cmdCLI("ip dhcp")
        sleep(30)
        s1.cmdCLI("default-gateway 2001:db8:0:1::128")
        output = s1.cmdCLI(" ")
        output = s1.cmdCLI("do show interface mgmt")
        assert '2001:db8:0:1::128' not in output,\
               "Test to add default gateway in DHCP mode failed"
        info("### Successfully verified "
             "configure of default gateway in DHCP mode ###\n")

    # Add IPV6 DNS Server 1 in DHCP mode.
    def config_primary_ipv6_dns_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 2001:db8:0:1::128")
        output = s1.cmdCLI(" ")
        output = s1.cmd("echo")
        output = s1.cmdCLI("do show interface mgmt")
        assert '2001:db8:0:1::128' not in output,\
               'Test to add Primary DNS in DHCP mode failed'
        info("### Successfully verified configure of "
             "Primary DNS in DHCP mode ###\n")

    # Add IPV6 DNS Server 2 in DHCP mode.
    def config_secondary_ipv6_dns_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 2001:db8:0:1::106 2001:db8:0:1::128")
        output = s1.cmdCLI(" ")
        output = s1.cmd("echo")
        output = s1.cmdCLI("do show interface mgmt")
        output += s1.cmd("echo")
        assert '2001:db8:0:1::128' not in output,\
               'Test to add Secondary in DHCP mode failed'
        info("### Successfully verified configure of "
             "Secondary DNS in DHCP mode ###\n")

    # config IPv6 DNS Server 2 through dhclient in DHCP mode.
    def config_secondary_ipv6_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None 2001:470:35:270::1  2001:470:35:270::2 None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
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
               '2001:470:35:270::2' in output,\
               'Test to add IPv6 secondary DNS by dhclient failed'
        info("### Successfully configured IPV6 secondary DNS by "
             "dhclient in dhcp mode ###\n")

    # Config IPv6 DNS Server 1 through dhclient in DHCP mode.
    def config_primary_ipv6_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None 2001:470:35:270::1 None None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            temp = re.findall("Primary Nameserver\s+: 2001:470:35:270::1",
                              output)
            if temp:
                break
            else:
                sleep(1)
                cnt -= 1
        assert '2001:470:35:270::1' in output,\
               'Test to add IPv6 Primary DNS by dhclient failed'
        info("### Successfully configured IPV6  Primary DNS by "
             "dhclient in dhcp mode ###\n")

    # reconfig IPv6 DNS Server 2 & 1 through dhclient in DHCP mode.
    def reconfig_ipv6_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None 2001:470:35:270::5  2001:470:35:270::6 None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
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
               '2001:470:35:270::6' in output,\
               'Test to reconfigure IPv6 DNS1 and DNS2  by dhclient failed'
        info("### Successfully reconfigured IPV6 DNS by "
             "dhclient in dhcp mode ###\n")

    # Remove IPV6 primary and secondary DNS through dhclient in DHCP mode.
    def remove_primary_secondary_ipv6_dns_by_dhclient_dhcp_mode(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None None None None")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
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
               '2001:470:35:270::6' not in output,\
               'Test to remove IPV6 DNS1 and DNS2  by dhclient failed'
        info("### Successfully removed IPV6 Primary and secondary DNS by "
             "dhclient in dhcp mode ###\n")

    # Static IPV6 config when mode is static.
    def config_ipv6_on_mgmt_intf_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip static 2001:db8:0:1::156/64")
        self.static_ip_config_check("2001:db8:0:1::156/64")
        info('### Successfully verified configure of Static IP ###\n')

    # Set the IPV6 again.
    def reconfig_ipv6_on_mgmt_intf_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip static 2001:db8:0:1::157/64")
        self.static_ip_config_check("2001:db8:0:1::157/64")
        info('### Successfully verified Reconfigure of Static IP ###\n')

    # Set Invalid IPV6 on mgmt-intf.
    def config_invalid_ipv6_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static ::")
        assert 'Unknown command' in output,\
               'Test to configure invalid static IP address failed'
        info("### Successfully verified configure of "
             "invalid static IP address ###\n")

    # Test to verify Multicast IPV6 on mgmt-intf.
    def config_multicast_ipv6_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static ff01:db8:0:1::101/64")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to configure multicast IP address in static mode failed'
        info("### Successfully verified configure of "
             "multicast IP address in static mode ###\n")

    # Test to verify link-local IPV6 on mgmt-intf.
    def config_link_local_ipv6_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static fe80::5484:7aff:fefe:9799/64")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to configure link-local IP address in static mode failed'
        info("### Successfully verified configure of "
             "link-local IP in static mode ###\n")

    # Test to verify loopback IPV6 on mgmt-intf
    def config_loopback_ipv6_on_mgmt_intf(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("ip static ::1")
        assert 'Unknown command' in output,\
               'Test to configure loopback IP address in static mode failed'
        info("### Successfully verified configure of loopback"
             " IP address in static mode ###\n")

    # Default gateway should be reachable. Otherwise test case will fail.
    # Add Default gateway in Static mode.
    def config_ipv6_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("default-gateway 2001:db8:0:1::128")
        output = s1.cmdCLI(" ")
        output = s1.cmdCLI("do show running-config")
        assert 'default-gateway 2001:db8:0:1::128' in output,\
               'Test to add default gateway in static mode failed'
        info("### Successfully verified configure of default"
             " gateway in static mode ###\n")

    # Add IPV4 Default gateway in static mode when IPV6 configured.
    def config_ipv4_default_gateway_ipv6_is_set_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway 192.168.1.2")
        assert 'IP should be configured first' in output, \
               "Test to Add IPV4 default gateway when IPV6"\
               " configured in static mode failed"
        info("### Successfully verified configuration of IPV4"
             " default gateway when IPV6 is configured in static mode ###\n")

    # Add Default Invalid gateway IPV6 in static mode.
    def config_invalid_default_gateway_ipv6_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway ::")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add Invalid default gateway ip in static mode failed'
        info("### Successfully verified configure of Invalid "
             "default gateway ip in static mode ###\n")

    # Add Deafult  multicast gateway ipv6 in static mode.
    def config_multicast_ipv6_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway ff01:db8:0:1::101")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add default multicast gateway ip in static mode failed'
        info("### Successfully verified configure of multicast"
             " gateway ip in static mode ###\n")

    # Add Default link-local  gateway ipv6 in static mode.
    def config_default_link_local_ipv6_gateway_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway fe80::5484:7aff:fefe:9799")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               "Test to add default link-local "\
               "gateway ip in static mode failed"
        info("### Successfully verified configure of Default"
             " link-local  gateway ip in static mode ###\n")

    # Add Default loopback gateway ipv6 in static mode.
    def config_loopback_ipv6_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("default-gateway ::1")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to add default loopback gateway ip in static mode failed'
        info("### Successfully verified configure of Default"
             " loopback gateway in static mode ###\n")

    # Remove Default gateway in static mode.
    def unconfig_ipv6_default_gateway_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("no default-gateway 2001:db8:0:1::128")
        output = s1.cmdCLI(" ")
        output = s1.cmdCLI("do show running-config")
        assert 'default-gateway 2001:db8:0:1::128' not in output,\
               'Test to remove default gateway in static mode failed'
        info('### Successfully Removed Default gateway in static mode ###\n')

    # Configure an invalid IPV6 for primary DNS.
    def config_invalid_primary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver ::")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to configure invalid Primary DNS failed'
        info("### Successfully verified configure of invalid"
             " Primary DNS static mode ###\n")

    # Configure an multicast for primary DNS.
    def config_multicast_ipv6_primary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver ff01:db8:0:1::101")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to Configure an multicast for primary DNS failed'
        info("### Successfully verified configure of "
             "multicast primary DNS in static mode ###\n")

    # Configure a link-local for primary DNS.
    def config_link_local_ipv6_primary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver fe80::5484:7aff:fefe:9799")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to Configure a link-local for primary DNS failed'
        info("### Successfully verified configure of "
             "link-local primary DNS in static mode ###\n")

    # Configure a loopback for primary DNS.
    def config_loopback_primary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver ::1")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               "Test to Configure a loopback for primary DNS failed"
        info("### Successfully verified configure of loopback"
             " primary DNS in static mode ###\n")

    # Configure an invalid IP for secondary DNS.
    def config_invalid_ipv6_secondary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 2001:db8:0:1::144 ::")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to Configure an invalid IP for secondary DNS failed'
        info("### Successfully verified configure of "
             "invalid secondary DNS in static mode ###\n")

    # Configure an multicast for secondary DNS.
    def config_multicast_ipv6_secondary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 2001:db8:0:1::144 ff01:db8:0:1::101")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to Configure an multicast for secondary DNS failed'
        info("### Successfully verified configure of multicast"
             " secondary DNS in static mode ###\n")

    # Configure a link-local for secondary DNS.
    def config_link_local_ipv6_secondary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 2001:db8:0:1::144 "
                           "fe80::5484:7aff:fefe:9799")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to Configure a link-local for secondary DNS failed'
        info("### Successfully verified configure of "
             "link-local secondary DNS in static mode ###\n")

    # Configure a loopback for secondary DNS.
    def config_loopback_ipv6_secondary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 2001:db8:0:1::144 ::1")
        assert 'Invalid IPv4 or IPv6 address' in output,\
               'Test to Configure a loopback for secondary DNS failed'
        info("### Successfully verified configure of loopback "
             "secondary DNS in static mode ###\n")

    # Configure primary and secondary DNS as same.
    def config_same_ipv6_primary_secondary_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 2001:db8:0:1::144 2001:db8:0:1::144")
        assert 'Duplicate value entered' in output,\
               'Test to Configure primary and secondary DNS as same failed'
        info("### Successfully verified configure of same primary "
             "and secondary DNS in static mode ###\n")

    # Add DNS Server 1 in static mode.
    def config_primary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 2001:db8:0:1::144")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 2001:db8:0:1::144",
                          output_show):
                cnt2 = 100
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
                    if 'nameserver 2001:db8:0:1::144' in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
            else:
                sleep(1)
                cnt -= 1
        assert 'nameserver 2001:db8:0:1::144' in output,\
            'Test to add Primary DNS in static mode failed'
        info("### Successfully configured the "
             "Primary DNS in static mode ###\n")

    # Add another DNS server 1.
    def reconfig_primary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 2001:db8:0:1::154")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 2001:db8:0:1::154",
                          output_show):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert 'nameserver 2001:db8:0:1::154' in output,\
            'Test to Reconfigure Primary DNS in static mode failed'
        assert 'nameserver 2001:db8:0:1::144' not in output,\
            'Test to Reconfigure Primary DNS in static mode failed'
        info("### Successfully Reconfigured the Primary "
             "DNS in static mode ###\n")

    # Remove DNS server 1.
    def remove_primary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("no nameserver 2001:db8:0:1::154")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall('Primary Nameserver\s+: 2001:db8:0:1::154',
                          output_show):
                sleep(1)
                cnt -= 1
            else:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
                    if 'nameserver 2001:db8:0:1::154' not in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
        assert 'nameserver 2001:db8:0:1::154' not in output,\
            'Test to Remove Primary DNS in static mode failed'
        info('### Successfully Removed Primary DNS in static mode ###\n')

    # Add DNS Server 2 in static mode.
    def config_secondary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        output = s1.cmdCLI("nameserver 2001:db8:0:1::150 2001:db8:0:1::156")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
               output_show) and re.findall("Secondary Nameserver\s+: 2001:"
                                           "db8:0:1::156", output_show):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert 'nameserver 2001:db8:0:1::156' in output,\
            'Test to add Secondary DNS in static mode failed'
        assert 'nameserver 2001:db8:0:1::150' in output,\
            'Test to add Secondary DNS in static mode failed'
        info('### Successfully Configured Secondary DNS in static mode ###\n')

    # Add another DNS server 2.
    def reconfig_secondary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("nameserver 2001:db8:0:1::150 2001:db8:0:1::154")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output = s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
                          output_show) and \
               re.findall("Secondary Nameserver\s+: 2001:db8:0:1::154",
                          output_show):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert 'nameserver 2001:db8:0:1::150' in output,\
            'Test to Reconfigure Secondary DNS in static mode failed'
        assert 'nameserver 2001:db8:0:1::156' not in output,\
            'Test to Reconfigure Secondary DNS in static mode failed'
        assert 'nameserver 2001:db8:0:1::154' in output,\
            'Test to Reconfigure Secondary DNS in static mode failed'
        info("### Successfully Reconfigured Secondary DNS "
             "in static mode ###\n")

    # Remove DNS server 2.
    def unconfig_secondary_ipv6_dns_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("no nameserver  2001:db8:0:1::150 2001:db8:0:1::154")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
                          output_show) and \
               re.findall("Secondary Nameserver\s+: 2001:db8:0:1::154",
                          output_show):
                sleep(1)
                cnt -= 1
            else:
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
                    if 'nameserver 2001:db8:0:1::154' not in output:
                        break
                    else:
                        cnt2 -= 1
                        sleep(1)
                break
        assert 'nameserver 2001:db8:0:1::154' not in output,\
            'Test to Remove Secondary DNS in static mode failed'
        info('### Successfully Removed Secondary DNS in static mode ###\n')

    # Change mode from static to dhcp.
    def change_mode_from_static_to_dhcp_ipv6(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip dhcp")
        output = s1.cmdCLI(" ")
        time.sleep(15)
        output = ''
        output = s1.cmdCLI("do show interface mgmt")
        output += s1.cmdCLI(" ")
        assert 'dhcp' in output,\
            'Test to change mode from static to dhcp failed'
        output = s1.ovscmd("ovs-vsctl list system")
        output += s1.cmd("echo")
        assert 'ipv6_linklocal' in output,\
            'Test to change mode from static to dhcp failed'
        assert 'dns-server-1' not in output,\
            'Test to change mode from static to dhcp failed'
        assert 'dns-server-2' not in output,\
            'Test to change mode from static to dhcp failed'
        info('### Successfully changed mode to DHCP from static ###\n')

    # Test if IPV6  got from DHCP is set.
    def ipv6_got_after_populated_ipv6_config(self):
        s1 = self.net.switches[0]
        time.sleep(5)
        s1.cmd("ip -6 addr add 2001:db8:0:1::150/64 dev eth0")
        s1.cmd("ip -6 route add default via 2001:db8:0:1::128")
        s1.cmd("echo nameserver 1.1.1.1  > /etc/resolv.conf")
        s1.cmd("echo nameserver 2.2.2.2 >> /etc/resolv.conf")

        output = s1.cmd("ip -6 addr show dev eth0")
        output = s1.cmd("cat /etc/resolv.conf")

        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmdCLI(" ")
            if re.findall("IPv6 address/prefix\s+: 2001:db8:0:1::150/64",
                          output):
                break
            else:
                sleep(1)
                cnt -= 1
        assert "IPv6 address/prefix\t\t: 2001:db8:0:1::150/64" in output,\
            "Test to verify IP got after changed the mode"\
            " from static to dhcp failed"
        info("### Successfully got IP after changed the"
             " mode from static to dhcp ###\n")

    # Test if Default gateway got from DHCP is set.
    def ipv6_default_gateway_got_after_populated_ipv6_config(self):
        s1 = self.net.switches[0]
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmdCLI(" ")
            if "Default gateway IPv6\t\t: 2001:db8:0:1::128" not in output:
                sleep(1)
                cnt -= 1
            else:
                break
        assert "Default gateway IPv6\t\t: 2001:db8:0:1::128" in output,\
            'Test to verify Default gateway got after changed the mode failed'
        info("### Successfully got the Default gateway after "
             "changed the mode Passed ###\n")

    # Tests to verify 'no ip static .. ' to remove static Ips

    # Verify to remove static IPv4 . Mode should be changed to 'dhcp'
    def remove_ipv4_on_mgmt_intf_static_mode(self):
        s1 = self.net.switches[0]
        IPV4_static = re.sub('\d+$', '128', self.Dhcp_Ipv4_submask[0])
        s1.cmdCLI("ip dhcp")
        s1.cmdCLI(" ")
        sleep(15)
        conf_ipv4 = IPV4_static+"/"+self.Dhcp_Ipv4_submask[1]
        output = s1.cmdCLI("ip static "+conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        s1.cmdCLI("no ip static "+conf_ipv4)
        self.static_ip_unconfigure_check(conf_ipv4)
        show_output = s1.cmdCLI("do show interface mgmt")
        assert 'dhcp' in show_output,\
            "DHCP mode change failed.Test to remove static "\
            "IP address in static mode failed"
        info('### Successfully removed IP address in static mode ###\n')

    # Verify to remove static IPv4 with static Ipv6. Mode should not changed
    def remove_ipv4_on_mgmt_intf_with_ipv6(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip static 2001:db8:0:1::156/64")
        self.static_ip_config_check("2001:db8:0:1::156/64")
        IPV4_static = re.sub('\d+$', '128', self.Dhcp_Ipv4_submask[0])
        conf_ipv4 = IPV4_static+"/" + self.Dhcp_Ipv4_submask[1]
        s1.cmdCLI("ip static "+conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        cmd_output = s1.cmdCLI("no ip static " + conf_ipv4)
        self.static_ip_unconfigure_check(conf_ipv4)
        show_output = s1.cmdCLI("do show interface mgmt")
        assert 'static' in show_output,\
            'Wrong mode.Test to remove IP address in static mode failed'
        info("### Successfully removed IP address"
             " with static IPv6 address  ###\n")

    # Verify to remove static IPv4 with default gw. Should not be removed
    def remove_ipv4_on_mgmt_intf_with_def_gw(self):
        s1 = self.net.switches[0]
        IPV4_static = re.sub('\d+$', '128', self.Dhcp_Ipv4_submask[0])
        IPV4_default = re.sub('\d+$', '130', self.Dhcp_Ipv4_submask[0])
        conf_ipv4 = IPV4_static+"/" + self.Dhcp_Ipv4_submask[1]
        s1.cmdCLI("ip static " + conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        s1.cmdCLI("default-gateway "+IPV4_default)
        self.default_ipv4_configure_check(IPV4_default)
        cmd_output = s1.cmdCLI("no ip static " + conf_ipv4)
        assert "Remove all IPv4 related info (Default gateway/DNS address)"
        " before removing the IP address from this interface" in cmd_output,\
            "Test to remove static IP address with default gateway "\
            "in static mode failed"
        info("### Successfully verified to remove IP address with "
             "default gateway in static mode ###\n")

    # Verify to remove static IPv4 with name server. Should not be removed
    def remove_ipv4_on_mgmt_intf_with_nameserver(self):
        s1 = self.net.switches[0]
        IPV4_static = re.sub('\d+$', '128', self.Dhcp_Ipv4_submask[0])
        conf_ipv4 = IPV4_static+"/" + self.Dhcp_Ipv4_submask[1]
        s1.cmdCLI("ip static " + conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        s1.cmdCLI("nameserver 10.10.10.4 10.10.10.20")
        output = s1.cmdCLI(" ")
        cnt = 15
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            output += s1.cmd("echo")
            if re.findall("Primary Nameserver\s+: 10.10.10.4", output) and \
               re.findall("Secondary Nameserver\s+: 10.10.10.20", output):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert '10.10.10.4' in output,\
               'Test to Reconfigure Secondary DNS failed'
        assert '10.10.10.5' not in output,\
               'Test to Reconfigure Secondary DNS failed'
        assert '10.10.10.20' in output,\
               'Test to Reconfigure Secondary DNS failed'
        cmd_output = s1.cmdCLI("no ip static " + conf_ipv4)
        assert "Remove all IPv4 related info (Default gateway/DNS address)"
        " before removing the IP address from this interface" in cmd_output,\
            "Test to remove static IP address with name"\
            " server in static mode failed"
        info("### Successfully verified to remove IP address with"
             " name server in static mode ###\n")

    # verify to remove static Ipv4 with mixed name server should not be removed
    def remove_ipv4_on_mgmt_intf_with_nameserver_ipv6(self):
        s1 = self.net.switches[0]
        IPV4_static = re.sub('\d+$', '128', self.Dhcp_Ipv4_submask[0])
        conf_ipv4 = IPV4_static+"/" + self.Dhcp_Ipv4_submask[1]
        s1.cmdCLI("ip static " + conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        s1.cmdCLI("nameserver 2001:db8:0:1::128 10.10.10.30")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 2001:db8:0:1::128",
               output_show) and re.findall("Secondary Nameserver\s+: "
                                           "10.10.10.30", output_show):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert '2001:db8:0:1::128' in output,\
            'Test to add Secondary DNS in static mode failed'
        assert '10.10.10.30' in output,\
            'Test to add Secondary DNS in static mode failed'

        cmd_output = s1.cmdCLI("no ip static " + conf_ipv4)
        assert "Remove all IPv4 related info (Default gateway/DNS address)"
        " before removing the IP address from this interface" in cmd_output,\
            "Test to remove static IP address with mixed name server"\
            " in static mode failed"
        info("### Successfully verified to remove IP address with IPv6"
             " name server in static mode ###\n")

    # Verify to remove static IPv6. Mode should be changed to DHCP
    def remove_ipv6_on_mgmt_intf_static_mode(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip dhcp")
        s1.cmdCLI(" ")
        sleep(15)
        s1.cmdCLI("ip static 2001:db8:0:1::156/64")
        self.static_ip_config_check("2001:db8:0:1::156/64")
        cmd_output = s1.cmdCLI("no ip static 2001:db8:0:1::156/64")
        self.static_ip_unconfigure_check("2001:db8:0:1::156/64")
        show_output = s1.cmdCLI("do show interface mgmt")
        assert 'dhcp' in show_output,\
               "DHCP mode change failed.Test to remove "\
               "static IPv6 address in static mode failed"
        info('### Successfully removed Static IPv6 ###\n')

    # Verify to remove static Ipv6 with static Ipv4. Mode should not be changed
    def remove_ipv6_on_mgmt_intf_with_ipv4(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip static 2001:db8:0:1::156/64")
        self.static_ip_config_check("2001:db8:0:1::156/64")
        IPV4_static = re.sub('\d+$', '128', self.Dhcp_Ipv4_submask[0])
        conf_ipv4 = IPV4_static+"/"+self.Dhcp_Ipv4_submask[1]
        s1.cmdCLI("ip static "+conf_ipv4)
        self.static_ip_config_check(conf_ipv4)
        cmd_output = s1.cmdCLI("no ip static 2001:db8:0:1::156/64")
        self.static_ip_unconfigure_check("2001:db8:0:1::156/64")
        show_output = s1.cmdCLI("do show interface mgmt")
        assert 'static' in show_output,\
               'Wrong mode.Test to remove static IPv6 address with IPv4 failed'
        info('### Successfully removed Static IPv6 with Ipv4 ###\n')

    # Verify to remove Ipv6 with default gw. Should not be allowed
    def remove_ipv6_on_mgmt_intf_with_def_gw(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip static 2001:db8:0:1::156/64")
        self.static_ip_config_check("2001:db8:0:1::156/64")
        s1.cmdCLI("default-gateway 2001:db8:0:1::128")
        output = s1.cmdCLI(" ")
        cnt = 30
        while cnt:
            output = s1.cmdCLI("do show interface mgmt")
            output += s1.cmd("echo")
            output += s1.cmd("echo")
            if '2001:db8:0:1::128' in output:
                break
            else:
                sleep(1)
                cnt -= 1
        assert '2001:db8:0:1::128' in output,\
            "Test to add Default gateway in static mode failed"
        cmd_output = s1.cmdCLI("no ip static 2001:db8:0:1::156/64")
        cmd_output += s1.cmdCLI(" ")
        assert "Remove all IPv6 related info (Default gateway/DNS address)"
        " before removing the IP address from this interface." in cmd_output,\
            'Test to remove static IPv6 address with default gw failed'
        info("### Successfully verified to remove"
             " Static IPv6 with default gw ###\n")

    # Verify to remove IPv6 with name server. Should not be allowed
    def remove_ipv6_on_mgmt_intf_with_nameserver(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip static 2001:db8:0:1::156/64")
        self.static_ip_config_check("2001:db8:0:1::156/64")
        output = s1.cmdCLI(" ")
        output = s1.cmdCLI("nameserver 2001:db8:0:1::150 2001:db8:0:1::156")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 2001:db8:0:1::150",
               output_show) and re.findall("Secondary Nameserver\s+: 2001:"
                                           "db8:0:1::156", output_show):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert '2001:db8:0:1::156' in output,\
            'Test to add Secondary DNS in static mode failed'
        assert '2001:db8:0:1::150' in output,\
            'Test to add Secondary DNS in static mode failed'
        cmd_output = s1.cmdCLI("no ip static 2001:db8:0:1::156/64")
        cmd_output += s1.cmdCLI(" ")
        assert "Remove all IPv6 related info (Default gateway/DNS address)"
        " before removing the IP address from this interface." in cmd_output,\
            'Test to remove static IPv6 address with name server failed'
        info("### Successfully verified to remove "
             "Static IPv6 with name server ###\n")

    # Verify to remove IPv6 with mixed name server. Should not be allowed
    def remove_ipv6_on_mgmt_intf_with_nameserver_ipv4(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("ip static 2001:db8:0:1::156/64")
        self.static_ip_config_check("2001:db8:0:1::156/64")
        s1.cmdCLI("nameserver 10.10.10.20 2001:db8:0:1::130")
        cnt = 15
        while cnt:
            output_show = s1.cmdCLI("do show interface mgmt")
            output_show += s1.cmdCLI(" ")
            if re.findall("Primary Nameserver\s+: 10.10.10.20",
               output_show) and re.findall("Secondary Nameserver\s+: 2001:"
                                           "db8:0:1::130", output_show):
                cnt2 = 15
                while cnt2:
                    output = s1.cmd("cat /etc/resolv.conf")
                    output += s1.cmd("echo")
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
        assert '10.10.10.20' in output,\
            'Test to add Secondary DNS in static mode failed'
        assert '2001:db8:0:1::130' in output,\
            'Test to add Secondary DNS in static mode failed'

        cmd_output = s1.cmdCLI("no ip static 2001:db8:0:1::156/64")
        assert "Remove all IPv6 related info (Default gateway/DNS address)"
        " before removing the IP address from this interface." in cmd_output,\
            "Test to remove static IPv6 address"\
            " with name server IPv4 failed"
        info("### Successfully verified to remove "
             "Static IPv6 with IPv4 name server ###\n")

    # Verify to configure system hostname through CLI
    def config_set_hostname_from_cli(self):
        s1 = self.net.switches[0]
        sleep(15)
        s1.cmdCLI("end")
        s1.cmdCLI("config terminal")
        sleep(15)
        s1.cmdCLI("hostname cli")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            hostname = s1.ovscmd("ovs-vsctl get system . "
                                 "hostname").rstrip('\r\n')
            output = s1.cmd("uname -n")
            if "hostname=cli" in cmd_output and \
               hostname == "cli" and \
               "cli" in output:
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'hostname=cli' in cmd_output and \
               hostname == 'cli' and \
               'cli' in output,\
               "Test to set hostname through CLI"\
               " has failed"
        info("### Successfully verified configuring"
             " hostname using CLI ###\n")

    # Verify to unconfigure system hostname through CLI
    def config_no_hostname_from_cli(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("config terminal")
        s1.cmdCLI("no hostname")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            hostname = s1.ovscmd("ovs-vsctl get system . "
                                 "hostname").rstrip('\r\n')
            output = s1.cmd("uname -n")
            if "hostname=switch" in cmd_output and \
               hostname == "" and \
               "switch" in output:
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'hostname=switch' in cmd_output and \
               hostname == '' and \
               'switch' in output,\
               "Test to unset hostname through CLI"\
               " has failed"
        info("### Successfully verified reconfiguring"
             " hostname to default value using CLI ###\n")

    # Verify to check system hostname defaults to switch
    def default_system_hostname(self):
        s1 = self.net.switches[0]
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            hostname = s1.ovscmd("ovs-vsctl get system . "
                                 "hostname").rstrip('\r\n')
            output = s1.cmd("uname -n")
            if "hostname=switch" in cmd_output and \
               hostname == "" and \
               "switch" in output:
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'hostname=switch' in cmd_output and \
               hostname == '' and \
               'switch' in output,\
               "Test to set default value of hostname has failed"
        info("### Successfully verified setting"
             " hostname to default value ###\n")

    # Verify to set hostname through dhclient
    def set_hostname_by_dhclient(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("interface mgmt")
        s1.cmdCLI("ip dhcp")
        #giving time for dhcp client to come up
        sleep(2)
        s1.cmd("dhcp_options dhcp-new None None None")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            hostname = s1.ovscmd("ovs-vsctl get system . "
                                 "hostname").rstrip('\r\n')
            output = s1.cmd("uname -n")
            if "dhcp_hostname=dhcp-new" in cmd_output and \
               "hostname=dhcp-new" in cmd_output and \
               hostname == "" and \
               "dhcp-new" in output:
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'dhcp_hostname=dhcp-new' in cmd_output and \
               'hostname=dhcp-new' in cmd_output and \
               hostname == '' and \
               'dhcp-new' in output,\
            "Test to set system hostname through dhclient"\
            " has failed"
        info("### Successfully verified to set system hostname"
             " by dhclient ###\n")

    # Verify to remove hostname through dhclient
    def remove_dhcp_hostname_by_dhclient(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None None None None")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            hostname = s1.ovscmd("ovs-vsctl get system . "
                                 "hostname").rstrip('\r\n')
            output = s1.cmd("uname -n")
            if "dhcp_hostname=" not in cmd_output and \
               "hostname=switch" in cmd_output and \
               hostname == "" and \
               "switch" in output:
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'dhcp_hostname=' not in cmd_output and \
               hostname == '' and \
               'switch' in output, \
            "Test to remove dhcp_hostname through dhclient"\
            " has failed"
        info("### Successfully verified to remove dhcp_hostname"
             " by dhclient ###\n")

    # Verify to configure system domainname through CLI
    def config_set_domainname_from_cli(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("end")
        s1.cmdCLI("config terminal")
        s1.cmdCLI("domain-name cli")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            domainname = s1.ovscmd("ovs-vsctl get system . "
                                   "domain_name").rstrip('\r\n')
            resolve_output = s1.cmd("cat /etc/resolv.conf")
            if "domain_name=cli" in cmd_output and \
               domainname == "cli" and \
               "domain cli" in resolve_output:
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'domain_name=cli' in cmd_output and \
               domainname == 'cli' and \
               "domain cli" in resolve_output,\
               "Test to set domainname through CLI"\
               " has failed"
        info("### Successfully verified configuring"
             " domainname using CLI ###\n")

    # Verify to unconfigure system domainname through CLI
    def config_no_domainname_from_cli(self):
        s1 = self.net.switches[0]
        s1.cmdCLI("config terminal")
        s1.cmdCLI("domain-name cli")
        s1.cmdCLI("no domain-name")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            domainname = s1.ovscmd("ovs-vsctl get system . "
                                   "domain_name").rstrip('\r\n')
            resolve_output = s1.cmd("cat /etc/resolv.conf")
            if domainname == '' and \
               "domain cli" not in resolve_output:
                break
            else:
                cnt -= 1
                sleep(1)
        assert "domain cli" not in resolve_output and \
               domainname == '',\
               "Test to unset domainname through CLI has failed"
        info("### Successfully verified reconfiguring"
             " domainame to default value using CLI ###\n")

    # Verify to set domainname through dhclient
    def set_domainname_by_dhclient(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None None None new_dom")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            domainname = s1.ovscmd("ovs-vsctl get system . "
                                   "domain_name").rstrip('\r\n')
            if "dhcp_hostname=new_dom" in cmd_output and \
               "domain_name=new_dom" in cmd_output and \
               domainname == '':
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'dhcp_domain_name=new_dom' in cmd_output and \
               'domain_name=new_dom' in cmd_output and \
               domainname == '',\
               "Test to set system domainname through dhclient"\
               " has failed"
        info("### Successfully verified to set system domain name"
             " by dhclient ###\n")

    # Verify to remove domainname through dhclient
    def remove_dhcp_domainname_by_dhclient(self):
        s1 = self.net.switches[0]
        s1.cmd("dhcp_options None None None None")
        cnt = 15
        while cnt:
            cmd_output = s1.ovscmd("ovs-vsctl list system")
            domainname = s1.ovscmd("ovs-vsctl get system . "
                                   "domain_name").rstrip('\r\n')
            if "dhcp_domain_name" not in cmd_output and \
               domainname == '':
                break
            else:
                cnt -= 1
                sleep(1)
        assert 'dhcp_domain_name' not in cmd_output and \
               domainname == '',\
               "Test to remove dhcp_domain_name through dhclient"\
               " has failed"
        info("### Successfully verified to remove dhcp_domain_name"
             " by dhclient ###\n")

    # Extra cleanup if test fails in middle.
    def mgmt_intf_cleanup(self):
        s1 = self.net.switches[0]
        output = s1.cmd("ip netns exec swns ip addr show dev 1")
        if 'inet' in output:
            s1.cmd("ip netns exec swns ip address flush dev 1")

@pytest.mark.skipif(True, reason="Disabling old tests")
class Test_mgmt_intf:

    def setup_class(cls):
        # Create the Mininet topology based on mininet.
        Test_mgmt_intf.test = mgmtIntfTests()

    def teardown_class(cls):
        # Stop the Docker containers, and
        # mininet topology.
        Test_mgmt_intf.test.net.stop()
        Enable = False

        if os.path.exists('mgmt_sys_var') is True:
            num = Test_mgmt_intf.test.file_read_for_mgmt_instance_count()
            if num == 0:
                Enable = True
            else:
                num = num - 1
                Test_mgmt_intf.test.file_write_for_mgmt_instance_count(num)

        # Enabling dhclient.profile on VM.
        if Enable is True:
            Test_mgmt_intf.test.enable_dhclient_profile()
            os.system('rm mgmt_sys_var')

    def teardown_method(self, method):
        self.test.mgmt_intf_cleanup()

    def __del__(self):
        del self.test

    # mgmt intf tests.
    def test_dhclient_started_on_mgmt_intf_ipv4(self):
        info("\n########## Test to configure Management "
             "interface with DHCP IPV4 ##########\n")
        self.test.dhclient_started_on_mgmt_intf_ipv4()

    def test_mgmt_intf_updated_during_bootup(self):
        self.test.mgmt_intf_updated_during_bootup()

    def test_mgmt_intf_context_enter(self):
        self.test.mgmt_intf_context_enter()

    def test_dhcp_mode_set_on_mgmt_intf(self):
        self.test.dhcp_mode_set_on_mgmt_intf()

    def test_config_default_gateway_ipv4_dhcp_mode(self):
        self.test.config_default_gateway_ipv4_dhcp_mode()

    def test_config_primary_ipv4_dns_dhcp_mode(self):
        self.test.config_primary_ipv4_dns_dhcp_mode()

    def test_config_secondary_ipv4_dns_dhcp_mode(self):
        self.test.config_secondary_ipv4_dns_dhcp_mode()

    def test_config_secondary_ipv4_dns_by_dhclient_dhcp_mode(self):
        self.test.config_secondary_ipv4_dns_by_dhclient_dhcp_mode()

    def test_config_primary_ipv4_dns_by_dhclient_dhcp_mode(self):
        self.test.config_primary_ipv4_dns_by_dhclient_dhcp_mode()

    def test_reconfig_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(self):
        self.test.reconfig_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode()

    def test_remove_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode(self):
        self.test.remove_primary_secondary_ipv4_dns_by_dhclient_dhcp_mode()

    def test_config_ipv4_on_mgmt_intf_static_mode(self):
        info("\n########## Test to configure Management "
             "interface with static IPV4 ##########\n")
        self.test.config_ipv4_on_mgmt_intf_static_mode()

    def test_reconfig_ipv4_on_mgmt_intf_static_mode(self):
        self.test.reconfig_ipv4_on_mgmt_intf_static_mode()

    def test_config_ipv4_default_gateway_static_mode(self):
        self.test.config_ipv4_default_gateway_static_mode()

    def test_unconfig_ipv4_default_gateway_static_mode(self):
        self.test.unconfig_ipv4_default_gateway_static_mode()

    def test_config_ipv6_default_gateway_ipv4_is_set_static_mode(self):
        self.test.config_ipv6_default_gateway_ipv4_is_set_static_mode()

    def test_config_primary_ipv4_dns_static_mode(self):
        self.test.config_primary_ipv4_dns_static_mode()

    def test_reconfig_primary_ipv4_dns_static_mode(self):
        self.test.reconfig_primary_ipv4_dns_static_mode()

    def test_remove_primary_ipv4_dns_static_mode(self):
        self.test.remove_primary_ipv4_dns_static_mode()

    def test_config_secondary_ipv4_dns_static_mode(self):
        self.test.config_secondary_ipv4_dns_static_mode()

    def test_reconfig_secondary_ipv4_dns_static_mode(self):
        self.test.reconfig_secondary_ipv4_dns_static_mode()

    def test_unconfig_secondary_ipv4_dns_static_mode(self):
        self.test.unconfig_secondary_ipv4_dns_static_mode()

    def test_config_invalid_ipv4_on_mgmt_intf(self):
        self.test.config_invalid_ipv4_on_mgmt_intf()

    def test_config_multicast_ipv4_on_mgmt_intf(self):
        self.test.config_multicast_ipv4_on_mgmt_intf()

    def test_config_broadcast_ipv4_on_mgmt_intf(self):
        self.test.config_broadcast_ipv4_on_mgmt_intf()

    def test_config_loopback_ipv4_on_mgmt_intf(self):
        self.test.config_loopback_ipv4_on_mgmt_intf()

    def test_config_invalid_default_gateway_ipv4_static_mode(self):
        self.test.config_invalid_default_gateway_ipv4_static_mode()

    def test_config_multicast_ipv4_default_gateway_static_mode(self):
        self.test.config_multicast_ipv4_default_gateway_static_mode()

    def test_config_broadcast_ipv4_default_gateway_static_mode(self):
        self.test.config_broadcast_ipv4_default_gateway_static_mode()

    def test_config_loopback_ipv4_default_gateway_static_mode(self):
        self.test.config_loopback_ipv4_default_gateway_static_mode()

    def test_config_invalid_primary_ipv4_dns_static_mode(self):
        self.test.config_invalid_primary_ipv4_dns_static_mode()

    def test_config_multicast_ipv4_primary_dns_static_mode(self):
        self.test.config_multicast_ipv4_primary_dns_static_mode()

    def test_config_broadcast_ipv4_primary_dns_static_mode(self):
        self.test.config_broadcast_ipv4_primary_dns_static_mode()

    def test_config_loopback_primary_ipv4_dns_static_mode(self):
        self.test.config_loopback_primary_ipv4_dns_static_mode()

    def test_config_invalid_ipv4_secondary_dns_static_mode(self):
        self.test.config_invalid_ipv4_secondary_dns_static_mode()

    def test_change_mode_from_static_to_dhcp_ipv4(self):
        self.test.change_mode_from_static_to_dhcp_ipv4()

    def test_ipv4_got_after_populated_ipv4_config(self):
        self.test.ipv4_got_after_populated_ipv4_config()

    def test_ipv4_default_gateway_got_after_populated_ipv4_config(self):
        self.test.ipv4_default_gateway_got_after_populated_ipv4_config()

    @pytest.mark.skipif(True, reason="Disabling this testcase "
                        "due to DHCP server dependencies")
    def test_dns_ipv4_got_after_populated_ipv4_config(self):
        self.test.dns_ipv4_got_after_populated_ipv4_config()

    def test_config_default_gateway_ipv6_dhcp_mode(self):
        info("\n########## Test to configure Management "
             "interface with Dhcp IPV6 ##########\n")
        self.test.config_default_gateway_ipv6_dhcp_mode()

    def test_config_primary_ipv6_dns_dhcp_mode(self):
        self.test.config_primary_ipv6_dns_dhcp_mode()

    def test_config_secondary_ipv6_dns_dhcp_mode(self):
        self.test.config_secondary_ipv6_dns_dhcp_mode()

    def test_config_secondary_ipv6_dns_by_dhclient_dhcp_mode(self):
        self.test.config_secondary_ipv6_dns_by_dhclient_dhcp_mode()

    def test_config_primary_ipv6_dns_by_dhclient_dhcp_mode(self):
        self.test.config_primary_ipv6_dns_by_dhclient_dhcp_mode()

    def test_reconfig_ipv6_dns_by_dhclient_dhcp_mode(self):
        self.test.reconfig_ipv6_dns_by_dhclient_dhcp_mode()

    def test_remove_primary_secondary_ipv6_dns_by_dhclient_dhcp_mode(self):
        self.test.remove_primary_secondary_ipv6_dns_by_dhclient_dhcp_mode()

    def test_config_ipv6_on_mgmt_intf_static_mode(self):
        info("\n########## Test to configure Management "
             "interface with static IPV6 ##########\n")
        self.test.config_ipv6_on_mgmt_intf_static_mode()

    def test_reconfig_ipv6_on_mgmt_intf_static_mode(self):
        self.test.reconfig_ipv6_on_mgmt_intf_static_mode()

    def test_config_invalid_ipv6_on_mgmt_intf(self):
        self.test.config_invalid_ipv6_on_mgmt_intf()

    def test_config_multicast_ipv6_on_mgmt_intf(self):
        self.test.config_multicast_ipv6_on_mgmt_intf()

    def test_config_link_local_ipv6_on_mgmt_intf(self):
        self.test.config_link_local_ipv6_on_mgmt_intf()

    def test_config_loopback_ipv6_on_mgmt_intf(self):
        self.test.config_loopback_ipv6_on_mgmt_intf()

    def test_config_ipv6_default_gateway_static_mode(self):
        self.test.config_ipv6_default_gateway_static_mode()

    def test_config_ipv4_default_gateway_ipv6_is_set_static_mode(self):
        self.test.config_ipv4_default_gateway_ipv6_is_set_static_mode()

    def test_config_invalid_default_gateway_ipv6_static_mode(self):
        self.test.config_invalid_default_gateway_ipv6_static_mode()

    def test_config_multicast_ipv6_default_gateway_static_mode(self):
        self.test.config_multicast_ipv6_default_gateway_static_mode()

    def test_config_default_link_local_ipv6_gateway_static_mode(self):
        self.test.config_default_link_local_ipv6_gateway_static_mode()

    def test_config_loopback_ipv6_default_gateway_static_mode(self):
        self.test.config_loopback_ipv6_default_gateway_static_mode()

    def test_unconfig_ipv6_default_gateway_static_mode(self):
        self.test.unconfig_ipv6_default_gateway_static_mode()

    def test_config_invalid_primary_ipv6_dns_static_mode(self):
        self.test.config_invalid_primary_ipv6_dns_static_mode()

    def test_config_multicast_ipv6_primary_dns_static_mode(self):
        self.test.config_multicast_ipv6_primary_dns_static_mode()

    def test_config_link_local_ipv6_primary_dns_static_mode(self):
        self.test.config_link_local_ipv6_primary_dns_static_mode()

    def test_config_loopback_primary_ipv6_dns_static_mode(self):
        self.test.config_loopback_primary_ipv6_dns_static_mode()

    def test_config_invalid_ipv6_secondary_dns_static_mode(self):
        self.test.config_invalid_ipv6_secondary_dns_static_mode()

    def test_config_multicast_ipv6_secondary_dns_static_mode(self):
        self.test.config_multicast_ipv6_secondary_dns_static_mode()

    def test_config_link_local_ipv6_secondary_dns_static_mode(self):
        self.test.config_link_local_ipv6_secondary_dns_static_mode()

    def test_config_loopback_ipv6_secondary_dns_static_mode(self):
        self.test.config_loopback_ipv6_secondary_dns_static_mode()

    def test_config_same_ipv6_primary_secondary_dns_static_mode(self):
        self.test.config_same_ipv6_primary_secondary_dns_static_mode()

    def test_config_primary_ipv6_dns_static_mode(self):
        self.test.config_primary_ipv6_dns_static_mode()

    def test_reconfig_primary_ipv6_dns_static_mode(self):
        self.test.reconfig_primary_ipv6_dns_static_mode()

    def test_remove_primary_ipv6_dns_static_mode(self):
        self.test.remove_primary_ipv6_dns_static_mode()

    def test_config_secondary_ipv6_dns_static_mode(self):
        self.test.config_secondary_ipv6_dns_static_mode()

    def test_reconfig_secondary_ipv6_dns_static_mode(self):
        self.test.reconfig_secondary_ipv6_dns_static_mode()

    def test_unconfig_secondary_ipv6_dns_static_mode(self):
        self.test.unconfig_secondary_ipv6_dns_static_mode()

    def test_change_mode_from_static_to_dhcp_ipv6(self):
        self.test.change_mode_from_static_to_dhcp_ipv6()

    def test_ipv6_got_after_populated_ipv6_config(self):
        self.test.ipv6_got_after_populated_ipv6_config()

    def test_ipv6_default_gateway_got_after_populated_ipv6_config(self):
        self.test.ipv6_default_gateway_got_after_populated_ipv6_config()

    def test_remove_ipv4_on_mgmt_intf_static_mode(self):
        info("\n########## Test to remove static IPv4 on management "
             "interface ##########\n")
        self.test.remove_ipv4_on_mgmt_intf_static_mode()

    def test_remove_ipv4_on_mgmt_intf_with_ipv6(self):
        self.test.remove_ipv4_on_mgmt_intf_with_ipv6()

    def test_remove_ipv4_on_mgmt_intf_with_def_gw(self):
        self.test.remove_ipv4_on_mgmt_intf_with_def_gw()

    def test_remove_ipv4_on_mgmt_intf_with_nameserver(self):
        self.test.remove_ipv4_on_mgmt_intf_with_nameserver()

    def test_remove_ipv4_on_mgmt_intf_with_nameserver_ipv6(self):
        self.test.remove_ipv4_on_mgmt_intf_with_nameserver_ipv6()

    def test_remove_ipv6_on_mgmt_intf_static_mode(self):
        info("\n########## Test to remove static IPv6 on management "
             "interface ##########\n")
        self.test.remove_ipv6_on_mgmt_intf_static_mode()

    def test_remove_ipv6_on_mgmt_intf_with_ipv4(self):
        self.test.remove_ipv6_on_mgmt_intf_with_ipv4()

    def test_remove_ipv6_on_mgmt_intf_with_def_gw(self):
        self.test.remove_ipv6_on_mgmt_intf_with_def_gw()

    def test_remove_ipv6_on_mgmt_intf_with_nameserver(self):
        self.test.remove_ipv6_on_mgmt_intf_with_nameserver()

    def test_remove_ipv6_on_mgmt_intf_with_nameserver_ipv4(self):
        self.test.remove_ipv6_on_mgmt_intf_with_nameserver_ipv4()

    def test_config_set_hostname_from_cli(self):
        info("\n########## Test to configure System Hostname "
             " ##########\n")
        self.test.config_set_hostname_from_cli()

    def test_config_no_hostname_from_cli(self):
        self.test.config_no_hostname_from_cli()

    def test_default_system_hostname(self):
        self.test.default_system_hostname()

    def test_set_hostname_by_dhclient(self):
        self.test.set_hostname_by_dhclient()

    def test_remove_dhcp_hostname_by_dhclient(self):
        self.test.remove_dhcp_hostname_by_dhclient()

    def test_config_set_domainname_from_cli(self):
        info("\n########## Test to configure System Domainname "
             " ##########\n")
        self.test.config_set_domainname_from_cli()

    def test_config_no_domainname_from_cli(self):
        self.test.config_no_domainname_from_cli()

    def test_set_domainname_by_dhclient(self):
        self.test.set_domainname_by_dhclient()

    def test_remove_dhcp_domainname_by_dhclient(self):
        self.test.remove_dhcp_domainname_by_dhclient()
