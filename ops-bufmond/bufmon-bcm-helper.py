#!/usr/bin/python

import sys, getopt
import yaml
import decorator

file_header = """
# Copyright (C) 2014-2015 Hewlett-Packard Development Company, L.P.
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
#    under the License.
#
#
#  This YAML file is auto generated for buffer monitoring feature
#  Buffer Monitoring Counters Description File for Broadcom Family %s ASIC
#  Switches and number of ports %s \n"""



# Default values for ASIC specific constants
NUM_PORTS = 104
NUM_UC_QUEUE = 2960
NUM_UC_QUEUE_GRP = 128
NUM_MC_QUEUE = 1040
NUM_SP = 4
NUM_COMMON_SP = 1
NUM_RQE = 11
NUM_RQE_POOL = 4
NUM_PG = 8
SUPPORT_1588 = 1
CPU_COSQ = 8

COUNTER_UNIQUE_ID = "name"
HW_UNIT = "hw_unit_id"
STATS_NAME = "counter_name"
REALM = "realm"
VENDOR_INFO = "counter_vendor_specific_info"
PORT = "port"
QUEUE = "queue"
PG = "priority-group"
SP = "service-pool"


counter_vendor_specific_info = { STATS_NAME: ""}
counter_info = {HW_UNIT: 0, COUNTER_UNIQUE_ID: "", VENDOR_INFO: {}}

bufmon_template = {
  'cap_mode_peak': True,
  'cap_mode_current': True,
  'cap_snapshot_on_threshold_trigger': True,
  'cap_threshold_trigger_collection': True,
  'counters': []
}

global_counter_list = []

def assignOrder(order):
  def do_assignment(to_func):
    to_func.order = order
    return to_func
  return do_assignment

