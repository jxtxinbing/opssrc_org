# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
OpenSwitch Test for Core Dump.
List of Test Cases
    1. Crash a Daemon in the switch and verify the following
        a. Post Crash Processing (Event Generation)
        b. Show Core Dump
        c. Copy Core Dump
"""

from pytest import mark
from time import sleep
# from .helpers import wait_until_interface_up
import random
import string

TOPOLOGY = """

#  +---------+       +--------+
#  |         |       |        |
#  |   sw1   |<----->|  hs1   |
#  |         |       |        |
#  +---------+       +--------+

# Nodes
[type=openswitch name="Switch 1"] sw1
[type=host name="Host 1"] hs1

# Ports
[force_name=oobm] sw1:sp1

# Links
sw1:sp1 -- hs1:if01
"""

# Helper Functions


def _run_dummy_daemon(switch):
    """
    Creates a dummy daemon by copying watch binary to a random name
    and runs is as a daemon with the help of nohup

    :return: Dummy daemon name
    """
    name_size = 12
    daemon_name = ''.join(random.SystemRandom().
                          choice(string.ascii_letters + string.digits)
                          for _ in range(name_size))
    watch_name = switch('which watch', shell='bash')
    switch('cp ' + watch_name + ' /usr/bin/' + daemon_name, shell='bash')
    switch('nohup %s ls&' % (daemon_name), shell='bash')
    return daemon_name


def _crash_dummy_daemon(switch, signal, daemon_name):
    """
    Crashes the specified daemon_name using the given signal
    """
    assert switch is not None
    assert daemon_name is not None
    assert signal is not None

    """
     get_pid = switch('ps -C %s -opid h' % (daemon_name), shell='bash')
    switch('kill -%s %s' % (signal, get_pid), shell='bash')

    """
    switch('killall -%s %s' % (signal, daemon_name), shell='bash')
    # wait for 2 seconds
    sleep(2)


def _check_event_log(switch, signal, daemon_name):
    """
    Verifies that a event has been logged in the event logging system for
    the crash of the given daemon and given signal
    :param switch:
    :param daemon_name:
    :return:
    """
    assert switch is not None
    assert daemon_name is not None
    assert signal is not None

    signal = int(signal)
    strsignal = ("Unknown signal", "Hangup", "Interrupt", "Quit",
                 "Illegal instruction", "Trace/breakpoint trap", "Aborted",
                 "Bus error", "Floating point exception", "Killed",
                 "User defined signal 1", "Segmentation fault",
                 "User defined signal 2", "Broken pipe", "Alarm clock",
                 "Terminated", "Stack fault", "Child exited", "Continued",
                 "Stopped (signal)", "Stopped", "Stopped (tty input)",
                 "Stopped (tty output)", "Urgent I/O condition",
                 "CPU time limit exceeded", "File size limit exceeded",
                 "Virtual timer expired", "Profiling timer expired",
                 "Window changed", "I/O possible", "Power failure",
                 "Bad system call")

    if signal >= len(strsignal):
        signal = 0

    # Event Message Format : {daemon_name} crashed due to
    find_event = (
        'cat /var/log/event.log |'
        ' grep "|14001|" |'
        ' grep "%s crashed due to %s"' %
        (daemon_name, strsignal[signal])
    )
    evnt_string = switch(find_event, shell='bash')
    print("Event Str Beg " + evnt_string + "Event Str End")
    if "crashed" in evnt_string and "ops-evt" in evnt_string:
        return True
    else:
        return False


@mark.gate
@mark.timeout(1800)
@mark.platform_incompatible(['docker'])
def test_core_dump(topology):
    """
    Verifies that a crash event log is generated whenever
    a daemon crashes.
    This test doesn't run on docker.

    :param topology:
    :return: None
    """
    no_of_retries = 3
    retry_instance = 0
    sw1 = topology.get('sw1')
    signal = '11'

    assert sw1 is not None

    daemon_name = _run_dummy_daemon(sw1)

    _crash_dummy_daemon(sw1, signal, daemon_name)

    retval = _check_event_log(sw1, signal, daemon_name)

    iter = 0
    while iter < 5:
        clean_buffer = sw1("touch /tmp/temp.sb", shell='bash')
        iter += 1
        sleep(1)

    while retry_instance < no_of_retries:
        if retval:
            break
        sleep(2)
        retval = _check_event_log(sw1, signal, daemon_name)
        retry_instance += 1

    sw1('rm /usr/bin/' + daemon_name, shell='bash')

    if retry_instance == no_of_retries:
        print("Event Log not found for crash event")
        print(clean_buffer)
        assert False
    else:
        assert True

    print("Crash Event Log passed")
    # Verify that the show core dump displays the new core dump
    iter = 0
    while iter < 5:
        clean_buffer = sw1("touch /tmp/temp.sb", shell='bash')
        iter += 1
        sleep(1)
    sleep(5)
    scd = sw1.libs.vtysh.show_core_dump()
    print(str(scd))
    no_of_core_dumps = len(scd)
    if no_of_core_dumps < 1:
        assert False

    show_cor_dump_found = 0
    instance_id_value = 0
    i = 0
    while i < no_of_core_dumps:
        if daemon_name in scd[i]['daemon_name']:
            show_cor_dump_found = 1
            instance_id_value = scd[i]['instance_id']
            print("Show core dump passed")
            break
        i += 1

    # hs1('instance_id_value', shell='bash')
    assert show_cor_dump_found

    # copy core dump check <copy core dump function have multiple parameter

    # switch and host config initial
    hs1 = topology.get('hs1')
    assert hs1 is not None

    # Configure IP and bring UP host 1 interfaces
    try:
        hs1('ip addr flush eth1')
        hs1.libs.ip.interface('if01', addr='10.0.12.1/24', up=True)

        # Configure IP and bring UP switch 1 interfaces
        with sw1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
            ctx.ip_static('10.0.12.2/24')
    except:
        print("Exception while setting the ip")

    print(str(sw1.libs.vtysh.show_running_config()))
    sleep(25)
    ping = hs1.libs.ping.ping(1, '10.0.12.2')
    print("ping-transmitted : " + str(ping['transmitted']))
    print("ping-received : " + str(ping['received']))

    hs1('chmod 777 /var/lib/tftpboot', shell='bash')
    hs1('touch /var/lib/tftpboot/abc.xz', shell='bash')
    hs1('chmod 777 /var/lib/tftpboot/abc.xz', shell='bash')

    # switch's core dump file size
    core_dump_size_switch = sw1(
        'stat -c "%s" /var/lib/systemd/coredump/core.' +
        daemon_name +
        '.*.xz',
        shell='bash')

    print("size_begin " + core_dump_size_switch + " size_end")
    cddata = core_dump_size_switch.splitlines()
    print("cddata : " + str(len(cddata)))

    for data in cddata:
        print("cd " + data)

    # Workaround for framework echo after crash issue

    core_dump_size_switch_int = int(cddata[len(cddata)-1])

    assert core_dump_size_switch_int
    assert instance_id_value

    scd = sw1.libs.vtysh.copy_core_dump(daemonname=daemon_name,
                                        instance_id=instance_id_value,
                                        transport='tftp',
                                        serveraddress='10.0.12.1',
                                        filename='abc.xz')
    length_of_result = len(scd)
    if length_of_result < 1:
        assert False

    print("status : " + scd['status'])
    print("reason : " + scd['reason'])

    core_dump_copied = 0
    if scd['status'] == 'success':
        core_dump_copied = 1
    else:
        core_dump_copied = 0

    assert core_dump_copied

    # STEP-2 login to host and check file present or not abc.xz

    comand_output = hs1(
        'stat -c "%s %n" /var/lib/tftpboot/abc.xz',
        shell='bash')
    if "No such file or directory" in comand_output:
        assert False

    # STEP-3 confirm desire file present or not

    # STPE-4 Check file size is not Zero. [optional]
    core_dump_size_host = hs1('stat -c "%s" /var/lib/tftpboot/abc.xz',
                              shell='bash')

    if "No such file or directory" in core_dump_size_host:
        assert False
    else:
        core_dump_size_host_int = int(core_dump_size_host)

    assert core_dump_size_host_int

    # compare size of core dump in switch and host

    equal_size_check = 0

    if core_dump_size_switch_int != core_dump_size_host_int:
        equal_size_check = 0
    else:
        equal_size_check = 1

    assert equal_size_check

    # STEP-6 delete the core dump from host-machine
    hs1('rm -f /var/lib/tftpboot/abc.xz', shell='bash')

    # clean up the core dumps
    sw1('rm -f /var/diagnostics/coredump/core.' +
        daemon_name + '.*.xz', shell='bash')

    # assert 0
