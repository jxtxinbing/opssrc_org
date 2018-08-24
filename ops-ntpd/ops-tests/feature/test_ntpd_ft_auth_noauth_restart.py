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
from time import sleep
from pytest import mark
TOPOLOGY = """

# +--------+     +---------+     +---------+
# |        |     |         <----->   hs1   |
# |        |     |         |     +---------+
# |  ops1  <----->   sw1   |
# |        |     |         |     +---------+
# |        |     |         <----->   hs2   |
# +--------+     +---------+     +---------+

# Nodes
[type=openswitch name="Switch 1"] ops1
[type=pvos_switch name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:1 -- sw2:1
hs2:1 -- sw2:2
[force_name=eth0] ops1:eth0
ops1:eth0 -- sw2:3
"""
# Global Variable
MGMT_IP_CONFIG = "172.17.0.1/24"
WORKSTATION_IP_ADDR_SER1 = "172.17.0.2"
WORKSTATION_IP_ADDR_SER2 = "172.17.0.3"
global SERVER_UNREACHABLE


def ntp_config(ops1, wrkston01, wrkston02, step):
    step("Step to configure ntp")
    global SERVER_UNREACHABLE
    step("CONFIGURING WS1 AND WS2 AS LOCAL NTP SERVER WITH AND WITHOUT AUTH")
    command = "echo \"authenticate yes\" >> /etc/ntp.conf"
    wrkston01(command, shell="bash")
    cmd = "ntpd -c /etc/ntp.conf"
    wrkston01(cmd, shell="bash")
    wrkston02(cmd, shell="bash")
    sleep(30)
    out = wrkston01("ntpq -p -n", shell="bash")
    if ".INIT." in out or "Connection refused" in out:
        SERVER_UNREACHABLE = True
    else:
        SERVER_UNREACHABLE = False
    out = wrkston02("ntpq -p -n", shell="bash")
    if SERVER_UNREACHABLE is False:
        if ".INIT." in out or "Connection refused" in out:
            SERVER_UNREACHABLE = True
        else:
            SERVER_UNREACHABLE = False
    with ops1.libs.vtysh.Configure() as ctx:
        ctx.ntp_authentication_key_md5("55", "secretpassword")
        ctx.ntp_trusted_key("55")
        ctx.ntp_authentication_enable()
        ctx.ntp_server_key_id(WORKSTATION_IP_ADDR_SER1, "55")
        ctx.ntp_server_prefer(WORKSTATION_IP_ADDR_SER2)


def validate_ntp_assoc_info(ops1, wrkston01, wrkston02, step):
    step("Step to validate ntp association info")
    out = ops1("show ntp associations", shell="vtysh")
    assert WORKSTATION_IP_ADDR_SER1 in out
    assert WORKSTATION_IP_ADDR_SER2 in out
    lines = out.split('\n')
    for line in lines:
        if WORKSTATION_IP_ADDR_SER1 in line:
            assert ('.NKEY.' or '.TIME.' or '.RATE.' or '.AUTH.') not in line,\
                "### NTP client has incorrect information###\n"
        if WORKSTATION_IP_ADDR_SER2 in line:
            assert ('.NKEY.' or '.TIME.' or '.RATE.' or '.AUTH.') not in line,\
                "### NTP client has incorrect information###\n"
    return True


def validate_ntp_status(ops1, wrkston01, wrkston02, step):
    step("Step to validate ntp status")
    out = ops1("show ntp status", shell="vtysh")
    if 'Synchronized' in out:
        return True
    return False


def restart_ntp_daemon(ops1, wrkston01, wrkston02, step):
    step("Step to restart ntp daemon")
    ops1("systemctl restart ops-ntpd", shell="bash")
    sleep(60)
    output = ops1("ps -ef | grep ntpd", shell="bash")
    assert 'ntpd -I' in output


def chk_ntp_association_status(ops1, wrkston01, wrkston02, step):
    step("Step to validate ntp association status")
    global SERVER_UNREACHABLE
    total_timeout = 600
    timeout = 10
    check1 = False
    check2 = False
    for t in range(0, total_timeout, timeout):
        sleep(5)
        if check1 is False:
            check1 = validate_ntp_assoc_info(ops1, wrkston01, wrkston02, step)
        if check2 is False:
            check2 = validate_ntp_status(ops1, wrkston01, wrkston02, step)
    if check1 is True and check2 is True:
        return True
    else:
        return False
    if SERVER_UNREACHABLE is True:
        ops1("show ntp status", shell="vtysh")
        ops1("show ntp associations", shell="vtysh")
        wrkston01("ntpq -p -n", shell="bash")
        wrkston02("ntpq -p -n", shell="bash")
        return True
    print('### TIMEOUT TEST CASE FAILED ###\n')
    ops1("show ntp status", shell="vtysh")
    ops1("show ntp associations", shell="vtysh")
    wrkston01("ntpq -p -n", shell="bash")
    wrkston02("ntpq -p -n", shell="bash")
    return False


@mark.timeout(1500)
@mark.platform_incompatible(['docker'])
def test_ntpd_ft_auth_noauth_restart(topology, step):
    step("Test case for test_ntpd_ft_auth_noauth_restart validation")
    ops1 = topology.get('ops1')
    sw2 = topology.get('sw2')
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')
    assert ops1 is not None
    assert sw2 is not None
    assert hs1 is not None
    assert hs2 is not None

    # Configure DUT's management interface IP address
    with ops1.libs.vtysh.ConfigInterfaceMgmt() as ctx:
        ctx.ip_static(MGMT_IP_CONFIG)

    # Configure host IP addresses
    hs1_ip = WORKSTATION_IP_ADDR_SER1 + "/24"
    hs2_ip = WORKSTATION_IP_ADDR_SER2 + "/24"

    hs1.libs.ip.interface("1", '{}'.format(hs1_ip), up=True)
    hs2.libs.ip.interface("1", '{}'.format(hs2_ip), up=True)

    mgmtintdetails = ops1.libs.vtysh.show_interface_mgmt()
    switch_ip = mgmtintdetails['ipv4'].split('/')[0]

    # Connectivity test
    ping = hs1.libs.ping.ping(5, switch_ip)
    assert ping['received'] > 0, "Ping failed between\
        host1 and the DUT"

    ping = hs2.libs.ping.ping(5, switch_ip)
    assert ping['received'] > 0, "Ping failed between\
        host2 and the DUT"

    # Configure NTP server profile and check the status
    ntp_config(ops1, hs1, hs2, step)
    status = chk_ntp_association_status(ops1, hs1, hs2, step)
    assert status is True

    # restart the ntpd daemon and check ntp status
    restart_ntp_daemon(ops1, hs1, hs2, step)
    status = chk_ntp_association_status(ops1, hs1, hs2, step)
    assert status is True
