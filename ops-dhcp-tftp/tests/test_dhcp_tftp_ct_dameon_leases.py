#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2015 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import os
import time
from opsvsi.docker import *
from opsvsi.opsvsitest import *


class dhcp_tftpDaemonLeasestest(OpsVsiTest):
    def setupNet(self):
        host_opts = self.getHostOpts()
        switch_opts = self.getSwitchOpts()
        dhcp_topo = SingleSwitchTopo(k=0, hopts=host_opts, sopts=switch_opts)
        self.net = Mininet(dhcp_topo, switch=VsiOpenSwitch,
                           host=Host, link=OpsVsiLink,
                           controller=None, build=True)

    def test_dhcp_tftp_add_range(self):
        info("\n########## Test to add DHCP dynamic configurations "
             "########## \n")

        range_created = False
        range_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("range test-range start-ip-address 10.0.0.1 \
                   end-ip-address 10.0.0.254 \
                   netmask 255.0.0.0 match tags tag1,tag2,tag3 \
                   set tag test-tag broadcast 10.255.255.255 \
                   lease-duration 60")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "10.0.0.1" in line \
                and "10.0.0.254" in line and "255.0.0.0" in line \
                and "tag1,tag2,tag3" in line and "tag" in line \
                    and "10.255.255.255" in line and "60" in line:
                    range_created = True
                    break

        assert range_created is True, 'Test to add DHCP Dynamic configuration \
                                        CLI - FAILED!'

        sleep(10)
        dump_bash = s1.cmd("ps -ef | grep dnsmasq")
        # print dump_bash
        lines = dump_bash.split('\n')
        for line in lines:
            if "10.0.0.1" in line \
                and "10.0.0.254" in line and "255.0.0.0" in line \
                and "tag1" in line and "tag2" in line \
                and "tag3" in line and "tag" in line \
                    and "10.255.255.255" in line and "60" in line:
                    range_in_use = True
                    break

        assert range_in_use is True, 'Test to add DHCP Dynamic configuration \
                                      -FAILED!'

        return True

    def test_dhcp_tftp_add_static(self):
        info("\n########## Test to add DHCP static configuration "
             "##########\n")

        static_created = False
        static_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("static 10.0.0.100 \
                   match-mac-addresses aa:bb:cc:dd:ee:ff \
                   set tags tag1,tag2,tag3 \
                   lease-duration 60")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "10.0.0.100" in line \
                and "aa:bb:cc:dd:ee:ff" in line \
                and "tag1,tag2,tag3" in line \
                    and "60" in line:
                    static_created = True
                    break

        assert static_created is True, 'Test to add DHCP static configuration \
                                        CLI - FAILED!'

        sleep(10)
        dump_bash = s1.cmd("ps -ef | grep dnsmasq")
        # print dump_bash
        lines = dump_bash.split('\n')
        for line in lines:
            if "10.0.0.100" in line \
                and "aa:bb:cc:dd:ee:ff" in line \
                and "tag1" and "tag2" and "tag3" in line \
                    and "60" in line:
                    static_in_use = True
                    break

        assert static_in_use is True, 'Test to add DHCP static configuration \
                                       - FAILED!'

        return True

    def test_dhcp_tftp_add_option_name(self):
        info("\n########## Test to add DHCP Options using option name "
             "##########\n")

        option_created = False
        option_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("option \
                   set option-name Router \
                   option-value 10.11.12.1 \
                   match tags opt1,opt2,opt3")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "Router" in line \
                and "10.11.12.1" in line \
                and "False" in line \
                    and "opt1,opt2,opt3" in line:
                    option_created = True
                    break

        assert option_created is True, 'Test to add DHCP Option using \
                option name CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "option:Router" in line \
                and "10.11.12.1" in line \
                and "opt1" in line \
                and "opt2" in line \
                    and "opt3" in line:
                    option_in_use = True
                    break

        assert option_in_use is True, 'Test to add DHCP Option using \
                option name - FAILED!'

        return True

    def test_dhcp_tftp_add_option_number(self):
        info("\n########## Test to add DHCP Options using option number "
             "########## \n")

        option_created = False
        option_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("option \
                   set option-number 3 \
                   option-value 10.10.10.1 \
                   match tags tag4,tag5,tag6")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.10.10.1" in line \
                and "False" in line \
                    and "tag4,tag5,tag6" in line:
                    option_created = True
                    break

        assert option_created is True, 'Test to add DHCP Options using \
                        option number CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.10.10.1" in line \
                and "tag4" in line \
                and "tag5" in line \
                    and "tag6" in line:
                    option_in_use = True
                    break

        assert option_in_use is True, 'Test to add DHCP Options using \
                        option number -FAILED!'

        return True

    def test_dhcp_tftp_add_match_number(self):
        info("\n########## Test to add DHCP Match using option number "
             "##########\n")

        match_created = False
        match_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("match \
                   set tag ops_match_num \
                   match-option-number 3 \
                   match-option-value 10.20.20.10")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.20.20.10" in line \
                    and "ops_match_num" in line:
                    match_created = True
                    break

        assert match_created is True, 'Test to add DHCP Match using option \
                number CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.20.20.10" in line \
                    and "ops_match_num" in line:
                    match_in_use = True
                    break

        assert match_in_use is True, 'Test to add DHCP Match using option \
                number -FAILED!'

        return True

    def test_dhcp_tftp_add_match_name(self):
        info("\n########## Test to add DHCP Match using option name "
             "########## \n")

        match_created = False
        match_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("match \
                   set tag ops_match_name \
                   match-option-name Router \
                   match-option-value 10.20.10.1")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "Router" in line \
                and "10.20.10.1" in line \
                    and "ops_match_name" in line:
                    match_created = True
                    break

        assert match_created is True, 'Test to add DHCP Match using option \
                name CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "Router" in line \
                and "10.20.10.1" in line \
                    and "ops_match_name" in line:
                    match_in_use = True
                    break

        assert match_in_use is True, 'Test to add DHCP Match using option \
                name - FAILED!'

        return True

    def test_dhcp_tftp_add_boot(self):
        info("\n##########  Test to add DHCP bootp configurations "
             "##########\n")

        boot_created = False
        boot_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("boot \
                   set file /tmp/testfile \
                   match tag ops_bootp")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "/tmp/testfile" in line and "ops_bootp" in line:
                boot_created = True
                break

        assert boot_created is True, 'Test to add DHCP bootp configuration \
                CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "/tmp/testfile" in line and "ops_bootp" in line:
                boot_in_use = True
                break

        assert boot_in_use is True, 'Test to add DHCP bootp configuration \
                -FAILED!'

        return True

    def test_tftp_server_enable(self):
        info("\n########## Test to enable tftp server ##########\n")

        tftp_enabled = False
        tftp_enabled_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("tftp-server")
        s1.cmdCLI("enable")

        dump = s1.cmdCLI("do show tftp-server")
        lines = dump.split('\n')
        for line in lines:
            if "TFTP server : Enabled" in line:
                tftp_enabled = True
                break

        assert tftp_enabled is True, 'Test to enable tftp server - \
                                      CLI FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "--enable-tftp" in line:
                tftp_enabled_in_use = True
                break

        assert tftp_enabled_in_use is True, 'Test to enable \
                                      tftp server -FAILED!'

        return True

    def test_tftp_secure_enable(self):
        info("\n########## Test to enable tftp server secure mode "
             "##########\n")

        tftp_secure_enabled = False
        tftp_secure_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("tftp-server")
        s1.cmdCLI("secure-mode")

        dump = s1.cmdCLI("do show tftp-server")
        lines = dump.split('\n')
        for line in lines:
            if "TFTP server secure mode : Enabled" in line:
                tftp_secure_enabled = True
                break

        assert tftp_secure_enabled is True, 'Test to enable tftp server \
                secure  mode CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "--tftp-secure" in line:
                tftp_secure_in_use = True
                break

        assert tftp_secure_in_use is True, 'Test to enable tftp server \
                secure  mode -FAILED!'

        return True

    def test_tftp_server_add_path(self):
        info("\n########## Test to add tftp path ##########\n")

        tftp_path = False
        tftp_path_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("tftp-server")
        s1.cmdCLI("path /tmp/")

        dump = s1.cmdCLI("do show tftp-server")
        lines = dump.split('\n')
        for line in lines:
            if "TFTP server file path : /tmp/" in line:
                tftp_path = True
                break

        assert tftp_path is True, 'Test to add tftp path CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "--tftp-root=/tmp/" in line:
                tftp_path_in_use = True
                break

        assert tftp_path_in_use is True, 'Test to add tftp path -FAILED!'

        return True

    def test_tftp_server_disable(self):
        info("\n########## Test to disable tftp server ##########\n")

        tftp_disabled = False
        tftp_disabled_in_use = True
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("tftp-server")
        s1.cmdCLI("no enable")

        dump = s1.cmdCLI("do show tftp-server")
        lines = dump.split('\n')
        for line in lines:
            if "TFTP server : Disabled" in line:
                tftp_disabled = True
                break

        assert tftp_disabled is True, 'Test to disable tftp server \
                                       CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "--enable-tftp" in line:
                tftp_disabled_in_use = False
                break

        assert tftp_disabled_in_use is True, 'Test to disable \
                                      tftp server - FAILED!'

        return True

    def test_tftp_secure_disable(self):
        info("\n########## Test to disable tftp server secure mode "
             "##########\n")

        tftp_secure_disabled = False
        tftp_secure_disabled_in_use = True
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("tftp-server")
        s1.cmdCLI("no secure-mode")

        dump = s1.cmdCLI("do show tftp-server")
        lines = dump.split('\n')
        for line in lines:
            if "TFTP server secure mode : Disabled" in line:
                tftp_secure_disabled = True
                break

        assert tftp_secure_disabled is True, 'Test to disable tftp server \
                                               secure mode CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "--tftp-secure" in line:
                tftp_secure_disabled_in_use = False
                break

        assert tftp_secure_disabled_in_use is True, 'Test to disable \
                                      tftp server - FAILED!'

        return True

    def test_dhcp_tftp_del_range(self):
        info("\n########## Test to delete DHCP dynamic configurations "
             "##########\n")

        range_created = False
        range_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("no range test-range start-ip-address 10.0.0.1 \
                   end-ip-address 10.0.0.254 \
                   netmask 255.0.0.0 match tags tag1,tag2,tag3 \
                   set tag test-tag broadcast 10.255.255.255 \
                   lease-duration 60")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "test-range" in line \
                and "10.0.0.1" in line \
                and "10.0.0.254" in line and "255.0.0.0" in line \
                and "tag1,tag2,tag3" in line and "tag" in line \
                    and "10.255.255.255" in line and "60" in line:
                    range_created = True
                    break

        assert range_created is False, 'Test to delete DHCP Dynamic \
                                       configuration CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "10.0.0.1" in line \
                and "10.0.0.254" in line and "255.0.0.0" in line \
                and "tag1,tag2,tag3" in line and "tag" in line \
                    and "10.255.255.255" in line and "60" in line:
                    range_in_use = True
                    break

        assert range_in_use is False, 'Test to delete DHCP Dynamic \
                                       configuration - FAILED!'

        return True

    def test_dhcp_tftp_del_static(self):
        info("\n########## Test to delete DHCP static configuration "
             "##########\n")

        static_created = False
        static_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("no static 10.0.0.100 \
                   match-mac-addresses aa:bb:cc:dd:ee:ff \
                   set tags tag1,tag2,tag3 \
                   match-client-id testid \
                   match-client-hostname testname \
                   lease-duration 60")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "10.0.0.100" in line \
                and "aa:bb:cc:dd:ee:ff" in line \
                and "testid" in line \
                and "tag1,tag2,tag3" in line \
                and "testname" in line \
                    and "60" in line:
                    static_created = True
                    break

        assert static_created is False, 'Test to delete DHCP static \
                                        configuration CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "10.0.0.100" in line \
                and "aa:bb:cc:dd:ee:ff" in line \
                and "testid" in line \
                and "tag1,tag2,tag3" in line \
                and "testname" in line \
                    and "60" in line:
                    static_in_use = True
                    break

        assert static_in_use is False, 'Test to delete DHCP static \
                                        configuration - FAILED!'

        return True

    def test_dhcp_tftp_del_option_name(self):
        info("\n########## Test to delete DHCP Option using option name "
             "##########\n")

        option_created = False
        option_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("no option \
                   set option-name Router \
                   option-value 10.11.12.1 \
                   match tags opt1,opt2,opt3")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "Router" in line \
                and "10.11.12.1" in line \
                and "False" in line \
                    and "opt1,opt2,opt3" in line:
                    option_created = True
                    break

        assert option_created is False, 'Test to delete DHCP Option using \
                                        option name CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "Router" in line \
                and "10.11.12.1" in line \
                    and "opt1,opt2,opt3" in line:
                    option_in_use = True
                    break

        assert option_in_use is False, 'Test to delete DHCP Option using \
                                        option name - FAILED!'

        return True

    def test_dhcp_tftp_del_option_number(self):
        info("\n########## Test to delete DHCP Option using option number "
             "##########\n")

        option_created = False
        option_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("no option \
                   set option-number 3 \
                   option-value 10.10.10.1 \
                   match tags tag4,tag5,tag6")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.10.10.1" in line \
                and "False" in line \
                    and "tag4,tag5,tag6" in line:
                    option_created = True
                    break

        assert option_created is False, 'Test to delete DHCP Option using \
                                         option number CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.10.10.1" in line \
                and "tag4" in line \
                and "tag5" in line \
                    and "tag6" in line:
                    option_in_use = True
                    break

        assert option_in_use is False, 'Test to delete DHCP Option using \
                                        option number - FAILED!'

        return True

    def test_dhcp_tftp_del_match_number(self):
        info("\n########## Test to delete DHCP match using option number "
             "##########\n")

        match_created = False
        match_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("no match \
                   set tag ops_match_num \
                   match-option-number 3 \
                   match-option-value 10.20.20.10")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.20.20.10" in line \
                    and "ops_match_num" in line:
                    match_created = True
                    break

        assert match_created is False, 'Test to delete DHCP match using option \
                                        number CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "3" in line \
                and "10.20.20.10" in line \
                    and "ops_match_num" in line:
                    match_in_use = True
                    break

        assert match_in_use is False, 'Test to delete DHCP match using option \
                                        number - FAILED!'

        return True

    def test_dhcp_tftp_del_match_name(self):
        info("\n########## Test to delete DHCP match using option name "
             "##########\n")

        match_created = False
        match_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("no match \
                   set tag ops_match_name \
                   match-option-name Router \
                   match-option-value 10.20.10.1")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "Router" in line \
                and "10.20.10.1" in line \
                    and "ops_match_name" in line:
                    match_created = True
                    break

        assert match_created is False, 'Test to delete DHCP match using option \
                                       name CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "Router" in line \
                and "10.20.10.1" in line \
                    and "ops_match_name" in line:
                    match_in_use = True
                    break

        assert match_in_use is False, 'Test to delete DHCP match using option \
                                       name  - FAILED!'

        return True

    def test_dhcp_tftp_del_boot(self):
        info("\n ########## Test to delete DHCP bootp configuration "
             "##########\n")

        boot_created = False
        boot_in_use = False
        s1 = self.net.switches[0]
        s1.cmdCLI("configure terminal")
        s1.cmdCLI("dhcp-server")
        s1.cmdCLI("no boot \
                   set file /tmp/testfile \
                   match tag ops_bootp")

        dump = s1.cmdCLI("do show dhcp-server")
        lines = dump.split('\n')
        for line in lines:
            if "/tmp/testfile" in line and "ops_bootp" in line:
                boot_created = True
                break

        assert boot_created is False, 'Test to delete DHCP bootp configuration \
                                       CLI - FAILED!'

        sleep(10)
        dump = s1.cmd("ps -ef | grep dnsmasq")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "/tmp/testfile" in line and "ops_bootp" in line:
                boot_in_use = True
                break

        assert boot_in_use is False, 'Test to delete DHCP bootp configuration \
                                      - FAILED!'

        return True

    def test_dhcp_tftp_add_leases(self):
        info("\n ########## Test to add DHCP leases information "
             "##########\n")

        s1 = self.net.switches[0]

        dhcp_leases_created = False

        # os.environ["DNSMASQ_LEASE_EXPIRES"] = "1440976224"
        s1.cmd("export DNSMASQ_LEASE_EXPIRES=1440976224")

        dump = s1.cmd("dhcp_leases add 11:22:33:44:55:66 10.0.0.100 test_s1")
        # print dump

        dump = s1.cmdCLI("do show dhcp-server leases")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "11:22:33:44:55:66" in line \
                and "10.0.0.100" in line \
                    and "test_s1" in line:
                    dhcp_leases_created = True
                    break

        assert dhcp_leases_created is True, 'Test to add DHCP leases \
                                             information - FAILED!'

        return True

    def test_dhcp_tftp_modify_leases(self):

        info("\n ########## Test to modify DHCP leases information "
             "##########\n")

        s1 = self.net.switches[0]

        dhcp_leases_modified = False

        # os.environ["DNSMASQ_LEASE_EXPIRES"] = "1440976224"
        s1.cmd("export DNSMASQ_LEASE_EXPIRES=1440976224")

        s1.cmd("dhcp_leases old 11:22:33:44:55:66 20.0.0.200 test_s1_new")

        dump = s1.cmdCLI("do show dhcp-server leases")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "11:22:33:44:55:66" in line \
                and "20.0.0.200" in line \
                    and "test_s1_new" in line:
                    dhcp_leases_modified = True
                    break

        assert dhcp_leases_modified is True, 'Test to delete DHCP leases \
                                              information - FAILED!'

        return True

    def test_dhcp_tftp_delete_leases(self):

        info("\n ########## Test to delete DHCP leases information "
             "##########\n")

        s1 = self.net.switches[0]

        dhcp_leases_deleted = True

        # os.environ["DNSMASQ_LEASE_EXPIRES"] = "1440976224"
        s1.cmd("export DNSMASQ_LEASE_EXPIRES=1440976224")

        s1.cmd("dhcp_leases del 11:22:33:44:55:66 20.0.0.200 test_s1_new")

        dump = s1.cmdCLI("do show dhcp-server leases")
        # print dump
        lines = dump.split('\n')
        for line in lines:
            if "11:22:33:44:55:66" in line \
                and "20.0.0.200" in line \
                    and "test_s1_new" in line:
                    dhcp_leases_deleted = False
                    break

        assert dhcp_leases_deleted is True, 'Test to delete DHCP leases \
                                              information - FAILED!'

        return True


