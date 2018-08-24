# (C) Copyright 2016 Hewlett Packard Enterprise Development LP
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

from pytest import mark
import uuid

TOPOLOGY = """
#
# +-------+
# |  sw1  |
# +-------+
#

# Nodes
[type=openswitch name="Switch 1"] sw1
"""


def check_show_tech_list(sw1):
    print("\n############################################")
    print("1.1 Running Show Tech List Test")
    print("############################################\n")

    # Run Show Tech List Command
    output = sw1("show tech list")

    assert "Show Tech Supported Features List" in output


def check_show_tech(sw1):
    print("\n############################################")
    print("1.2 Running Show Tech Test")
    print("############################################\n")

    # Run Show Tech Command
    output = sw1("show tech")

    assert "Show Tech commands executed successfully" in output


def check_show_tech_feature(sw1):
    print("\n############################################")
    print("1.3 Running Show tech Feature Test ")
    print("############################################\n")

    outputfile = str(uuid.uuid4()) + ".txt"

    # Run Show Tech basic Command and store output to file
    sw1._timeout = 360
    output = sw1("show tech basic localfile " + outputfile)
    sw1._timeout = -1
    # Read the file and check the output
    output = sw1("cat /tmp/" + outputfile +
                 " | grep 'Show Tech commands executed successfully'",
                 shell="bash")
    assert "Show Tech commands executed successfully" in output


def check_show_tech_sub_feature(sw1):
    print("\n############################################")
    print("1.4 Running Show tech Sub Feature Test ")
    print("############################################\n")

    # Run Show Tech lldp statistics Command
    output = sw1("show tech lldp statistics")

    assert "Show Tech commands executed successfully" in output


def check_show_tech_to_file(sw1):
    print("\n############################################")
    print("1.5 Running Show tech to File ")
    print("############################################\n")
    outputfile = str(uuid.uuid4()) + ".txt"

    # Run Show Tech Command and store output to file
    sw1._timeout = 360
    output = sw1("show tech localfile " + outputfile)
    sw1._timeout = -1
    # Read the file and check the output
    output = sw1("cat /tmp/" + outputfile +
                 " | grep 'Show Tech commands executed successfully'",
                 shell="bash")
    assert "Show Tech commands executed successfully" in output


def check_show_tech_feature_lag(sw1):
    print("\n############################################")
    print("1.7 Running Show tech Feature LAG Test ")
    print("############################################\n")

    # Run Show Tech LAG Command
    output = sw1("show tech LAG")

    assert "Show Tech commands executed successfully" in output


def check_invalid_command_failure(sw1):
    print("\n############################################")
    print("2.1 Running Show tech Cli Command Failure")
    print("############################################\n")

    # Backup the Default Yaml File
    command = "cp /etc/openswitch/supportability/ops_showtech.yaml \
    /etc/openswitch/supportability/ops_showtech.yaml2 "
    output = sw1(command, shell="bash")

    command = "ls /etc/openswitch/supportability "
    output = sw1(command, shell="bash")

    # Add Test Feature with invalid show command (feature_name: test1234)
    command = "printf '\n  feature:\n  -\n    feature_desc: \"sttest\"\n\
    feature_name: test1234\n    cli_cmds:\n      - \"show testing\"' >> \
     /etc/openswitch/supportability/ops_showtech.yaml"
    output = sw1(command, shell="bash")

    # Run Show Tech test1234 Command
    output = sw1("show tech test1234")

    sw1("mv \
    /etc/openswitch/supportability/ops_showtech.yaml2 \
    /etc/openswitch/supportability/ops_showtech.yaml", shell="bash")

    assert "% Unknown command." in output


def check_show_tech_invalid_parameters(sw1):
    print("\n#################################################")
    print("2.2 Running Show tech Command with extra Parameter ")
    print("##################################################\n")

    # Run Show Tech lldp statistics Command
    output = sw1("show tech lldp statistics extraparameter")

    assert "% Unknown command" in output


def check_show_tech_un_supported_feature(sw1):
    print("\n#########################################################")
    print("2.3 Running Show tech Command with Unsupported Feature Name ")
    print("############################################################\n")

    # Run Show Tech Unsupported Command
    output = sw1("show tech  !@#$%^&*((QWERTYUIOPLFDSAZXCVBNM<>)(&^%$#!")

    assert "Unknown command" in output


