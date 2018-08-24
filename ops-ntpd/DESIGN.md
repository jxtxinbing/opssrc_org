# NTP Client Component Design

## Contents

- [High level design of NTP](#high-level-design-of-ntp)
  - [Configuration workflow](#configuration-workflow)
  - [Show information workflow](#show-information-workflow)
- [OVSDB design](#ovsdb-design)
- [OVSDB representation](#ovsdb-representation)
  - [NTP global configuration](#ntp-global-configuration)
  - [NTP global statistics](#ntp-global-statistics)
  - [NTP Association table](#ntp-association-table)
  - [NTP Key table](#ntp-key-table)
- [Design choices](#design-choices)
  - [Open source repository](#open-source-repository)
- [References](#references)


## High level design of NTP

```
            +----+             +----------------+
    +-----> |NTPD|             |                |
    |       +-+--+             |  CLI and REST  |
    |         |                |                |
    |       +-+--+             +-------+--------+
    |       |NTPQ|                     |
    |       +-+--+                     |
    |         |                        |
    |   +-----+--------+       +-------+---------+
    |   |              |       |                 |
    +---+   OPS-NTPD   +-------+      OVSDB      |
        |              |       |                 |
        +--------------+       +-----------------+

```
The NTP client feature provides the Network Time Protocol client functionality which synchronizes information from NTP servers. OpenSwitch uses the open source classic `ntpd` daemon for NTP functionality. The classic `ntpd` daemon provides both server and client functionality. However, OpenSwitch uses it only in NTP client mode.

The `ops-ntpd` Python daemon manages the `ntpd` daemon and sends configuration information using the `ntpq` query program. Periodically the `ops-ntpd` Python daemon polls and updates status information for the associations with the OVSDB database. This is the association status information used for the `show ntp associations` command.

By enabling NTP Authentication, the `ntpd` daemon uses the trusted keyid information configured with the association to authenticate servers, and uses only those servers for synchronizing time.

### Configuration workflow
When using NTP client, the operator is configuring NTP Association (servers) to be used by the NTP client to synchronize time information. The configuration specific to NTP client is maintained in the OVSDB protocol. The user configuration for NTP client is updated in the OVSDB database through the CLI and REST daemons.

The NTP client Python daemon monitors the OVSDB database for any configuration changes specific to NTP client, and if there are any configuration changes, the `ops-ntpd` Python daemon communicates the updates to the `ntpd` daemon using `ntpq`.

### Show information workflow
The `ops-ntpd` daemon periodically updates the NTP Association status information with the `ntpd` protocol (using `ntpq`) into OVSDB. This information is used to display when a call to `show NTP Association` is made.

The `ops-ntpd` daemon also updates the system info and statistics information about `ntpd` daemon which can be used for debugging purposes.

The `ntpd` daemon updates a log file whose output is displayed by issuing the `show ntp logging` command.

## OVSDB design
The OVSDB database is the central database used in OpenSwitch. All communication between different modules are facilitated through this database. The following tables and columns are used in the OVSDB database for NTP client functionality.
## OVSDB representation
```
  +---------------------------------------------------------+
  |                       OVSDB                             |
  |   +--------------------+                                |
  |   |                    |           +----------+         |
  |   |      SYSTEM        |           |          |         |
  |   |                    +----------->   VRF    |         |
  |   |  global config     |           |          |         |
  |   |  global statistics |           +----^-----+         |
  |   |                    |                |               |
  |   +--------------------+                |               |
  |                                         |               |
  |                                         |               |
  |                                         |               |
  |   +--------------------+        +-------+----------+    |
  |   |     NTP Key       |        |      NTP         |    |
  |   |                    <--------+   ASSOCIATIONS   |    |
  |   |   key id           |        |                  |    |
  |   |   key trust conf   |        | configuration    |    |
  |   |   md5 password     |        | status info      |    |
  |   |                    |        |                  |    |
  |   +--------------------+        +------------------+    |
  |                                                         |
  +---------------------------------------------------------+
```

### NTP global configuration
The following key=value pair mappings are used in the NTP config column of the System table for the global NTP configuration:

* The key **authentication_enable** has the value **true** if NTP Authentication is enabled, and the value **false** if NTP Authentication is disabled.

### NTP global statistics

The following key=value pair mappings are used in the NTP statistics column of the System table for global NTP statistics:

* The key **uptime** keeps information about the time in hours since the system was last rebooted.
* The key **ntp\_pkts\_received** keeps statistics about the total number of packets received.
* The key **ntp\_pkts\_with\_current\_version** keeps statistics about the number of packets matching the current NTP version.
* The key **ntp\_pkts\_with\_older\_version** keeps statistics about the number of packets matching the previous NTP version.
* The key **ntp\_pkts\_with\_bad\_length\_or\_format** keeps statistics about the number of packets with invalid length, format, or port number.
* The key **ntp\_pkts\_with\_auth\_failed** keeps statistics about the number of packets not verified as authentic.
* The key **ntp\_pkts\_declined** keeps statistics about the number of packets denied access for any reason.
* The key **ntp\_pkts\_restricted** keeps statistics about the number of packets restricted for any reason.
* The key **ntp\_pkts\_rate\_limited** keeps statistics about the number of packets discarded due to rate limitation.
* The key **ntp\_pkts\_kod\_responses** keeps statistics about the number of KoD packets from the server.

### NTP Association table
The NTP Association table has the following columns:


- **address**: The FQDN or IP address for the association.
- **key_id**: This column contains a reference to the NTP Key table.
- **vrf**: This column contains a weak reference to the VRF table.
- **association_attributes**: This column contains key=value pair mappings of association status information. The following key=value pair mappings are used:
  * The key **ref\_clock_id** stores the refclock driver ID. If available, a refclock driver ID like "127.127.1.0" is used for non uni/multi/broadcast associations.
  * The key **prefer** stores the preference flag for this association. Set this to <code>true</code> to enable the preference for this association.
  * The key **ntp_version** stores the NTP version used when communicating with this association.

- **association_status**: This column contains key=value pairs mapping of association status information. The following key=value pair mappings are used:

  * The key **remote\_peer_address** stores the remote peer's IP address to which the association is being synced. If FQDN is used as "address" during configuration, then it is the IP address.
  * The key **remote\_peer\_ref\_id** stores the reference ID used by the remote peer. This can be either another server or a stratum 1 devices like .GPS., .USNO., etc.
  * The key **stratum** stores the remote peer or server stratum.
  * The key **peer_type** stores the peer type (u: unicast or manycast client, b: broadcast or multicast client, l: local reference clock, s: symmetric peer, A: manycast server, B: broadcast server, or M: multicast server).
  * The key **last\_polled** stores when the peer was last polled ('d' days ago, 'h' hours ago, or seconds ago). For example, 5d, 6h, or 5 (this refers to seconds).
  * The key **polling_interval** stores the polling frequency (in seconds) used for this peer.
  * The key **reachability_register** stores status about the last consecutive polls for this peer (1 bit per poll).
  * The key **network_delay** stores the round trip communication delay to the remote peer or server
  (milliseconds).
  * The key **time_offset** stores the Root Mean Square time (in milliseconds) between the local host and the remote peer or server.
  * The key **jitter** stores jitter (in milliseconds) in the time reported for the remote peer or server.
  * The key **reference_time** stores the time (in "day, month date year hh:mm" format) when the server clock of refid was last adjusted. For example, in the format Wed, Jan 13 2016  7:56:26.126.
  * The key **root_dispersion** stores maximum error relative time (in seconds) to the primary reference clock.
  * The key **peer_status_word** stores information about the peer status. It can be either a candidate or a system selected peer. It can take on other states suuch as 'reject', 'falsetick', 'excess', 'outlier', or 'pps_peer'.
  * The key **associd** stores the Association ID for the peer. This is an Internal ID.

### NTP Key table
The NTP Key table has the following columns:


- **key_id**: This column specifies a key_id which is used for NTP authentication.
- **key_password**: This column specifies a key_password which is used for NTP authentication.
- **trust_enable**: This column enables trust settings for the key_id. By default it is **false**.


##Design choices

###Open source repository
There are multiple open source choices available for NTP. The open source from [ntp.org](http://www.ntp.org/) was chosen based on the following considerations:

* It is the standard NTP reference implementation and is widely used.
* It can be cross compiled without issues.
* It supports NTP authentication and advanced security measures for time synchronization.
* The NTP Project conducts research and development in NTP, and produces the Official Reference Implementation of NTP.
* The NTP Project drives standards, formalizes RFCs for newer implementations, and provides maintenance releases for common zero day issues.

##References
* [NTP references](http://doc.ntp.org/)
* [NTPQ references](http://doc.ntp.org/4.2.6p5/debug.html)
