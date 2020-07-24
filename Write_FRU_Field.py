import subprocess
import re
import argparse
import sys
import os
from os import path
import time
import copy
import logging


inter_files = []
logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.INFO , filename='Write_FRU_Field.log')

def Write_FRU(ip,username,passwd,slot, field_id, value):
    slot_map = {'CMM':'1' ,'A1':'3', 'A2':'4', 'B1':'5', 'B2':'6', 'CMM2':'18'}
    fields = {'1':'PS', '2':'PPM', '3':'PN','4':'BS','5':'BP','6':'BPN'}
    if sys.platform.lower() == 'win32':
        tool_cmd = f'SMCIPMITool.exe'
    else:
        tool_cmd = 'SMCIPMITool'
    com = [tool_cmd, ip, username, passwd]
    c1 = copy.deepcopy(com)

    run_SMCIPMITool(c1 + ['ipmi', 'raw', '30', '6', '0'])
    if slot != 'CMM' and slot != 'CMM2':
        slot_txt = slot.lower()
        run_SMCIPMITool(c1 + ['ipmi','raw', '30', '33', '28', slot_txt, '0'])
    msg = run_SMCIPMITool(c1 + ['ipmi', 'fruidw', slot_map[slot], fields[field_id], value], True)
    run_SMCIPMITool(c1 + ['ipmi', 'raw', '30', '6', '1'])
    if slot != 'CMM' and slot != 'CMM2':
        run_SMCIPMITool(c1 + ['ipmi','raw', '30', '33', '28', slot_txt, '1'])
    #print(msg)
    result = re.search(r'\(' + fields[field_id] + '\)\s+\=\s?(.+?)\s+\n+', msg)
    if result:
        #print(result)
        if value != result.group(1).rstrip().lstrip():
            print("Failed to write {}.".format(fields[field_id]))
            logging.error("Field value not identical in {}. {} vs {}".format(fields[field_id], value, result.group(1).rstrip().lstrip()))
            return False
    else:
        print("Failed to write {}.".format(fields[field_id]))
        logging.error("Failed to write {}.".format(fields[field_id]))
        return False
    return True

def run_SMCIPMITool(com, check=False):

    try:
        output = subprocess.run(com, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # os.system(cmd)
    except Exception as e:
        print("Error has occurred in updating FRU. " + str(e))
        logging.warning("Error has occurred in updating FRU. " + str(e))
        sys.exit()
    if output.returncode != 0:
        print("Failed running SMCIPMITool " + output.stdout.decode("utf-8", errors='ignore'))
        logging.error("Failed running SMCIPMITool " +  output.stdout.decode("utf-8", errors='ignore'))
        sys.exit()
    if check:
        return output.stdout.decode("utf-8", errors='ignore')

def check_connectivity(ip):
    if sys.platform.lower() == 'win32':
        res = subprocess.run(['ping','-n','3', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        res = subprocess.run(['ping', '-c', '3', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode  != 0:
        return False
    else:
        out_text = res.stdout.decode("utf-8", errors='ignore')
        #print(out_text)
        if 'Destination host unreachable' in out_text:
            return False
        else:
            return True

def main():
    data = {}
    try:
        with open('config.txt', 'r') as file:
        #with open(sys.argv[1], 'r') as file:
            for line in file:
                result = re.match(r'^(\w+.*?)\:(.*?)$', line)
                if result:
                    value = result.group(2).rstrip().lstrip()
                    if value and value != '':
                        field = result.group(1).rstrip().lstrip()
                        field = re.sub(r'\(.*?\)', '', field)
                        if field.upper() not in data.keys():
                            data[field.upper()] = value
                        else:
                            if type(data[field.upper()]) is list:
                                data[field.upper()].append(value)
                            else:
                                data[field.upper()] = [data[field.upper()], value]
    except IOError as e:
        print("config file is not available. Please read readme file and run this program again. Leave program!")
        logging.error("config file is not available.")
        sys.exit()
    #print(data)

    if 'CMM IP' in data.keys():
        ip = data['CMM IP']

    else:
        print("CMM IP is missing. Leave program!")
        sys.exit()

    if 'CMM USER NAME' in data.keys():
        username =  data['CMM USER NAME']

    else:
        print("CMM user name is missing. Leave program!")
        sys.exit()

    if 'CMM PASSWORD' in data.keys():
        password = data['CMM PASSWORD']

    else:
        print("CMM Password is missing. Leave program!")
        sys.exit()

    if not check_connectivity(ip):
        print("Failed to access to {}. Leave program!!".format(ip))
        sys.exit()

    print(data)
    devices = {}
    for k in data.keys():
        field = data[k]
        k = k.upper()
        result = re.match(r'^(\w+)\s+Field$', k, re.IGNORECASE)
        if result:
            slot = result.group(1).rstrip().lstrip()
            val_text = slot + ' VALUE'

            if val_text in data.keys():
                value = data[val_text]

                if type(field) is list:
                    devices[slot] = []
                    for i in range(len(field)):
                        devices[slot].append([field[i], value[i]])
                else:
                    devices[slot] = [[field, value]]

            else:
                print("ERROR! Can Not find value of {}. Skip programming this slot.".format(slot))
                logging.ERROR("ERROR! Can Not find value of {}.".format(slot))
    print(devices)

    for slot, f in devices.items():
        print("Programming {}".format(slot))
        logging.info("Programming {}".format( slot))
        for v in f:
            field_id, value = [v[i] for i in range(2)]
            print(field_id, value)
            if Write_FRU(ip, username, password,slot,field_id,value):
                print("Program successfully in {}".format(slot))
                logging.info("Program successfully in {}".format(slot))

if __name__ == '__main__':
    main()