def check_show_tech_un_supported_sub_feature(sw1):
    print("\n#########################################################")
    print("2.4 Running Show tech Command with Unsupported Sub Feature Name ")
    print("############################################################\n")

    output = sw1("show tech lldp !@#$%^&*((QWERTYUIOPLFDSAZXCVBNM<>)(&^%$#!")

    assert "Sub Feature !@#$%^&*((QWERTYUIOPLFDSAZXCVBNM<>)" \
           "(&^%$#! is not supported" in output


def check_show_tech_un_supported_feature_and_sub_feature(sw1):
    print("\n#########################################################")
    print("2.5 Running Show tech Command with Unsupported Feature and \
          Sub Feature Name ")
    print("############################################################\n")

    output = sw1("show tech !@#$%^&*^%$#! !@#$%^&*^%$#!")

    assert "Sub Feature !@#$%^&*^%$#! is not supported" in output


def show_tech_config_duplicate_entries_test(sw1):
    print("\n############################################")
    print("3.3 Running Show Tech Duplicated Config Entries Test")
    print("############################################\n")
    # Variables
    command = "cp /etc/openswitch/supportability/ops_showtech.yaml\
     /etc/openswitch/supportability/ops_showtech.yaml2 "
    output = sw1(command, shell="bash")

    command = "printf '\n  feature:\n  -\n    feature_desc: \"sttest\"\n\
    feature_name: test1234\n    cli_cmds:\n      - \"show testing\"' >> \
     /etc/openswitch/supportability/ops_showtech.yaml"

    sw1(command, shell="bash")
    sw1(command, shell="bash")
    sw1(command, shell="bash")
    sw1._timeout = 360
    output = sw1("show tech basic")
    sw1._timeout = -1
    sw1("mv \
    /etc/openswitch/supportability/ops_showtech.yaml2 \
    /etc/openswitch/supportability/ops_showtech.yaml", shell="bash")

    assert "Show Tech commands executed successfully" in output


def show_tech_feature_version_test(sw1):
    print("\n############################################")
    print("5.0 Running Show tech Feature Versioning Test ")
    print("############################################\n")

    # Run Show Tech Versioning Command
    output = sw1("show tech version")

    assert "Show Tech commands executed successfully" in output


def check_show_tech_feature_ntp(sw1):
    print("\n############################################")
    print("4.0 Running Show tech Feature NTP Test ")
    print("############################################\n")

    # Run Show Tech NTP Command
    output = sw1("show tech ntp")

    assert "Show Tech commands executed successfully" in output


def check_show_tech_feature_unicast_routing(sw1):
    print("\n##################################################")
    print("7.0 Running Show tech Feature Unicast Routing Test ")
    print("##################################################\n")

    # Run Show Tech UCast Routing Command
    output = sw1("show tech ucast-routing")

    # Verify if the expected cli commands for u-cast routing is seen in the
    # output buffer
    expected_commands = ['show ip route',
                         'show ipv6 route',
                         'show rib',
                         'show ip interface',
                         'show ipv6 interface',
                         'show arp',
                         'show ipv6 neighbors',
                         'show ip ecmp']

    for command in expected_commands:
        assert command in output, "Failed to run 'show tech ucast-routing"


@mark.gate
def test_showtech(topology, step):
    sw1 = topology.get('sw1')

    assert sw1 is not None

    step("Positive TestCases")
    check_show_tech_list(sw1)

    # removing show tech test case since it is redundant to show tech localfile
    # check_show_tech(sw1)

    check_show_tech_feature(sw1)

    # def test_show_tech_subfeature(self):
    #    assert(check_show_tech_sub_feature(sw1))

    check_show_tech_to_file(sw1)

    step("Failure Test Cases")
    check_invalid_command_failure(sw1)

    check_show_tech_invalid_parameters(sw1)

    check_show_tech_un_supported_feature(sw1)

    # def test_unsupported_subfeature(self):
    #   global sw1
    #    assert(check_show_tech_un_supported_sub_feature(sw1))

    # def test_unsupported_feature_and_subfeature(self):
    #    assert(check_show_tech_un_supported_feature_and_sub_feature(sw1))

    step("Destructive Test Cases")

    show_tech_config_duplicate_entries_test(sw1)

    # check_show_tech_feature_ntp(sw1)

    # show_tech_feature_version_test(sw1)

    check_show_tech_feature_unicast_routing(sw1)
