#!/usr/bin/env python

# Copyright (C) 2016 Hewlett Packard Enterprise Development LP
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

import pytest
import re
import collections
from opstestfw import *
from opstestfw.switch.CLI import *
from opstestfw.switch import *

#
# The purpose of this test is to test
# if namespace are created when a new VRF
# is configured and namespace is deleted
# when a vrf is removed.
#
# For this test, we need below topology
#
#       +---+----+
#       |        |
#       +switch1 |
#       |(Client)|
#       |        |
#       +---+----+
#
# Topology definition
topoDict = {"topoExecution": 1000,
            "topoTarget": "dut01",
            "topoDevices": "dut01",
            "topoFilters": "dut01:system-category:switch"}

NO_OF_VRF_TO_CREATE = 20


def configure_vrf(**kwargs):
    device1 = kwargs.get('device1', None)
    vrf_name = kwargs.get('vrf', None)

    cmd = "ovs-vsctl add-vrf " + vrf_name
    devIntRetStruct = device1.DeviceInteract(command=cmd)
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to Configre VRF"
    LogOutput('info', "### Configured VRF %s ###" % vrf_name)


def get_vrf_table_id(**kwargs):
    device1 = kwargs.get('device1', None)
    vrf_name = kwargs.get('vrf', None)

    cmd = "ovs-vsctl list vrf " + vrf_name
    devIntRetStruct = device1.DeviceInteract(command=cmd)
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to get the VRF table"

    out = devIntRetStruct.get('buffer')
    if "no row \"vrf3\" in table VRF" in out:
        return

    lines = out.split('\n')
    for line in lines:
        if "table_id" in line:
            table_id_str, id_value = line.split(':')
            id_value = id_value.strip()
    return id_value


def vrf_configuration(**kwargs):
    device1 = kwargs.get('device1', None)

    device1.commandErrorCheck = 0

    # Defining the test steps
    green_vrf = None
    blue_vrf = None

    LogOutput('info', "########## Configure VRF's on the switch ##########")
    # Configure green VRF
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl add-vrf green")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to Configre VRF"
    LogOutput('info', "### Configured VRF green ###")

    buff = device1.DeviceInteract(command="ip netns")
    out = buff.get('buffer')
    lines = out.split('\n')
    for line in lines:
        if "nonet" not in line and "swns" not in line and "netns" not in line:
            green_vrf = line.strip()
            LogOutput('info', "### Created namespace "+green_vrf+" ###")
            break

    if green_vrf is None:
        assert 0, "Failed to create green namespace"

    # Configure blue VRF
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl add-vrf blue")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to Configre VRF"
    LogOutput('info', "### Configured VRF blue ###")

    buff = device1.DeviceInteract(command="ip netns")
    out = buff.get('buffer')
    lines = out.split('\n')
    for line in lines:
        if "nonet" not in line and "swns" not in line and green_vrf not in \
                line and "netns" not in line:
            blue_vrf = line.strip()
            LogOutput('info', "### Created namespace "+blue_vrf+" ###")
            break

    vrf_creation_success = False

    if green_vrf is not None and blue_vrf is not None:
        vrf_creation_success = True
        LogOutput('info', "########## Namespaces are successfully created "
                          "##########")

    assert vrf_creation_success is True, "Failed to create namespace " \
                                         "for the VRF's we configured"

    # Un-Configure green VRF
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl del-vrf green")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to remove green VRF"
    LogOutput('info', "### Unconfigured green VRF ###")

    # Un-Configure blue VRF
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl del-vrf blue")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to remove blue VRF"
    LogOutput('info', "### Unconfigured blue VRF ###")

    vrf_deletion_success = True

    buff = device1.DeviceInteract(command="ip netns")
    out = buff.get('buffer')
    lines = out.split('\n')
    for line in lines:
        if green_vrf in line or blue_vrf in line:
            vrf_deletion_success = False

    assert vrf_deletion_success is True, "Failed to delete the namespaces " \
                                         "for the VRF's we de-configured"
    LogOutput('info', "### Deleted namespace " + blue_vrf + " ###")
    LogOutput('info', "### Deleted namespace " + green_vrf + " ###")
    LogOutput('info', "########## Namespaces are successfully deleted"
                      " ##########")


def vrf_loopback_configuration(**kwargs):
    device1 = kwargs.get('device1', None)

    device1.commandErrorCheck = 0

    green_vrf = None
    LogOutput('info', "########## Configure VRF on the switch ##########")
    # Configure green VRF
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl add-vrf green")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to Configre VRF"
    LogOutput('info', "### Configured VRF green ###")

    buff = device1.DeviceInteract(command="ip netns")
    out = buff.get('buffer')
    lines = out.split('\n')
    for line in lines:
       if "nonet" not in line and "swns" not in line and "netns" not in line:
            green_vrf = line.strip()
            LogOutput('info', "### Created namespace "+green_vrf+" ###")
            break

    if green_vrf is None:
        assert 0, "Failed to create green namespace"

    # Verify the loopback status Up and IP address in namespace created.
    devIntRetStruct = device1.DeviceInteract(command="ip netns exec "+green_vrf+" ifconfig -a lo")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to get the ifconfig info of lo in namespace"

    out = devIntRetStruct.get('buffer')
    assert 'inet addr:127.0.0.1' in out, "IP address configuration for loopback failed"
    assert 'UP' in out, "Failed to get the loopback interface UP in new namespace"

    # Un-Configure green VRF
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl del-vrf green")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to remove green VRF"
    LogOutput('info', "### Unconfigured green VRF ###")

    vrf_deletion_success = True

    buff = device1.DeviceInteract(command="ip netns")
    out = buff.get('buffer')
    lines = out.split('\n')
    for line in lines:
        if green_vrf in line:
            vrf_deletion_success = False

    assert vrf_deletion_success is True, "Failed to delete the namespaces " \
                                         "for the VRF's we de-configured"
    LogOutput('info', "### Deleted namespace " + green_vrf + " ###")
    LogOutput('info', "########## Namespace successfully deleted"
                      " ##########")


