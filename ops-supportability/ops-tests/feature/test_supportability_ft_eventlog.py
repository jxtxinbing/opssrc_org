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

TOPOLOGY = """
#
# +-------+
# |  sw1  |
# +-------+
#

# Nodes
[type=openswitch name="Switch 1"] sw1
"""


# Negative test case for show events severity filter
def evtlogfilter_severity_cli(sw1):
    print("\n############################################")
    print(" Running Event Log Test Script")
    print("############################################\n")

    # enable lldp
    sw1("configure terminal")
    sw1("lldp enable")
    # disable lldp
    sw1("no lldp enable")
    sw1("lldp timer 200")
    sw1("end")

    print("-"*10)
    print("=====----")
    print("-"*10)

    output = sw1("show events severity emer")

    assert "No event match the filter provided" in output


# Negative test case for show events category filter
def evtlogfilter_category_cli(sw1):
    print("\n############################################")
    print(" Running Event Log Test Script")
    print("############################################\n")

    # enable lldp
    sw1("configure terminal")
    sw1("lldp enable")
    # disable lldp
    sw1("no lldp enable")
    sw1("lldp timer 200")
    sw1("end")

    print("-"*10)
    print("=====----")
    print("-"*10)

    output = sw1("show events category abc")

    assert "% Unknown command." in output


# Negative test case for show events event id filter
def evtlogfilter_event_id_cli_fail(sw1):
    print("\n############################################")
    print(" Running Event Log Test Script 1.2")
    print("############################################\n")

    print("-"*10)
    print("=====----")
    print("-"*10)
    output = sw1("show events event-id 999998")

    assert "No event has been logged in the system" in output


# Positive test case for show events event id filter
def evtlogfilter_event_id_cli_pass(sw1):
    print("\n############################################")
    print(" Running Event Log Test Script 1.1")
    print("############################################\n")

    # enable lldp
    sw1("configure terminal")
    sw1("lldp enable")
    # disable lldp
    sw1("no lldp enable")
    sw1("lldp timer 100")
    sw1("end")

    print("-"*10)
    print("=====----")
    print("-"*10)

    output = sw1("show events event-id 1003")

    assert "Configured LLDP tx-timer with" and "LLDP Disabled" not in output


def evtlogfeature_cli(sw1):
    print("\n############################################")
    print(" Running Event Log Test Script")
    print("############################################\n")

    # enable lldp
    sw1("configure terminal")
    sw1("lldp enable")
    # disable lldp
    sw1("no lldp enable")
    sw1("lldp timer 100")
    sw1("end")

    print("-"*10)
    print("=====----")
    print("-"*10)

    output = sw1("show events")

    assert "LLDP Enabled" or "LLDP Disabled" in output


@mark.gate
def test_ft_evtlog_feature(topology, step):
    sw1 = topology.get('sw1')

    assert sw1 is not None

    step("Test basic show events command")
    evtlogfeature_cli(sw1)

    step("Test show events event ID FIlter (Positive & negative case)")
    # Positive test case
    evtlogfilter_event_id_cli_pass(sw1)
    # Negative
    evtlogfilter_event_id_cli_fail(sw1)

    step("Test show events event category Filter(negative case)")
    evtlogfilter_category_cli(sw1)

    step("Test show events severity negative test case")
    evtlogfilter_severity_cli(sw1)
