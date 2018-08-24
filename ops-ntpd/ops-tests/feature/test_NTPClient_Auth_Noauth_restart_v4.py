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


from pytest import mark
from time import sleep
from re import search


TOPOLOGY = """
# +--------+         +--------+
# |        |eth0     |        |
# |  hs2   +---------+  ops1  |
# |        |     eth1|        |
# +--------+         +-+------+
#                      |eth0
#                      |
#                      |eth0
#                  +---+----+
#                  |        |
#                  |  hs1   |
#                  |        |
#                  +--------+

# Nodes
[type=openswitch name="OpenSwitch 1"] ops1
[type=oobmhost name="Host 1" image="openswitch/ubuntu_ntp:latest"] hs1
[type=oobmhost name="Host 2" image="openswitch/ubuntu_ntp:latest"] hs2

# Links
[force_name=oobm] ops1:eth0
[force_name=oobm] ops1:eth1
ops1:eth0 -- hs1:eth0
ops1:eth1 -- hs2:eth0
"""

# Local Variables
MD5_PASSWORD = 'secretpassword'
KEY_ID = 55
packets = 5
TOTAL_TIMEOUT = 1020
TIMEOUT = 5
NTP_SERVER = 'time.apple.com'
HS1_IP = ''
HS2_IP = ''
OPS_IP = ''


def ops_ntp_servers_config(hs1, hs2, ops1, step):

    global HS1_IP
    global HS2_IP
    global OPS_IP

    out = hs1("ntpq -p -n")
    #check if the public NTP server is reachable fot the local NTP server
    assert "Connection refused" not in out, \
        "NTP service is not running on the NTP servr 1"

    #retrieve the IP address of the workstation 1
    ifConfigCmdOut = hs1("ifconfig eth0")
    target = (r"inet addr:(?P<IP4>[\d\.]+)\s")
    result = search(target, ifConfigCmdOut)
    result = result.groupdict()
    HS1_IP = result["IP4"]
    step("### NTP server 2 IP address: %s\n" % HS2_IP)

    out = hs2("ntpq -p -n")
    assert "Connection refused" not in out, \
        "NTP service is not running on the NTP servr 2"

    #retrieve the IP address of the workstation 2
    ifConfigCmdOut = hs2("ifconfig eth0")
    target = (r"inet addr:(?P<IP4>[\d\.]+)\s")
    result = search(target, ifConfigCmdOut)
    result = result.groupdict()
    HS2_IP = result["IP4"]
    step("### NTP server 2 IP address: %s\n" % HS2_IP)

    #retrieve the IP address of the OPS
    ifConfigCmdOut = ops1("ifconfig eth0", shell='bash')
    target = (r"inet addr:(?P<IP4>[\d\.]+)\s")
    result = search(target, ifConfigCmdOut)
    result = result.groupdict()
    OPS_IP = result["IP4"]
    step("### Openswitch IP address: %s\n" % OPS_IP)


# Function that configures the host's IP address and ntpd for authentication
def set_host_ntpd(hs1, hs2, ntp_server, key_id, md5_password, step):
    step("Configure host1 with auth and host2 without auth")

    out = hs1("/etc/init.d/ntp stop")
    assert 'OK' in out, "ntp stop command failed for host1"

    hs1.libs.ntpd.add_ntp_server(ntp_server)

    hs1.libs.ntpd.add_trustedkey(key_id)

    hs1.libs.ntpd.add_trustedkey_password(key_id,
                                          md5_password)

    hs1.libs.ntpd.ntpd_config_files(True, key_id)

    out = hs1("/etc/init.d/ntp start")
    assert 'OK' in out, "ntp start command failed for host1"

    out = hs2("/etc/init.d/ntp stop")
    assert 'OK' in out, "ntp stop command failed for host2"

    hs2.libs.ntpd.add_ntp_server(ntp_server)

    out = hs2("/etc/init.d/ntp start")
    assert 'OK' in out, "ntp start command failed for host2"


# Function that checks connectivity between host and DUT
def verify_connectivity_host(hs1, hs2, ops_ip, packets, step):
    step("Test ping between host and DUT")
    ping_hs1 = hs1.libs.ping.ping(packets, ops_ip)
    assert ping_hs1['received'] > 3, (
        "Total of received packets is below the expected, " +
        "Expected: {}".format(packets)
    )
    ping_hs2 = hs2.libs.ping.ping(packets, ops_ip)
    assert ping_hs2['received'] > 3, (
        "Total of received packets is below the expected, " +
        "Expected: {}".format(packets)
    )


# Function that enable or disable NTP authentication on switch
def set_ntp_authentication(ops1, step, auth_enabled=True):
    if auth_enabled:
        step("Enable NTP authentication")
        with ops1.libs.vtysh.Configure() as ctx:
            ctx.ntp_authentication_enable()
    else:
        step("Disable NTP authentication")
        with ops1.libs.vtysh.Configure() as ctx:
            ctx.no_ntp_authentication_enable()


# Function to set the NTP authentication-keys on switch
def set_ntp_authentication_keys(ops1, key_id, md5_password):
    print("Add NTP authentication key: %d" % key_id)
    with ops1.libs.vtysh.Configure() as ctx:
        ctx.ntp_authentication_key_md5(key_id, md5_password)
        ctx.ntp_trusted_key(key_id)


# Function to set a key-id in NTP server profile
def set_ntp_server_with_key(ops1, hs1_ip, key_id):
    print("Add NTP server {} with authentication key {}".
          format(hs1_ip, key_id))
    with ops1.libs.vtysh.Configure() as ctx:
        ctx.ntp_server_key_id(hs1_ip, key_id)