def vrf_table_id_configuration(**kwargs):
    device1 = kwargs.get('device1', None)

    device1.commandErrorCheck = 0

    table_id_list = []
    LogOutput('info', "########## Verifying default VRF table_id ##########")
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl list vrf \
                                             vrf_default")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to get the default VRF table"

    out = devIntRetStruct.get('buffer')
    lines = out.split('\n')
    for line in lines:
        if "table_id" in line:
            table_id_str, id_value = line.split(':')
            id_value = id_value.strip()
            assert id_value is '0', "Failed to verify that the table_id value"\
                                    " of default VRF is 0"

    LogOutput('info', "########## Verified the default VRF table_id value is"
                      " Zero##########")

    table_id_list.append(id_value)

    for x in range(1, NO_OF_VRF_TO_CREATE):
        vrf_name = str("vrf%d" % x)
        configure_vrf(device1=device1, vrf=vrf_name)
        table_id = get_vrf_table_id(device1=device1, vrf=vrf_name)
        table_id_list.append(table_id)

        # Assert if any of the table_id is repeated.
        assert [item for item, count in
                collections.Counter(table_id_list).items() if count == 1]

    LogOutput('info', "########## Verified the VRF table_id assigned are"
                      " Unique: %s##########" % table_id_list)

    # Delete a VRF and verify that a new table_id is assigned to the VRF,
    # not the old deleted one.
    LogOutput('info', "########## Deleting vrf3 ##########")
    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl del-vrf vrf3")
    retCode = devIntRetStruct.get('returnCode')
    assert retCode == 0, "Failed to get the delete vrf3"

    devIntRetStruct = device1.DeviceInteract(command="ovs-vsctl list vrf \
                                             vrf3")
    out = devIntRetStruct.get('buffer')
    assert "no row \"vrf3\" in table VRF" in out, "VRF deletion Failed"

    # Add a new VRF and verify that the table_id it gets is not in list.
    configure_vrf(device1=device1, vrf="vrf3")
    table_id = get_vrf_table_id(device1=device1, vrf="vrf3")
    assert table_id not in table_id_list, "table_id obtained of the deleted \
        VRF"
    LogOutput('info', "########## Deleted and added back vrf3, new table_id"
                      " is generated ##########")

    # Compare table_id list before and after process restart.
    # Obtain the current table_id_list
    table_id_list_before_restart = []
    table_id_list_after_restart = []
    for x in range(1, NO_OF_VRF_TO_CREATE):
        vrf_name = str("vrf%d" % x)
        table_id = get_vrf_table_id(device1=device1, vrf=vrf_name)
        table_id_list_before_restart.append(table_id)

    # Restart the vrfmgrd process
    device1.DeviceInteract(command="systemctl stop ops-vrfmgrd")
    device1.DeviceInteract(command="systemctl start ops-vrfmgrd")

    for x in range(1, NO_OF_VRF_TO_CREATE):
        vrf_name = str("vrf%d" % x)
        table_id = get_vrf_table_id(device1=device1, vrf=vrf_name)
        table_id_list_after_restart.append(table_id)

    for x in range(0, len(table_id_list_before_restart)):
        assert \
            table_id_list_before_restart[x] == table_id_list_after_restart[x],\
            "Table_id after obtained after process restart is not same as \
            before"
    LogOutput('info', "########## VRF table_id assigned before the"
                      " restart process: %s##########"
                      % table_id_list_before_restart)
    LogOutput('info', "########## VRF table_id assigned after the "
                      " restart process: %s##########"
                      % table_id_list_after_restart)
    LogOutput('info', "########## Verified the table_id List before and after"
                      " restart of vrfmgrd process ##########")


@pytest.mark.timeout(1000)
class Test_vrf_configuration:
    def setup_class(cls):
        # Test object will parse command line and formulate the env
        Test_vrf_configuration.testObj = testEnviron(topoDict=topoDict)
        #    Get topology object
        Test_vrf_configuration.topoObj = \
            Test_vrf_configuration.testObj.topoObjGet()

    def teardown_class(cls):
        Test_vrf_configuration.topoObj.terminate_nodes()

    def test_vrf_configuration(self):
        dut01Obj = self.topoObj.deviceObjGet(device="dut01")
        retValue = vrf_configuration(device1=dut01Obj)

    def test_vrf_loopback_configuration(self):
        dut01Obj = self.topoObj.deviceObjGet(device="dut01")
        retValue = vrf_loopback_configuration(device1=dut01Obj)

    def test_vrf_table_id_configuration(self):
        dut01Obj = self.topoObj.deviceObjGet(device="dut01")
        retValue = vrf_table_id_configuration(device1=dut01Obj)
