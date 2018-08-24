
Component Test Cases
=======
The Following test cases verify VRF configuration on the switch.
- [Test Cases](#test-cases)
	- [Test case 1.01 : Verify VRF namespace creation by configuring VRF's](#test-case-1.01-:-verify-vrf-namespace-creation-by-configuring-vrf's)
	- [Test case 1.02 : Verify attaching a interface to VRF namespace](#test-case-1.02-:-verify-attaching-a-interface-to-vrf-namespace)
	- [Test case 1.03 : Verify removing a namespace moves interface to default namespace](#test-case-1.03-:-verify-removing-a-namespace-moves-interface-to-default-namespace)
	- [Test case 1.04 : Verify VRF namespace deletion by deleting VRF's](#test-case-1.04-:-verify-vrf-namespace-deletion-by-deleting-vrf's)

##  Test case 1.01 : Verify VRF namespace creation by configuring VRF's ##
### Objective ###
Configure a VRF on the OVSDB, so that a namespace shall be created for the VRF.
### Requirements ###
The requirements for this test case are:
 - Switch NOS docker instance

### Setup ###
A DUT with NOS image.
#### Topology Diagram ####
#### Test Setup ####
              +-----------------------+
              |                       |
              |  NOS switch instance  |
              |                       |
              +-----------------------+
### Description ###
Configure a VRF on the switch, which internally creates an entry in OVSDB. Daemon listening on this table gets a notification and creates a namespace with unique name.

### Test Result Criteria ###
When a new VRF is created on OVSDB, a network namespace should be created for it.
The cases in which the above behaviour would fail is:
	- OVSDB not reachable, so new VRF notification is not reached to daemon.
	- Daemon responsble to create namesapce is killed

#### Test Pass Criteria ####
A namespace with unique name should be created for the VRF configured.
#### Test Fail Criteria ####
No Namespace created for the VRF.

##  Test case 1.02 : Verify attaching a interface to VRF namespace ##
### Objective ###
Attach an interface to an existing and non default VRF, and the actual kernel interface should be moved to the namespace VRF belongs to.
### Requirements ###
The requirements for this test case are:
 - Switch NOS docker instance

### Setup ###
A DUT with NOS image.

#### Topology Diagram ####
#### Test Setup ####
              +-----------------------+
              |                       |
              |  NOS switch instance  |
              |                       |
              +-----------------------+
### Description ###
Attach a interface to a VRF on the switch, which internally creates an entry in OVSDB. Daemon listening on this table gets a notification and moves interface to the namespace belonging to the VRF.

### Test Result Criteria ###
When an interface is attched to a VRF on OVSDB, a kernel interface should be moved to the namespace belonging to the VRF.
The cases in which the above behaviour would fail is:
	- OVSDB not reachable, so new interface attach notification is not reached to daemon.
	- Daemon responsble to move the interface is killed.

#### Test Pass Criteria ####
Kernel interface moved to the namespace of the VRF to which interface is attached to on OVSDB.
#### Test Fail Criteria ####
Kernel interface is not moved to the namespace of the VRF to which interface is attached to on OVSDB. But still present on swns namespace.

##  Test case 1.03 : Verify removing a namespace moves interface to default namespace ##
### Objective ###
Remove a VRF from the OVSDB, then the interface attached to the VRF namespace are moved back to default namespace.
### Requirements ###
The requirements for this test case are:
 - Switch NOS docker instance

### Setup ###
A DUT with NOS image.

#### Topology Diagram ####
#### Test Setup ####
              +-----------------------+
              |                       |
              |  NOS switch instance  |
              |                       |
              +-----------------------+
### Description ###
On a VRF delete on the switch, which internally removes an entry in OVSDB. Daemon listening on this table gets a notification and moves interface to the default namespace belonging to the VRF before actually deleting the namespace.

### Test Result Criteria ###
When a interface is detatched from a VRF on OVSDB, a kernel interface should be moved to the default namespace.
The cases in which the above behaviour would fail is:
	- OVSDB not reachable, so interface movement notification is not reached to daemon.
	- Daemon responsble to move the interface is killed.

#### Test Pass Criteria ####
Kernel interface moved to the default namespace.
#### Test Fail Criteria ####
Kernel interface is not moved to the default namespace.

##  Test case 1.04 : Verify VRF namespace deletion by deleting VRF's ##
### Objective ###
Unconfigure a VRF on the OVSDB, so that a namespace shall be deleted for the VRF.
### Requirements ###
The requirements for this test case are:
 - Switch NOS docker instance

### Setup ###
A DUT with NOS image.
#### Topology Diagram ####
#### Test Setup ####
              +-----------------------+
              |                       |
              |  NOS switch instance  |
              |                       |
              +-----------------------+
### Description ###
Unconfigure a VRF on the switch, which internally deletes an entry in OVSDB. Daemon listening on this table gets a notification and deletes a namespace.

### Test Result Criteria ###
When a VRF entry is deleted on OVSDB, the network namespace belonging to the VRF should be deleted.
The cases in which the above behaviour would fail is:
	- OVSDB not reachable, so VRF deletion notification is not reached to daemon.
	- Daemon responsble to delete namesapce is killed

#### Test Pass Criteria ####
The namespace corresponding to VRF is deleted.
#### Test Fail Criteria ####
The namespace corresponding to VRF is not deleted.