# Function to add the NTP server to DUT's configuration
def set_ntp_servers(ops1, hs1_ip, key_id, md5_password, hs2_ip, step):
    step("Adding NTP servers to the OPS")
    set_ntp_authentication_keys(ops1, key_id, md5_password)
    set_ntp_server_with_key(ops1, hs1_ip , key_id)


# Function that changes the preferred NTP server
def set_ntp_server_prefer(ops1, hs2_ip):
    with ops1.libs.vtysh.Configure() as ctx:
        ctx.ntp_server_prefer(hs2_ip)


# Function that checks if NTP authentication-keys are set correctly
def check_ntp_authentication_keys(ops1, key_id, md5_password, step):
    step("Check NTP authentication keys")
    show_ntp_auth_keys_re = ops1.libs.vtysh.show_ntp_authentication_key()
    assert str(key_id) in show_ntp_auth_keys_re, (
        "KEY_ID not included in show ntp authentication-keys command, " +
        "Expected: %d" % key_id
    )

    assert show_ntp_auth_keys_re[str(key_id)]['md5_password'] \
         == md5_password,\
        "MD5 password value is not the expected, Expected: %s" % md5_password


# Function that checks if NTP trusted keys are set correctly
def check_ntp_trusted_keys(ops1, key_id, step):
    step("Check NTP trusted keys")
    show_ntp_trusted_keys_re = ops1.libs.vtysh.show_ntp_trusted_keys()
    assert str(key_id) in show_ntp_trusted_keys_re, (
        "KEY_ID not included in show NTP trusted-keys command, " +
        "Expected: %d" % key_id
        )


# Function that validates if switch is synchronized with NTP server
def validate_ntp_status(ops1, hs1_ip, hs2_ip):
    show_ntp_status_re = ops1.libs.vtysh.show_ntp_status()
    assert show_ntp_status_re['authentication_status'] == 'enabled', (
        "Authentication status is not the expected, Expected: enabled"
    )
    if 'server' in show_ntp_status_re:
        if show_ntp_status_re['server'] == hs1_ip or \
           show_ntp_status_re['server'] == hs2_ip :
            return True
    else:
        return False


# Function that validates if an NTP association is properly added
def validate_ntp_associations(ops1):
    show_ntp_assoc_re = ops1.libs.vtysh.show_ntp_associations()
    for key in show_ntp_assoc_re.keys():
        code = show_ntp_assoc_re[key]['code']
        if code == '*':
            return True
    return False


# Function that checks if switch synchronized with NTP server or not
def check_ntp_status_and_associations(ops1, hs1_ip, hs2_ip, total_timeout, timeout, step):
    step("Check NTP status and NTP associations")

    check_status = False
    check_associations = False
    for t in range(0, total_timeout, timeout):
        # Timeout check for each iteration
        sleep(timeout)
        if check_status is False:
            check_status = validate_ntp_status(ops1, hs1_ip, hs2_ip)
        if check_associations is False:
            check_associations = validate_ntp_associations(ops1)
        if check_status is True and check_associations is True:
            return True

    assert check_status is True and check_associations is True, (
        "Timeout occurred. DUT didn't synch with NTP server"
    )


def restart_ntp_daemon(ops1, step):
    step("### Verifying the NTPD restartability ###")
    ops1("systemctl restart ops-ntpd", shell='bash')
    sleep(30)
    out = ops1("ps -ef | grep ntpd", shell='bash')
    assert'ntpd -I eth0 -c' in out, "### OPS-NTPD Daemon restart failed ###\n"


@mark.gate
@mark.timeout(1200)
@mark.platform_incompatible(['ostl'])
def test_authentication_enabled_keys(topology, step):
    """
    Connect max. NTP servers with authentication enabled and keys
    """
    ops1 = topology.get('ops1')
    hs1 = topology.get('hs1')
    hs2 = topology.get('hs2')

    assert ops1 is not None
    assert hs1 is not None
    assert hs2 is not None

    # Configure host ntpd process
    set_host_ntpd(hs1, hs2, NTP_SERVER, KEY_ID, MD5_PASSWORD, step)

    # get OPS and ntp server IPs
    ops_ntp_servers_config(hs1, hs2, ops1, step)

    # Connectivity test
    verify_connectivity_host(hs1, hs2, OPS_IP, packets, step)

    # Enable authentication
    set_ntp_authentication(ops1, step)

    # Configure NTP server profile with authentication-key
    set_ntp_servers(ops1, HS1_IP, KEY_ID, MD5_PASSWORD, HS2_IP, step)

    # Set last NTP server as preferred
    set_ntp_server_prefer(ops1, HS2_IP)

    # Check show NTP authentication-keys command
    check_ntp_authentication_keys(ops1, KEY_ID, MD5_PASSWORD, step)

    # Check show NTP authentication-keys command
    check_ntp_trusted_keys(ops1, KEY_ID, step)

    # Check show commands with authentication enabled
    check_ntp_status_and_associations(ops1, HS1_IP, HS2_IP, TOTAL_TIMEOUT, TIMEOUT, step)

    # restart NTP daemon on the OPS
    restart_ntp_daemon(ops1, step)

    # Check show commands with authentication enabled
    check_ntp_status_and_associations(ops1, HS1_IP, HS2_IP, TOTAL_TIMEOUT, TIMEOUT, step)
