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
logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.INFO , filename='Write_FRU.log')

def Write_FRU(ip,username,passwd,ps,slot):
    slot_map = {'CMM':'1' ,'A1':'3', 'A2':'4', 'B1':'5', 'B2':'6', 'CMM2':'18'}
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
    msg = run_SMCIPMITool(c1 + ['ipmi', 'fruidw', slot_map[slot], 'PS', ps], True)
    run_SMCIPMITool(c1 + ['ipmi', 'raw', '30', '6', '1'])
    if slot != 'CMM' and slot != 'CMM2':
        run_SMCIPMITool(c1 + ['ipmi','raw', '30', '33', '28', slot_txt, '1'])

    result = re.search(r'Product\s+Serial\s+Number\s+\(PS\)\s+\=\s?(\w+)', msg)
    if result:
        if ps != result.group(1).rstrip().lstrip():
            print("Failed to write product serial number.")
            logging.error("Product serial number not identical")
            return False
    else:
        print("Failed to write product serial number.")
        logging.error("Product serial number not found")
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
                        data[field] = value
    except IOError as e:
        print("config file is not available. Please read readme file and run this program again. Leave program!")
        logging.error("config file is not available.")
        sys.exit()
    #print(data)

    if 'CMM IP' in data.keys():
        ip = data['CMM IP']
        del data['CMM IP']
    else:
        print("CMM IP is missing. Leave program!")
        sys.exit()

    if 'CMM User Name' in data.keys():
        username =  data['CMM User Name']
        del data['CMM User Name']
    else:
        print("CMM user name is missing. Leave program!")
        sys.exit()

    if 'CMM Password' in data.keys():
        password = data['CMM Password']
        del data['CMM Password']
    else:
        print("CMM Password is missing. Leave program!")
        sys.exit()

    if not check_connectivity(ip):
        print("Failed to access to {}. Leave program!!".format(ip))
        sys.exit()

    #print(data)

    for slot, ps in data.items():
        print("Programming {} to {}".format(ps, slot))
        logging.info("Programming {} to {}".format(ps, slot))
        if Write_FRU(ip, username, password,ps,slot):
            print("Program successfully in {}".format(slot))
            logging.info("Program successfully in {}".format(slot))

if __name__ == '__main__':
    main()
