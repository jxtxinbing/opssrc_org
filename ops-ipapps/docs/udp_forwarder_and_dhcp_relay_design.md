High level design of UDP Forwarder and DHCP-Relay
=================================================

UDP Broadcast Forwarder:
The routers by default do not forward broadcast packets. This is to avoid packet flooding on the network. However, there are situations where it is desirable to forward certain broadcast packets.The UDP (User Datagram Protocol) broadcast forwarder takes up the client's UDP broadcast packet and forwards it to the configured server(s) in a different subnet.

DHCP-Relay:
A DHCP-Relay as name indicates relay the DHCP packets between a client and server(s). The requests are broadcasted by the clients on their local network, the relay-agent forwards them to the DHCP server as a unicast packet.  The returned DHCP answer gets to the relay-agent as a unicast packet, and the relay-agent sends the answer on the client’s network.

A DHCP-Relay modifies IP TTL in the DHCP packet, understands DHCP protocol and does relay packet in accordance to RFC-2131. The UDP forwarder on the other hand, just forwards the configured UDP protocol broadcast packets to the configured server(s). The DHCP relay and UDP forwarder expects the packet to be non fragmented, the fragmented packets will not be forwarded.

## Contents
- [Responsibilities](#responsibilities)
- [Design choices](#design-choices)
- [Participating Modules](#participating-modules)
- [Sub-module interactions](#sub-module-interactions)
- [OVSDB-Schema](#ovsdb-schema)
- [Any other sections that are relevant for the module](#any-other-sections-that-are-relevant-for-the-module)
- [References](#references)


## Responsibilities
-------------------
UDP Forwarder daemon supports forwarding following application UDP broadcast packets to configured server(s)
 dns(53), ntp(123), netbios-ns(137), netbios-dgm(138), radius(1812), radius-old(1645),
 rip(520), snmp(161), snmp-trap(162), tftp(69), timep(37)

DHCP-Relay enables support for the following features
1. IPv4 DHCP-Relay Agent
2. IPv4 DHCP-Relay options support

## Design choices
-----------------
UDP forwarder daemon functions with the help of following threads.

Main Thread : Schedule idl cache updations and if any configuration change is noticed, update the local database by acquiring a lock.
Packet Receiver Thread : This thread is used to receive UDP broadcast packets and also DHCP unicast server replies to the relay agent. Received packets are delegated to DHCP-Relay/UDP forwarder handler for further processing within the same thread context.

Following sequence diagrams describe the packet handling high-level design.

UDP-Forwarder :

```ditaa
                         +-------------------------------------------------------+
                         |                                                       |
 UDP-Client              |      UDP-Bcast-Receiver            UDP-Forwarder      |                  UDP-Server
     |                   |           |                            |              |                      |
     |  UDP bcast packet from client |                            |              |                      |
     |-------------------|---------->|                            |              |                      |
     |                   |           | client pkt to UDP forwarder|              |                      |
     |                   |           |--------------------------->|              |                      |
     |                   |           |                            |  Ucast/Bcast |pkt to server         |
     |                   |           |                            |--------------|--------------------->|
     |                   |           |                            |              |                      |
     |                   |           |                            |              |                      |
                         |                                                       |
                         |                  UDP Forwarder                        |
                         +-------------------------------------------------------+

```


DHCP-Relay :

```ditaa
                         +-------------------------------------------------------+
                         |                                                       |
DHCP-Client              |      UDP-Bcast-Receiver            DHCP-Relay         |                  DHCP-Server
     |                   |           |                            |              |                      |
     |   DHCP packet to s|erver      |                            |              |                      |
     |-------------------|---------->|                            |              |                      |
     |                   |           |  DHCP Bcast pkt to relay   |              |                      |
     |                   |           |--------------------------->|              |                      |
     |                   |           |                            |  Unicast pkt |to server             |
     |                   |           |                            |--------------|--------------------->|
     |                   |           |                            |       unicast| resp from server     |
     |                   |           |                            |<-------------|----------------------|
     |              Serve|r response to client                    |              |                      |
     |<------------------|-----------|----------------------------|              |                      |
     |                   |           |                            |              |                      |
     |                   |           |                            |              |                      |
                         |                                                       |
                         |                  DHCP-Relay Agent                     |
                         +-------------------------------------------------------+

```


## Participating modules
------------------------

```ditaa
                            +--------------------------+
                            |     UDP-Forwarer and     |
                            |     DHCP-Relay UI        |
                            |   (CLI/REST/Ansible)     |
                            |                          |
                            +-----------^--------------+
                                        |
                                        |
 +-----------------------+              |
 |                       |        +-----v-------+      +-------------+
 |    UDP Forwarder/     |        |             |      |             |
 |    DHCP-Relay         |        |             |      | DHCP-Server |
 |                       <-------->             <------>             |
 |                       |        |             |      |             |
 +---^---------------^---+        |             |      +-------------+
     |               |            |             |
     | UDP Bcast Pkt |            |    OVSDB    |
     |     Tx/Rx     |            |             |
     |               |            |             |
     |               |            |             |
+----v---------------v---+        |             |      +--------------+
|                        |        |             |      |              |
|    Kernel Interfaces   |        |             <------>     port     |
|                        |        |             |      |              |
|                        |        |             |      |              |
+------------------------+        +-------------+      +--------------+
```

Detailed description of the relationships and interactions
1. UDP Forwarder and DHCP-Relay UI : DHCP global configurations and interface level configurations. Also this module takes care of the statistics display
2. UDP Forwarder/DHCP-Relay : Listens to OVSDB notifications for config changes and interacts with kernel interfaces to receive and send DHCP packets to DHCP client/server
3. DHCP-Server : DHCP-Server and DHCP-Relay configuration on an interface are mutually-exclusive.
4. port : When a port is deleted, DHCP-Relay configuration on it shall be flushed.

## Sub-module interactions
--------------------------

```ditaa
     /-----------\               /----------\             /-------------\            /-------\
     |UDP pkt    |               |DHCP relay|             |UDP Forwarder|            |Raw pkt|
     |receiver   |               \----------/             \-------------/            |sender |
     \-----------/                                                                   \-------/
           |                           |                         |                        |
           | DHCP broadcast received   |                         |                        |
           | on dest port (67)         |                         |                        |
           |-------------------------->|                         |                        |
           |                           |If bootp request and i/p |                        |
           |                           |iface has helper config  |                        |
           |                           |Send ucast pkt to server |                        |
           |                           |------------------------------------------------->|
           |                           |                         |                        |
           |                           |                         |                        |
           | DHCP unicast received     |                         |                        |
           | on dest port (67)         |                         |                        |
           |-------------------------->|                         |                        |
           |                           |If bootp reply & gw in   |                        |
           |                           |dhcp hdr is local ip,    |                        |
           |                           |ucast or bcast the packet|                        |
           |                           |through helper intf      |                        |
           |                           |------------------------------------------------->|
           |                           |                         |                        |
           |UDP broadcast is received f|rom client               |                        |
           |---------------------------|------------------------>|                        |
           |                           |                         |If bcast server is      |
           |                           |                         |configured, send the pkt|
           |                           |                         |to ucast/bcast          |
           |                           |                         |destination             |
           |                           |                         |----------------------->|
           |                           |                         |                        |
           |                           |                         |                        |
```

##OVSDB-Schema
--------------

Following OVSDB tables are introduced for DHCP-Relay functionality. Schema is designed in such a way that it accommodates the UDP forwarder feature going forward.

VRF:other_config
Key:
dhcp_relay_enabled
Value:
true, false

Key:
udp_fwd_enabled
Value:
true, false


New Tables :

UDP_Bcast_Forwarder_Server : Place holder for server configuration for dhcp-relay and udp forwarder.
DHCP_Relay_Statistics : Place holder for DHCP relayed packets statistics.

```

Table descriptions:

  UDP_Bcast_Forwarder_Server Table:
    ports : Port on which current configuration is made
    dst_udp_port : Destination UDP port of the broadcast packet
    ipv4_ucast_server : List of IPv4 server destinations
    ipv6_ucast_server : List of IPv6 server destinations
    ipv6_server : Key, value pairs of multicast or link local destination and the output port

  Dhcp_Relay_Statistics:
    ports : Port to which statistics belong to
    ipv4_stats : IPv4 dhcp-relay packet statistics
    ipv6_stats : IPv6 dhcp-relay packet statistics

```

##Any other sections that are relevant for the module
-----------------------------------------------------
N/A


##References
------------
Dynamic Host Configuration Protocol (https://tools.ietf.org/html/rfc2131)
DHCP Relay Agent Information Option (https://tools.ietf.org/html/rfc3046)

