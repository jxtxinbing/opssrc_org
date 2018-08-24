#Read Me for ops-bufmond repository

##What is ops-bufmond?
The primary goal of the buffer monitoring  module is to monitor the buffer space consumption inside the switch hardware device.

The ops-bufmond module can be managed through any monitoring agent application, similar to the broadview project [broadview](https://github.com/Broadcom-Switch/BroadView-Instrumentation).

##What is the structure of the repository?

The buffer monitoring feature changes spread across multiple repositories.

* The ops-bufmond/ops_bufmond.py python daemon populates the counter information in the ovs-db tables described in the hardware description file.
* The ops-config-<asic>/bufmond.yaml buffer monitors the counter's hardware description file.
* The ops-openvswitch/vswitchd/bufmon-provider.c bufmon layer (bufmon provider) provides APIs to configure switch hardware.


##What is the license?
The ops-bufmond inherits its Apache 2.0 license. For more details refer to [COPYING](http://www.apache.org/licenses/LICENSE-2.0)


##What other documents are available?

For the high level design of ops-bufmond, refer to [DESIGN.md](http://git.openswitch.net/cgit/openswitch/ops-bufmond/tree/DESIGN.md)

For general information about OpenSwitch project, refer to http://www.openswitch.net.
