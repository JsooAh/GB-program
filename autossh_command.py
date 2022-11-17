# autossh_command.py
# 최종 수정일 : 221117
# 입력받은 GB code의 AE에 autossh 커맨드를 보내줍니다.

import sys
import os
import pandas as pd
import numpy as np
import requests
import json

host="218.232.234.232"  #건교부 테스트 사이트
#host="m.damoa.io"  #교수님 개인 서버
cse={'name':'cse-gnrb-mon'}

# AE 정보는 해당 디렉토리에 하위에 존재하는 conf.py를 참고한다

def actuate_autossh(aename):
    #print('Actuator')
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F'{host}',
        "Content-Type":"application/vnd.onem2m-res+json; ty=4"
    }
    body={
        "m2m:cin":{
            "con": {
                "cmd":"autossh"
                }
            }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/ctrl"
    r = requests.post(url, data=json.dumps(body), headers=h, timeout = 5)
    print(url, json.dumps(r.json()))
    if "m2m:dbg" in json.dumps(r.json()):
        print("존재하지 않는 주소입니다")
        return False
    else:
        return True

def do_autossh(GBcode):

    dir_list = os.listdir("conf")
    dir_list.sort()

    if GBcode not in dir_list:
        is_lower = GBcode.lower() in dir_list
        is_upper = GBcode.upper() in dir_list
        if is_lower:
            GB_dir = GBcode.lower()
        elif is_upper:
            GB_dir = GBcode.upper()
        else:
            print(F"{GBcode} : 해당 고유번호에 패치된 conf.py를 찾지 못했습니다. 확인 요망.")
            return
    else:
        GB_dir = GBcode
        
    conf_dir = F"./conf/{GB_dir}/conf.py"
    ae_list = list()

    with open(conf_dir, 'r', encoding='UTF8') as f:
        lines = f.readlines() #conf.py 파일을 한줄씩 읽어내려간다. 이때 lines은 줄 맨끝의 개행문자(\n)을 포함하고 있음에 유의.
        for l in lines:
            if "bridge=" in l.replace(" ", ""):
                bridge_num = l.split('"')[1]
            elif "make_ae(" in l:
                #print(l)
                ae_list.append(l.split("'")[1].replace("{bridge}", bridge_num))
                #대표 AE 하나만 뽑아도 되지만... 유사시에 대비해 모든 AE를 받아둔다
                
    is_exist = actuate_autossh(ae_list[0])

    if not is_exist:
        print("autossh 실패. conf.py 파일과 info.xlsx에 차이가 있는 것으로 추정됩니다.")
    else:
        print("autossh 성공")

do_autossh("0019b")
        
'''
GBcode = input("autossh 명령어를 보낼 GB의 고유번호를 입력해주세요. \n")
do_autossh(GBcode)
'''