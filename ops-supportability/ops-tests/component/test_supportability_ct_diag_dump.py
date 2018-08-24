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

from re import match, I
from time import sleep
from pytest import mark

# Topology definition. the topology contains two back to back switches
# having four links between them.


TOPOLOGY = """
# +-------+
# |  sw1  |
# +-------+

# Nodes
[type=openswitch name="Switch 1"] sw1
"""


# Generates shell command to add feature in config file

def gen_shell_cmd_add_conf(daemon, feature):
    shell_cmd = ("printf \"\n---\n  -\n    feature_name: \'{}\'\n"
                 "    feature_desc: \'Sample feature\'\n"
                 "    daemon:\n     - [name: \'{}\', \'diag_dump\':\'y\']\""
                 " > /etc/openswitch/supportability/ops_featuremapping.yaml"
                 "".format(feature, daemon))
    print("**", shell_cmd, "**")
    return shell_cmd


def check_unknown_command(output):
    assert match(".*(unknown command)", output, I) is not None


def gen_shell_cmd_backup_conf():
    shell_cmd = "mv \
    /etc/openswitch/supportability/ops_featuremapping.yaml \
      /etc/openswitch/supportability/ops_featuremapping.yaml.bak"
    return shell_cmd

# Generates shell command to restore old backup config


def gen_shell_cmd_restore_conf():
    shell_cmd = "mv \
            /etc/openswitch/supportability/ops_featuremapping.yaml.bak \
    /etc/openswitch/supportability/ops_featuremapping.yaml"
    return shell_cmd


def check_diag_dump_list(step, sw1):
    # Variables
    str_check = 'Diagnostic Dump Supported Features List'
    vtysh_cmd = 'diag-dump list'
    tc_desc = vtysh_cmd + ' test '

    step("\n############################################")
    step('1.1 Running' + tc_desc)
    step("############################################\n")

    output = sw1(vtysh_cmd)
    step(str(output))

    assert str_check in output


def check_diag_dump_feature(step, sw1, feature):
    # Variables
    str_check = 'Diagnostic dump captured for feature'
    vtysh_cmd = 'diag-dump ' + feature + ' basic'
    tc_desc = vtysh_cmd + ' test '
    step("\n############################################")
    step("1.2 Running" + tc_desc)
    step("############################################\n")

    output = sw1(vtysh_cmd)
    step(str(output))

    assert str_check in output


def check_diag_dump_feature_file(step, sw1, feature, file_txt):
    # Variables
    str_check = 'PASS'
    str_check_file = "\[Start\] Feature"
    vtysh_cmd = 'diag-dump ' + feature + ' basic ' + file_txt
    tc_desc = vtysh_cmd + ' test '
    diag_file_path = '/tmp/ops-diag/' + file_txt

    step("\n############################################")
    step("1.3 Running" + tc_desc)
    step("############################################\n")

    # Run diag-dump lldp basic <file> Command
    output = sw1(vtysh_cmd)
    step(str(output))

    shell_cmd = ' if [[ -f ' + diag_file_path \
        + ' ]]; then if [[ $(grep ' + str_check_file + ' ' + diag_file_path  \
        + ' ) -eq 0 ]]  ; then echo  PASS ; else echo FAIL; fi; '\
        + 'else echo FAIL; fi'

    output = sw1(shell_cmd, shell='bash')

    shell_cmd = ' rm -f ' + diag_file_path
    sw1(shell_cmd, shell='bash')  # outputclean

    print(str_check, output)
    # assert str_check in output


def check_diag_dump_feature_file_path(step, sw1, feature, diag_file):
    # Variables
    vtysh_cmd = 'diag-dump ' + feature + ' basic ' + diag_file
    tc_desc = vtysh_cmd + ' test '
    diag_file_path = '/tmp/ops-diag/' + diag_file
    str_check = diag_file_path

    step("\n############################################")
    step('1.4 Running ' + tc_desc)
    step("############################################\n")

    shell_cmd = 'rm -f ' + diag_file_path
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    # Run diag-dump lldp basic <file> Command
    output = sw1(vtysh_cmd)
    step(str(output))

    shell_cmd = 'ls ' + diag_file_path

    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    shell_cmd = 'rm -f ' + diag_file_path
    sw1(shell_cmd, shell='bash')

    assert str_check in output


def check_diag_dump_feature_file_size(step, sw1, feature, diag_file):
    # Variables
    vtysh_cmd = 'diag-dump ' + feature + ' basic ' + diag_file
    tc_desc = vtysh_cmd + ' size test '
    diag_file_path = '/tmp/ops-diag/' + diag_file
    str_check = 'PASS'

    step("\n############################################")
    step('1.5 Running ' + tc_desc)
    step("############################################\n")

    shell_cmd = 'rm -f ' + diag_file_path
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    # Run diag-dump lldp basic <file> Command
    output = sw1(vtysh_cmd)
    step(str(output))
    # exit the vtysh shell

    shell_cmd = ' if [[ -f ' + diag_file_path \
        + ' ]]; then if [[ $(stat -c %s ' + diag_file_path  \
        + ' ) -gt 1 ]]  ; then echo  PASS ; else echo FAIL; fi; '\
        + 'else echo FAIL; fi'

    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    # output
    # 1st line contains script
    # 2nd line contains output result

    shell_cmd = 'rm -f ' + diag_file_path
    sw1(shell_cmd, shell='bash')

    assert str_check in output


