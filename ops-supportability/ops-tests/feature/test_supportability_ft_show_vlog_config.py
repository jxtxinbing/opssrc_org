# -*- coding: utf-8 -*-

# (c) Copyright 2016 Hewlett Packard Enterprise Development LP
#
# GNU Zebra is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# GNU Zebra is distributed in the hope that it will be useful, but
# WITHoutput ANY WARRANTY; withoutput even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Zebra; see the file COPYING.  If not, write to the Free
# Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.


# Topology definition. the topology contains two back to back switches
# having four links between them.

from re import search
from re import compile as re_compile
from pytest import mark

TOPOLOGY = """
# +-------+
# |  sw1  |
# +-------+

# Nodes
[type=openswitch name="Switch 1"] sw1
"""


def get_into_config(sw1, step):
    step("Getting into configure terminal")
    sw1("configure terminal")


def get_out_of_config(sw1, step):
    step("Getting out from configure terminal")
    sw1("end")


def check_show_vlog_list(sw1, step):
    step("\n############################################")
    step("1.1 Running show-vlog config list test        ")
    step("############################################\n")

    output = sw1("show vlog config list")

    step(output)
    assert "Features" in output
    assert "Description" in output
    assert "lldp" in output


def check_show_vlog_feature(sw1, step):
    step("\n############################################")
    step("1.2 Running show vlog feature test            ")
    step("############################################\n")

    output = sw1("show vlog config feature lldp")

    step(output)
    assert "Feature" in output
    assert "Syslog" in output
    assert "lldp" in output


def check_show_vlog(sw1, step):
    step("\n############################################")
    step("1.3 Running show vlog config test             ")
    step("############################################\n")

    output = sw1("show vlog config")

    step(output)
    assert "Feature" in output
    assert "Daemon" in output
    assert "Syslog" in output
    assert "lldp" in output


def check_vlog_config_feature(sw1, step):
    step("\n############################################")
    step("1.4 Check basic Vlog Configuration Feature    ")
    step("############################################\n")

    get_into_config(sw1, step)

    output = sw1("vlog feature lacp syslog info")

    output = sw1("vlog feature lacp file dbg")

    # Clean Up
    get_out_of_config(sw1, step)

    step(str(output))

    output = sw1("show vlog config feature lacp")

    step(str(output))
    regex = re_compile(r"lacp\s+INFO\s+DBG")

    assert search(regex, output) is not None

    # Now change the setting to DBG and check whether it changes
    get_into_config(sw1, step)

    output = sw1("vlog feature lacp syslog dbg")

    output = sw1("vlog feature lacp file info")

    # Clean Up
    get_out_of_config(sw1, step)

    step(str(output))

    output = sw1("show vlog config feature lacp")

    step(str(output))
    regex = re_compile(r"lacp\s+DBG\s+INFO")

    assert search(regex, output) is not None


def check_vlog_config_daemon(sw1, step):
    step("\n############################################")
    step("1.5 Check basic Vlog Configuration for Daemon ")
    step("############################################\n")

    get_into_config(sw1, step)

    output = sw1("vlog daemon ops-lacpd syslog info")

    output = sw1("vlog daemon ops-lacpd file dbg")
    # Clean Up
    get_out_of_config(sw1, step)

    step(str(output))

    output = sw1("show vlog config daemon ops-lacpd")

    step(str(output))
    regex = re_compile(r"ops-lacpd\s+INFO\s+DBG")

    assert search(regex, output) is not None

    # Now change the setting to DBG and check whether it changes
    get_into_config(sw1, step)

    output = sw1("vlog daemon ops-lacpd syslog dbg")

    output = sw1("vlog daemon ops-lacpd file info")

    # Clean Up
    get_out_of_config(sw1, step)

    step(str(output))

    output = sw1("show vlog config daemon ops-lacpd")

    step(str(output))
    regex = re_compile(r"ops-lacpd\s+DBG\s+INFO")

    assert search(regex, output) is not None


def check_invalid_daemon(sw1, step):
    step("\n############################################")
    step("2.1 Run Show vlog for invalid daemon          ")
    step("############################################\n")

    # simply@#$*beland
    output = sw1("show vlog config daemon adsf@f$*ASDfjaklsdf@#Q@3r")
    step(str(output))
    check = "Not able to communicate with daemon adsf@f$*ASDfjaklsdf@#Q@3r"
    assert check in output


def check_invalid_feature(sw1, step):
    step("\n############################################")
    step("2.2 Run Show vlog for invalid feature          ")
    step("############################################\n")

    output = sw1("show vlog config feature adsf@f$*ASDfjaklsdf@#Q@3r")

    step(str(output))

    assert "Feature not present" in output


def check_invalid_sub_command(sw1, step):
    step("\n############################################")
    step("2.3 Run Show vlog invalid subcommand          ")
    step("############################################\n")

    output = sw1("show vlog config adsf@f$*ASDfjaklsdf@#Q@3r")

    step(str(output))

    assert "Unknown command" in output


def check_vlog_config_invalid_feature(sw1, step):
    step("\n############################################")
    step("2.4 Check Vlog Configuration for Invaild Feature ")
    step("############################################\n")

    get_into_config(sw1, step)

    output = sw1("vlog feature adsf@f$*ASDfjaklsdf@#Q@3r syslog info")

    # Clean Up
    get_out_of_config(sw1, step)

    assert "Feature not present" in output


def check_vlog_config_invalid_daemon(sw1, step):
    step("\n############################################")
    step("2.5 Check Vlog Configuration for Invaild Daemon ")
    step("############################################\n")

    get_into_config(sw1, step)

    output = sw1("vlog daemon adsf@f$*ASDfjaklsdf@#Q@3r syslog info")

    # Clean Up
    get_out_of_config(sw1, step)

    check = "Not able to communicate with daemon adsf@f$*ASDfjaklsdf@#Q@3r"
    assert check in output


def check_vlog_config_invalid_destination(sw1, step):
    step("\n############################################")
    step("2.6 Check Vlog Configuration for Invaild Destination ")
    step("############################################\n")

    get_into_config(sw1, step)

    output = sw1("vlog feature lldpd adsf@f$*ASDfjaklsdf@#Q@3r info")

    # Clean Up
    get_out_of_config(sw1, step)

    assert "Unknown command" in output


def check_vlog_config_invalid_log_level(sw1, step):
    step("\n############################################")
    step("2.7 Check Vlog Configuration for Invaild Loglevel ")
    step("############################################\n")

    get_into_config(sw1, step)

    output = sw1("vlog feature lldpd syslog adsf@f$*ASDfjaklsdf@#Q@3r")

    # Clean Up
    get_out_of_config(sw1, step)

    assert "Unknown command" in output


@mark.gate
def test_supportability_show_vlog(topology, step):
    sw1 = topology.get("sw1")
    assert sw1 is not None

    # Positive Test Cases
    check_show_vlog_list(sw1, step)
    check_show_vlog_feature(sw1, step)
    check_show_vlog(sw1, step)
    check_vlog_config_feature(sw1, step)
    check_vlog_config_daemon(sw1, step)

    # Negative Test Cases
    check_invalid_daemon(sw1, step)
    check_invalid_feature(sw1, step)
    check_invalid_sub_command(sw1, step)
    check_vlog_config_invalid_log_level(sw1, step)
    check_vlog_config_invalid_destination(sw1, step)
    check_vlog_config_invalid_daemon(sw1, step)
    check_vlog_config_invalid_feature(sw1, step)
