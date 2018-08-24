## Buffer Monitoring component test cases ##

- verify the buffer monitoring  daemon without hardware description file

- verify the buffer monitoring daemon with proper hardware description file
    - Verify the buffer monitoring counter configuration
    - Confirm the periodic polling interval configuration
    - Verify the trigger based counter collection
    - Confirm the trigger rate and limit (trigger\_rate\_limit ) settings

##Test cases to verify the Buffer Monitoring Component##
### Objective ###
Verify that the buffer monitoring daemon works.
### Requirements ###
The requirements for this test case are:

 - AS5712 switch
 - Ixia

### Setup ###
#### Topology diagram ####
```ditaa
                                +-----------------------------------+
                                |                                   |
                                |           AS5712 switch           |
                                |                                   |
                                |                                   |
                                |                                   |
                                |   +-----+---+---+----+--------+   |
                                |   |  1  | 2 | 3 | 4  |  ...   |   |
                                |   +---------------------------+   |
                                +-----------------------------------+
                                       |     |
                                       |     +-+
                                       +-+     |
                                         |     |
                                    +-----------------------+
                                    |  +-----------------+  |
                                    |  |  1  | 2 | 3 | 4 |  |
                                    |  +-----+---+---+---+  |
                                    |                       |
                                    |                       |
                                    |                       |
                                    |                       |
                                    |        Ixia           |
                                    +-----------------------+

```

### Test case 1.01 : Verify bufmond without hardware description file   ###
#### Description ####
Verify that the bufmond daemon does not work without the buffer monitoring counters hardware description file (bufmond.yaml).

### Test result criteria ###
#### Test pass criteria ####
This test is successful if the error message "File not found. bufmond Exiting" is displayed and the bufmond daemon exits properly.
#### Test fail criteria ####
This test fails if the "File not found. bufmond Exiting" error message is not displayed.

### Test case 2.01 : Verify bufmond with hardware description file  ###
#### Description ####
Confirm that the bufmond daemon does work with the buffer monitoring counters hardware description file (bufmond.yaml) in place.

### Test result criteria ###
#### Test pass criteria ####
This test is successful if the bufmond is able to:
-Detect bufmond.yaml
-Parse the hardware description file
-Add all the counters to the bufmon table
#### Test fail criteria ####
This test fails if the bufmond is not able to
-Locate the path to the bufmond.yaml
-Display any counters in the bufmon table

### Test case 2.02 : Verify buffer monitoring counters configuration   ###
#### Description ####
Verify that the buffer monitoring counter configuration option is enabled or disabled.

### Test result criteria ###
#### Test pass criteria ####
This test is successful if the counter option is enabled and the "Counters Statistics" value is updated in the ovsdb bufmon table".

If the counter option is disabled the "Counters statistics" value is not updated.
#### Test fail criteria ####
This test fails if the counter configuration is enabled but the "bufmon" table counter row is not showing updated statistics.

### Test case 2.03 : Verify periodic polling interval configuration  ###
#### Description ####
Confirm that the periodic polling interval changes for the buffer monitoring collection.

### Test result criteria ###
#### Test pass criteria ####
This test is successful if the collection_period of "5"seconds is changed from 5 to 30 seconds and the "Counter statistics" are updated every 30 seconds in the ovsdb bufmon table.

#### Test fail criteria ####
This test fails if "Counter statistics" is not updated every 30 seconds in the ovsdb bufmon table.

### Test case 2.04 : Verify trigger based counter collection ###
#### Description ####
Confirm that the trigger-based buffer monitoring counters collection is working. Set the threshold limit for the buffer monitoring counter in the bufmon table and send traffic from the traffic generator.
### Test result criteria ###
#### Test pass criteria ####
This test is successful if the threshold limit is crossed, the "Counter statistics" are updated in the bufmon table row and the status is set to triggered.
#### Test fail criteria ####
This test fails if the "Counter statistics" are not updated in the bufmon table row.

### Test case 2.05 : Verify trigger\_rate\_limit settings ###
#### Description ####
Verify that the trigger, rate, and limit (trigger\_rate\_limit)settings for the counter collection works.

Set the threshold limit to lower values and wait for the trigger notification from the switch hardware. Verify the trigger rate limit is applied as per the trigger, rate, and limit settings.
### Test result criteria ###
#### Test pass criteria ####
This test is successful if the trigger rate limit is crossed and the "Counter statistics" are not updated in the bufmon table row and the "trigger notifications from the switch hardware dropped" messages are received.
#### Test fail criteria ####
This test fails if the "Counter statistics" are updated in the bufmon table row".