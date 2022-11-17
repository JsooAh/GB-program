import os
import requests
import json
from time import sleep

host="218.232.234.232"  #건교부 테스트 사이트
#host="m.damoa.io"  #교수님 개인 서버
cse={'name':'cse-gnrb-mon'}
updir = "conf"

already_patched_list = list() # 이미 conf.py 변경을 완료한 GBcode list
with open("patch_list.txt", 'r',  encoding='UTF8') as f:
    lines = f.readlines()
    for l in lines:
        already_patched_list.append(l.replace("\n", ""))


def sensor_type(aename):
    return aename[0:2]

# void actuate_autossh(aename)
# 입력받은 AE에 autossh 명령어를 보냅니다.
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

def actuate_fwupdate(aename):
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
                "cmd":"fwupdate",
                "protocol":"HTTP",
                "ip":host,
                "port":2883,
                "path":"/fwupdate/20221028_151642.BIN"
                }
            }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/ctrl"
    r = requests.post(url, data=json.dumps(body), headers=h, timeout = 5)
    print(url, json.dumps(r.json()))

# void conf_patch(string GBcode, int c = 0)
# 제시받은 GBcode를 기반으로 ssh 접속을 하고, 디렉토리명을 기반으로 conf.py를 패치합니다.
def conf_patch(GBcode, c = 0): #GB code는 
    print(F"다음 고유번호의 conf.py를 패치 중... : {GBcode}")
    conf_dir = F"./{updir}/{GBcode}/conf.py"
    if not os.path.exists(F"{updir}/{GBcode}"):
        print(F"없는 고유 번호입니다 : {GBcode}")
        return
    '''
    bridge_num = ""
    aename = ""
    with open(conf_dir, 'r', encoding='UTF8') as f:
        lines = f.readlines() #conf.py 파일을 한줄씩 읽어내려간다. 이때 lines은 줄 맨끝의 개행문자(\n)을 포함하고 있음에 유의.
        for l in lines:
            if "bridge=" in l.replace(" ", ""):
                bridge_num = l.split('"')[1]
            elif "make_ae(" in l:
                #print(l)
                aename = l.split("'")[1].replace("{bridge}", bridge_num)
                break #aename을 확정했다면 break
    '''
    exist = actuate_autossh(F"ae.T{GBcode.lower()}-AC_S1M_01_X")
    if not exist:
        print(F"임시 AE가 존재하지 않습니다: {GBcode}")
        with open("error_list.txt", 'a', encoding='UTF8') as f:
            f.write(F"{GBcode} : resource does not exist\n") # 패치에 실패한 파일 리스트를 작성
        print("-------------------")
        return
    sleep(2) # autossh 명령 이후, 로딩시간을 가진다

    standard_dir = os.getcwd().replace("/home/ubuntu/", "")
    print("standard_dir:", standard_dir)

    child = pexpect.spawn(F"ssh pi@localhost -p 1{GBcode[0:4]}")
    try:
        child.expect(F"pi@")
        child.sendline(F"rcp ubuntu@bridge.ino-on.net:{standard_dir}/{updir}/{GBcode}/conf.py ~/GB") #conf.py 파일 바꿔치기
        print("rcp")

        sleep(2)

        child.expect(F"pi@")
        child.sendline("pm2 restart all")
        print("pm2 restart all")

        sleep(4)

        child.expect(F"pi@")
        child.sendline("exit")
        print("exit")

    except pexpect.TIMEOUT:
        print(F"conf.py 수정에 실패함(timeout) : {GBcode}")
        with open("error_list.txt", 'a', encoding='UTF8') as f:
            f.write(F"{GBcode} : timeout\n") # 패치에 실패한 파일 리스트를 작성
        print("-------------------")
        return
    
    except pexpect.EOF:
        print(F"conf.py 수정에 실패함(connection refused) : {GBcode}")
        count = c+1
        if count >= 2:
            print(F"업데이트 재시도 횟수 초과. conf.py 수정에 실패함(connection refused) : {GBcode}")
            with open("error_list.txt", 'a', encoding='UTF8') as f:
                f.write(F"{GBcode} : connection refused\n") # 패치에 실패한 파일 리스트를 작성
            print("-------------------")
            return
        print("업데이트 시도 : 20221028_151642.BIN")
        actuate_fwupdate(F"ae.T{GBcode.lower()}-AC_S1M_01_X")
        print("30초간 대기합니다...")
        sleep(30)
        print("conf.py 수정 재시도...")
        conf_patch(GBcode, count)
        return
    print(F"conf.py 파일 패치 및 재실행 완료 : {GBcode}")
    with open("patch_list.txt", 'a', encoding='UTF8') as f:
        f.write(F"{GBcode}\n") # 패치가 된 파일 리스트를 새롭게 작성
    print("-------------------")

def patch_start(GBcode):
    #actuate_autossh(F"ae.T{GBcode.lower()}-AC_S1M_01_X") #autossh 재실행 명령을 보낸다
    conf_patch(GBcode)

try:
    import pexpect
except ImportError: # import할 수 없었다는 것은 pexpect 모듈이 설치되어있지 않다는 의미. 설치를 시행하고 import한다
    print("there is no pexpect module.")
    print("install pexpect...")
    os.system("pip install pexpect")
    import pexpect

dir_list = os.listdir("conf")
dir_list.sort()
#print(dir_list)


#test_code = "0150a"
conf_patch("0042B")
'''
'''

'''
print("#################")
print(F"이미 패치된 GB code list")
print(already_patched_list)
print("이미 패치된 GB code를 제외하고 패치 리스트를 구성합니다...")
for rem in already_patched_list:
    try:
        dir_list.remove(rem)
    except:
        pass # 중복된 GB code가 저장되어있을 가능성에 대비
print("패치할 GBcode 리스트")
print(dir_list)
print("#################")

for dir in dir_list:
    conf_patch(dir)
    
''' 


