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
from pytest import raises
from topology_lib_vtysh.exceptions import UnknownVtyshException
from pytest import mark

TOPOLOGY = """
#               +-------+
# +-------+     |       |
# |  sw1  <----->  hs1  |
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


def num_to_dotted_quad(n):
    d = 256 * 256 * 256
    q = []
    # FIXME
    # while d > 0:
    m, n = divmod(n, d)
    q.append(str(m))
    d = d/256
    return d
    # return '.'.join(q)


# DHCP client started on management interface.
def dhclient_started_on_mgmt_intf_ipv4(sw1, step):
    cnt = 15
    output_tmp = ''
    output = ''
    while cnt:
        output = sw1("systemctl status dhclient@eth0.service -l", shell="bash")
        output_tmp = sw1("ifconfig eth0", shell="bash")
        output_log = sw1("cat /var/log/messages | grep \"dhclient\" ",
                         shell="bash")
        if output in 'running':
            break
        else:
            cnt -= 1
            sleep(1)

    step("DHCLIENT status debug info : %s\n" % (output))
    step("Mgmt port status debug info : %s\n" % (output_tmp))
    step("SYSLOG output : %s\n" % (output_log))
    assert 'running' in output, "Test to verify dhcp client has started failed"
    step('### Successfully verified dhcp client has started ###\n')


# Mgmt Interface updated during bootup.
def mgmt_intf_updated_during_bootup(sw1, step):
    output = sw1("ovs-vsctl list system", shell="bash")
    output += sw1("echo", shell="bash")
    assert 'name="eth0"' in output, "Test to mgmt interface has "\
        " updated from image.manifest file failed"
    step("### Successfully verified mgmt interface"
         " has updated from image.manifest file ###\n")


# Set mode as DHCP.
def dhcp_mode_set_on_mgmt_intf(sw1, step):
    global dhcp_ipv4_submask

    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.ip_dhcp()
    cnt = 15
    tmp = []
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        tmp = output["ipv4"]

        if tmp:
            break
        else:
            sleep(1)
            cnt -= 1

    dhcp_ipv4_submask = re.findall("\d+.\d+.\d+.\d+/.\d+",
                                   tmp)[0].split("/")

    assert output["address_mode"] == 'dhcp', 'Test to set mode as DHCP failed'
    output = sw1("systemctl status dhclient@eth0.service", shell="bash")
    assert 'running' in output, 'Test to set mode as DHCP failed'
    step('### Successfully configured DHCP mode ###\n')


# Static IP config when mode is static.
def config_ipv4_on_mgmt_intf_static_mode(sw1, step):
    ipv4_static = re.sub('\d+$', '128', dhcp_ipv4_submask[0])
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.ip_static("%s/%s" % (ipv4_static, dhcp_ipv4_submask[1]))
    cnt = 30
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        if output["ipv4"] == "%s/%s" % \
           (ipv4_static, dhcp_ipv4_submask[1]):
            cnt2 = 15
            while cnt2:
                output = sw1("ifconfig", shell="bash")
                output += sw1("echo", shell="bash")
                if ipv4_static in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert ipv4_static in output, \
        'Test to add static IP address in static mode failed'
    subnet = (1 << 32) - (1 << 32 >> int(dhcp_ipv4_submask[1]))
    step("SUBNET " + str(subnet))
    assert "%s" % str(int(num_to_dotted_quad(subnet))) in output, \
        'Test to add static IP address in static mode failed'
    step("### Successfully configured static IP address in static mode ###\n")


# Add Default gateway in Static mode.
def config_ipv4_default_gateway_static_mode(sw1, step):
    ipv4_default = re.sub('\d+$', '130', dhcp_ipv4_submask[0])
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.default_gateway(ipv4_default)
    cnt = 15
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        if output["default_gateway_ipv4"] == ipv4_default:
            cnt2 = 15
            while cnt2:
                output = sw1("ip route show", shell="bash")
                output += sw1("echo", shell="bash")
                if ipv4_default in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert ipv4_default in output, \
        "Test to add Default gateway in static mode failed"
    step("### Successfully configured Default gateway"
         " in static mode ###\n")


# Remove Default gateway in static mode.
def unconfig_ipv4_default_gateway_static_mode(sw1, step):
    ipv4_default = re.sub('\d+$', '130', dhcp_ipv4_submask[0])
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.no_default_gateway(ipv4_default)
    output = sw1.libs.vtysh.show_interface_mgmt()
    temp = output["default_gateway_ipv4"]
    assert temp is None, 'Test to remove default gateway failed'
    cnt2 = 15
    while cnt2:
        output = sw1("ip route show", shell="bash")
        output += sw1("echo", shell="bash")
        if ipv4_default not in output:
            break
        else:
            cnt2 -= 1
            sleep(1)
    assert ipv4_default not in output, \
        'Test to remove default gateway failed'
    step('### Successfully Removed Default gateway in static mode ###\n')


# Configure Secondary DNS Server in static mode.
def config_secondary_ipv4_dns_static_mode(sw1, step):
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.nameserver("10.10.10.4", "10.10.10.5")
    cnt = 15
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        if output["primary_nameserver"] is not None and \
           output["secondary_nameserver"] is not None:
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
    assert '10.10.10.5' in output, 'Test to add Secondary DNS failed'
    assert '10.10.10.4' in output, 'Test to add Secondary DNS failed'
    step('### Successfully Configured Secondary DNS in static mode ###\n')


# Remove Secondary DNS ipv4 in static mode.
def unconfig_secondary_ipv4_dns_static_mode(sw1, step):
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.no_nameserver("10.10.10.4", "10.10.10.5")
    cnt = 15
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        if '10.10.10.20' not in output:
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
    assert '10.10.10.20' not in output, \
        'Test to Remove Secondary DNS failed'
    step('### Successfully Removed Secondary DNS in static mode ###\n')


# Add Default gateway IPV6 in DHCP mode.
def config_default_gateway_ipv6_dhcp_mode(sw1, step):
    with raises(UnknownVtyshException):
        with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
            ctx.ip_dhcp()
            ctx.default_gateway("2001:db8:0:1::128")

    output = sw1.libs.vtysh.show_interface_mgmt()
    assert '2001:db8:0:1::128' not in output, \
        "Test to add default gateway in DHCP mode failed"
    step("### Successfully verified "
         "configure of default gateway in DHCP mode ###\n")


# Static IPV6 config when mode is static.
def config_ipv6_on_mgmt_intf_static_mode(sw1, step):
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.ip_static("2001:db8:0:1::156/64")
    cnt = 15
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        if output["ipv6"] == '2001:db8:0:1::156/64':
            cnt2 = 15
            while cnt2:
                output = sw1("ip -6 addr show dev eth0", shell="bash")
                if '2001:db8:0:1::156/64' in output:
                    break
                else:
                    cnt2 -= 1
                    sleep(1)
            break
        else:
            sleep(1)
            cnt -= 1
    assert '2001:db8:0:1::156/64' in output, \
        'Test to add static IP address failed'
    step('### Successfully verified configure of Static IP ###\n')


# Default gateway should be reachable. Otherwise test case will fail.
# Add Default gateway in Static mode.
def config_ipv6_default_gateway_static_mode(sw1, step):
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.default_gateway("2001:db8:0:1::128")

    # FIXME
    output = sw1("show run")
    # output = sw1.libs.vtysh.show_running_config()
    assert 'default-gateway 2001:db8:0:1::128' in output, \
        'Test to add default gateway in static mode failed'
    step("### Successfully verified configure of default"
         " gateway in static mode ###\n")


# Remove Default gateway in static mode.
def unconfig_ipv6_default_gateway_static_mode(sw1, step):
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.no_default_gateway("2001:db8:0:1::128")

    # FIXME
    # output = sw1.libs.vtysh.show_running_config()
    output = sw1("show run")
    assert 'default-gateway 2001:db8:0:1::128' not in output, \
        'Test to remove default gateway in static mode failed'
    step('### Successfully Removed Default gateway in static mode ###\n')


# Add DNS Server 2 in static mode.
def config_secondary_ipv6_dns_static_mode(sw1, step):
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.nameserver("2001:db8:0:1::150", "2001:db8:0:1::156")

    cnt = 15
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        if output["primary_nameserver"] == "2001:db8:0:1::150" and \
           output["secondary_nameserver"] == "2001:db8:0:1::156":
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
    assert '2001:db8:0:1::156' in output, \
        'Test to add Secondary DNS in static mode failed'
    assert '2001:db8:0:1::150' in output, \
        'Test to add Secondary DNS in static mode failed'
    step('### Successfully Configured Secondary DNS in static mode ###\n')


# Remove DNS server 2.
def unconfig_secondary_ipv6_dns_static_mode(sw1, step):
    with raises(UnknownVtyshException):
        with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
            ctx.no_nameserver("2001:db8:0:1::150", "2001:db8:0:1::154")

    cnt = 15
    while cnt:
        output = sw1.libs.vtysh.show_interface_mgmt()
        if '2001:db8:0:1::154' not in output:
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
        else:
            sleep(1)
            cnt -= 1
    assert '2001:db8:0:1::154' not in output, \
        'Test to Remove Secondary DNS in static mode failed'
    step('### Successfully Removed Secondary DNS in static mode ###\n')


# Change mode from static to dhcp.
def change_mode_from_static_to_dhcp_ipv6(sw1, step):
    with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.ip_dhcp()

    sleep(5)
    output = ''
    output = sw1.libs.vtysh.show_interface_mgmt()
    assert output["address_mode"] == "dhcp", \
        'Test to change mode from static to dhcp failed'
    output = sw1("ovs-vsctl list system", shell="bash")
    output += sw1("echo", shell="bash")
    assert 'ipv6_linklocal' in output, \
        'Test to change mode from static to dhcp failed'
    assert 'dns-server-1' not in output, \
        'Test to change mode from static to dhcp failed'
    assert 'dns-server-2' not in output, \
        'Test to change mode from static to dhcp failed'
    step('### Successfully changed mode to DHCP from static ###\n')


# Verify to configure system hostname through CLI
def config_set_hostname_from_cli(sw1, step):
    # FIXME
    sw1("config terminal")
    sw1("hostname cli")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        hostname = sw1("ovs-vsctl get system . "
                       "hostname", shell="bash").rstrip('\r\n')
        output = sw1("uname -n", shell="bash")
        if "hostname=cli" in cmd_output and \
           hostname == "cli" and \
           "cli" in output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'hostname=cli' in cmd_output and \
           hostname == 'cli' and 'cli' in output, \
        "Test to set hostname through CLI has failed"
    step("### Successfully verified configuring"
         " hostname using CLI ###\n")

    sw1._shells['vtysh']._prompt = (
        '(^|\n)cli(\\([\\-a-zA-Z0-9]*\\))?#'
    )


# Verify to set hostname through dhclient
def set_hostname_by_dhclient(sw1, step):
    sw1._shells['vtysh']._prompt = (
        '(^|\n)cli(\\([\\-a-zA-Z0-9]*\\))?#'
    )
    sw1("end")
    sw1("config terminal")
    sw1("interface mgmt")
    sw1("ip dhcp")
    sleep(2)
    sw1("dhcp_options open-vswitch-new None None None", shell="bash")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        sw1("uname -n", shell="bash")
        if "dhcp_hostname=open-vswitch-new" in cmd_output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'dhcp_hostname=open-vswitch-new' in cmd_output, \
        "Test to set system hostname through dhclient has failed"
    step("### Successfully verified to set system hostname"
         " by dhclient ###\n")

    sw1._shells['vtysh']._prompt = (
        '(^|\n)open-vswitch-new(\\([\\-a-zA-Z0-9]*\\))?#'
    )


# Verify to configure system domainname through CLI
def config_set_domainname_from_cli(sw1, step):

    sw1._shells['vtysh']._prompt = (
        '(^|\n)cli(\\([\\-a-zA-Z0-9]*\\))?#'
    )

    sw1("domain-name cli")
    sw1(" ")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        domainname = sw1("ovs-vsctl get system . "
                         "domain_name", shell="bash").rstrip('\r\n')
        if "domain_name=cli" in cmd_output and \
           domainname == "cli":
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'domain_name=cli' in cmd_output and \
           domainname == 'cli' and 'cli' in cmd_output, \
        "Test to set domainname through CLI has failed"
    step("### Successfully verified configuring"
         " domainname using CLI ###\n")


# Verify to set domainname through dhclient
def set_domainname_by_dhclient(sw1, step):
    sw1("dhcp_options None None None dhcp_domain", shell="bash")
    cnt = 15
    while cnt:
        cmd_output = sw1("ovs-vsctl list system", shell="bash")
        if "dhcp_domain_name=dhcp_domain" in cmd_output:
            break
        else:
            cnt -= 1
            sleep(1)
    assert 'dhcp_domain_name=dhcp_domain' in cmd_output, \
        "Test to set system domainname through dhclient has failed"
    step("### Successfully verified to set system domainname"
         " by dhclient ###\n")


# Extra cleanup if test fails in middle.
def mgmt_intf_cleanup(sw1):
    output = sw1("ip netns exec swns ip addr show dev 1", shell="bash")
    if 'inet' in output:
        sw1("ip netns exec swns ip address flush dev 1", shell="bash")


@mark.gate
def test_mgmt_intf(topology, step):

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

    dhclient_started_on_mgmt_intf_ipv4(sw1, step)

    mgmt_intf_updated_during_bootup(sw1, step)

    dhcp_mode_set_on_mgmt_intf(sw1, step)

    step("\n########## Test to configure Management "
         "interface with static IPV4 ##########\n")
    config_ipv4_on_mgmt_intf_static_mode(sw1, step)

    config_ipv4_default_gateway_static_mode(sw1, step)

    unconfig_ipv4_default_gateway_static_mode(sw1, step)

    config_secondary_ipv4_dns_static_mode(sw1, step)

    unconfig_secondary_ipv4_dns_static_mode(sw1, step)

    step("\n########## Test to configure Management "
         "interface with Dhcp IPV6 ##########\n")
    config_default_gateway_ipv6_dhcp_mode(sw1, step)

    change_mode_from_static_to_dhcp_ipv6(sw1, step)

    step("\n########## Test to configure Management "
         "interface with static IPV6 ##########\n")
    config_ipv6_on_mgmt_intf_static_mode(sw1, step)

    config_ipv6_default_gateway_static_mode(sw1, step)

    unconfig_ipv6_default_gateway_static_mode(sw1, step)

    config_secondary_ipv6_dns_static_mode(sw1, step)

    unconfig_secondary_ipv6_dns_static_mode(sw1, step)

    step("\n########## Test to configure System Hostname "
         " ##########\n")
    config_set_hostname_from_cli(sw1, step)

    set_hostname_by_dhclient(sw1, step)

    step("\n########## Test to configure System Domainname "
         " ##########\n")
    config_set_domainname_from_cli(sw1, step)

    set_domainname_by_dhclient(sw1, step)

    mgmt_intf_cleanup(sw1)

    # Stop the Docker containers, and
    # mininet topology.
    enable = False

    if os.path.exists('mgmt_sys_var') is True:
        num = file_read_for_mgmt_instance_count()
        if num == 0:
            enable = True
        else:
            num = num - 1
            file_write_for_mgmt_instance_count(num)

    # Enabling dhclient.profile on VM.
    if enable:
        enable_dhclient_profile()
        os.system('rm mgmt_sys_var')