class realm:
    #------------------ device_data_stats() ----------------
    @assignOrder(1)
    def device_data_stats(self):
        '''
        EXPECTED YAML FORMAT:
        name: device/data/NONE/NONE
            counter_vendor_specific_info:
              counter_name: data
        '''
        counter_vendor_specific_info = { STATS_NAME: ""}
        counter_info[HW_UNIT] = 0
        counter_info[COUNTER_UNIQUE_ID] = "device/data/NONE/NONE"
        counter_vendor_specific_info[STATS_NAME] = "data"
        counter_vendor_specific_info[REALM] = "device"
        counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
        global_counter_list.append(counter_info.copy())
        return counter_info

    #------------------ ingress_port_priority_group ----------------
    @assignOrder(2)
    def ingress_port_priority_group(self):
        '''
        EXPECTED YAML FORMAT:
        name: ingress-port-priority-group/um-share-buffer-count/port/pg
            counter_vendor_specific_info:
              counter_name: um-share-buffer-count
              port: "1"
              priority-group: "1"
        '''
        global NUM_PORTS
        global NUM_PG
        
        for index1 in range(1, NUM_PORTS + 1):
            for index2 in range(1, NUM_PG + 1):
                counter_vendor_specific_info = { STATS_NAME: ""}
                counter_info[HW_UNIT] = 0
                counter_info[COUNTER_UNIQUE_ID] = "ingress-port-priority-group/um-share-buffer-count/" \
                            + str(index1)+"/" + str(index2)
                counter_vendor_specific_info[STATS_NAME] = "um-share-buffer-count"
                counter_vendor_specific_info[REALM] = "ingress-port-priority-group"
                counter_vendor_specific_info[PORT] = str(index1)
                counter_vendor_specific_info[PG] = str(index2)
                counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
                global_counter_list.append(counter_info.copy())

                counter_vendor_specific_info = { STATS_NAME: ""}
                counter_info[HW_UNIT] = 0
                counter_info[COUNTER_UNIQUE_ID] = "ingress-port-priority-group/um-headroom-buffer-count/" \
                                + str(index1)+"/" + str(index2)
                counter_vendor_specific_info[STATS_NAME] = "um-headroom-buffer-count"
                counter_vendor_specific_info[REALM] = "ingress-port-priority-group"
                counter_vendor_specific_info[PORT] = str(index1)
                counter_vendor_specific_info[PG] = str(index2)
                counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
                global_counter_list.append(counter_info.copy())


    #------------------ ingress_port_service_pool ----------------
    @assignOrder(3)
    def ingress_port_service_pool(self):
        '''
        EXPECTED YAML FORMAT:
        name: ingress-port-service-pool/um-share-buffer-count/port/service-pool
            counter_vendor_specific_info:
              counter_name: um-share-buffer-count
              port: "1"
              service-pool: "1"
        '''
        global NUM_PORTS
        global NUM_SP

        for index1 in range(1, NUM_PORTS + 1):
            for index2 in range(1, NUM_SP + 1):
                counter_vendor_specific_info = { STATS_NAME: ""}
                counter_info[HW_UNIT] = 0
                counter_info[COUNTER_UNIQUE_ID] = "ingress-port-service-pool/um-share-buffer-count/" \
                            + str(index1)+"/" + str(index2)
                counter_vendor_specific_info[STATS_NAME] = "um-share-buffer-count"
                counter_vendor_specific_info[REALM] = "ingress-port-service-pool"
                counter_vendor_specific_info[PORT] = str(index1)
                counter_vendor_specific_info[SP] = str(index2)
                counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
                global_counter_list.append(counter_info.copy())

        #------------------ ingress_service_pool ----------------
    @assignOrder(4)
    def ingress_service_pool(self):
        '''
        EXPECTED YAML FORMAT:
        name: ingress-service-pool/um-share-buffer-count/service-pool/NONE
            counter_vendor_specific_info:
              counter_name: um-share-buffer-count
              service-pool: "1"
        '''
        global NUM_PG

        for index1 in range(1, NUM_SP + 1):
            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "ingress-service-pool/um-share-buffer-count/" \
                        + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "um-share-buffer-count"
            counter_vendor_specific_info[REALM] = "ingress-service-pool"
            counter_vendor_specific_info[SP] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

    #------------------ egress_port_service_pool ----------------
    @assignOrder(5)
    def egress_port_service_pool(self):
        '''
        EXPECTED YAML FORMAT:
        name: egress-port-service-pool/uc-share-buffer-count/port/service-pool
            counter_vendor_specific_info:
              counter_name: uc-share-buffer-count
              port: "1"
              service-pool: "1"
        '''
        global NUM_PORTS
        global NUM_SP

        for index1 in range(1, NUM_PORTS + 1):
            for index2 in range(1, NUM_SP + 1):
                #uc-share-buffer-count counter
                counter_vendor_specific_info = { STATS_NAME: ""}
                counter_info[HW_UNIT] = 0
                counter_info[COUNTER_UNIQUE_ID] = "egress-port-service-pool/uc-share-buffer-count/" \
                            + str(index1)+"/" + str(index2)
                counter_vendor_specific_info[STATS_NAME] = "uc-share-buffer-count"
                counter_vendor_specific_info[REALM] = "egress-port-service-pool"
                counter_vendor_specific_info[PORT] = str(index1)
                counter_vendor_specific_info[SP] = str(index2)
                counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
                global_counter_list.append(counter_info.copy())

                #um-share-buffer-count counter
                counter_vendor_specific_info = { STATS_NAME: ""}
                counter_info[HW_UNIT] = 0
                counter_info[COUNTER_UNIQUE_ID] = "egress-port-service-pool/um-share-buffer-count/" \
                                  + str(index1)+"/" + str(index2)
                counter_vendor_specific_info[STATS_NAME] = "um-share-buffer-count"
                counter_vendor_specific_info[REALM] = "egress-port-service-pool"
                counter_vendor_specific_info[PORT] = str(index1)
                counter_vendor_specific_info[SP] = str(index2)
                counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
                global_counter_list.append(counter_info.copy())

    #------------------ egress_service_pool ----------------
    @assignOrder(6)
    def egress_service_pool(self):
        '''
        EXPECTED YAML FORMAT:
        name: egress-service-pool/uc-share-buffer-count/service-pool/NONE
            counter_vendor_specific_info:
              counter_name: data
              service-pool: "1"
        '''
        global NUM_SP

        for index1 in range(1, NUM_SP + 1):
            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "egress-service-pool/um-share-buffer-count/" \
                        + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "um-share-buffer-count"
            counter_vendor_specific_info[REALM] = "egress-service-pool"
            counter_vendor_specific_info[SP] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "egress-service-pool/mc-share-buffer-count/" \
                        + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "mc-share-buffer-count"
            counter_vendor_specific_info[REALM] = "egress-service-pool"
            counter_vendor_specific_info[SP] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

    #------------------ egress_uc_queue ----------------
    @assignOrder(7)
    def egress_uc_queue(self):
        '''
        EXPECTED YAML FORMAT:
        name: egress-uc-queue/uc-buffer-count/queue/NONE
            counter_vendor_specific_info:
              counter_name: uc-buffer-count
              queue: "1"
        '''
        global NUM_UC_QUEUE

        for index1 in range(1, NUM_UC_QUEUE + 1):
            #um-share-buffer-count counter
            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "egress-uc-queue/uc-buffer-count/" \
                        + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "uc-buffer-count"
            counter_vendor_specific_info[REALM] = "egress-uc-queue"
            counter_vendor_specific_info[QUEUE] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

    #------------------ egress_uc_queue_group ----------------
    @assignOrder(8)
    def egress_uc_queue_group(self):
        '''
        EXPECTED YAML FORMAT:
        name: egress-uc-queue-group/uc-buffer-count/queue/NONE
            counter_vendor_specific_info:
              counter_name: uc-buffer-count
              queue: "1"
        '''
        global NUM_UC_QUEUE_GRP

        for index1 in range(1, NUM_UC_QUEUE_GRP + 1):
            #um-share-buffer-count counter
            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "egress-uc-queue-group/uc-buffer-count/" \
                        + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "uc-buffer-count"
            counter_vendor_specific_info[REALM] = "egress-uc-queue-group"
            counter_vendor_specific_info[QUEUE] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

    #------------------ egress_mc_queue ----------------
    @assignOrder(9)
    def egress_mc_queue(self):
        '''
        EXPECTED YAML FORMAT:
        name: egress-mc-queue/mc-buffer-count/queue/NONE
            counter_vendor_specific_info:
              counter_name: mc-buffer-count
              queue: "1"
        '''
        global NUM_MC_QUEUE

        for index1 in range(1, NUM_MC_QUEUE + 1):
            #um-share-buffer-count counter
            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "egress-mc-queue/mc-buffer-count/" \
                          + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "mc-buffer-count"
            counter_vendor_specific_info[REALM] = "egress-mc-queue"
            counter_vendor_specific_info[QUEUE] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

    #------------------ egress_cpu_queue ----------------
    @assignOrder(10)
    def egress_cpu_queue(self):
        '''
        EXPECTED YAML FORMAT:
        name: egress-cpu-queue/cpu-buffer-count/queue/NONE
            counter_vendor_specific_info:
              counter_name: mc-buffer-count
              queue: "1"
        '''
        global CPU_COSQ

        for index1 in range(1, CPU_COSQ + 1):
            #um-share-buffer-count counter
            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "egress-cpu-queue/cpu-buffer-count/" \
                        + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "cpu-buffer-count"
            counter_vendor_specific_info[REALM] = "egress-cpu-queue"
            counter_vendor_specific_info[QUEUE] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

    #------------------ egress_rqe_queue ----------------
    @assignOrder(11)
    def egress_rqe_queue(self):
        '''
        EXPECTED YAML FORMAT:
        name: egress-rqe-queue/rqe-buffer-count/queue/NONE
            counter_vendor_specific_info:
              counter_name: mc-buffer-count
              queue: "1"
        '''
        global NUM_RQE

        for index1 in range(1, NUM_RQE + 1):
            #um-share-buffer-count counter
            counter_vendor_specific_info = { STATS_NAME: ""}
            counter_info[HW_UNIT] = 0
            counter_info[COUNTER_UNIQUE_ID] = "egress-rqe-queue/rqe-buffer-count/" \
                        + str(index1)+"/NONE"
            counter_vendor_specific_info[STATS_NAME] = "rqe-buffer-count"
            counter_vendor_specific_info[REALM] = "egress-rqe-queue"
            counter_vendor_specific_info[QUEUE] = str(index1)
            counter_info[VENDOR_INFO] = counter_vendor_specific_info.copy()
            global_counter_list.append(counter_info.copy())

 