@pytest.mark.skipif(True, reason="Disabling old tests")
class Test_vtysh_dhcp_tftp:

    def setup_class(cls):

        # Create a test topology

        Test_vtysh_dhcp_tftp.test = dhcp_tftpDaemonLeasestest()

    def teardown_class(cls):

        # Stop the Docker containers, and
        # mininet topology

        Test_vtysh_dhcp_tftp.test.net.stop()

    def test_dhcp_tftp_add_range(self):
        if self.test.test_dhcp_tftp_add_range():
            info('''
#### Test to add DHCP dynamic configurations - SUCCESS! ###''')

    def test_dhcp_tftp_add_static(self):
        if self.test.test_dhcp_tftp_add_static():
            info('''
### Test to add DHCP static configurations - SUCCESS! ###''')

    def test_dhcp_tftp_add_option_name(self):
        if self.test.test_dhcp_tftp_add_option_name():
            info('''
### Test to add DHCP Option using option name  - SUCCESS! ###''')

    def test_dhcp_tftp_add_option_number(self):
        if self.test.test_dhcp_tftp_add_option_number():
            info('''
### Test to add DHCP Option using option number  - SUCCESS! ###''')

    def test_dhcp_tftp_add_match_name(self):
        if self.test.test_dhcp_tftp_add_match_name():
            info('''
### Test to add DHCP Match using option name - SUCCESS! ###''')

    def test_dhcp_tftp_add_match_number(self):
        if self.test.test_dhcp_tftp_add_match_number():
            info('''
### Test to add DHCP Match using option number  - SUCCESS! ###''')

    def test_dhcp_tftp_add_boot(self):
        if self.test.test_dhcp_tftp_add_boot():
            info('''
### Test to add DHCP Bootp configuration  - SUCCESS! ###''')

    def test_dhcp_tftp_del_range(self):
        if self.test.test_dhcp_tftp_del_range():
            info('''
### Test to delete dhcp dynamic confguration - SUCCESS! ###''')

    def test_dhcp_tftp_del_static(self):
        if self.test.test_dhcp_tftp_del_static():
            info('''
### Test to delete DHCP static configurations - SUCCESS! ###''')

    def test_dhcp_tftp_del_option_name(self):
        if self.test.test_dhcp_tftp_del_option_name():
            info('''
### Test to delete DHCP Option using option name  - SUCCESS! ###''')

    def test_dhcp_tftp_del_option_number(self):
        if self.test.test_dhcp_tftp_del_option_number():
            info('''
### Test to delete DHCP Option using option number  - SUCCESS! ###''')

    def test_dhcp_tftp_del_match_name(self):
        if self.test.test_dhcp_tftp_del_match_name():
            info('''
###  Test to delete DHCP Match using option name  - SUCCESS! ###''')

    def test_dhcp_tftp_del_match_number(self):
        if self.test.test_dhcp_tftp_del_match_number():
            info('''
### Test to add delete DHCP Match using option number  - SUCCESS! ###''')

    def test_dhcp_tftp_del_boot(self):
        if self.test.test_dhcp_tftp_del_boot():
            info('''
### Test to delete DHCP Bootp configuration  - SUCCESS! ###''')

    def test_tftp_server_enable(self):
        if self.test.test_tftp_server_enable():
            info('''
### Test to enable TFTP server  - SUCCESS! ###''')

    def test_tftp_secure_enable(self):
        if self.test.test_tftp_secure_enable():
            info('''
### Test to enable TFTP secure mode  - SUCCESS! ###''')

    def test_tftp_server_add_path(self):
        if self.test.test_tftp_server_add_path():
            info('''
### Test to add  TFTP path - SUCCESS! ###''')

    def test_tftp_server_disable(self):
        if self.test.test_tftp_server_disable():
            info('''
###  Test to disable TFTP server  - SUCCESS! ###''')

    def test_tftp_secure_disable(self):
        if self.test.test_tftp_secure_disable():
            info('''
###  Test to disable TFTP secure mode- SUCCESS! ###''')

    def test_dhcp_tftp_add_leases(self):
        if self.test.test_dhcp_tftp_add_leases():
            info('''
###  Test to add DHCP leases - SUCCESS! ###''')

    def test_dhcp_tftp_modify_leases(self):
        if self.test.test_dhcp_tftp_modify_leases():
            info('''
###  Test to modify DHCP leases - SUCCESS! ###''')

    def test_dhcp_tftp_delete_leases(self):
        if self.test.test_dhcp_tftp_delete_leases():
            info('''
###  Test to delete DHCP leases - SUCCESS! ###''')
