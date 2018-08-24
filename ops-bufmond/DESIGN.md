#High level design of ops-bufmond (Buffer Monitoring)

Buffers Monitoring (BufMon) is a feature that provides OpenSwitch users the ability to monitor buffer space consumption inside the ASIC. It's useful for troubleshooting complex performance problems in the data center networking environment.

The feature is derived from Broadcom BroadView ([https://github.com/Broadcom-Switch/BroadView-Instrumentation](https://github.com/Broadcom-Switch/BroadView-Instrumentation "Broadview")), however, it is designed to be generic and not tied to specific ASICs. Any ASIC which has buffer counters, can provide this information through this feature's interface.

##Reponsibilities
The ops-bufmond module is responsible for monitoring and collecting the buffer space consumption inside the ASIC.

## Design choices

The design decisions made for buffer monitoring modules are:

- bufmond:
	- The bufmond python script is responsible for creating counter details in the ovsdb bufmon table.
	- The bufmond python script uses the pyyaml library to parse the hardware description file.

- Sysd: The sysd daemon creates the proper symlink to the ASIC specific bufmond hardware description yaml file.

- Switchd:
  -  The platform independent piece of code handles configuration and statistics collection, based on the buffer monitoring counters configuration that resides in the database.
  -  The platform dependent bufmon layer (bufmon provider) provides the interface to configure switch hardware and collects periodic statistics from the switch hardware.

##Relationships to external OpenSwitch entities

The following diagram provides a detailed description of the buffer monitoring module's relationships and interactions with other modules in the switch.

```ditaa



	                    +-------------------------------------------------------+
	                    |                                                       |
	                    |                            +-----------------------+  |
	                    |                       +-+  | Switchd               |  |
	+------------+      |      +-----------+    |O|  | +------------------+  |  |
	| Broadview  |      |      | Broadview +<-->+V|  | | ASIC Independent |  |  |
	| Collectors +<----------> |  Daemon   |    |S+<-->|   Bufmon.c       |  |  |
	+------------+      |      +-----------+    |D|  | +------------------+  |  |
	                    |      +-----------+    |B|  |                       |  |
	                    |      |   Sysd    +<-->+ |  | +------------------+  |  |
	                    |      |           |    |S|  | |   ASIC Bufmon    |  |  |
	                    |      +-----------+    |E|  | |    Provider      |  |  |
	                    |      +-----------+    |R|  | +------------------+  |  |
	                    |      |  Bufmond  +<-->+V|  |                       |  |
	                    |      |           |    |E|  | +------------------+  |  |
	                    |      +-----------+    |R|  | |    ASIC SDK      |  |  |
	                    |                       +-+  | +------------------+  |  |
	                    |                            +-----------------------+  |
	                    |      +----------------------------------------+       |
	                    |      |                          +-----------+ |       |
	                    |      |                          |ASIC Driver| |       |
	                    |      |                          +-----------+ |       |
	                    |      | Kernel                                 |       |
	                    |      +----------------------------------------+       |
	                    |                                                       |
	                    +-------------------------------------------------------+
```


##OVSDB-Schema
The buffer monitoring related columns on the OpenSwitch table are bufmon\_config column and bufmon\_info column. The "bufmon\_config" column has the configuration information and the "bufmon\_info" has the  switch hardware buffer monitoring capabilities information. The buffer monitoring counter details the related columns handled on the bufmon table.

```ditaa
+------------------------------------------------------------------------------------+
|                                                                                    |
|                                                                   OVSDB            |
|                                                                                    |
|  +----------------------------+       +--------------------------------+           |
|  |                   System   |       |                       bufmon   |           |
|  |                            |       |  hw_unit_id                    |           |
|  |                            |       |  name                          |           |
|  |                            |       |  counter_vendor_specific_info  |           |
|  |                            |       |  enabled                       |           |
|  | bufmon_config              |       |  counter_value                 |           |
|  | bufmon_info                |       |  status                        |           |
|  |                            |       |  trigger_threshold             |           |
|  +----------------------------+       +--------------------------------+           |
|                                                                                    |
+------------------------------------------------------------------------------------+
```

System Table:

The keys and values supported by the bufmon\_config column are:

|    Key                                  |    Value       | Description               |
| ----------------------------------------|----------------|-----------------------------------
| enabled                                 | string         | Specifies  whether the feature is         															  enabled on the system.  False, if the                                                                value is not present.
| counters_mode                           | string         | Specifies whether counters should 															         report their current values or peak                                                                  values since last collection.
| periodic_collection_enabled             | string         | Specifies  whether  periodic                                                                        collection of the counters is enabled.                                                              False, if the value is not present.
| collection_period                       | string         | Specifies the collection time period in 															  seconds. Five seconds is the default,                                                                if the value is not present.
| threshold_trigger_collection_enabled    | string         | Specifies whether the counters should 																 be collected immediately or not when                                                                one of the thresholds is crossed. The 																 default is "True" if the value is not 														         present.
| threshold_trigger_rate_limit            | string         | Specifies the maximum number of trigger 															  generated  reports per minute. The 														         limit is averaged and imposed upon a 																 per second basis. For example, the 															     value of 600 allows a report every                                                                  100ms. If no value is set, the default                                                              is 60 trigger generated  reports once                                                                per second.
| snapshot_on_threshold_trigger           | string         | Specifies whether or not counters 																     should be frozen when one of the                                                                    thresholds is crossed. the default is                                                                True, if the value not present.


The keys and values supported by the bufmon\_info column are:

|    Key                                  |    Value       | Description               |
| ----------------------------------------|----------------|-----------------------------------
| cap_mode_peak                           | string         | Specifies whether or not the system is 															 capable of collecting the peak values                                                                of the counters. The default is False,                                                              if the value is not present.
| cap_mode_current                        | string         | Specifies whether or not the system is 												             capable of collecting current values of                                                              the counters. The default is False if                                                                the value is not present.
| cap_snapshot_on_threshold_trigger       | string         | Specifies whether or not the system is capable of freezing counter values on the threshold crossing. The default is False if the value is not present
| cap_threshold_trigger_collection        | string         | Specifies whether or not the system is capable of immediately collecting values on the threshold crossing. The default is False if the value is not present.
| last_collection_timestamp               | string         | Specifies the timestamp of the last                                                                  collection in seconds from Jan 1, 1970.
Bufmon Table:

|    Column                               | Type           | Description               |
| ----------------------------------------|----------------|-----------------------------------
| hw_unit_id                              | integer        | Identifies the switch hardware unit 															     number that the counter belongs to.
| name                                    | string         | Name of the counter as it is displayed 															 in the management systems and is                                                                    referenced by all the interested                                                                    agents. No spaces should be used in the                                                              name.
| counter_vendor_specific_info            | map string     |  Help the ASIC specific driver to 																	  identify the counter. Both keys and                                                                 values are driver and ASIC specific.
| enabled                                 | bool           | Specifies if the counter is enabled.
| trigger_threshold                       | integer        | Specified counter specific threshold                                                                limit that would trigger  collection.
| counter_value                           | integer        | Last collected value of the counter.
| status 						          | string         | Specifies the status of the counter. 														         The options are: -Ok -Not properly 																 configured -Triggered


##Internal structure

The various functionality of sub-modules are:

####BroadView####
This daemon is being contributed by Broadcom and is based on the Broadview Github ([https://github.com/Broadcom-Switch/BroadView-Instrumentation](https://github.com/Broadcom-Switch/BroadView-Instrumentation "Broadview")). The main difference from the one in GitHub, would be the way it communicates to the OVSDB. The daemon's responsibility is to communicate to the user, over its JSON-RPC protocol and configure or retrieve counters throughout the OVSDB database.

####Bufmond####
This daemon creates one row per counter in the bufmon table according to hardware description file. This daemon also publishes the buffer monitoring capabilities information to the bufmon\_info column which is part of system table.

####Sysd####
Sysd creates a proper symlink in the ASIC specific hardware description file, It contains a description of all the counters that exist in a given ASIC as well as capabilities of the specific ASIC.
####Switchd####
Switchd configures switch hardware based on a buffer monitoring configuration in the system and in the bufmon table.

Switchd uses the bufmon layer (bufmon provider) API's to configure the switch hardware and to collect statistics from the switch hardware.

In switchd, the thread "bufmon_ stats_thread" collects statistics periodically and monitors trigger notifications in the switch hardware. The same thread notifies the switchd main thread to push the counter statistics into the database.
####Hardware description file####
The buffer monitoring counters hardware description YAML file (bufmond.yaml) has to be generated per specific platform and not generically for the switch hardware. The reason is that the ASICs might provide different sets of counters given different configurations on the specific platform.

Example buffer monitoring capabilities and counters yaml description:

cap_mode_current: true
cap_mode_peak: true
cap_snapshot_on_threshold_trigger: true
cap_threshold_trigger_collection: true
counters:
\- name: device/data/NONE/NONE
  counter_vendor_specific_info:
    counter_name: data
  hw_unit_id: 0
\- name: ingress-port-priority-group/um-share-buffer-count/1/1
  counter_vendor_specific_info:
    counter_name: um-share-buffer-count
    port: '1'
    priority-group: '1'
  hw_unit_id: 0


##References

* [Broadcom BroadView](https://github.com/Broadcom-Switch/BroadView-Instrumentation)
