/****************************************************************************
 * (c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP
 *
 *    Licensed under the Apache License, Version 2.0 (the "License"); you may
 *    not use this file except in compliance with the License. You may obtain
 *    a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 *    License for the specific language governing permissions and limitations
 *    under the License.
 *
 ***************************************************************************/

#ifndef _QOS_DSCP_PORT_VTY_H_
#define _QOS_DSCP_PORT_VTY_H_

/**
 * Initializes vty functions for port qos dscp.
 */
void qos_dscp_port_vty_init(void);

/**
 * Initializes ovsdb functions for port qos dscp.
 */
void qos_dscp_port_ovsdb_init(void);

#endif /* _QOS_DSCP_PORT_VTY_H_ */
