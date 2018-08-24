#!/usr/bin/env python
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
 OPS-NTPD python daemon.
 - This is a helper daemon to retrieve the NTP configs from OVSDB
   during bootup and starts the NTPD dameon.
 - Any updates from OVSDB is synced to NTPD using NTPQ and NTPDC
 - Periodic updates from NTPD is synced to OVSDB using
   ops_ntpd_sync_to_ovsdb script.
'''

import os
import sys
import time
import signal
import copy
import hashlib
import argparse
import subprocess
import json
import pprint
import ovs.dirs
import ovs.daemon
import ovs.db.idl
import ovs.unixctl
import ovs.unixctl.server
from ops_ntpd_sync_to_ovsdb import ops_ntpd_sync_mgr_run
import multiprocessing
from ops_eventlog import event_log_init
from ops_eventlog import log_event
import ops_diagdump

# OVSDB information
idl = None
def_db = 'unix:/var/run/openvswitch/db.sock'
ovs_schema = '/usr/share/openvswitch/vswitch.ovsschema'

# vlog setup
vlog = ovs.vlog.Vlog("ops-ntpd")

# Globals
exiting = False
seqno = 0
ntpd_process = None
ntpq_process = None
ntpd_started = False
ntpd_command = None
ntpd_info = None
ntpq_info = None
g_ntpa_map = {}
g_ntpk_db = {}
controlkey = 65535
cmdline_str = ""
auth_state = "false"
default_assoc_info = {
    "remote_peer_address": "-",
    "remote_peer_ref_id": "-",
    "stratum": "-",
    "peer_type": "-",
    "last_polled": "-",
    "polling_interval": "-",
    "reachability_register": "-",
    "network_delay": "-",
    "time_offset": "-",
    "jitter": "-",
    "root_dispersion": "-",
    "peer_status_word": "-",
    "associd": "-",
}

translate_peer_status_word = {
    "sel_reject": "reject",
    "sel_falsetick": "falsetick",
    "sel_excess": "excess",
    "sel_outlier": "outlier",
    "sel_candidate": "candidate",
    "sel_backup": "backup",
    "sel_sys.peer": "system_peer",
    "sel_pps.peer": "pps_peer"
}
translate_peer_type = {
    "u": "uni_or_many_cast",
    "b": "bcast_or_mcast_client",
    "l": "local_ref_clock",
    "s": "symm_peer",
    "A": "manycast_server",
    "B": "bcast_server",
    "M": "mcast_server"
}
transaction_queue = None
sync_mgr_process = None

# Defaults
DEFAULT_NTP_KEY_ID = 0
DEFAULT_NTP_PREF = "false"
DEFAULT_NTP_VERSION = "3"
DEFAULT_NTP_REF_CLOCK_ID = ".LOCL."
DEFAULT_NTP_TRUST_ENABLE = False

# Tables definitions
NTP_ASSOCIATION_TABLE = 'NTP_Association'
NTP_KEY_TABLE = 'NTP_Key'
SYSTEM_TABLE = 'System'
# Columns definitions
SYSTEM_CUR_CFG = 'cur_cfg'
SYSTEM_NTP_CONFIG = 'ntp_config'
NTP_ASSOCIATION_VRF = 'vrf'
NTP_ASSOCIATION_ADDRESS = 'address'
NTP_ASSOCIATION_KEY_ID = 'key_id'
NTP_ASSOCIATION_ATTR = 'association_attributes'
NTP_KEY_ID = 'key_id'
NTP_KEY_PASSWORD = 'key_password'
NTP_KEY_TRUST_ENABLE = 'trust_enable'

# String keys
NTPQ_REMOTE = "remote"
NTPQ_ASSOCID = "assid"
NTPQ_REFID = "refid"
NTPQ_ST = "st"
NTPQ_T = "t"
NTPQ_WHEN = "when"
NTPQ_POLL = "poll"
NTPQ_REACH = "reach"
NTPQ_DELAY = "delay"
NTPQ_OFFSET = "offset"
NTPQ_JITTER = "jitter"

NTPQ_REMOTE_PEER_ADDRESS = "remote_peer_address"
NTPQ_REMOTE_PEER_REF_ID = "remote_peer_ref_id"
NTPQ_ROOT_DISPERSION = "root_dispersion"
NTPQ_STRATUM = "stratum"
NTPQ_PEER_TYPE = "peer_type"
NTPQ_LAST_POLLED = "last_polled"
NTPQ_POLLING_INTERVAL = "polling_interval"
NTPQ_REACHABILITY_REGISTER = "reachability_register"
NTPQ_NETWORK_DELAY = "network_delay"
NTPQ_TIME_OFFSET = "time_offset"
NTPQ_JITTER = "jitter"
NTPQ_REFERENCE_TIME = "reference_time"
NTPQ_PEER_STATUS_WORD = "peer_status_word"
NTPQ_ASSOCID = "associd"

NTPQ_UPTIME = "uptime"
NTPQ_SYSSTATS_RESET = "sysstats reset"
NTPQ_PACKETS_RECEIVED = "packets received"
NTPQ_CURRENT_VERSION = "current version"
NTPQ_OLDER_VERSION = "older version"
NTPQ_BAD_LENGTH_OR_FORMAT = "bad length or format"
NTPQ_AUTHENTICATION_FAILED = "authentication failed"
NTPQ_DECLINED = "declined"
NTPQ_RESTRICTED = "restricted"
NTPQ_RATE_LIMITED = "rate limited"
NTPQ_KOD_RESPONSES = "KoD responses"
NTPQ_PROCESSED_FOR_TIME = "processed for time"

# NTP global info keys/columns
NTP_UPTIME = "uptime"
NTP_STAT_NTP_PKTS_RECEIVED = "ntp_pkts_received"
NTP_STAT_NTP_PKTS_WITH_CURRENT_VERSION = "ntp_pkts_with_current_version"
NTP_STAT_NTP_PKTS_WITH_OLDER_VERSION = "ntp_pkts_with_older_version"
NTP_STAT_NTP_PKTS_WITH_BAD_LENGTH_OR_FORMAT = \
    "ntp_pkts_with_bad_length_or_format"
NTP_STAT_NTP_PKTS_WITH_AUTH_FAILED = "ntp_pkts_with_auth_failed"
NTP_STAT_NTP_PKTS_DECLINED = "ntp_pkts_declined"
NTP_STAT_NTP_PKTS_RESTRICTED = "ntp_pkts_restricted"
NTP_STAT_NTP_PKTS_RATE_LIMITED = "ntp_pkts_rate_limited"
NTP_STAT_NTP_PKTS_KOD_RESPONSES = "ntp_pkts_kod_responses"

NTP_ASSOC_REMOTE_PEER_ADDRESS = "remote_peer_address"
NTP_ASSOC_REMOTE_PEER_REF_ID = "remote_peer_ref_id"
NTP_ASSOC_STRATUM = "stratum"
NTP_ASSOC_PEER_TYPE = "peer_type"
NTP_ASSOC_LAST_POLLED = "last_polled"
NTP_ASSOC_POLLING_INTERVAL = "polling_interval"
NTP_ASSOC_REACH_REGISTER = "reachability_register"
NTP_ASSOC_NETWORK_DELAY = "network_delay"
NTP_ASSOC_TIME_OFFSET = "time_offset"
NTP_ASSOC_JITTER = "jitter"
NTP_ASSOC_ROOT_DISPERSION = "root_dispersion"
NTP_ASSOC_PEER_STATUS_WORD = "peer_status_word"
NTP_ASSOC_ASSOCID = "associd"
NTP_ASSOC_REFERENCE_TIME = "reference_time"


def ops_ntpd_create_working_dir(ntp_working_dir_path):
    '''
       This function helps create a working directory for ntp
       It sets the file permission so that root user can access it
    '''
    try:
        ops_ntpd_cleanup_working_dir(ntp_working_dir_path)
    finally:
        os.system("mkdir %s" % ntp_working_dir_path)
        os.system("chmod 700 %s" % ntp_working_dir_path)


def ops_ntpd_cleanup_working_dir(ntp_working_dir_path):
    os.system("rm -rf %s;" % (ntp_working_dir_path))


def ops_ntpd_update_content_buffer(file_buffer, line):
    return file_buffer + [line + "\n"]


def ops_ntpd_get_file_contents(filename):
    fh = open(filename, 'r')
    contents = fh.readlines()
    fh.close()
    return contents


def ops_ntpd_set_file_contents(filename, contents):
    with open(filename, "w+") as f:
        f.writelines(contents)


def ops_ntpd_setup_ntpq_integration(ntp_working_dir_path):
    '''
       This function helps setup the NTPQ integration wiht NTPD
       NTPQ communicates to NTPD using the control msg protocol.
       More info: http://doc.ntp.org/4.1.0/ntpq.htm
    '''
    global ntpq_info, cmdline_str
    random_data = os.urandom(128)
    controlkey_answer = hashlib.sha224(random_data).hexdigest()[:16]
    ntpq_info = (controlkey, controlkey_answer)
    # Build a commandline string to execute
    cmdline_str = "ntpq -c \"keyid %d\" -c \"passwd %s\"" %\
        (controlkey, controlkey_answer)
    return (controlkey, controlkey_answer)


def ops_ntpd_setup_ntpd_default_config_file(ntp_working_dir_path):
    '''
       This function sets up default configuration file used by
       the NTPD daemon when it is launched.
       It sets up information required for NTPQ and NTPDC to connect
       to NTPD.
    '''
    global ntpq_info
    os.system("cd %s;" % ntp_working_dir_path)
    conf = []
    conf = ops_ntpd_update_content_buffer(conf,
                                          "#This is generated from ops-ntpd")
    conf = ops_ntpd_update_content_buffer(conf,
                                          "tinker panic 0")
    conf = ops_ntpd_update_content_buffer(conf,
                                          "trustedkey %s" % (ntpq_info[0]))
    conf = ops_ntpd_update_content_buffer(conf,
                                          "requestkey %s" % (ntpq_info[0]))
    conf = ops_ntpd_update_content_buffer(conf,
                                          "controlkey %s" % (ntpq_info[0]))
    conf = ops_ntpd_update_content_buffer(conf,
                                          "enable mode7")
    conf_file = ntp_working_dir_path + "ops_ntp.conf"
    ops_ntpd_set_file_contents(conf_file, conf)
    return conf_file


def ops_ntpd_get_ntpd_default_keys_file_content():
    '''
       This function sets up default keys file content.
       It sets up information required for NTPQ and NTPDC to connect
       to NTPD.
    '''
    global ntpq_info
    keys_content = "#This is generated from ops-ntpd\n"
    keys_content += " %s MD5 %s\n" % (ntpq_info[0], ntpq_info[1])
    return keys_content


def ops_ntpd_setup_ntpd_default_keys_file(ntp_working_dir_path):
    '''
       This function creates a default keys file and adds
       default information in the keys file
    '''
    global ntpq_info
    os.system("cd %s;" % ntp_working_dir_path)
    keys_info = []
    keys_info = ops_ntpd_update_content_buffer(
            keys_info,
            ops_ntpd_get_ntpd_default_keys_file_content())
    keys_file = ntp_working_dir_path + "ops_ntp.keys"
    ops_ntpd_set_file_contents(keys_file, keys_info)
    return keys_file


def ops_ntpd_setup_ntpd_default_log_file(ntp_working_dir_path):
    '''
       This function sets the log file location and file name.
       This is kept in lines with how we create default conf
       and default keys file.
    '''
    return ntp_working_dir_path + "ops_ntp.log"


def ops_ntpd_run_command(command):
    '''
       This function runs the command provided through 'command'
       and returns the error and output info
    '''
    process = subprocess.Popen(args=command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
    error = process.stderr.read()
    output = process.communicate()
    return error, output


def ops_ntpd_setup_ntp_key_map(ntpk_db, key_id, key_pass, trust_flag):
    '''
       This function updates the 'ntpk_db' with information about keys
    '''
    ntpk_db[key_id] = (key_pass, trust_flag)


def ops_ntpd_setup_ntp_config_map(ntpa_map, vrf, address,
                                  associd, key_id, ref_clock_id, prefer,
                                  ntp_version):
    '''
       This function updates the 'ntpa_map' with information about
       server config
    '''
    ntpa_map[(vrf, address)] = associd
    ntpa_map[(vrf, address)] = (address, vrf,
                                key_id, ref_clock_id, prefer, ntp_version)


def ops_ntpd_sync_updates_to_ntpd(server_configs, key_configs,
                                  keys_file_content):
    '''
       This function synchronizes information from OVSDB to NTPD
    '''
    global cmdline_str
    global ntpd_info
    global ntpq_info
    command = copy.copy(cmdline_str)
    for config in server_configs + key_configs:
        command += " -c \"%s\"" % (config)

    ops_ntpd_set_file_contents(ntpd_info[1], keys_file_content)
    e, o = ops_ntpd_run_command("ntpdc -c \"keyid %d\" -c \"passwd \
            %s\" -c \"readkeys\"" % (ntpq_info[0], ntpq_info[1]))
    time.sleep(2)
    vlog.dbg("NTPDC command was %s: done" % e)
    e, o = ops_ntpd_run_command(command)
    vlog.dbg("NTPQ command was %s: done" % e)
    vlog.dbg("Sync OVSDB -> NTPD : done")


def ops_ntpd_get_ntpd_associations_info(ntpd_updates):
    '''
       This function creates a table containing all the
       information about NTP associations
       This information is used to push information into
       ntp_association_status into the NTP Associations
       table
    '''
    a_table = {}
    assoc_db = {}
    associations_info_table = {}
    err, cmd_output = ops_ntpd_run_command("ntpq -n -c \"apeers\"")
    n_out = cmd_output[0].strip().split('\n')[2:]
    for n in n_out:
        n = n.strip().split()
        a_entry = {}
        a_entry[NTPQ_REMOTE] = n[0]
        a_entry[NTPQ_REFID] = n[1]
        a_entry[NTPQ_ASSOCID] = n[2]
        a_entry[NTPQ_ST] = n[3]
        a_entry[NTPQ_T] = n[4]
        a_entry[NTPQ_WHEN] = n[5]
        a_entry[NTPQ_POLL] = n[6]
        a_entry[NTPQ_REACH] = n[7]
        a_entry[NTPQ_DELAY] = n[8]
        a_entry[NTPQ_OFFSET] = n[9]
        a_entry[NTPQ_JITTER] = n[10]
        a_table[a_entry[NTPQ_ASSOCID]] = a_entry
        assoc_db[a_entry[NTPQ_ASSOCID]] = a_entry

    for assoc_id in assoc_db.keys():
        err, cmd_output = ops_ntpd_run_command(
            "ntpq -n -c \"rv %s\"" % assoc_id)
        n_out = " ".join(cmd_output[0].split("\n"))
        n = n_out.split(",")
        peer_status_word = [x.strip() for x in n if "sel_" in x][0]
        root_dispersion = [x.strip() for x in n
                           if "rootdisp" in x][0].strip().split("=")[1]
        remote_peer_address = [x.strip() for x in n
                               if "srcadr" in x][0].strip().split("=")[1]
        reference_time = " ".join([n[i] + n[i + 1] for i in
                                   range(len(n)) if "reftime" in n[i]][0].
                                  strip().split("=")[1].split()[1:])
        ref_id = [x.strip() for x in n if "refid" in x][
            0].strip().split("=")[1]
        if assoc_db[assoc_id][NTPQ_REFID][0] == ".":
            ref_id = assoc_db[assoc_id][NTPQ_REFID]
        a_table[assoc_id][NTPQ_REMOTE] = remote_peer_address
        a_table[assoc_id][NTPQ_ROOT_DISPERSION] = root_dispersion
        a_table[assoc_id][NTPQ_REFERENCE_TIME] = reference_time
        a_table[assoc_id][NTPQ_PEER_STATUS_WORD] = peer_status_word
        a_table[assoc_id][NTPQ_REFID] = ref_id
        associations_info_table[remote_peer_address] = a_table[assoc_id]

    for address in associations_info_table.keys():
        assoc_info = copy.copy(default_assoc_info)
        vlog.dbg("Gathering information about address %s" % address)
        assoc_info[NTP_ASSOC_REMOTE_PEER_ADDRESS] = \
            associations_info_table[address][NTPQ_REMOTE]
        assoc_info[NTP_ASSOC_REMOTE_PEER_REF_ID] = \
            associations_info_table[address][NTPQ_REFID]
        assoc_info[NTP_ASSOC_STRATUM] = associations_info_table[
            address][NTPQ_ST]
        assoc_info[NTP_ASSOC_PEER_TYPE] = translate_peer_type[
            associations_info_table[address][NTPQ_T]]
        assoc_info[NTP_ASSOC_LAST_POLLED] = \
            associations_info_table[address][NTPQ_WHEN]
        assoc_info[NTP_ASSOC_POLLING_INTERVAL] = \
            associations_info_table[address][NTPQ_POLL]
        assoc_info[NTP_ASSOC_REACH_REGISTER] = \
            associations_info_table[address][NTPQ_REACH]
        assoc_info[NTP_ASSOC_NETWORK_DELAY] = \
            associations_info_table[address][NTPQ_DELAY]
        assoc_info[NTP_ASSOC_TIME_OFFSET] = \
            associations_info_table[address][NTPQ_OFFSET]
        assoc_info[NTP_ASSOC_JITTER] = \
            associations_info_table[address][NTPQ_JITTER]
        assoc_info[NTP_ASSOC_ROOT_DISPERSION] = \
            associations_info_table[address][NTPQ_ROOT_DISPERSION]
        assoc_info[NTP_ASSOC_PEER_STATUS_WORD] = \
            translate_peer_status_word[
            associations_info_table[address][NTPQ_PEER_STATUS_WORD]]
        assoc_info[NTP_ASSOC_ASSOCID] = \
            associations_info_table[address][NTPQ_ASSOCID]
        assoc_info[NTP_ASSOC_REFERENCE_TIME] = \
            associations_info_table[address][NTPQ_REFERENCE_TIME]
        ntpd_updates["associations_info"][address] = assoc_info
        if assoc_info[NTP_ASSOC_PEER_STATUS_WORD] == "system_peer":
            os.system("hwclock -w")


def ops_ntpd_get_ntpd_global_status(ntpd_updates):
    '''
       This function create a table containing all information
       relevant to global statistics and status.
       This information is used to push into
       ntp_status and ntp_statistics in the SYSTEM table
    '''
    err, cmd_output = ops_ntpd_run_command("ntpq -n -c \"sysstats\"")
    n_out = cmd_output[0].strip().split("\n")
    sysstat_table = {}
    for n in n_out:
        n = [i.lstrip() for i in n.strip().split(":")]
        sysstat_table[n[0]] = n[1]
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_RECEIVED] = \
        str(sysstat_table[NTPQ_PACKETS_RECEIVED])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_WITH_CURRENT_VERSION] = \
        str(sysstat_table[NTPQ_CURRENT_VERSION])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_WITH_OLDER_VERSION] = \
        str(sysstat_table[NTPQ_OLDER_VERSION])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_WITH_BAD_LENGTH_OR_FORMAT] = \
        str(sysstat_table[NTPQ_BAD_LENGTH_OR_FORMAT])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_WITH_AUTH_FAILED] = \
        str(sysstat_table[NTPQ_AUTHENTICATION_FAILED])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_DECLINED] = \
        str(sysstat_table[NTPQ_DECLINED])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_RESTRICTED] = \
        str(sysstat_table[NTPQ_RESTRICTED])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_RATE_LIMITED] = \
        str(sysstat_table[NTPQ_RATE_LIMITED])
    ntpd_updates["statistics"][NTP_STAT_NTP_PKTS_KOD_RESPONSES] = \
        str(sysstat_table[NTPQ_KOD_RESPONSES])
    ntpd_updates["status"][NTP_UPTIME] = str(sysstat_table[NTPQ_UPTIME])


def ops_ntpd_sync_updates_to_ovsdb():
    '''
       This function pools all the information which needs to be
       send to the OVSDB as part of the status update.
    '''
    global g_ntpa_map
    ntpd_updates = {}
    ntpd_updates["associations_info"] = {}
    ntpd_updates["statistics"] = {}
    ntpd_updates["status"] = {}
    try:
        ops_ntpd_get_ntpd_associations_info(ntpd_updates)
        ops_ntpd_get_ntpd_global_status(ntpd_updates)
        str_ntpd_updates = json.dumps(ntpd_updates)
        vlog.dbg("Sync information is \n %s" % (
            pprint.pformat(ntpd_updates, indent=5)))

        ops_ntpd_send_info_to_transaction_mgr(str_ntpd_updates)
        vlog.dbg("Sync NTPD -> OVSDB : done")
    except Exception as e:
        vlog.warn("Unable to sync NTPD info -> OVSDB : err %s" % (str(e)))


def ops_ntpd_check_updates_with_ntp_associations(l_ntpa_map, trigger_reconfig):
    '''
        This function checks if there are any updates in the NTP
        associations and accordingly updates the global database
        with that info.
        It also provides what configuration change has to be sent
        to the NTPD daemon.
    '''
    global g_ntpa_map
    add = []
    delete = []
    add_configs = []
    revise_configs = []
    add_template_string = ":config server "
    delete_template_string = ":config unconfig "
    for k in list(set(l_ntpa_map.keys() + g_ntpa_map.keys())):
        if k in l_ntpa_map.keys():
            v = l_ntpa_map[k]
            event = ""
            if v[2] != 0:
                server_info = "prefer %s, ver %s, key %s" %\
                            (str(v[4]), str(v[5]), str(v[2]))
            else:
                server_info = "prefer %s, ver %s" %\
                            (str(v[4]), str(v[5]))
            if k not in g_ntpa_map.keys():
                add.append(k)
                g_ntpa_map[k] = v
                event = "Add"
            elif v != g_ntpa_map[k]:
                delete.append(k)
                add.append(k)
                g_ntpa_map[k] = v
                event = "Change"
            if event != "":
                log_event(
                          "NTP_ASSOC",
                          ["event", event],
                          ["server", v[0]],
                          ["server_info", server_info])
        else:
            delete.append(k)
            v = g_ntpa_map[k]
            log_event(
                      "NTP_ASSOC",
                      ["event", "Delete"],
                      ["server", v[0]],
                      ["server_info", ""])
            del g_ntpa_map[k]
    delete_configs = [delete_template_string + x[1] for x in delete]
    for x in add:
        (addr, vrf, key_id, ref_clk, pref, ver) = g_ntpa_map[x]
        add_config = add_template_string + addr
        add_config += " version " + ver
        if key_id != DEFAULT_NTP_KEY_ID:
            add_config += " key " + key_id
        if pref != DEFAULT_NTP_PREF:
            add_config += " prefer"
        add_configs += [add_config]
    if trigger_reconfig is True:
        for x in list(g_ntpa_map.keys()):
            (addr, vrf, key_id, ref_clk, pref, ver) = g_ntpa_map[x]
            if key_id != DEFAULT_NTP_KEY_ID:
                revise_configs += [delete_template_string + addr]
                if pref != DEFAULT_NTP_PREF:
                    revise_configs += [
                            add_template_string + addr +
                            " version %s key %s prefer" % (ver, key_id)]
                else:
                    revise_configs += [add_template_string + addr +
                                       " version %s key %s" % (ver, key_id)]
    server_configs = revise_configs + delete_configs + add_configs
    vlog.dbg("server configs %s" % (pprint.pformat(server_configs)))
    return server_configs


def ops_ntpd_check_updates_with_ntp_keys(l_ntpk_db):
    '''
       This function checks if there are any updates in NTP keys
       and accordingly updates the global database with that info.
       It also provides what configuration change has to be sent
       to the NTPD daemon.
    '''
    global g_ntpk_db, ntpq_info
    add_template_string = " %s MD5 %s"
    trustedkey_template_string = ":config trustedkey "
    untrustedkey_template_string = ":config unconfig trustedkey "
    t_keys_str = "-"
    unt_keys_str = "-"
    trusted_keys = []
    untrusted_keys = []
    trusted_key_config = []
    untrusted_key_config = []
    keys_file_content = ops_ntpd_get_ntpd_default_keys_file_content()
    if len(l_ntpk_db) > 0 and len(g_ntpk_db) > 0:
        untrusted_keys = set(g_ntpk_db.keys()) - set(l_ntpk_db.keys())
        g_ntpk_db = copy.copy(l_ntpk_db)
        trusted_keys = g_ntpk_db.keys()
    elif len(g_ntpk_db) == 0:
        g_ntpk_db = copy.copy(l_ntpk_db)
        trusted_keys = g_ntpk_db.keys()
    elif len(l_ntpk_db) == 0:
        untrusted_keys = g_ntpk_db.keys()
        g_ntpk_db = {}
    keys_file_content += "\n".join([add_template_string % (
        k, v[0]) for k, v in g_ntpk_db.iteritems()])
    if len(trusted_keys) > 0:
        trusted_key_config += [trustedkey_template_string +
                               " ".join([str(x) for x in trusted_keys])]
        t_keys_str = " ".join([str(x) for x in trusted_keys])
    if len(untrusted_keys) > 0:
        untrusted_key_config += [untrustedkey_template_string +
                                 " ".join([str(x) for x in untrusted_keys])]
        unt_keys_str = " ".join([str(x) for x in untrusted_keys])
    if t_keys_str != "-" or unt_keys_str != "-":
        log_event("NTP_KEY",
                  ["trusted_keys", t_keys_str],
                  ["untrusted_keys", unt_keys_str])
    key_config = untrusted_key_config + trusted_key_config
    keys_file_content += "\n"
    return key_config, keys_file_content


def ops_ntpd_check_updates_from_ovsdb():
    '''
        This function checks if there are any updates in the NTP
        associations and accordingly reconfigures the NTP daemon to
        pick up the configuration changes.
    '''
    global idl
    global ntpd_command
    global ntpq_process
    global cmdline_str
    global g_ntpk_db
    global auth_state
    ovs_rec = None
    associd = 0
    vlog.dbg("ops_ntpd_check_updates_from_ovsdb")
    authentication_enable = "false"
    trigger_reconfig = False

    update_map = {}
    # Check if ntp authentication is enabled
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.ntp_config and ovs_rec.ntp_config is not None:
            for key, value in ovs_rec.ntp_config.iteritems():
                if key == 'authentication_enable':
                    authentication_enable = value
    vlog.dbg("Authentication is %s " % (authentication_enable))

    if (auth_state != authentication_enable):
        trigger_reconfig = True
        log_event(
                  "NTP_GLOBAL",
                  ["old", auth_state], ["new", authentication_enable])
        auth_state = authentication_enable

    update_map = {}
    # Get the NTP key changes
    for ovs_rec in idl.tables[NTP_KEY_TABLE].rows.itervalues():
        trust_enable = DEFAULT_NTP_TRUST_ENABLE
        if ovs_rec.key_id and ovs_rec.key_id is not None:
            key_id = ovs_rec.key_id
        if ovs_rec.key_password and ovs_rec.key_password is not None:
            key_password = ovs_rec.key_password
        if ovs_rec.trust_enable and ovs_rec.trust_enable is not None:
            trust_enable = ovs_rec.trust_enable
        vlog.dbg("trust_enable is %s and auth is %s" % (trust_enable,
                                                        authentication_enable))
        if trust_enable is True and authentication_enable == "true":
            ops_ntpd_setup_ntp_key_map(update_map,
                                       key_id, key_password, trust_enable)

    key_configs, keys_file_content = \
        ops_ntpd_check_updates_with_ntp_keys(update_map)
    vlog.dbg("Key config changes %s " % (pprint.pformat(key_configs)))

    update_map = {}
    # Get the NTP association configuration changes
    for ovs_rec in idl.tables[NTP_ASSOCIATION_TABLE].rows.itervalues():
        key_id = DEFAULT_NTP_KEY_ID
        prefer = DEFAULT_NTP_PREF
        ntp_version = DEFAULT_NTP_VERSION
        ref_clock_id = DEFAULT_NTP_REF_CLOCK_ID
        vrf = ovs_rec._data['vrf'].to_json()[1]
        if ovs_rec.address and ovs_rec.address is not None:
            ip_address = ovs_rec.address
        if ovs_rec.key_id and len(ovs_rec.key_id) > 0:
            key_id = str(ovs_rec.key_id[0].key_id)
        if ovs_rec.association_attributes and \
                ovs_rec.association_attributes is not None:
            for key, value in \
                    ovs_rec.association_attributes.iteritems():
                if key == 'ref_clock_id':
                    ref_clock_id = value
                if key == 'prefer':
                    prefer = value
                if key == 'version':
                    ntp_version = value
        ops_ntpd_setup_ntp_config_map(
                update_map, vrf, ip_address,
                associd, key_id, ref_clock_id, prefer, ntp_version)

    server_configs = \
        ops_ntpd_check_updates_with_ntp_associations(update_map,
                                                     trigger_reconfig)
    vlog.dbg("Server config changes %s " %
             (pprint.pformat(server_configs)))

    ops_ntpd_sync_updates_to_ntpd(server_configs, key_configs,
                                  keys_file_content)


def ops_ntpd_init_transaction_mgr():
    global transaction_queue, sync_mgr
    transaction_queue = multiprocessing.Queue()
    sync_mgr = multiprocessing.Process(target=ops_ntpd_sync_mgr_run,
                                       args=(transaction_queue,))
    sync_mgr.start()


def ops_ntpd_send_info_to_transaction_mgr(ntpd_update_str):
    global transaction_queue, sync_mgr
    transaction_queue.put(ntpd_update_str)


def ops_ntpd_shutdown_transaction_mgr():
    global transaction_queue, sync_mgr
    transaction_queue.put("shutdown")
    transaction_queue.close()
    transaction_queue.join_thread()
    sync_mgr.join()
    transaction_queue = None
    sync_mgr = None


def ops_ntpd_connection_exit_handler(conn, unused_argv, unused_aux):
    global exiting
    exiting = True
    conn.reply(None)


def ops_ntpd_check_system_status():
    '''
    Checks if the system initialization is completed.
    If System:cur_cfg > 0:
        configuration completed: return True
    else:
        return False
    '''
    global idl
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.cur_cfg:
            if ovs_rec.cur_cfg == 0:
                return False
            else:
                return True

    return False


def ops_ntpd_setup_ovsdb_monitoring(remote):
    '''
    Initializes the OVS-DB connection
    '''
    global idl
    schema_helper = ovs.db.idl.SchemaHelper(location=ovs_schema)
    schema_helper.register_columns(SYSTEM_TABLE,
                                   [SYSTEM_NTP_CONFIG, SYSTEM_CUR_CFG])
    schema_helper.register_columns(NTP_ASSOCIATION_TABLE,
                                   [NTP_ASSOCIATION_VRF,
                                    NTP_ASSOCIATION_ADDRESS,
                                    NTP_ASSOCIATION_KEY_ID,
                                    NTP_ASSOCIATION_ATTR])
    schema_helper.register_columns(NTP_KEY_TABLE,
                                   [NTP_KEY_ID,
                                    NTP_KEY_PASSWORD,
                                    NTP_KEY_TRUST_ENABLE])
    idl = ovs.db.idl.Idl(remote, schema_helper)


def ops_ntpd_setup_ntpd_default_config():
    '''
       This function sets the default configuration for the NTPD daemon
    '''
    ntp_dir_path = "/etc/ntp/"
    ops_ntpd_create_working_dir(ntp_dir_path)
    ops_ntpd_setup_ntpq_integration(ntp_dir_path)
    conf_file = ops_ntpd_setup_ntpd_default_config_file(ntp_dir_path)
    keys_file = ops_ntpd_setup_ntpd_default_keys_file(ntp_dir_path)
    log_file = ops_ntpd_setup_ntpd_default_log_file(ntp_dir_path)
    vlog.info("NTP default files setup done")
    return (conf_file, keys_file, log_file)


def ops_ntpd_start_ntpd(ntpd_info):
    '''
       This function starts the NTPD daemon
    '''
    global ntpd_process
    global ntpd_command
    ntpd_process = None
    (conf_file, keys_file, log_file) = ntpd_info
    ntpd_command = "ntpd -I eth0 -c %s -k %s -l %s" % (conf_file, keys_file, log_file)
    err, out = ops_ntpd_run_command(ntpd_command)
    if err != "":
        vlog.emer("%s" % (err))
        vlog.emer("Error with config, ntpd failed, command %s" %
                  (ntpd_command))
    else:
        vlog.info("ops-ntpd - ntpd started")


def ops_ntpd_provision_ntpd_daemon():
    '''
       This function provisions NTPD default config and launches the
       NTPD daemon
    '''
    global idl
    global seqno
    global ntpd_started
    global ntpd_info
    idl.run()
    if seqno != idl.change_seqno:
        vlog.dbg("ops-ntpd-debug - seqno change from %d to %d "
                 % (seqno, idl.change_seqno))
        seqno = idl.change_seqno
        # Check if system is configured and startup config is restored
        if ops_ntpd_check_system_status() is False:
            return
        else:
            # Get the default ntp config, keys file
            ntpd_info = ops_ntpd_setup_ntpd_default_config()
            # Kill zombie ntpd process and Start a new ntpd daemon
            ops_ntpd_cleanup_ntpd_processes()
            ops_ntpd_start_ntpd(ntpd_info)
            ops_ntpd_init_transaction_mgr()
            # Get the ntp config
            time.sleep(5)
            ops_ntpd_check_updates_from_ovsdb()
            ntpd_started = True


def ops_ntpd_cleanup_ntpd_processes():
    '''
       This function cleans up zombie NTPD processes
    '''
    err, out = ops_ntpd_run_command("ps -A")
    for line in out[0].splitlines():
        if 'ntpd -c' in line or 'ntpq' in line:
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)
            vlog.dbg("Killing zombie ntpd process pid : %s" % pid)


def ops_ntpd_diagnostics_handler(argv):
    global ntpd_info
    # argv[0] is basic
    # argv[1] is feature name
    feature = argv.pop()
    buff = 'Diagnostic dump for ' + feature + '.\n'
    (conf_file, keys_file, log_file) = ntpd_info

    # Capture the configuration file info with ntpd
    with open(conf_file, "r") as f:
        fbuff = ['NTPD configuration file\n']
        fbuff += ['===============================================\n']
        fbuff += f.readlines()

    # Capture the keys_file info with ntpd
    with open(keys_file, "r") as f:
        fbuff += ['NTPD keys file\n']
        fbuff += ['===============================================\n']
        fbuff += f.readlines()

    # Capture the log_file info with ntpd
    with open(log_file, "r") as f:
        fbuff += ['NTPD log file\n']
        fbuff += ['===============================================\n']
        fbuff += f.readlines()

    for x in fbuff:
        buff += x

    return buff


def ops_ntpd_init():
    '''
       This function
       - intiializes with OVSDB
       - provisions the NTPD daemon
       - keeps checking of configuration changes in OVSDB
    '''
    global exiting
    global idl
    global seqno
    global ntpd_started

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', metavar="DATABASE",
                        help="A socket on which ovsdb-server is listening.",
                        dest='database')

    ovs.vlog.add_args(parser)
    ovs.daemon.add_args(parser)
    args = parser.parse_args()
    ovs.vlog.handle_args(args)
    ovs.daemon.handle_args(args)

    if args.database is None:
        remote = def_db
    else:
        remote = args.database
    ops_ntpd_setup_ovsdb_monitoring(remote)
    ovs.daemon.daemonize()
    ovs.daemon.set_pidfile(None)
    ovs.daemon._make_pidfile()
    ovs.unixctl.command_register("exit", "", 0, 0,
                                 ops_ntpd_connection_exit_handler, None)
    error, unixctl_server = ovs.unixctl.server.UnixctlServer.create(None)

    if error:
        ovs.util.ovs_fatal(error, "ops_ntpd_helper: could not create "
                                  "unix-ctl server", vlog)
    while ntpd_started is False:
        ops_ntpd_provision_ntpd_daemon()
        time.sleep(2)

    # Event logging init for NTP
    event_log_init("NTP")

    # Diags callback init for NTP
    ops_diagdump.init_diag_dump_basic(ops_ntpd_diagnostics_handler)

    seqno = idl.change_seqno    # Sequence number when we last processed the db
    exiting = False
    while not exiting:
        unixctl_server.run()
        if exiting:
            break
        idl.run()
        if seqno == idl.change_seqno:
            ops_ntpd_sync_updates_to_ovsdb()
            time.sleep(2)
        else:
            vlog.dbg("ops-ntpd-debug main - seqno change from %d to %d "
                     % (seqno, idl.change_seqno))
            ops_ntpd_check_updates_from_ovsdb()
            seqno = idl.change_seqno

    # Daemon exit
    unixctl_server.close()
    if ntpd_process is not None:
        vlog.dbg("ops-ntpd-debug - killing ntpd")
    idl.close()
    ops_ntpd_cleanup_ntpd_processes()
    ops_ntpd_shutdown_transaction_mgr()

if __name__ == '__main__':
    try:
        ops_ntpd_init()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except:
        vlog.exception("traceback")
        sys.exit(ovs.daemon.RESTART_EXIT_CODE)
