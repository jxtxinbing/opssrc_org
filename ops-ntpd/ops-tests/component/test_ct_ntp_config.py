# (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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

from pytest import mark

TOPOLOGY = """
#
# +--------+
# |  ops1  |
# +--------+
#

# Nodes
[type=openswitch name="Switch 1"] ops1
"""


default_ntp_version = '3'


def ntp_auth_enable_disable_config(dut, step):
    step('\n### === authentication enable disable test start === ###')
    dut("configure terminal")
    dut("ntp authentication enable")
    dut("end")
    dump = dut("show ntp status")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if "NTP authentication is enabled" in line:
            step('\n### auth has been enabled as per show cli - passed ###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if "ntp authentication enable" in line:
            step('\n### auth has been enabled as per running-config - '
                 'passed ###')
            count = count + 1

    dut("configure terminal")
    dut("no ntp authentication enable")
    dut("end")
    dump = dut("show ntp status")
    lines = dump.splitlines()
    for line in lines:
        if "NTP authentication is disabled" in line:
            step('\n### auth has been disabled as per show cli - passed ###')
            count = count + 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if "ntp authentication enable" in line:
            '\n### auth has been enabled as per running-config - '
            'failed ###'
            count = count - 1

    assert count == 4, \
        '\n### authentication enable disable test failed ###'

    step('\n### authentication enable disable test passed ###')
    step('\n### === authentication enable disable test end === ###\n')


def ntp_valid_auth_key_add(dut, step):
    step('\n### === valid auth-key addition test start === ###')
    dut("configure terminal")
    dut("ntp authentication-key 10 md5 password10")
    dut("end")
    dump = dut("show ntp authentication-keys")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("10" in line and "password10" in line):
            step('\n### valid auth-key present as per show cli - passed ###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if "ntp authentication-key 10 md5 password10" in line:
            step('\n### valid auth-key present in running-config - passed')
            count = count + 1

    assert count == 2,\
            '\n### valid auth-key addition test failed ###'

    step('\n### valid auth-key addition test passed ###')
    step('\n### === valid auth-key addition test end === ###\n')


def ntp_valid_auth_key_delete(dut, step):
    step('\n### === auth-key deletion test start === ###')
    dut("configure terminal")
    dut("no ntp authentication-key 10")
    dut("end")
    dump = dut("show ntp authentication-keys")
    lines = dump.splitlines()
    count = 1
    for line in lines:
        if ("10" in line and "password10" in line):
            step('\n### deleted key still present as per show cli')
            count = count - 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if "ntp authentication-key 10 md5 password10" in line:
            step('\n### auth-key found in running-config inspite of '
                 'deleting it')
            count = count - 1

    assert count == 2,\
            '\n### valid auth-key deletion test failed ###'

    step('\n### valid auth-key deletion test passed ###')
    step('\n### === auth-key deletion test end === ###\n')


def ntp_invalid_auth_key_add(dut, step):
    step('\n### === invalid auth-key addition test start === ###')
    dut("configure terminal")
    dut("ntp authentication-key 0 md5 password0")
    dut("end")
    dump = dut("show ntp authentication-keys")
    lines = dump.splitlines()
    count = 0
    count = count + 1
    for line in lines:
        if ("0" in line and "password0" in line):
            '\n### invalid auth-key present as per show cli - '
            'failed ###'
            count = count - 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if "ntp authentication-key 0 md5 password0" in line:
            '\n### invalid auth-key present in running-config - failed'
            count = count - 1

    assert count == 2,\
            '\n### invalid auth-key addition test failed ###'

    step('\n### invalid auth-key addition test passed ###')
    step('\n### === invalid auth-key addition test end === ###\n')


def ntp_short_pwd_add(dut, step):
    step('\n### === invalid (short) auth-key password addition test start ==='
         ' ###')
    dut("configure terminal")
    dut("ntp authentication-key 2 md5 short")
    dut("end")
    dump = dut("show ntp authentication-keys")
    lines = dump.splitlines()
    count = 0
    count = count + 1
    for line in lines:
        if ("2" in line and "short" in line):
            '\n### invalid (short) auth-key password present as per '
            'show cli - failed ###'
            count = count - 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if "ntp authentication-key 2 md5 short" in line:
            '\n### invalid (short) auth-key password present in '
            'running-config - failed'
            count = count - 1

    assert count == 2,\
            '\n### invalid (short) auth-key password addition test failed ###'

    step('\n### invalid (short) auth-key password addition test passed ###')
    step('\n### === invalid (short) auth-key password addition test end ==='
         ' ###\n')


def ntp_tool_on_gpwd_add(dut, step):
    step('\n### === invalid (too-long) auth-key password addition test start '
         '=== ###')
    dut("configure terminal")
    dut("ntp authentication-key 17 md5 longerthansixteen")
    dut("end")
    dump = dut("show ntp authentication-keys")
    lines = dump.splitlines()
    count = 0
    count = count + 1
    for line in lines:
        if ("17" in line and "longerthansixteen" in line):
            '\n### invalid (too-long) auth-key password present as per '
            'show cli - failed ###'
            count = count - 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if "ntp authentication-key 17 md5 longerthansixteen" in line:
            '\n### invalid (too-long) auth-key password present in '
            'running-config - failed'
            count = count - 1

    assert count == 2,\
            '\n### invalid (too-long) auth-key password addition test failed ###'

    step('\n### invalid (too-long) auth-key password addition test passed '
         '###')
    step('\n### === invalid (too-long) auth-key password addition test end '
         '=== ###\n')


def ntp_add_server_no_options(dut, step):
    step('\n### === server (with no options) addition test start === ###')
    dut("configure terminal")
    dut("ntp server 1.1.1.1")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("1.1.1.1" in line and default_ntp_version in line):
            step('\n### server (with no options) present as per show cli - '
                 'passed ###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 1.1.1.1" in line and default_ntp_version not in line):
            step('\n### server (with no options) present in running config - '
                 'passed ###')
            count = count + 1

    assert count == 2,\
            '\n### server (with no options) addition test failed ###'

    step('\n### server (with no options) addition test passed ###')
    step('\n### === server (with no options) addition test end === ###\n')


def ntp_add_server_prefer_option(dut, step):
    step('\n### === server (with prefer option) addition test start === ###')
    dut("configure terminal")
    dut("ntp server 2.2.2.2 prefer")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("2.2.2.2" in line and default_ntp_version in line):
            step('\n### server (with no options) present as per show cli - '
                 'passed ###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 2.2.2.2 prefer" in line and
           default_ntp_version not in line):
            step('\n### server (with prefer options) present in running '
                 'config - passed ###')
            count = count + 1

    assert count == 2,\
            '\n### server (with prefer options) addition test failed ###'

    step('\n### server (with prefer options) addition test passed ###')
    step('\n### === server (with prefer option) addition test end === ###\n')


def ntp_add_server_valid_version_option(dut, step):
    step('\n### === server (with version option) addition test start === ###')
    dut("configure terminal")
    dut("ntp server 3.3.3.3 version 4")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("3.3.3.3" in line and "4" in line):
            step('\n### server (with version option) present as per show cli '
                 '- passed ###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 3.3.3.3 version 4" in line):
            step('\n### server (with version option) present in running '
                 'config - passed ###')
            count = count + 1

    assert count == 2,\
            '\n### server (with version option) addition test failed ###'

    step('\n### server (with version option) addition test passed ###')
    step('\n### === server (with version option) addition test end === ###\n')


def ntp_add_server_invalid_version_option(dut, step):
    step('\n### === server (with version option) addition test start === ###')
    dut("configure terminal")
    dut("ntp server 4.4.4.4 version 5")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    count = count + 1
    for line in lines:
        if ("4.4.4.4" in line and "5" in line):
            '\n### server (with invalid version option) present as per '
            'show cli - failed ###'
            count = count - 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 4.4.4.4 version 5" in line):
            '\n### server (with invalid version option) present in '
            'running config - failed ###'
            count = count - 1

    assert count == 2,\
            '\n### server (with invalid version option) addition test failed ###'

    step('\n### server (with invalid version option) addition test passed '
         '###')
    step('\n### === server (with invalid version option) addition test end '
         '=== ###\n')


def ntp_add_server_with_fqdn(dut, step):
    step('\n### === server (with fqdn) addition test start === ###')
    dut("configure terminal")
    dut("ntp server abc.789.com")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("abc.789.com" in line and default_ntp_version in line):
            step('\n### server (with fqdn) present as per show cli - passed '
                 '###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server abc.789.com" in line and
           default_ntp_version not in line):
            step('\n### server (with fqdn) present in running config - passed'
                 ' ###')
            count = count + 1

    assert count == 2,\
            '\n### server (with fqdn) addition test failed ###'

    step('\n### server (with fqdn) addition test passed ###')
    step('\n### === server (with fqdn) addition test end === ###\n')


def ntp_add_server_with_invalid_server_name(dut, step):
    step('\n### === server (with invalid server name) addition test start '
         '=== ###')
    dut("configure terminal")

    ''' ill-formatted ip addreses '''
    dut("ntp server 4.4")
    dut("ntp server 4.5.6.")
    dut("ntp server 5.5.275.5")

    ''' loopback, multicast,broadcast and experimental ip addresses '''
    dut("ntp server 127.25.25.25")
    dut("ntp server 230.25.25.25")
    dut("ntp server 250.25.25.25")

    ''' ip addresses starting with 0 '''
    dut("ntp server 0.1.1.1")

    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    count = count + 1
    for line in lines:
        if (
            "4.4" in line or "4.5.6." in line or "5.5.275.5" in line or
            "127.25.25.25" in line or "230.25.25.25" in line or
            "250.25.25.25" in line or "0.1.1.1" in line
        ):
            '\n### server (with ill-formatted ) present as per show '
            'cli - failed ###'
            count = count - 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if (
            "ntp server 4.4" in line or "ntp server 4.5.6." in line or
            "ntp server 5.5.275.5" in line or
            "ntp server 127.25.25.25" in line or
            "ntp server 230.25.25.25" in line or
            "ntp server 250.25.25.25" in line or "0.1.1.1" in line
        ):
            '\n### server (with ill-formatted) present in running '
            'config - failed ###'
            count = count - 1

    assert count == 2,\
            '\n### server (with invalid server name) addition test '\
            'failed ###'

    step('\n### server (with invalid server name) addition test passed ###')
    step('\n### === server (with invalid server name) addition test end ==='
         ' ###\n')


def ntp_add_server_key_id_option(dut, step):
    step('\n### === server (with key-id option) addition test start === ###')
    dut("configure terminal")
    dut("ntp authentication-key 10 md5 password10")
    dut("ntp server 4.4.4.4 key-id 10")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("4.4.4.4" in line and "10" in line):
            step('\n### server (with key-id option) present as per show cli -'
                 ' passed ###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 4.4.4.4 key-id 10" in line):
            step('\n### server (with key-id option) present in running config'
                 ' - passed ###')
            count = count + 1

    assert count == 2,\
            '\n### server (with key-id option) addition test failed '\
            '###'

    step('\n### server (with key-id option) addition test passed ###')
    step('\n### === server (with key-id option) addition test end === ###\n')


def ntp_add_server_all_options(dut, step):
    step('\n### === server (with all options) addition test start === ###')
    dut("configure terminal")
    dut("ntp authentication-key 11 md5 password11")
    dut("ntp server 5.5.5.5 key-id 11 version 4 prefer")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("5.5.5.5" in line and "11" in line and "4" in line):
            step('\n### server (with all options) present as per show cli - '
                 'passed ###')
            count = count + 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 5.5.5.5 key-id 11 version 4 prefer" in line):
            step('\n### server (with all options) present in running config -'
                 ' passed ###')
            count = count + 1

    assert count == 2,\
            '\n### server (with all options) addition test failed ###'

    step('\n### server (with all options) addition test passed ###')
    step('\n### === server (with all options) addition test end === ###\n')


def ntp_add_more_than_8_servers(dut, step):
    step('\n### === addition of more than 8 servers test start === ###')
    morethan8serverserror = "Maximum number of configurable NTP server limit has been reached"
    "has been reached"
    dut("configure terminal")
    dut("ntp server 6.6.6.6")
    dut("ntp server 7.7.7.7")
    dut("ntp server 8.8.8.8")

    dump = dut("ntp server 9.9.9.9")
    print(dump)
    assert morethan8serverserror in dump,\
            '\n### more than 8 server addition test failed ###'

    dut("end")

    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("6.6.6.6" in line or "7.7.7.7" in line or "8.8.8.8" in line):
            count = count + 1
        if ("9.9.9.9" in line):
            count = count - 1

    ''' now check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 6.6.6.6" in line or "ntp server 7.7.7.7" in line or
           "ntp server 8.8.8.8" in line):
            count = count + 1
        if ("ntp server 9.9.9.9" in line):
            count = count - 1

    assert count == 6,\
            '\n### === addition of more than 8 servers test failed ==='\
            ' ###'

    step('\n### === addition of more than 8 servers test passed === ###')
    step('\n### === addition of more than 8 servers test end === ###')


def ntp_modify_8th_ntp_server(dut, step):
    step('\n### === modifying version for the 8th ntp association test start '
         '=== ###')
    dut("configure terminal")
    dut("ntp server 8.8.8.8 version 4")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("8.8.8.8" in line):
            server_version = line.split()[3]
            if server_version != "4":
                '\n### server configuration is not latest failed === '\
                '###'
                count = count - 1
            else:
                count = count + 1

    ''' check the running config '''
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 8.8.8.8 version 4" in line):
            count = count + 1

    assert count == 2,\
            '\n### === modifying version for the 8th ntp association '\
            'test failed === ###'

    step('\n### === modifying version for the 8th ntp association test passed'
         ' === ###')
    step('\n### === modifying version for the 8th ntp association test end '
         '=== ###')


def ntp_del_server(dut, step):
    step('\n### === server deletion test start === ###')
    dut("configure terminal")
    dut("no ntp server 8.8.8.8")
    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    count = count + 1
    for line in lines:
        if ("8.8.8.8" in line):
           '\n### server still present as per show cli - failed ###'
           count = count - 1

    ''' now check the running config '''
    count = count + 1
    dump = dut("show running-config")
    lines = dump.splitlines()
    for line in lines:
        if ("ntp server 8.8.8.8" in line):
            '\n### server still present in running config - failed ###'
            count = count - 1

    assert count == 2,\
            '\n### server deletion test failed ###'

    step('\n### server deletion test passed ###')
    step('\n### === server deletion test end === ###\n')


def ntp_add_server_with_long_server_name(dut, step):
    step('\n### === server (with long server name) addition test start === '
         '###')
    dut("configure terminal")
    count = 0

    ''' long server name '''
    lines = dut("ntp server vabcdefghijklmnopqrstuvwxyzeabcdefghijklmnopqrstuvwxyzrabcdefghijklmnopqrstuvwxy version 4 prefer")
    if "NTP server name should be less than 57 characters" in lines:
        count += 1
    assert count == 1,\
            '\n###  server (with max chars with server name) addition test failed'\
            ' ###'

    dut("ntp server 1.cr.pool.ntp.org version 4 prefer")
    dut("ntp server abcdefghijklmnopqrstuvwxyz")
    dut("ntp server 192.168.101.125")

    ''' short server name '''
    dut("ntp server aaa")

    dut("end")
    dump = dut("show ntp associations")
    lines = dump.splitlines()
    count = 0
    for line in lines:
        if ("1.cr.pool.ntp.org" in line):
            count = count + 1
        if ("abcdefghijklmnopqrstuvwxyz" in line):
            count = count + 1
        if ("192.168.101.125" in line):
            count = count + 1
        if ("aaa" in line):
            count = count + 1

    ''' clean up '''
    dut("configure terminal")
    dut("no ntp server 1.cr.pool.ntp.org")
    dut("no ntp server abcdefghijklmnopqrstuvwxyz")
    dut("no ntp server 192.168.101.125")
    dut("no ntp server aaa")
    dut("exit")

    assert count == 4,\
            '\n###  server (with long server name) addition test failed'\
            ' ###'

    step('\n### server (with long server name) addition test passed ###')
    step('\n### === server (with long server name) addition test end === ###'
         '\n')


@mark.gate
def test_ct_ntp_config(topology, step):
    ops1 = topology.get("ops1")
    assert ops1 is not None

    ntp_auth_enable_disable_config(ops1, step)

    ntp_valid_auth_key_add(ops1, step)

    ntp_invalid_auth_key_add(ops1, step)

    ntp_short_pwd_add(ops1, step)

    ntp_tool_on_gpwd_add(ops1, step)

    ntp_add_server_no_options(ops1, step)

    ntp_add_server_prefer_option(ops1, step)

    ntp_add_server_valid_version_option(ops1, step)

    ntp_add_server_invalid_version_option(ops1, step)

    ntp_add_server_with_long_server_name(ops1, step)

    ntp_add_server_with_invalid_server_name(ops1, step)

    ntp_add_server_key_id_option(ops1, step)

    ntp_add_server_all_options(ops1, step)

    ntp_add_more_than_8_servers(ops1, step)

    ntp_modify_8th_ntp_server(ops1, step)

    ntp_del_server(ops1, step)

    ntp_add_server_with_fqdn(ops1, step)
