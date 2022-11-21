import os
import requests
import json
from time import sleep
from datetime import datetime

host="218.232.234.232"  #건교부 테스트 사이트
#host="m.damoa.io"  #교수님 개인 서버
cse={'name':'cse-gnrb-mon'}
updir = "conf"

state_text = ""

def sensor_type(aename):
    return aename[0:2]

#void actuate_state_check(string aename)
#제시된 AE의 가장 최근 state cin 정보를 가져옵니다. 형태는 dict.
def actuate_state_check(aename):
    #print('Actuator')
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F'{host}',
        "Content-Type":"application/vnd.onem2m-res+json; ty=4"
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/state/la"
    r = requests.get(url, headers=h, timeout = 5)
    #print(json.dumps(r.json()))
    if "m2m:dbg" in json.dumps(r.json()):
        print("존재하지 않는 주소입니다")
        return "NONE"
    else:
        return r.json()["m2m:cin"]["con"]

#print(actuate_state_check("ae.025507-AC_S1Q2_01_Z"))

def actuate_reqstate(aename):
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
                "cmd":"reqstate"
                }
            }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/ctrl"
    r = requests.post(url, data=json.dumps(body), headers=h)
    print("reqstate")
    #print(url, json.dumps(r.json()))

def AE_check(GBcode):
    global state_text
    ERROR_text = ""
    print("다음 GB code에 대한 AE를 체크 중... :", GBcode)
    conf_dir = F"./{updir}/{GBcode}/conf.py"

    if not os.path.exists(F"{updir}/{GBcode}"):
        print(F"없는 고유 번호입니다 : {GBcode}")
        return

    with open(conf_dir, 'r', encoding='UTF8') as f:
        lines = f.readlines() #conf.py 파일을 한줄씩 읽어내려간다. 이때 lines은 줄 맨끝의 개행문자(\n)을 포함하고 있음에 유의.
        for l in lines:
            if "bridge=" in l.replace(" ", ""):
                bridge_num = l.split('"')[1]
            elif "install=" in l.replace(" ", ""):
                bridge_name = l.split(",")[1].replace(" ", "").split("'")[3]
            elif "make_ae(" in l:
                #print(l)
                aename = l.split("'")[1].replace("{bridge}", bridge_num)
                break #aename을 확정했다면 break

    #print(aename)

    state_dict = actuate_state_check(aename)
    if state_dict == "NONE": # 1관문 : AE가 존재하는가?
        ERROR_text = F"{bridge_name}({GBcode}) - {aename} : AE가 존재하지 않습니다.\n"
        state_text += F"{GBcode} :: state가 존재하지 않음\n"
    else:
        state_time = state_dict["time"]
        state_text += F"{GBcode} :: battery = {state_dict['battery']}, solarchargevolt = {state_dict['solarchargevolt']}\n"
        if (datetime.now() - datetime.strptime(state_time, "%Y-%m-%d %H:%M:%S")).total_seconds() >= 7200: # 2관문 : 가장 최근에 state를 갱신한 것이 2시간 이내인가?
            ERROR_text = F"{bridge_name}({GBcode}) - {aename} : state cin이 오랫동안 갱신되지 않았습니다. {state_time} :: battery = {state_dict['battery']}, solarchargevolt = {state_dict['solarchargevolt']}\n"
        else:
            actuate_reqstate(aename)
            sleep(2)
            state_dict_after = actuate_state_check(aename)
            state_time_after = state_dict_after["time"]

            if state_time == state_time_after:# 3관문 : mqtt가 살아있는가?
                ERROR_text = F"{bridge_name}({GBcode}) - {aename} : mqtt 명령어가 작동하지 않습니다.\n"

    if len(ERROR_text) == 0:
        print(F"{bridge_name}({GBcode}) - {aename} : 테스트 통과!")
    else:
        print(ERROR_text)
    print("-----------------")
    return ERROR_text


dir_list = os.listdir("conf")
dir_list.sort()

print("작동확인을 시작합니다.")
print("확인 대상 GB code : ", dir_list)

text_file = ""

for code in dir_list:
    text = AE_check(code)
    if len(text) != 0: # 에러가 난 경우
        text_file += text

print("검사 종료")

if len(text_file) == 0:
    print("에러 AE 없음!")
    print("state 정보를 작성합니다...")
    with open(F"{datetime.now().strftime('%Y%m%d%H%M')}_AEcheck.txt", 'a', encoding='UTF8') as f:
        f.write("GBcode별 배터리/전압 정보\n") # 모든 AE에 문제가 없는 경우, state 정보만을 담은 파일 생성
        f.write(state_text)

else:
    print("에러 AE에 대한 정보를 작성합니다...")
    print(text_file)
    with open(F"{datetime.now().strftime('%Y%m%d%H%M')}_AEcheck.txt", 'a', encoding='UTF8') as f:
        f.write(text_file) # 패치에 실패한 파일 리스트를 작성
        f.write("-----------------\n")
        f.write("GBcode별 배터리/전압 정보\n")
        f.write(state_text)