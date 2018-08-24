High-level design of ops-utils
==============================
The ops-utils repository containts the source to create the opsutils library. The opsutils library is a small library of functions that are commonly used, such as converting MAC addresses from strings to ulong long.

Reponsibilities
---------------
Any commonly used function that is not already provided in another library (Linux provided, OVS provided, etc), may be included in this library.

Design choices
--------------
This library was created to collect commonly used functions that are not provided in other libraries.