def check_unknown_daemon(step, sw1):
    # Variables
    str_check = 'failed to connect'
    daemon = 'ops-garb-abcd'
    feature = 'garbage'
    vtysh_cmd = 'diag-dump ' + feature + ' basic'
    tc_desc = vtysh_cmd + ' test '

    step("\n############################################")
    step('2.2 Running ' + tc_desc)
    step("############################################\n")

    shell_cmd = gen_shell_cmd_backup_conf()
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    shell_cmd = gen_shell_cmd_add_conf(daemon, feature)
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    output = sw1(vtysh_cmd)
    step(str(output))

    shell_cmd = gen_shell_cmd_restore_conf()

    sw1(shell_cmd, shell='bash')
    step(str(output))

    # assert str_check in output
    print(str_check, output)


def check_unknown_garb_daemon(step, sw1):
    # Variables
    daemon = 'ops-garb-abcd'
    feature = 'ops-garb-abcd'
    vtysh_cmd = 'diag-dump ' + feature + 'basic'
    tc_desc = vtysh_cmd + ' test '

    step("\n############################################")
    step('2.3 Running ' + tc_desc)
    step("############################################\n")

    shell_cmd = gen_shell_cmd_backup_conf()
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    shell_cmd = gen_shell_cmd_add_conf(daemon, feature)

    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    output = sw1(vtysh_cmd)
    step(str(output))

    shell_cmd = gen_shell_cmd_restore_conf()

    sw1(shell_cmd, shell='bash')
    step(str(output))

    check_unknown_command(output)


def check_no_config_file(step, sw1):
    # Variables
    vtysh_cmd = 'diag-dump lldp basic'
    tc_desc = vtysh_cmd + ' test '

    step("\n############################################")
    step("3.1 Running " + tc_desc)
    step("############################################\n")

    shell_cmd = gen_shell_cmd_backup_conf()
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    shell_cmd = "ls /etc/openswitch/supportability "
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    output = sw1(vtysh_cmd)
    step(str(output))

    shell_cmd = gen_shell_cmd_restore_conf()

    sw1(shell_cmd, shell='bash')
    step(str(output))

    # check_unknown_command(output)


def check_empty_file(step, sw1):
    # Variables
    vtysh_cmd = 'diag-dump list'
    str_check = ('Feature to daemon mapping failed. '
                 'Unable to retrieve the daemon name.')

    step("\n############################################")
    step("3.2 Running diag-dump empty config file test")
    step("############################################\n")

    shell_cmd = gen_shell_cmd_backup_conf()
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    shell_cmd = "touch /etc/openswitch/supportability/ops_featuremapping.yaml"
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    output = sw1(vtysh_cmd)
    step(str(output))

    shell_cmd = gen_shell_cmd_restore_conf()

    sw1(shell_cmd, shell='bash')
    step(str(output))

    print(str_check, output)
    # assert str_check in output


def check_corrupted_yaml_file(step, sw1):
    # Variables
    # str_check = 'Diagnostic dump captured for feature'
    daemon = 'lldp'
    vtysh_cmd = 'diag-dump ' + daemon + ' basic'
    tc_desc = vtysh_cmd + ' test '

    step("\n############################################")
    step("3.3 Running" + tc_desc)
    step("############################################\n")

    shell_cmd = gen_shell_cmd_backup_conf()
    output = sw1(shell_cmd, shell='bash')
    step(str(output))

    shell_cmd = 'printf  ---   -     feature_name: \"lldp\"' + \
        ' feature_desc: \"Link Layer Discovery Protocol\" ' + \
        ' daemon:       - \"ops-lldpd\" xxxxxxxxxxxxxxxxxxxxxxxxx ' + \
        ' aksjsjjdkdkdjddj kdkdkdkdkdkdkdk ---   ' + \
        ' -     feature_name: \"lldp\" ' + \
        '  feature_desc: \"Link Layer Discovery Protocol\" ' + \
        '    daemon:       - \"ops-lldpd\" xxxxxxxxxxxxxxxxxxxxxxxxx ' + \
        ' aksjsjjdkdkdjddj kdkdkdkdkdkdkdk ' + \
        ' ---   -     feature_name: \"lldp\"     feature_desc: ' + \
        ' \"Link Layer Discovery Protocol\"     daemon:       - \"ops-lldpd\"'\
        + '  xxxxxxxxxxxxxxxxxxxxxxxxx aksjsjjdkdkdjddj kdkdkdkdkdkdkdk' + \
        ' >>  /etc/openswitch/supportability/ops_featuremapping.yaml'

    sw1(shell_cmd, shell='bash')
    step(str(output))

    output = sw1(vtysh_cmd)
    step(str(output))

    shell_cmd = gen_shell_cmd_restore_conf()
    sw1(shell_cmd, shell='bash')

    # check_unknown_command(output)


@mark.gate
def test_supportability_diag_dump(topology, step):
    sw1 = topology.get("sw1")
    assert sw1 is not None

    # positive test case
    check_diag_dump_list(step, sw1)

    check_diag_dump_feature(step, sw1, 'lldp')
    check_diag_dump_feature(step, sw1, 'lacp')

    check_diag_dump_feature_file(step, sw1, 'lldp', 'diag.txt')
    check_diag_dump_feature_file(step, sw1, 'lacp', 'diag.txt')

    check_diag_dump_feature_file_path(step, sw1, 'lldp', 'diag.txt')
    check_diag_dump_feature_file_path(step, sw1, 'lacp', 'diag.txt')

    check_diag_dump_feature_file_size(step, sw1, 'lldp', 'diag.txt')
    check_diag_dump_feature_file_size(step, sw1, 'lacp', 'diag.txt')

    # negative test case
    # When ops-bgpd daemon implement diag feature this TC will fail and they
    # can't commit their changes. In that case we have to identify some other
    # daemon which doesn't support diag feature

    check_unknown_daemon(step, sw1)

    check_unknown_garb_daemon(step, sw1)

    check_no_config_file(step, sw1)

    check_empty_file(step, sw1)

    check_corrupted_yaml_file(step, sw1)
