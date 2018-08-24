# Traceroute Utility

## Contents

- [Traceroute options](#traceroute-options)
- [Traceroute6 options](#traceroute6-options)

## Traceroute options
### IPv4 address
#### Syntax
`traceroute <IPv4-address>`
#### Description
This command is used to traceroute the specified IPv4 address.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv4-address*|Required| A.B.C.D | IPv4 address to traceroute.|
#### Examples
```
switch# traceroute 10.0.10.1
traceroute to 10.0.10.1 (10.0.10.1) , 1 hops min, 30 hops max, 3 sec. timeout, 3 probes
  1   10.0.40.2  0.002ms  0.002ms  0.001ms
  2   10.0.30.1  0.002ms  0.001ms  0.001ms
  3   10.0.10.1  0.001ms  0.002ms  0.002ms
```

### Hostname
#### Syntax
`traceroute <hostname>`
#### Description
This command is used to traceroute the specified Hostname.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*hostname* |Required | string | Hostname to traceroute. Length must be less than 256 characters.|

#### Examples
```
switch# traceroute localhost
traceroute to localhost (127.0.0.1), 1 hops min, 30 hops max, 3 sec. timeout, 3 probes
  1   127.0.0.1  0.018ms  0.006ms  0.003ms
```

### Set maximum TTL
#### Syntax
`traceroute ( <IPv4-address> | <hostname> ) maxttl <number>`
#### Description
This command sets the maximum number of hops used in outgoing probe packets. The default value is 30.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv4-address*|Required| A.B.C.D | IPv4 address to traceroute.|
|*hostname* |Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *number*  |Optional |<1-255> | Select maximum number of hops used in outgoing probe packets between 1 to 255.|
#### Examples
```
switch# traceroute 10.0.10.1 maxttl 20
traceroute to 10.0.10.1 (10.0.10.1) , 1 hops min, 20 hops max, 3 sec. timeout, 3 probes
  1   10.0.40.2  0.002ms  0.002ms  0.001ms
  2   10.0.30.1  0.002ms  0.001ms  0.001ms
  3   10.0.10.1  0.001ms  0.002ms  0.002ms
```

### Set minimum TTL
#### Syntax
`traceroute ( <IPv4-address> | <hostname> ) minttl <number>`
#### Description
This command sets the minimum number of hops used in outgoing probe packets. The default value is 1.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv4-address*|Required| A.B.C.D | IPv4 address to traceroute.|
|*hostname* |Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *number*  |Optional |<1-255> | Select minimum number of hops used in outgoing probe packets between 1 to 255.|
#### Examples
```
switch# traceroute 10.0.10.1 minttl 1
traceroute to 10.0.10.1 (10.0.10.1) , 1 hops min, 30 hops max, 3 sec. timeout, 3 probes
  1   10.0.40.2  0.002ms  0.002ms  0.001ms
  2   10.0.30.1  0.002ms  0.001ms  0.001ms
  3   10.0.10.1  0.001ms  0.002ms  0.002ms
```

### Set destination port
#### Syntax
`traceroute ( <IPv4-address> | <hostname> ) dstport <number>`
#### Description
This command sets the destination port. The default value is dstport 33434.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv4-address*|Required| A.B.C.D | IPv4 address to traceroute.|
|*hostname* |Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *number*  |Optional |<1-34000>| Select the destination port number.|
#### Examples
```
switch# traceroute 10.0.10.1 dstport 33434
traceroute to 10.0.10.1 (10.0.10.1) , 1 hops min, 30 hops max, 3 sec. timeout, 3 probes
  1   10.0.40.2  0.002ms  0.002ms  0.001ms
  2   10.0.30.1  0.002ms  0.001ms  0.001ms
  3   10.0.10.1  0.001ms  0.002ms  0.002ms
```

### Set probes
#### Syntax
`traceroute ( <IPv4-address> | <hostname> ) probes <number>`
#### Description
This command sets the number of probe queries to send out for each hop. The default value is 3.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv4-address*|Required| A.B.C.D | IPv4 address to traceroute.|
|*hostname* |Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *number*  | Optional| <1-5>  | Select the number of probe queries to send out for each hop between 1 to 5.|
#### Examples
```
switch# traceroute 10.0.10.1 probes 3
traceroute to 10.0.10.1 (10.0.10.1) , 1 hops min, 30 hops max, 3 sec. timeout, 3 probes
  1   10.0.40.2  0.002ms  0.002ms  0.001ms
  2   10.0.30.1  0.002ms  0.001ms  0.001ms
  3   10.0.10.1  0.001ms  0.002ms  0.002ms
```

### Set timeout
#### Syntax
`traceroute ( <IPv4-address> | <hostname> ) timeout <time>`
#### Description
This command sets the time in seconds to wait for a response to a probe. The default value is 3 seconds.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv4-address*|Required| A.B.C.D | IPv4 address to traceroute.|
|*hostname* |Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *time* | Optional|<1-60> | Select time in seconds to wait for a response to a probe between 1 and 60.|
#### Examples
```
switch# traceroute 10.0.10.1 timeout 5
traceroute to 10.0.10.1 (10.0.10.1) , 1 hops min, 30 hops max, 5 sec. timeout, 3 probes
  1   10.0.40.2  0.002ms  0.002ms  0.001ms
  2   10.0.30.1  0.002ms  0.001ms  0.001ms
  3   10.0.10.1  0.001ms  0.002ms  0.002ms
```

### Set ip-option loose source route
#### Syntax
`traceroute ( <IPv4-address> | <hostname> ) ip-option loosesourceroute <IPv4-Address> `
#### Description
This command is used to set the the intermediate loose source route address.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv4-address*|Required| A.B.C.D | IPv4 address to traceroute.|
|*hostname* |Required | string | Hostname to traceroute. Length must be less than 256 characters.|
|*IPv4-address*|Optional | A.B.C.D | Loose source route address to traceroute.|
#### Examples
```
switch# traceroute 10.0.10.1 ip-option loosesourceroute 10.0.40.2
traceroute to 10.0.10.1 (10.0.10.1) , 1 hops min, 30 hops max, 3 sec. timeout, 3 probes
  1   10.0.40.2  0.002ms  0.002ms  0.001ms
  2   10.0.30.1  0.002ms  0.001ms  0.001ms
  3   10.0.10.1  0.001ms  0.002ms  0.002ms
 ```

##Traceroute6 options

### IPv6 address
#### Syntax
`traceroute6 <IPv6-address>`
#### Description
This command is used to traceroute the specified IPv6 address.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv6-address*|Required|X:X::X:X| IPv6 address to traceroute.|
#### Examples
```
switch# traceroute6 0:0::0:1
traceroute to 0:0::0:1 (::1) from ::1, 30 hops max, 3 sec. timeout, 3 probes, 24 byte packets
 1  localhost (::1)  0.117 ms  0.032 ms  0.021 ms
```

### Hostname
#### Syntax
`traceroute6 <hostname>`
#### Description
This command is used to traceroute the specified Hostname.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
| *hostname*|Required | string | Hostname to traceroute. Length must be less than 256 characters.|
#### Examples
```
switch# traceroute6 localhost
traceroute to localhost (::1) from ::1, 30 hops max, 3 sec. timeout, 3 probes, 24 byte packets
 1  localhost (::1)  0.189 ms  0.089 ms  0.025 ms
```

### Set maximum TTL
#### Syntax
`traceroute6 ( <IPv6-address> | <hostname> ) maxttl <number>`
#### Description
This command sets the maximum number of hops used in outgoing probe packets. The default value is 30.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv6-address*|Required|X:X::X:X| IPv6 address to traceroute.|
| *hostname*|Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *number*  | Optional| <1-255>|Select maximum number of hops used in outgoing probe packets between 1 to 255.|
#### Examples
```
switch# traceroute6 0:0::0:1 maxttl 30
traceroute to 0:0::0:1 (::1) from ::1, 30 hops max, 3 sec. timeout, 3 probes, 24 byte packets
 1  localhost (::1)  0.117 ms  0.032 ms  0.021 ms
```

### Set destination port
#### Syntax
`traceroute6 ( <IPv6-address> | <hostname> ) dstport <number>`
#### Description
This command sets the destination port. The default value is dstport 33434.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv6-address*|Required|X:X::X:X| IPv6 address to traceroute.|
| *hostname*|Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *number* |Optional |<1-34000>| Select the destination port number.|
#### Examples
```
switch# traceroute6 0:0::0:1 dsrport 33434
traceroute to 0:0::0:1 (::1) from ::1, 30 hops max, 3 sec. timeout, 3 probes, 24 byte packets
 1  localhost (::1)  0.117 ms  0.032 ms  0.021 ms
```

### Set probes
#### Syntax
`traceroute6 ( <IPv6-address> | <hostname> ) probes <number>`
#### Description
This command sets the number of probe queries to send out for each hop. The default value is 3.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv6-address*|Required|X:X::X:X| IPv6 address to traceroute.|
| *hostname*|Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *number*  |Optional | <1-5>  | Select the number of probe queries to send out for each hop between 1 to 5.|
#### Examples
```
switch# traceroute6 0:0::0:1 probes 3
traceroute to 0:0::0:1 (::1) from ::1, 30 hops max, 3 sec. timeout, 3 probes, 24 byte packets
 1  localhost (::1)  0.117 ms  0.032 ms  0.021 ms
```

### Set timeout
#### Syntax
`traceroute6 ( <IPv6-address> | <hostname> ) timeout <time>`
#### Description
This command sets the time in seconds to wait for a response to a probe. The default value is 3 seconds.
#### Authority
Root user.
#### Parameters
| Parameter | Status  | Syntax | Description |
|-----------|---------|--------|-------------|
|*IPv6-address*|Required|X:X::X:X| IPv6 address to traceroute.|
| *hostname*|Required | string | Hostname to traceroute. Length must be less than 256 characters.|
| *time* |Optional | <1-60>| Select time in seconds to wait for a response to a probe between 1 and 60.|
#### Examples
```
switch# traceroute6 0:0::0:1 timeout 3
traceroute to 0:0::0:1 (::1) from ::1, 30 hops max, 3 sec. timeout, 3 probes, 24 byte packets
 1  localhost (::1)  0.117 ms  0.032 ms  0.021 ms
```
