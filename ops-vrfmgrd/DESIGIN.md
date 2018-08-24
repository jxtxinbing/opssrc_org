High level design of OPS_VRFMGRD
============================
The `ops-vrfmgrd daemon` manages to create a namespace and delete a namespace when a new VRF is added or deleted in the database.

Reponsibilities
---------------
- Manages to create a namepace on configuring a new VRF on the database.
- Moves the interfaces to default namespace if any, and deletes a namespace when a VRF is deleted from the database.

Design choices
--------------
The `ops-vrfmgrd` was added to enterprise openswitch architecture so that there would be ne entity responsiblle for managing creation and deletion of namespaces

Relationships to external OpenSwitch entities
---------------------------------------------

               +--------------------+             +--------------------+
               |                    |             |                    |
               |        CLI         |             |       REST         |
               |                    |             |                    |
               +---------+----------+             +---------+----------+
                         |                                  |
                         |                                  |
                         |                                  |
               +---------v----------------------------------v-----------+
               |                      OVSDB                             |
               | +-------------------------+       +------------------+ |
               | |      System             |       |                  | |
               | |       table             |       |   VRF Table      | |
               | |-vrfs Ref Table          +------>|                  | |
               | +-------------------------+       +------------------+ |
               +--------------------------------------------------------+
                                     |
                                     |
                                     |
                        +------------v--------------+       +---------------------------+
                        |                           |       | Create a namesapce        |
                        |  ops-vrfmgrd Daemon       +------>|                           |
                        |                           |       | Delete a namespcae        |
                        +---------------------------+       +---------------------------+

OVSDB-Schema
------------
The `ops-vrfmgrd` reads the following columns in system table
```
cur_cfg - To know system is check system is configured at startup
```

The `ops-vrfmgrd` reads the following columns in vrf table.
```
name - To know what is the name of the VRF that is configured.
```

The `ops-vrfmgrd` writes the following columns in vrf table.
```
status - Updates the key:value pair, which specifies if a namespace is created for a VRF or not.
```

Internal structure
------------------
Initially subscribe to database table and columns that are needed for ops-vrfmgrd daemon.

The ops-vrfmgrd daemon main loop monitors  the:

* On a VRF addition, the OVSDB triggers a insert notification which is listened by the daemon and creates a namespace on the switch with a unique name which is the uuid of the newly created VRF table.
* On a VRF deletion, the OVSDB triggers a delete notification which is listened by the daemon and daemon checks if any interfaces are associated with the namespace, if yes then the daemon is responsible to move interfaces to deafult namespace and delet the namespace else daemin directlydletes the namespace.


References
----------
* [vrf-cli](/documents/user/vrf-cli)
