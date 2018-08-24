High level design of OPS-RESTAPI
============================

The rendering of REST API documentation primarily utilizes Swagger-UI for presenting to users. The REST API data file is automatically generated from the extended OVSDB schema file and its companion XML description. The REST API data file also includes API definitions for other interfaces such as full configuration manipulation and user login management.

Reponsibilities
---------------
The REST API rendering module is responsible for serving the generated REST API documentation on switches. The generatiing of the REST API data file is done by the REST API servicing module during the build.

Design choices
--------------
The REST API data file is mostly generated automatically based on the extended OVSDB schema file and its companion XML description file instead of creating a completely new resource structure. There are a few fixed sections that are not derived automatically from the extended schema, such as full configuration manipulation and user login. This works for DevOps, but may not be the best choice for other uses such as replacing a web UI that is geared towards serving system administrators.

Both the rendering and servicing of the REST API are from the same IP address and port number, but differ only in their URL paths. By default when the server of the REST API is left unspecified in the REST API data file, the REST API server is assumed to be on the same IP address and port number as where the API data file is rendered from. If a customized REST server setting is used, both the IP address and the port number need to be specified. In order to avoid retrieving IP address information from the switch and dynamically setting it at runtime, the above tradeoff is made for simplicity.

Relationships to external OpenSwitch entities
---------------------------------------------

```ditaa
                    +
 Build time         |       Runtime
                    |
                    |
apidocgen.py        |       REST daemon
         ^          |          ^
         |          |          |
         |          +          |
         |                     |
      +--+---------------------+-+
      | Tables and relationships |
      | Column attributes        |
      +-----------+--------------+
                  ^
                  +
             restparser.py
                  ^
                  |
      +-------------------------+
      | Extended  | XML         |
      | OVSDB     | description |
      | schema    | file        |
      +-----------+-------------+

```

The automatic generation of the REST API documentation and the REST API service engine share a common Python library for analyzing the extended OVSDB schema and its companion XML description. The result is a list of OVSDB tables that need to be exposed in the REST API and the column attributes of each table. This data is used at build time for generating REST API documentation and at runtime for driving the processing of REST API requests.

OVSDB-Schema
------------
In addition to using the extended OVSDB schema, the shared Python library restparser.py uses information contained in the XML description file for the OVSDB schema.

Internal structure
------------------
The automatic generation of the REST API documentation is done in two steps.

The first step is to analyze the extended OVSDB schema based on the tagging information added and to also analyze its companion XML description for the description and extra type information of each column. This is processed in restparser.py.

From the extended OVSDB schema, two groups of tags ("category" and "relationship") are analyzed to capture the following information, namely:

 - A list of tables that are exposed to REST API.
 - The relationships between the tables (parent-child or reference).
 - Column attributes of each table ("configuration", "status" or "statistics") and their valid ranges.

From the companion XML description file, the information utilized is the description and the extra type information for certain columns. For regular attributes of base types (integer, string), there may be additional restrictions on the range of valid values. For attributes of key-value pairs, there can be information on the allowed keys as well as information about the valid ranges for the values.

The second step is to generate the REST API documentation for use by Swagger-UI automatically based on the information collected in the first step. The following procedures are performed:

 - The URI and allowed operations on the system table are generated;
 - The URI and allowed operations for each child table of the table processed are recursively generated;
 - The reference list to other tables in a table are treated the same as other attributes of the given table;
 - Those tables referenced by other tables but do not belong to any other table as children are treated as subresources under /system;
 - Regular columns of a table are grouped into one of the three categories ("configuration", "status" and "statistics") and definitions are created for them accordingly;
 - Each attribute contains descriptions extracted from the XML description file.

The generated REST API data file is then combined with other sections that are not derived from OVSDB schema. These include:

 - /system/full-configuration: it handles full declarative configuration manipulations;
 - /login: it handles user login and cookie setting.

References
----------
* [REST API servicing engine](http://www.openswitch.net/docs/REST_daemon_design.md)
* [Sample REST API documentation](http://api.openswitch.net/rest/dist/index.html)
* [Swagger-UI](http://swagger.io)