def create_bufmond_yaml():
    bufmon_template["counters"] = global_counter_list
    ff = open('bufmond.yaml', 'wb')
    ff.write(file_header)
    yaml.dump(bufmon_template, ff, default_flow_style=False)
    ff.close()


def trident(ports):
    '''
    Initialize Trident specific constants
    Call the realm function and populate the counters list
    '''
    global NUM_PORTS
    global NUM_UC_QUEUE
    global NUM_UC_QUEUE_GRP
    global NUM_MC_QUEUE
    global NUM_SP
    global NUM_COMMON_SP
    global NUM_RQE
    global NUM_RQE_POOL
    global NUM_PG
    global CPU_COSQ

    NUM_PORTS = int(ports)
    NUM_UC_QUEUE = 2960
    NUM_UC_QUEUE_GRP = 128
    NUM_MC_QUEUE = 1040
    NUM_SP = 4
    NUM_COMMON_SP = 1
    NUM_RQE = 11
    NUM_RQE_POOL = 4
    NUM_PG = 8
    CPU_COSQ = 48

    #create the realm class object
    realm_obj = realm()

    #Get all the realms functions in the class
    relams_functions_list =  sorted(
             #get a list of fields that have the order set
             [
               getattr(realm_obj, field) for field in dir(realm_obj)
               if hasattr(getattr(realm_obj, field), "order")
             ],
             #sort them by their order
             key = (lambda field: field.order)
            )


    for realm_func in relams_functions_list:
        realm_func()
    #Writing the counters list to the YAML file
    create_bufmond_yaml()

def main(argv):
    global file_header

    if argv[1] == "trident":
        header = file_header % (argv[1], argv[2])
        file_header = header
        trident(argv[2])
    else:
        print 'Only trident asic supported for buffer montioring feature'

if __name__ == '__main__':

    if len (sys.argv) < 3:
        print (['Usage:  [trident] [number of ports]',
            'Please enter chip and number of ports'])
        sys.exit();

    main(sys.argv)
 

