# High-level Design of OPS-MGMT-INTF

Table of contents

- [Goals](#goals)
- [Responsibilities](#responsibilities)
- [Design choices](#design-choices)
- [Relationships to external OpenSwitch entities](#relationships-to-external-openswitch-entities)
- [OVSDB schema](#ovsdb-schema)
- [Internal structure](#internal-structure)
 - [CLI](#cli)
 - [REST](#rest)
 - [Management interface daemon](#management-interface-daemon)
 - [DHCP client](#dhcp-client)
- [References](#references)

## Goals
The primary goal of the management module is to facilitate the management of the device. It provides the following:

- Device access and configuration
- Event collection for monitoring, analysis, and correlation
- Device and user authentication, authorization, and accounting
- Device time synchronization
- Device image downloading

The device is configured or monitored through the management interface. All management traffic such as `ssh` to the device, `tftp`, etc., goes through the management interface.

## Responsibilities

The management interface module is responsible for:

- Configuring the mode in which the management interface should operate.

- Populating the OSVDB protocol with DHCP client populated values (IP, subnet, default gateway, and nameserver) when the mode is `dhcp`.

-  Providing support for configuration of the IP, default gateway and nameserver when the mode is `static`.
- Starting the DHCP client when the mode is configured as `DHCP`.

- Updating the DHCP populated values in the OVSDB protocol when the DHCP server provides new values.

- Stoping the DHCP client when the mode is configured as `static`.

- Configuring the system hostname through `CLI` or `DHCP`.

- Configuring the system domain name through `CLI` or `DHCP`.

## Design choices

The design decisions made for management interface modules are:

- The same mode is used for both IPv4 and IPv6 configuration.
- No configurations are allowed in DHCP mode other than mode change.
- Users cannot modify the physical interface that is marked as management interface.


##Relationships to external OpenSwitch entities

The management interface related columns on the OpenSwitch table are the **mgmt\_intf** column and the **mgmt\_intf\_status** column. The **mgmt\_intf** column has the configuration information and the **mgmt\_intf\_status** column has the status information of the attributes configured.
```ditaa
        +---------------+              +---------------+        +------------------------+
        |               |              |               |        |  Modules that require  |
        |   CLI         |              |    REST       |        |  Mgmt Intf attributes  |
        |               |              |               |        |                        |
        +--------+------+              +------+--------+        +----------+-------------+
                 |                            |                            |
                 |                            |                            |
                 |                            |                            |
            +--------------------------------------------------------------v---------------------+
            |  +----------------------------------------+                          OVSDB         |
            |  |                             System     |                                        |
            |  | mgmt_intf_col                          |                                        |
            |  | mgmt_intf_status_col                   |                                        |
            |  | hostname                               |                                        |
            |  | domain_name                            |                                        |
            |  +----------------------------------------+                                        |
            +------------------------------------------------------------------------------------+
                                  |
                                  |
                                  |
                                  |
                +-----------------+--------------------+
                |                                      |
                |  Management Interface                |        +------------------+
                |                                      +--------+                  |
                |                  Daemon              |        |   Dhclient       |
                |                                      |        |                  |
                +--------------------------------------+        +------------------+
```


## OVSDB schema

The management interface related columns in the OpenSwitch table are the **mgmt\_intf** and **mgmt\_intf\_status** columns. The **mgmt\_intf** column has the configuration information, and the **mgmt\_intf\_status** has the status information of the configured attributes.
```ditaa
        +------------------------------------------------------------------------------------+
        |  +----------------------------------------+                          OVSDB         |
        |  |                             System     |                                        |
        |  | mgmt_intf_col                          |                                        |
        |  | mgmt_intf_status_col                   |                                        |
        |  | hostname                               |                                        |
        |  | domain_name                            |                                        |
        |  +----------------------------------------+                                        |
        +------------------------------------------------------------------------------------+
```

The keys and values supported by the management interface columns are:

|    Key  |    Value       |
| --------|----------------|
| name      | string       |
| mode      | string       |
| ip      | An IPv4 address   |
| subnet_mask    | Integer with range 1 to 31   |
| ipv6    | An IPv6 address   |
| default_gateway      | An IPv4 address   |
| default_gateway_v6    | An IPv6 address   |
| dns_server_1      | An IPv4 address   |
| dns_server_2    | An IPv4 address   |
| ipv6_linklocal| An IPv6 address   |
| link_state      | string       |
| hostname      | string       |
| dhcp_hostname      | string       |
| domain_name   | string   |
| dhcp_domain_name   | string       |

## Internal structure

The following describes the functionality of the submodules:

### CLI
The CLI module is used for configuring the various management interface modes and attributes, system hostname, and domain name. The CLI provides a basic check of the parameters entered, like checking the validity of the IP entered, checking the mode before any parameter configuration, and checking if the hostname provided is alpha-numeric. The **mgmt\_intf** and **hostname** columns are updated by the CLI.

The CLI displays the interface parameters configured using the **mgmt\_intf\_status** column. If the configuration fails at the daemon, then those configurations are present in the **mgmt\_intf** column and not in the **mgmt\_intf\_status** column.

### REST
The REST module works similar to CLI. The operations allowed on the **System** table are GET and PUT.

### Management interface daemon
The management interface daemon is responsible for retrieving the configurations from CLI, and configuring them on the physical interface marked as management interface. In DHCP mode, the management interface reads the DHCP client populated values and updates the **mgmt\_intf\_status** column.

The other responsibilities of the management interface daemon include:
- The management interface maintains the state of the physical port configured as management interface.
- When the hostname is configured through management interfaces like CLI or DHCP, the management interface daemon configures the new hostname in the system. If none of these are available, the system hostname defaults to **switch**
- When the domain name is configured through management interfaces such as CLI or DHCP, the management interface daemon appends the host name with the domain name and configures the new hostname to the system. If host name contains the default value, then no modification is made.

In `static` mode, the user configures the IP, default gateway, and name servers addresses through CLI/REST. The management interface daemon configures these values in the physical interface marked as management interface, and updates the **mgmt\_intf\_status** column.

In `DHCP` mode, the management interface daemon listens on the netlink socket. Any change in the IP or link state is notified to the management interface daemon by the netlink module. On reception of notification, the management interface daemon reads the IP, default gateway,and nameservers addresses populated by DHCP client, and updates the **mgmt\_intf\_status** column.

### DHCP client
The `dhclient` is used as a DHCP client. The management interface starts or stops the DHCP client based on the mode. Separate DHCP client instances are spawned for IPv4 and IPv6. Since the same mode parameter is used to control both IPv4 and IPv6, both the instances are started and stopped at the same time.

## References

* [Management Interface Command Reference](/documents/user/mgmt_intf_cli)
