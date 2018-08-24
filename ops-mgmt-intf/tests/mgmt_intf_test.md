# Management Interface Component Test Cases

## Contents

- [Overview](#overview)
- [Test cases in IPv4 DHCP mode](#test-cases-in-ipv4-dhcp-mode)
	- [Verifying the DHCP client has started](#verifying-the-dhcp-client-has-started)
	- [Verifying that the management interface is updated during boot](#verifying-that-the-management-interface-is-updated-during-boot)
	- [Verifying that the user is able to enter the management interface context](#verifying-that-the-user-is-able-to-enter-the-management-interface-context)
	- [Verifying management interface attributes in DHCP mode](#verifying-management-interface-attributes-in-dhcp-mode)
	- [Verifying that the default gateway is configurable in DHCP mode](#verifying-that-the-default-gateway-is-configurable-in-dhcp-mode)
	- [Verifying that the primary DNS is configurable in DHCP mode](#verifying-that-the-primary-dns-is-configurable-in-dhcp-mode)
	- [Verifying that the secondary DNS is configurable in DHCP mode](#verifying-that-the-secondary-dns-is-configurable-in-dhcp-mode)
- [Test cases in static IPv4 mode](#test-cases-in-static-ipv4-mode)
	- [Verifying that the static IPv4 address is configured on the management interface](#verifying-that-the-static-ipv4-address-is-configured-on-the-management-interface)
	- [Verifying that the static IPv4 address is reconfigured on the management interface](#verifying-that-the-static-ipv4-address-is-reconfigured-on-the-management-interface)
	- [Verifying that the default gateway is configured in static mode](#verifying-that-the-default-gateway-is-configured-in-static-mode)
	- [Verifying that the default gateway is removed in static mode](#verifying-that-the-default-gateway-is-removed-in-static-mode)
	- [Verifying that the primary DNS is configured in static mode](#verifying-that-the-primary-dns-is-configured-in-static-mode)
	- [Verifying that the primary DNS is reconfigured in static mode](#verifying-that-the-primary-dns-is-reconfigured-in-static-mode)
	- [Verifying that the primary DNS is removed in static mode](#verifying-that-the-primary-dns-is-removed-in-static-mode)
	- [Verifying that the secondary DNS is configured in static mode](#verifying-that-the-secondary-dns-is-configured-in-static-mode)
	- [Verifying that the secondary DNS is reconfigured in static mode](#verifying-that-the-secondary-dns-is-reconfigured-in-static-mode)
	- [Verifying that the secondary DNS is removed in static mode](#verifying-that-the-secondary-dns-is-removed-in-static-mode)
	- [Verifying that an invalid IPv4 address is configurable in static mode](#verifying-that-an-invalid-ipv4-address-is-configurable-in-static-mode)
	- [Verifying that a multicast IPv4 address is configurable in static mode](#verifying-that-a-multicast-ipv4-address-is-configurable-in-static-mode)
	- [Verifying that a broadcast IPv4 address is configurable in static mode](#verifying-that-a-broadcast-ipv4-address-is-configurable-in-static-mode)
	- [Verifying that a loopback IPv4 address is configurable in static mode](#verifying-that-a-loopback-ipv4-address-is-configurable-in-static-mode)
	- [Verifying that an invalid IPv4 default gateway address is configurable in static mode](#verifying-that-an-invalid-ipv4-default-gateway-address-is-configurable-in-static-mode)
	- [Verifying that the multicast IPv4 default gateway address is configurable in static mode](#verifying-that-the-multicast-ipv4-default-gateway-address-is-configurable-in-static-mode)
	- [Verifying that a broadcast IPv4 default gateway address is configurable in static mode](#verifying-that-a-broadcast-ipv4-default-gateway-address-is-configurable-in-static-mode)
	- [Verifying that a loopback IPv4 default gateway address is configurable in static mode](#verifying-that-a-loopback-ipv4-default-gateway-address-is-configurable-in-static-mode)
	- [Verifying that an invalid IPv4 primary DNS address is configurable in static mode](#verifying-that-an-invalid-ipv4-primary-dns-address-is-configurable-in-static-mode)
	- [Verifying that a multicast IPv4 primary DNS address is configurable in static mode](#verifying-that-a-multicast-ipv4-primary-dns-address-is-configurable-in-static-mode)
	- [Verifying that a broadcast IPv4 primary DNS address is configurable in static mode](#verifying-that-a-broadcast-ipv4-primary-dns-address-is-configurable-in-static-mode)
	- [Verifying that a loopback IPv4 primary DNS address is configurable in static mode](#verifying-that-a-loopback-ipv4-primary-dns-address-is-configurable-in-static-mode)
	- [Verifying that an invalid IPv4 secondary DNS address is configurable in static mode](#verifying-that-an-invalid-ipv4-secondary-dns-address-is-configurable-in-static-mode)
	- [Verifying that the management interface mode is changeable](#verifying-that-the-management-interface-mode-is-changeable)
	- [Verifying that the management interface is got IPv4 if DHCP mode is set](#verifying-that-the-management-interface-is-got-ipv4-if-dhcp-mode-is-set)
	- [Verifying that the management interface is got default gateway IPv4 address if DHCP mode is set](#verifying-that-the-management-interface-is-got-default-gateway-ipv4-address-if-dhcp-mode-is-set)
	- [Verifying that the management interface is got DNS IPv4 address if DHCP set](#verifying-that-the-management-interface-is-got-dns-ipv4-address-if-dhcp-set)
	- [Verifying that the static IPv4 address is removed and the mode is changed to DHCP](#verifying-that-the-static-ipv4-address-is-removed-and-the-mode-is-changed-to-dhcp)
	- [Verifying that the static IPv4 address is removed if IPv6 address is configured](#verifying-that-the-static-ipv4-address-is-removed-if-ipv6-address-is-configured)
	- [Verifying that the static IPv4 address is removable if the default gateway IPv4 address is configured](#verifying-that-the-static-ipv4-address-is-removable-if-the-default-gateway-ipv4-address-is-configured)
	- [Verifying that the static IPv4 address is removable if IPv4 nameserver address is configured](#verifying-that-the-static-ipv4-address-is-removable-if-ipv4-nameserver-address-is-configured)
	- [Verifying that the static IPv4 address is removable if IPv4 and IPv6 nameserver addresses are configured](#verifying-that-the-static-ipv4-address-is-removable-if-ipv4-and-ipv6-nameserver-addresses-are-configured)
- [Test cases in IPv6 DHCP mode](#test-cases-in-ipv6-dhcp-mode)
	- [Verifying that the default gateway is configurable in DHCP mode](#verifying-that-the-default-gateway-is-configurable-in-dhcp-mode)
	- [Verifying that the primary DNS is configurable in DHCP mode](#verifying-that-the-primary-dns-is-configurable-in-dhcp-mode)
	- [Verifying that the secondary DNS is configurable in DHCP mode](#verifying-that-the-secondary-dns-is-configurable-in-dhcp-mode)
- [Test cases in static IPv6 mode](#test-cases-in-static-ipv6-mode)
	- [Verifying that the static IPv6 address is configured](#verifying-that-the-static-ipv6-address-is-configured)
	- [Verifying that the static IPv6 address is reconfigured](#verifying-that-the-static-ipv6-address-is-reconfigured)
	- [Verifying that the invalid IPv6 address is configurable in static mode](#verifying-that-the-invalid-ipv6-address-is-configurable-in-static-mode)
	- [Verifying that the multicast IPv6 address is configurable in static mode](#verifying-that-the-multicast-ipv6-address-is-configurable-in-static-mode)
	- [Verifying that the link-local IPv6 address is configurable in static mode](#verying-that-the-link-local-ipv6-address-is-configurable-in-static-mode)
	- [Verifying that the loopback IPv6 address is configurable in static mode](#verifying-that-the-loopback-ipv6-address-is-configurable-in-static-mode)
	- [Verifying that the default gateway is configured in static mode](#verifying-that-the-default-gateway-is-configured-in-static-mode)
	- [Verifying that the invalid IPv6 default gateway address is configurable in static mode](#verifying-that-the-invalid-ipv6-default-gateway-address-is-configurable-in-static-mode)
	- [Verifying that the multicast IPv6 default gateway address is configurable in static mode](#verifying-that-the-multicast-ipv6-default-gateway-address-is-configurable-in-static-mode)
	- [Verifying that the link-local default gateway IPv6 address is configurable in static mode](#verifying-that-the-link-local-default-gateway-ipv6-address-is-configurable-in-static-mode)
	- [Verifying that the loopback IPv6 default gateway address is configurable in static mode](#verifying-that-the-loopback-ipv6-default-gateway-address-is-configurable-in-static-mode)
	- [Verifying that the default gateway is removable in static mode](#verifying-that-the-default-gateway-is-removable-in-static-mode)
	- [Verifying that the invalid IPv6 primary DNS address is configurable in static mode](#verifying-that-the-invalid-ipv6-primary-dns-address-is-configurable-in-static-mode)
	- [Verifying that the multicast IPv6 primary DNS address is configurable in static mode](#verifying-that-the-multicast-ipv6-primary-dns-address-is-configurable-in-static-mode)
	- [Verifying that the link-local IPv6 primary DNS address configurable in static mode](#verifying-that-the-link-local-ipv6-primary-dns-address-configurable-in-static-mode)
	- [Verifying that the loopback IPv6 primary address is configurable in static mode](#verifying-that-the-loopback-ipv6-primary-address-is-configurable-in-static-mode)
	- [Verifying that the invalid IPv6 secondary DNS address is configurable in static mode](#verifying-that-the-invalid-ipv6-secondary-dns-address-is-configurable-in-static-mode)
	- [Verifying that the multicast IPv6 secondary DNS address is configurable in static mode](#verifying-that-the-multicast-ipv6-secondary-dns-address-is-configurable-in-static-mode)
	- [Verifying that the link-local IPv6 secondary DNS address is configurable in static mode](#verifying-that-the-link-local-ipv6-secondary-dns-address-is-configurable-in-static-mode)
	- [Verifying that the loopback IPv6 secondary address is configurable in static mode](#verifying-that-the-loopback-ipv6-secondary-address-is-configurable-in-static-mode)
	- [Verifying that the same IPv6 primary and secondary DNS address is configurable in static mode](#verifying-that-the-same-ipv6-primary-and-secondary-dns-address-is-configurable-in-static-mode)
	- [Verifying that the primary DNS address is configured in static mode](#verifying-that-the-primary-dns-address-is-configured-in-static-mode)
	- [Verifying that the primary DNS address is reconfigured in static mode](#verifying-that-the-primary-dns-address-is-reconfigured-in-static-mode)
	- [Verifying that the primary DNS address is removed in static mode](#verifying-that-the-primary-dns-address-is-removed-in-static-mode)
	- [Verifying that the secondary DNS address is configured in static mode](#verifying-that-the-secondary-dns-address-is-configured-in-static-mode)
	- [Verifying that the secondary DNS address is reconfigured in static mode](#verifying-that-the-secondary-dns-address-is-reconfigured-in-static-mode)
	- [Verifying that the secondary DNS address is removed in static mode](#verifying-that-the-secondary-dns-address-is-removed-in-static-mode)
	- [Verifying that the management interface mode is changeable](#verifying-that-the-management-interface-mode-is-changeable)
	- [Verifying that the management interface is got IPv6 if DHCP mode set](#verifying-that-the-management-interface-is-got-ipv6-if-dhcp-mode-set)
	- [Verifying that the management interface is got default gateway IPv6 address in DHCP mode](#verifying-that-the-management-interface-is-got-default-gateway-ipv6-address-in-dhcp-mode)
	- [Verifying that the static IPv6 address is removed and the mode is changed to DHCP](#verifying-that-the-static-ipv6-address-is-removed-and-the-mode-is-changed-to-dhcp)
	- [Verifying that the static IPv6 address is removable if IPv4 address is configured in static mode](#verifying-that-the-static-ipv6-address-is-removable-if-ipv4-address-is-configured-in-static-mode)
	- [Verifying that the static IPv6 address is removable if a default gateway IPv6 address is configured](#verifying-that-the-static-ipv6-address-is-removable-if-a-default-gateway-ipv6-address-is-configured)
	- [Verifying that the static IPv6 address is removable if an IPv6 nameserver address is configured](#verifying-that-the-static-ipv6-address-is-removable-if-an-ipv6-nameserver-address-is-configured)
	- [Verifying that the static IPv6 address is removable if IPv4 and IPv6 nameserver addresses are configured](#verifying-that-the-static-ipv6-address-is-removable-if-ipv4-and-ipv6-nameserver-addresses-are-configured)
- [Test cases for system hostname configuration](#test-cases-for-system-hostname-configuration)
	- [Verifying that the system hostname is configured using CLI](#verifying-that-the-system-hostname-is-configured-using-cli)
	- [Verifying that the system hostname is unconfigured using CLI](#verifying-that-the-system-hostname-is-unconfigured-using-cli)
	- [Verifying that the system hostname defaults to switch](#verifying-that-the-system-hostname-defaults-to-switch)
	- [Verifying that the system hostname is configured though the DHCP Server](#verifying-that-the-system-hostname-is-configured-though-the-dhcp-server)
	- [Verifying that the system hostname is unconfigured through the DHCP Server](#verifying-that-the-system-hostname-is-unconfigured-through-the-dhcp-server)
- [Test cases for system domain name configuration](#test-cases-for-system-domain-name-configuration)
	- [Verifying that the system domain name is configured using CLI](#verifying-that-the-system-domain-name-is-configured-using-cli)
	- [Verifying that the system domain name is unconfigured using CLI](#verifying-that-the-system-domain-name-is-unconfigured-using-cli)
	- [Verifying that the system domain name is configured through the DHCP Server](#verifying-that-the-system-domain-name-is-configured-through-the-dhcp-server)
	- [Verifying that the system domain name is unconfigured through the DHCP Server](#verifying-that-the-system-domain-name-is-unconfigured-through-the-dhcp-server)

##Overview

The following test cases verify management interface configurations in:
- [IPv4 DHCP mode](#verifying-management-interface-configuration-test-cases-in-ipv4-dhcp-mode)
- [Static IPv4 mode](#verifying-management-interface-configuration-test-cases-in-static-ipv4-mode)
- [IPv6 DHCP mode](#verifying-management-interface-configuration-test-cases-in-ipv6-dhcp-mode)
- [Static IPv6 mode](#verifying-management-interface-configuration-test-cases-in-static-ipv6-mode)
- [System Hostname](#verifying-system-hostname-configuration-testcases)
- [System Domainname](#verifying-system-domainname-configuration-testcases)

## Test cases in IPv4 DHCP mode
### Objectives
These test cases are used for:
- Configuring, reconfiguring, and unconfiguring the management interface.
- Verifying the expected behavior of the management interface with the DHCP IPv4 addressing mode.

### Requirements
The requirements for this test case are:
 - IPv4 DHCP Server

### Setup
#### Topology diagram
                                                           +-------------------+
              +------------------+                         | Linux workstation |
              |                  |eth0                eth0 |+-----------------+|
              |  AS5712 switch   |-----+         +-------- ||DHCP IPv4 Server ||
              |                  |     |         |         |+-----------------+|
              +------------------+     |         |         +-------------------+
                                       |         |
                                       v         v
                                 +---------------------+
                                 | port 1      port 2  |
                                 |                     |
                                 |      Switch         |
                                 +---------------------+

### Verifying the DHCP client has started
#### Description
After booting the switch, verify that the DHCP client has started on the management interface by using the system ctl command: `systemctl status dhclient@eth0.service`.
#### Test result criteria
##### Pass criteria
The test is successful if the `dhcpclient` service is in a running state.
##### Fail criteria
The test failed if the `dhcpclient` service is not in a running state.


### Verifying that the management interface is updated during boot
#### Description
Verify that the management interface name is updated from the `image.manifest` file during boot.
#### Test result criteria
##### Pass criteria
The test is successful if `name=eth0` is present in the **mgmt_intf** column.
##### Fail criteria
The test fails if `name=eth0` is missing from the **mgmt_intf** column.


### Verifying that the user is able to enter the management interface context
#### Description
Verify that the user is able to enter the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the user is in management context.
##### Fail criteria
The test fails if the user is not in management context.


### Verifying management interface attributes in DHCP mode
#### Description
Verify that the management interface attributes are configured in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the following criteria are met:
   - The **IPv4 address/subnet-mask**, **Default gateway IPv4**, **Primary Nameserver**, and  **Secondary Nameserver** addresses are present in the `show interface mgmt` output.
   - The `dhcp client` service is running.

##### Fail criteria
   The test fails if:
   - The **IPv4 address/subnet-mask**, **Default gateway IPv4**, **Primary Nameserver**, **Secondary Nameserver** addresses are missing in the `show interface mgmt` output.
   - The `dhcp client` is not running.


### Verifying that the default gateway is configurable in DHCP mode
#### Description
Configure the IPv4 default gateway in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the IPv4 default gateway is not configured.
##### Fail criteria
The test fails if the IPv4 default gateway is configured.


### Verifying that the primary DNS is configurable in DHCP mode
#### Description
Configure the IPv4 primary DNS in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the IPv4 primary DNS is not configured.
##### Fail criteria
The test fails if the IPv4 primary DNS is configured.


### Verifying that the secondary DNS is configurable in DHCP mode
#### Description
Configure the IPv4 secondary DNS in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the IPv4 secondary DNS is not configured.
##### Fail criteria
The test fails if the IPv4 secondary DNS is configured.


## Test cases in static IPv4 mode

### Objectives
These cases test are used for:
- Configuring, reconfiguring, and unconfiguring the management interface.
- Verifying the expected behavior of the management interface with the static IPv4 addressing mode.

### Requirements
No requirements.
### Setup
#### Topology diagram
              +------------------+                         +-------------------+
              |                  |eth0                eth0 |                   |
              |  AS5712 switch   |----+          +-------- | Linux Workstation |
              |                  |     |         |         |                   |
              +------------------+     |         |         +-------------------+
                                       |         |
                                       v         v
                                 +---------------------+
                                 | port 1      port 2  |
                                 |                     |
                                 |      Switch         |
                                 +---------------------+

### Verifying that the static IPv4 address is configured on the management interface
#### Description
Configure the static IPv4 address on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the **IPv4 address/subnet-mask** address is present in the `show interface mgmt` output and the `ifconfig` ouptut.
##### Fail criteria
The test fails if the **IPv4 address/subnet-mask** address is missing from the `show interface mgmt` output or the `ifconfig` ouptut.

### Verifying that the static IPv4 address is reconfigured on the management interface
#### Description
Reconfigure the static IPv4 address on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the new **IPv4 address/subnet-mask** address is present in the `show interface mgmt` output and `ifconfig` ouptut.
##### Fail criteria
The test fails if the new **IPv4 address/subnet-mask** address is missing in the `show interface mgmt` output or the `ifconfig` ouptut.


### Verifying that the default gateway is configured in static mode
#### Description
Configure the static default IPv4 gateway in the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the **Default gateway IPv4** address is present in the `show interface mgmt` output and the `ip route show` output.
##### Fail criteria
The test fails if the **Default gateway IPv4** address is missing in the `show interface mgmt` output or the `ip route show` ouput.


### Verifying that the default gateway is removed in static mode
#### Description
Remove the IPv4 default gateway in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the **Default gateway IPv4** address is missing in the `show interface mgmt ` output and the `ip route show` output.
##### Fail criteria
The test fails if the **Default gateway IPv4** address is present in the `show interface mgmt` output or the `ip route show` output.


### Verifying that the primary DNS is configured in static mode
#### Description
Configure the IPv4 primary DNS in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the **Primary Nameserver** address is present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the **Primary Nameserver** address is missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the primary DNS is reconfigured in static mode
#### Description
Reconfigure the IPv4 primary DNS in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the new **Primary Nameserver** address is present in the `show interface mgmt` output and the`/etc/resolv.conf` file.
##### Fail criteria
The test fails if the new **Primary Nameserver** address is missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the primary DNS is removed in static mode
#### Description
Remove the IPv4 primary DNS in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the **Primary Nameserver** address is missing in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the **Primary Nameserver** address is present in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the secondary DNS is configured in static mode
#### Description
Configure the IPv4 secondary DNS in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the **Secondary Nameserver** address is present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the **Secondary Nameserver** address is missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the secondary DNS is reconfigured in static mode
#### Description
Reconfigure the IPv4 secondary DNS in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the new **Secondary Nameserver** address is present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the new **Secondary Nameserver** address is missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the secondary DNS is removed in static mode
#### Description
Remove the IPv4 secondary DNS in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the **Secondary Nameserver** address is missing in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the **Secondary Nameserver** address is present in the `show interface mgmt` output or the `/etc/resolv.conf` file.



### Verifying that an invalid IPv4 address is configurable in static mode
#### Description
Configure a static invalid IPv4 address on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv4 address is configured.
##### Fail criteria
The test fails if the invalid IPv4 address is not configured.


### Verifying that a multicast IPv4 address is configurable in static mode
#### Description
Configure a static multicast IPv4 address on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the multicast IPv4 address is configured.
##### Fail criteria
The test fails if the multicast IPv4 address is not configured.


### Verifying that a broadcast IPv4 address is configurable in static mode
#### Description
Configure a static broadcast IPv4 address on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the broadcast IPv4 address is configured.
##### Fail criteria
The test fails if the broadcast IPv4 address is not configured.


### Verifying that a loopback IPv4 address is configurable in static mode
#### Description
Configure a static loopback IPv4 address on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the loopback IPv4 address is configured.
##### Fail criteria
The test fails if the loopback IPv4 address is not configured.


### Verifying that an invalid IPv4 default gateway address is configurable in static mode
#### Description
Configure an invalid default IPv4 gateway on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv4 default gateway address is configured.
##### Fail criteria
The test fails if the invalid IPv4 default gateway address is not configured.


### Verifying that the multicast IPv4 default gateway address is configurable in static mode
#### Description
Configure a multicast IPv4 default gateway on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the multicast IPv4 default gateway address is configured.
##### Fail criteria
The test fails if the multicast IPv4 default gateway address is not configured.


### Verifying that a broadcast IPv4 default gateway address is configurable in static mode
#### Description
Configure a broadcast IPv4 default gateway on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the broadcast IPv4 default gateway address is configured.
##### Fail criteria
The test fails if the broadcast IPv4 default gateway address is not configured.


### Verifying that a loopback IPv4 default gateway address is configurable in static mode
#### Description
Configure a loopback IPv4 default gateway on the management interface using the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the loopback IPv4 default gateway address is configured.
##### Fail criteria
The test fails if the loopback IPv4 default gateway address is not configured.


### Verifying that an invalid IPv4 primary DNS address is configurable in static mode
#### Description
Configure an invalid IPv4 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv4 primary DNS address is configured.
##### Fail criteria
The test fails if the invalid IPv4 primary DNS address is not configured.


### Verifying that a multicast IPv4 primary DNS address is configurable in static mode
#### Description
Configure a multicast IPv4 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the multicast IPv4 primary DNS address is configured.
##### Fail criteria
The test fails if the multicast IPv4 primary DNS address is not configured.


### Verifying that a broadcast IPv4 primary DNS address is configurable in static mode
#### Description
Configure a broadcast IPv4 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the broadcast IPv4 primary DNS address is configured.
##### Fail criteria
The test fails if the broadcast IPv4 primary DNS address is not configured.


### Verifying that a loopback IPv4 primary DNS address is configurable in static mode
#### Description
Configure a loopback IPv4 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the loopback IPv4 primary DNS address is configured.
##### Fail criteria
The test fails if the loopback IPv4 primary DNS address is not configured.



### Verifying that an invalid IPv4 secondary DNS address is configurable in static mode
#### Description
Configure an invalid IPv4 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv4 secondary DNS address is configured.
##### Fail criteria
The test fails if the invalid IPv4 secondary DNS address is not configured.


### Verifying that the management interface mode is changeable
#### Description
Verify that the management interface is changed from static mode to DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if `Address Mode=DHCP` is present in the `show interface mgmt` output.
##### Fail criteria
The test fails if `Address Mode=DHCP` is missing in the `show interface mgmt` output.


### Verifying that the management interface is got IPv4 if DHCP mode is set
#### Description
Verify that the management interface is got IPv4 address after populated static IP in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the new `IPv4 address/subnet-mask` address is present in the `show interface mgmt` output and `ifconfig` ouptut.
##### Fail criteria
The test fails if the new `IPv4 address/subnet-mask` address is missing in the `show interface mgmt` output and `ifconfig` ouptut.


### Verifying that the management interface is got default gateway IPv4 address if DHCP mode is set
#### Description
Verify that the management interface is the got default gateway IPv4 address after populating the static IP in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Default gateway IPv4` address is present in the `show interface mgmt` and `ip route show` output.
##### Fail criteria
The test fails if the `Default gateway IPv4` address is missing in the `show interface mgmt` output and `ip route show` output.



### Verifying that the management interface is got DNS IPv4 address if DHCP set
#### Description
Verify that the management interface is the got primary and secondary DNS IPv4 addresses after populating the static IP in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Primary Nameserver` and `Secondary Nameserver` addresses are present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the `Primary Nameserver` and `Secondary Nameserver` addresses are missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the static IPv4 address is removed and the mode is changed to DHCP
#### Description
Verify that the configured static IPv4 address is removed and the mode is changed to DHCP.
#### Test result criteria
##### Pass criteria
The test case result is successful if the new `IPv4 address/subnet-mask` and `IPv6 address/prefix` addresses, and `Address Mode=DHCP` are present in the `show interface mgmt` ouput.
##### Fail criteria
The test fails if the new `IPv4 address/subnet-mask` and`IPv6 address/prefix` address, or `Address Mode=DHCP` are missing in the `show interface mgmt` ouput.


### Verifying that the static IPv4 address is removed if IPv6 address is configured
#### Description
Verify that the static IPv4 address is removed if IPv6 address is configured, and the mode is static.
#### Test result criteria
##### Pass criteria
The test is successful if the `IPv4 address/subnet-mask` address is removed and `IPv6 address/prefix` address is present in the `show interface mgmt` ouput.
##### Fail criteria
The test fails if `IPv4 address/subnet-mask` address is present in a `show interface mgmt` ouput.


### Verifying that the static IPv4 address is removable if the default gateway IPv4 address is configured
#### Description
Verify that the static IPv4 address is removable if the default gateway IPv4 address is configured.
#### Test result criteria
##### Pass criteria
The test is successful if the `IPv4 address/subnet-mask` address is present in the `show interface mgmt` output and the `ifconfig` output.
##### Fail criteria
The test fails if the `IPv4 address/subnet-mask` address is missing in the `show interface mgmt` output or the `ifconfig` ouptut.


### Verifying that the static IPv4 address is removable if IPv4 nameserver address is configured
#### Description
Verify that the static IPv4 address is removable if the IPv4 nameserver address is configured.
#### Test result criteria
##### Pass criteria
The test is successful if the `IPv4 address/subnet-mask` address is present in the `show interface mgmt` output and the `ifconfig` ouptut.
##### Fail criteria
The test fails if the `IPv4 address/subnet-mask` address is missing in the `show interface mgmt` output or the `ifconfig` ouptut.


### Verifying that the static IPv4 address is removable if IPv4 and IPv6 nameserver addresses are configured
#### Description
Verify that the static IPv4 address is removable if IPv4 and IPv6 nameserver addresses are configured.
#### Test result criteria
##### Pass criteria
The test is successful if the `IPv4 address/subnet-mask` address is present in the `show interface mgmt` output and the `ifconfig` ouptut.
##### Fail criteria
The test fails if the `IPv4 address/subnet-mask` address is missing in the `show interface mgmt` output or the `ifconfig` ouptut.



## Test cases in IPv6 DHCP mode
### Objectives
These cases test:
- Configuring, reconfiguring, and unconfiguring the management interface.
- Verifying the expected behavior of the management interface with the DHCP IPv6 addressing mode.

### Requirements
The requirements for this test case are:

 -  IPv6 DHCP server

### Setup
#### Topology diagram
                                                           +-------------------+
              +------------------+                         | Linux workstation |
              |                  |eth0                eth0 |+-----------------+|
              |  AS5712 switch   |-----+         +---------||DHCP IPv6 Server ||
              |                  |     |         |         |+-----------------+|
              +------------------+     |         |         +-------------------+
                                       |         |
                                       v         v
                                 +---------------------+
                                 | port 1      port 2  |
                                 |                     |
                                 |      Switch         |
                                 +---------------------+

### Verifying that the default gateway is configurable in DHCP mode
#### Description
Configure the IPv6 default gateway in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the IPv6 default gateway is configured.
##### Fail criteria
The test fails if the IPv6 default gateway is not configured.

### Verifying that the primary DNS is configurable in DHCP mode
#### Description
Configure the IPv6 primary DNS in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the IPv6 primary DNS is configured.
##### Fail criteria
The test fails if the IPv6 primary DNS is not configured.


### Verifying that the secondary DNS is configurable in DHCP mode
#### Description
Configure the IPv6 secondary DNS in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the IPv6 secondary DNS is configured.
##### Fail criteria
The test fails if the IPv6 secondary DNS is not configured.



## Test cases in static IPv6 mode
### Objectives
These cases test:
- Configuring, reconfiguring, and unconfiguring the management interface.
- Verifying the expected behavior of the management interface in static IPv6 mode.

### Requirements
No requirements.

### Setup
#### Topology diagram
                                                           +-------------------+
              +------------------+                         |                   |
              |                  |eth0                eth0 |                   |
              |  AS5712 switch   |-----+         +---------| Linux Workstation |
              |                  |     |         |         |                   |
              +------------------+     |         |         +-------------------+
                                       |         |
                                       v         v
                                 +---------------------+
                                 | port 1      port 2  |
                                 |                     |
                                 |      Switch         |
                                 +---------------------+

### Verifying that the static IPv6 address is configured
#### Description
Configure the static IPv6 address on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the `IPv6 address/prefix` address is present in the `show interface mgmt` output and the `ip -6 addr show dev eth0` output.
##### Fail criteria
The test fails if the `IPv6 address/prefix` address is missing in the `show interface mgmt` output or the `ip -6 addr show dev eth0` output.


### Verifying that the static IPv6 address is reconfigured
#### Description
Reconfigure the static IPv6 address on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the new`IPv6 address/prefix` address is present in the `show interface mgmt` output and the `ip -6 addr show dev eth0` output.
##### Fail criteria
The test fails if the new `IPv6 address/prefix` address is missing in the `show interface mgmt` output or the `ip -6 addr show dev eth0` output.


### Verifying that the invalid IPv6 address is configurable in static mode
#### Description
Configure a static invalid IPv6 address on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv6 address is configured.
##### Fail criteria
The test fails if the invalid IPv6 address is not configured.


### Verifying that the multicast IPv6 address is configurable in static mode
#### Description
Configure a static multicast IPv6 address on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the multicast IPv6 address is configured.
##### Fail criteria
The test fails if the multicast IPv6 address is not configured.


### Verifying that the link-local IPv6 address is configurable in static mode
#### Description
Configure a static link-local IPv6 address on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the link-local IPv6 address is configured.
##### Fail criteria
The test fails if the link-local IPv6 address is not configured.


### Verifying that the loopback IPv6 address is configurable in static mode
#### Description
Configure a static loopback IPv6 address on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the loopback IPv6 address is configured.
##### Fail criteria
The test fails if the loopback IPv6 address is not configured.


### Verifying that the default gateway is configured in static mode
#### Description
Configure a static default IPv6 gateway on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the `Default gateway IPv6` address is present in the `show running-config` output.
##### Fail criteria
The test fails if the `Default gateway IPv6` address is missing in the `show running-config` output.


### Verifying that the invalid IPv6 default gateway address is configurable in static mode
#### Description
Configure an invalid default IPv6 gateway on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv6 default gateway address is configured.
##### Fail criteria
The test fails if the invalid IPv6 default gateway address is not configured.


### Verifying that the multicast IPv6 default gateway address is configurable in static mode
#### Description
Configure a multicast default IPv6 gateway on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the multicast IPv6 default gateway address is configured.
##### Fail criteria
The test fails if the multicast IPv6 default gateway address is not configured.


### Verifying that the link-local default gateway IPv6 address is configurable in static mode
#### Description
Configure a link-local IPv6 default gateway on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the link-local IPv6 default gateway address is configured.
##### Fail criteria
The test fails if the link-local IPv6 default gateway address is not configured.


### Verifying that the loopback IPv6 default gateway address is configurable in static mode
#### Description
Configure a loopback IPv6 default gateway on the management interface in the management interface context.
#### Test result criteria
##### Pass criteria
The test is successful if the loopback IPv6 default gateway address is configured.
##### Fail criteria
The test fails if the loopback IPv6 default gateway address is not configured.


### Verifying that the default gateway is removable in static mode
#### Description
Remove the IPv6 default gateway in state mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Default gateway IPv6` address is missing in the `show running-config` output.
##### Fail criteria
The test fails if the `Default gateway IPv6` address is present in the `show running-config` output.


### Verifying that the invalid IPv6 primary DNS address is configurable in static mode
#### Description
Configure an invalid IPv6 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv6 primary DNS address is configured.
##### Fail criteria
The test fails if the invalid IPv6 primary DNS address is not configured.


### Verifying that the multicast IPv6 primary DNS address is configurable in static mode
#### Description
Configure a multicast IPv6 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the multicast IPv6 primary DNS address is configured.
##### Fail criteria
The test fails if the multicast IPv6 primary DNS address is not configured.


### Verifying that the link-local IPv6 primary DNS address configurable in static mode
#### Description
Configure a link-local IPv6 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the link-local IPv6 primary DNS address is configured.
##### Fail criteria
The test fails if the link-local IPv6 primary DNS address is not configured.


### Verifying that the loopback IPv6 primary address is configurable in static mode
#### Description
Configure a loopback IPv6 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the loopback IPv6 primary DNS address is configured.
##### Fail criteria
The test fails if the loopback IPv6 primary DNS address is not configured.


### Verifying that the invalid IPv6 secondary DNS address is configurable in static mode
#### Description
Configure an invalid IPv6 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the invalid IPv6 secondary DNS address is configured.
##### Fail criteria
The test fails if the invalid IPv6 secondary DNS address is not configured.


### Verifying that the multicast IPv6 secondary DNS address is configurable in static mode
#### Description
Configure a multicast IPv6 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the multicast IPv6 secondary DNS address is configured.
##### Fail criteria
The test fails if the multicast IPv6 secondary DNS address is not configured.


### Verifying that the link-local IPv6 secondary DNS address is configurable in static mode
#### Description
Configure a link-local IPv6 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the link-local IPv6 secondary DNS address is configured.
##### Fail criteria
The test fails if the link-local IPv6 secondary DNS address is not configured.


### Verifying that the loopback IPv6 secondary address is configurable in static mode
#### Description
Configure a loopback IPv6 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the loopback IPv6 secondary DNS address is configured.
##### Fail criteria
The test fails if the loopback IPv6 secondary DNS address is not configured.


### Verifying that the same IPv6 primary and secondary DNS address is configurable in static mode
#### Description
Configure the same IPv6 primary and secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the same IPv6 primary and secondary DNS address is configured.
##### Fail criteria
The test fails if the same IPv6 primary and secondary DNS is not configured.


### Verifying that the primary DNS address is configured in static mode
#### Description
Configure an IPv6 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Primary Nameserver` address is present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the `Primary Nameserver` address is missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the primary DNS address is reconfigured in static mode
#### Description
Reconfigure an IPv6 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the new `Primary Nameserver` address is present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the new `Primary Nameserver` address is missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the primary DNS address is removed in static mode
#### Description
Remove an IPv6 primary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Primary Nameserver` address is missing in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the `Primary Nameserver` address is present in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the secondary DNS address is configured in static mode
#### Description
Configure an IPv6 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Primary Nameserver` and `Secondary Nameserver` addresses are present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the `Primary Nameserver` and `Secondary Nameserver` addresses are missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.



### Verifying that the secondary DNS address is reconfigured in static mode
#### Description
Reconfigure an IPv6 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Primary Nameserver` and the new `Secondary Nameserver` addresses are present in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the `Primary Nameserver` and the new `Secondary Nameserver` addresses are missing in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the secondary DNS address is removed in static mode
#### Description
Remove an IPv6 secondary DNS address in static mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Secondary Nameserver` address is missing in the `show interface mgmt` output and the `/etc/resolv.conf` file.
##### Fail criteria
The test fails if the `Secondary Nameserver` address is present in the `show interface mgmt` output or the `/etc/resolv.conf` file.


### Verifying that the management interface mode is changeable
#### Description
Verify that the management interface is changed from static mode to DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Address Mode=DHCP` is present in the `show interface mgmt` output.
##### Fail criteria
The test fails if the `Address Mode=DHCP` is missing in the `show interface mgmt` output.


### Verifying that the management interface is got IPv6 if DHCP mode set
#### Description
Verify that the management interface got IPv6 address after populating the static IPv6 in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the new `IPv6 address/prefix` address is present in the `show interface mgmt` output.
##### Fail criteria
The test fails if the new `IPv6 address/prefix` address is missing in the `show interface mgmt` output.


### Verifying that the management interface is got default gateway IPv6 address in DHCP mode
#### Description
Verify that the management interface got default gateway IPv6 address after populating the static IP in DHCP mode.
#### Test result criteria
##### Pass criteria
The test is successful if the `Default gateway IPv6` address is missing in the `show interface mgmt` or `ip route show` output.
##### Fail criteria
The test fails if the `Default gateway IPv6` address is present in the `show interface mgmt` and `ip route show` output.


### Verifying that the static IPv6 address is removed and the mode is changed to DHCP
#### Description
Verify that the configured static IPv6 address is removed and the mode is changed to DHCP.
#### Test result criteria
##### Pass criteria
The test is successful if the new `IPv4 address/subnet-mask` and `IPv6 address/prefix` addresses, and `Address Mode=DHCP` are present in the `show interface mgmt` ouput.
##### Fail criteria
The test fails if the new `IPv4 address/subnet-mask` and `IPv6 address/prefix` addresses, or `Address Mode=DHCP` are missing in the `show interface mgmt` ouput.


### Verifying that the static IPv6 address is removable if IPv4 address is configured in static mode
#### Description
Verify that the static IPv6 address is removed if an IPv4 address is configured, and the mode is in static.
#### Test result criteria
##### Pass criteria
The test is successful if the `IPv6 address/prefix` address is removed and the `IPv4 address/subnet-mask` address is present in the `show interface mgmt` ouput.
##### Fail criteria
The test fails if the `IPv6 address/prefix` address is present in the `show interface mgmt` ouput.


### Verifying that the static IPv6 address is removable if a default gateway IPv6 address is configured
#### Description
Verify that the static IPv6 address is removed if a default gateway IPv6 address is configured.
#### Test result criteria
##### Pass criteria
The test is successful if the new `IPv6 address/prefix` address is present in the `show interface mgmt` and `ip -6 addr show dev eth0` output.
##### Fail criteria
The test fails if the new `IPv6 address/prefix` address is missing in the `show interface mgmt` or `ip -6 addr show dev eth0` output.


### Verifying that the static IPv6 address is removable if an IPv6 nameserver address is configured
#### Description
Verify that the static IPv6 address is removable if an IPv6 nameserver address is configured.
#### Test result criteria
##### Pass criteria
The test is successful if the new `IPv6 address/prefix` address is present in the `show interface mgmt` and `ip -6 addr show dev eth0` output.
##### Fail criteria
The test fails if the new `IPv6 address/prefix` address is missing in the `show interface mgmt` or `ip -6 addr show dev eth0` output.


### Verifying that the static IPv6 address is removable if IPv4 and IPv6 nameserver addresses are configured
#### Description
Verify that the static IPv6 address is removed if the IPv4 and IPv6 nameserver addresses are configured.
#### Test result criteria
##### Pass criteria
The test is successful if the new `IPv6 address/prefix` address is present in the `show interface mgmt` and `ip -6 addr show dev eth0` output.
##### Fail criteria
The test fails if the new `IPv6 address/prefix` address is missing in the `show interface mgmt` or `ip -6 addr show dev eth0` output.

## Test cases for system hostname configuration

### Objectives
These cases test the following:
   - Configuring, reconfiguring and unconfiguring the system hostname.
   - Verifying the expected behavior of the system hostname.

### Requirements
The requirements for this test case are:

 -  DHCP server

### Setup
#### Topology diagram

                                                +-------------------+
              +------------------+              | Linux workstation |
              |                  |eth0     eth1 |+-----------------+|
              |  AS5712 switch   |--------------||   DHCP Server   ||
              |                  |              |+-----------------+|
              +------------------+              +-------------------+


### Verifying that the system hostname is configured using CLI
#### Description
Test to verify whether the hostname of the system changes to the value configured using the "hostname new-name" command in config mode.
#### Test result criteria
##### Pass criteria
The test is successful if the configured value is present in the `uname -n` output.
##### Fail criteria
The test fails if the configured hostname is missing in the `uname -n` output.

### Verifying that the system hostname is unconfigured using CLI
#### Description
Test to verify whether the hostname of the system changes to the default value **switch** when unconfigured using the `no hostname` command in config mode.
#### Test result criteria
##### Pass criteria
The test is successful if the default hostname **switch** is present in the `uname -n` output.
##### Fail criteria
The test fails if the default value **switch** is not present in the `uname -n` output.

### Verifying that the system hostname defaults to switch
#### Description
Test to verify whether the system hostname defaults to **switch** when nothing is configured through the CLI in config mode.
#### Test result criteria
##### Pass criteria
The test is successful if the default hostname **switch** is present in the `uname -n` output.
##### Fail criteria
The test fails if the default value **switch** is not present in the `uname -n` output.

### Verifying that the system hostname is configured though the DHCP Server
#### Description
Test to verify whether the hostname of the system changes to the value configured by the DHCP server through the **dhclient** using option12 `option host-name`.
#### Test result criteria
##### Pass criteria
The test is successful if the configured value is present in `uname -n` output.
##### Fail criteria
The test fails if  the configured hostname is not present in `uname -n` output.

### Verifying that the system hostname is unconfigured through the DHCP Server
#### Description
Test to verify whether the system hostname defaults to **switch** when option12 `option host-name` is not configured by the DHCP server.
#### Test result criteria
##### Pass criteria
The test is successful if default hostname **switch** is present in the `uname -n` output.
##### Fail criteria
The test fails if the default value **switch** is missing in the `uname -n` output.

## Test cases for system domain name configuration

### Objectives
These cases test the following:
   - Configuring, reconfiguring and unconfiguring the system domain name.
   - Verifying the expected behavior of the system domain name.

### Requirements
The requirements for this test case are:

 -  DHCP server

### Setup
#### Topology diagram

                                                +-------------------+
              +------------------+              | Linux workstation |
              |                  |eth0     eth1 |+-----------------+|
              |  AS5712 switch   |--------------||   DHCP Server   ||
              |                  |              |+-----------------+|
              +------------------+              +-------------------+


### Verifying that the system domain name is configured using CLI
#### Description
Test to verify whether the domain name of the system changes to the value configured using the `domain-name new-name` command in config mode.
#### Test result criteria
##### Pass criteria
The test is successful if the configured value is present in the `uname -n` output.
##### Fail criteria
The test fails if the configured domainname is missing in the `uname -n` output.

### Verifying that the system domain name is unconfigured using CLI
#### Description
Test to verify whether the domain name of the system is removed when unconfigured using the `no domain-name` command in config mode.
#### Test result criteria
##### Pass criteria
The test is successful if the pre existing domain name is no longer present in the `uname -n` output.
##### Fail criteria
The test fails if the pre existing value of domain name is  present in the `uname -n` output.

### Verifying that the system domain name is configured through the DHCP Server
#### Description
Test to verify whether the domain name of the system changes to the value configured by DHCP server via **dhclient** using option12 `option domain-name`.
#### Test result criteria
##### Pass criteria
The test is successful if the domain name value received through DHCP is present in the `uname -n` output.
##### Fail criteria
The test fails if  the configured domain name is not present in the `uname -n` output.

### Verifying that the system domain name is unconfigured through the DHCP Server
#### Description
Test to verify whether the system domain name ceases to exist when option12 `option domain-name` is not configured by the DHCP server.
#### Test result criteria
##### Pass criteria
The test is successful if preexisting domain name is no longer present in the `uname -n` output.
##### Fail criteria
The test fails if the preexisting domain name continues to be present in the `uname -n` output.
