#!/usr/bin/python
# (C) Copyright 2016 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License..

'''
NOTES:
 OPS_NTPD_SYNC_TO_OVSDB script
 - This script pushes status updates from NTPD
   (modified and given by OPS-NTPD).
 - Intention of detaching this code from OPS_NTPD
   daemon script is so that
   we can use this script as a standlone script to
   push 'instrumented' ntp status to OVSDB.
'''

import json
import sys
from time import sleep
import ovs.dirs
from ovs.db import error
import ovs.db.idl
import ovs.vlog

vlog = ovs.vlog.Vlog("ops_ntpd_sync_mgr")

# ovs definitions
idl = None

# OPS_TODO: Need to pull this from the build env
def_db = 'unix:/var/run/openvswitch/db.sock'

# OPS_TODO: Need to pull this from the build env
ovs_schema = '/usr/share/openvswitch/vswitch.ovsschema'

# Tables definitions
NTP_ASSOCIATION_TABLE = 'NTP_Association'
NTP_KEY_TABLE = 'NTP_Key'
SYSTEM_TABLE = 'System'

# Columns definitions
SYSTEM_CUR_CFG = 'cur_cfg'
SYSTEM_NTP_STATUS = 'ntp_status'
SYSTEM_NTP_STATISTICS = 'ntp_statistics'
NTP_ASSOCIATION_ADDRESS = 'address'
NTP_ASSOCIATION_STATUS = 'association_status'


class NTPTransactionMgr(object):

    def __init__(self, location=None):
        '''
        Create a IDL connection to the OVSDB and register all the
        columns with schema helper.
        '''
        self.idl = None
        self.txn = None
        self.schema_helper = ovs.db.idl.SchemaHelper(
            location=ovs_schema)
        self.schema_helper.register_columns(SYSTEM_TABLE,
                                            [SYSTEM_NTP_STATUS,
                                             SYSTEM_NTP_STATISTICS,
                                             SYSTEM_CUR_CFG])
        self.schema_helper.register_columns(NTP_ASSOCIATION_TABLE,
                                            [NTP_ASSOCIATION_ADDRESS,
                                             NTP_ASSOCIATION_STATUS])
        self.idl = ovs.db.idl.Idl(def_db, self.schema_helper)
        self.address = None
        while not self.idl.run():
            sleep(.1)

    def set_ntp_association_status(self, row, entry):
        setattr(row, 'association_status', entry)

    def find_row_by_ip_addr(self, server_ip_addr):
        '''
        Walk through the rows in the NTP Association table (if any)
        looking for a row with mac addr passed in argument
        If row is found, set variable tbl_found to True and return
        the row object to caller function
        '''
        tbl_found = False
        ovs_rec = None
        for ovs_rec in \
                self.idl.tables[NTP_ASSOCIATION_TABLE].rows.itervalues():
            if ovs_rec.address == server_ip_addr:
                tbl_found = True
                break
        return ovs_rec, tbl_found

    def update_row_in_ntp_association_table(self, entry):
        '''
        Update a row with NTP Association table with latest modified values.
        '''
        for k, v in entry["associations_info"].iteritems():
            server_ip_addr = k
            row, row_found = self.find_row_by_ip_addr(server_ip_addr)
            if row_found:
                self.set_ntp_association_status(row, v)
        return

    def update_system_table(self, entry):
        '''
        Update a SYSTEM table with global NTP statistics and uptime info.
        '''
        ovs_rec = None
        for ovs_rec in self.idl.tables[SYSTEM_TABLE].rows.itervalues():
            break
        setattr(ovs_rec, 'ntp_status', entry["status"])
        setattr(ovs_rec, 'ntp_statistics', entry["statistics"])
        return ovs_rec

    def update_info(self, ntp_info):
        self.txn = ovs.db.idl.Transaction(self.idl)
        # Update NTP associations table
        self.update_row_in_ntp_association_table(ntp_info)
        # Update NTP status with SYSTEM table
        self.update_system_table(ntp_info)
        status = self.txn.commit_block()
        if status != ovs.db.idl.Transaction.SUCCESS:
            vlog.err("ops_ntpd_sync_mgr update_row for ntp config in SYSTEM \
                    table failed")

    def close(self):
        self.idl.close()


def ops_ntpd_sync_mgr_run(transaction_queue):
    ops_ntpd_sync_mgr = NTPTransactionMgr()
    while(True):
        str_obj = transaction_queue.get()
        if str_obj == "shutdown":
            break
        ntp_info = {}
        msg_info = json.loads(str_obj)
        ntp_info["associations_info"] = msg_info['associations_info']
        ntp_info["statistics"] = msg_info['statistics']
        ntp_info["status"] = msg_info['status']
        ops_ntpd_sync_mgr.update_info(ntp_info)
    ops_ntpd_sync_mgr.close()

if __name__ == '__main__':
    try:
        ops_ntpd_sync_mgr_run()
        sys.exit()
    except error.Error, e:
        vlog.err("Error: \"%s\" \n" % e)
