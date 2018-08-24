#Read Me for OPS-MGMT-INTF repository


##What is ops-mgmt-intf?
The primary goal of the management module is to facilitate the management of the device. It provides the following:

	•	Device access and configuration

	•	Event collection for monitoring, analysis, and correlation

	•	Device and user authentication, authorization, and accounting

	•	Device time synchronization

	•	Device image downloading


The device is configured or monitored through the management interface. All management traffic like `ssh` to the device, `tftp`, etc goes through the management interface.

What is the structure of the repository?
----------------------------------------
* src/ops-mgmt-intf/ contains the management interface daemon code.
* src/ops-mgmt-intf/test/ contains all the component tests of ops-mgmt-intf based on [ops-test-framework](http://git.openswitch.net/openswitch/ops-test-framework).


What is the license?
--------------------
NA

What other documents are available?
-----------------------------------
For the high level design of ops-mgmt-intf, refer to [Management Interface design](/documents/user/mgmt_intf_design)
For Command Reference document of ops-mgmt-intf, refer to [Management Interface Command Reference](/documents/user/mgmt_intf_cli)

For general information about OpenSwitch project refer to http://www.openswitch.net
