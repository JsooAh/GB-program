# makeConf.py
# 최종 수정일 : 221024
# 같은 디렉토리 내에 존재하는 'info.xlsx' 파일의 내용을 읽어 그 내용에 따른 conf.py를 생성합니다.
# 프로그램을 실행시키기 위해서는 같은 디렉토리 내에 참고로 삼을 conf.py 파일이 있어야 합니다.
# 파일명은 전부 conf.py로 통일하나, GB 고유번호에 따라 디렉토리를 따로 생성하여 집어넣습니다.
# 따라서 센서에 conf.py를 실적용할때에는 디렉토리명으로 conf 파일을 구분합니다.
# 1013 업데이트 : [교량명/고유번호] 디렉토리가 아닌 [conf/고유번호]로 conf 파일을 구분하도록 변경 (더 이상 교량명을 conf.py 구분에 사용하지 않음)
# 1024 업데이트 : AE type이 틀렸거나, 끝에 '_X', '_Y', '_Z'로 끝나지 않는 AE명이 포함되어있는 경우 conf.py를 생성하지 않도록 변경

#필요한 모듈 import
import pandas as pd
import numpy as np
import openpyxl
import datetime
import os
import shutil

def sensor_type(aename):
    return aename[0:2]

error_code = list()

# boolean make_conf(dict inf)
# 교량과 AE에 관한 정보가 담긴 dict 정보를 통해 적절한 디렉토리에 conf.py 파일을 새로 생성합니다.
# 성공적으로 파일을 생성한 경우 True를, 아직 정보가 작성되지 않아 파일 생성을 건너뛴 경우 False를 반환합니다.
def make_conf(inf):
    global error_code
    if pd.isnull(inf["GB고유번호"]) or pd.isnull(inf["교량번호"]) or pd.isnull(inf["설치일자"]) or pd.isnull(inf["ae명 1"]):
        print(F"아직 설치정보가 작성되지 않은 교량입니다 : {str(inf)[:80]}...")
        print("conf 파일을 생성하지 않습니다.")
        return False
    #dir1 = inf["교량이름"]
    updir = "conf"
    dir = inf["GB고유번호"]
    # 가장 먼저 conf.py를 저장할 디렉토리가 존재하는지 검사. 없을 경우, 새로 생성한다
    if not os.path.exists(F"{updir}"):
        os.makedirs(F"{updir}")    
    if not os.path.exists(F"{updir}/{dir}"):
        os.makedirs(F"{updir}/{dir}")
    shutil.copy("conf.py", F"./{updir}/{dir}/conf.py") # 적절한 파일 경로에 conf.py 복사

    bridge = str(int(inf["교량번호"]))
    #print(bridge)
    if len(bridge)<6: #교량번호가 6글자 이하라면 "0"을 추가해 자릿수를 맞춰준다
        zero_count = 6-len(bridge)
        while zero_count > 0 :
            bridge = "0"+bridge
            zero_count -= 1

    inf["설치일자"] = inf["설치일자"].strftime("%Y-%m-%d") #pandas의 Timestamp 형식이기 때문에, str로 변환해주어야 한다

    if pd.isnull(inf["설치단면"]): inf["설치단면"] = "."
    # 새롭게 입력할 install정보 입력
    new_install = {"date":inf["설치일자"],"place":inf["교량이름"],"placecode":F"{bridge}","location":inf["설치경간"],"section":inf["설치단면"],"latitude":str(inf["위도"]),"longitude":str(inf["경도"]),"aetype":"D"}
    new_conf = ''
    ae_list= ["ae명 1", "ae명 2", "ae명 3", "ae명 4", "ae명 5", "ae명 6", "ae명 7", "ae명 8", "ae명 9", "ae명 10"]

    #축 방향 결정을 위해 변수 지정

    axis = {"X":"x", "Y":"y", "Z":"z"}

    inf["X축(교축)"]
    inf["Y축(교직)"]
    
    if pd.isnull(inf["X축(교축)"]):
        pass
    else:
        axis["X"] = inf["X축(교축)"]

    if pd.isnull(inf["Y축(교직)"]):
        pass
    else:
        axis["Y"] = inf["Y축(교직)"]

    if pd.isnull(inf["Z축(연직)"]):
        pass
    else:
        axis["Z"] = inf["Z축(연직)"]

    with open(F"./{updir}/{dir}/conf.py", 'r', encoding='UTF8') as f:
        lines = f.readlines() #복사한 conf.py 파일을 한줄씩 읽어내려간다. 이때 lines은 줄 맨끝의 개행문자(\n)을 포함하고 있음에 유의.
        for l in lines:
            if "bridge=" in l.replace(" ", ""): #bridge number 수정
                new_conf += F'bridge = "{bridge}"'

            elif "install=" in l.replace(" ", ""): #install 정보 수정
                new_conf += "install = "+str(new_install)+"\n"

            elif "connect=" in l.replace(" ", ""): #connect를 설정하는 부분 하단에 AE 생성 명령어와 축 변경 명령어를 추가해야한다
                new_conf += l+"\n"
                for i in ae_list:
                    if pd.isnull(inf[i]) : #AE표기 칸이 비어있는 경우, 기입하지 않음
                        continue
                    elif sensor_type(inf[i]) not in {"AC", "DS", "DI", "TI", "TP", "CM"}: # AE type이 틀린 경우, conf.py 파일 생성자체를 하지않는다
                        if sensor_type(inf[i]) == "SW": # 태양광의 경우 아무것도 생성하지 않고 다음 AE로 넘어감
                            continue
                        print("잘못된 AE type이 포함되어 있습니다 :", sensor_type(inf[i]))
                        print("파일을 다시 확인해주세요.")
                        error_code.append(inf["GB고유번호"])
                        return False
                    elif "-" in inf[i] or inf[i][-2:] not in {"_X", "_Y", "_Z"}:
                        print("형식을 위반한 AE명이 포함되어 있습니다 :", inf[i])
                        print("파일을 다시 확인해주세요.")
                        error_code.append(inf["GB고유번호"])
                        return False
                    else:
                        ae_type = sensor_type(inf[i]) # 센서의 type명 추출
                        new_conf += "make_ae(F'ae.{bridge}-"+inf[i]+"', csename, install, connect)\n" #make_ae 추가
                        if ae_type == "AC" or ae_type == "TI": # 축이 구분되는 AE라면 축 변경에 대한 설정을 시행
                            ae_axis = inf[i][len(inf[i])-1:] # X, Y, Z 중 하나
                            if ae_axis.lower() != axis[ae_axis]: # 설정된 축과 실제 축이 다르다면 변경식을 작성
                                new_conf += "ae[F'ae.{bridge}-"+inf[i]+"']['local']['axis']='"+axis[ae_axis].lower()+"'\n"
                    new_conf += "\n" # AE별로 개행


            else: # 바꿀 것이 없는 라인이라면 그대로 new_conf에 추가
                new_conf += l

    with open(F"./{updir}/{dir}/conf.py", 'w', encoding='UTF8') as f:
        f.write(new_conf) #새롭게 구성한 string new_conf를 이용해 새롭게 파일을 작성한다
        return True

info_file = "info.xlsx" # 만일 참고로 삼을 엑셀파일명이 바뀌었다면 이것을 수정한다
header = 0
df = pd.read_excel(info_file, sheet_name = 0, header = header)
info_dict = df.to_dict('records') # DataFrame을 dict 형식으로 변환
#print(info_dict)

print("conf.py 파일 생성 시작")
file_num = 0

for inf in info_dict:
    #print("다음 GB에 대한 파일 생성 중 :", str(inf)[:60], "...")
    check = make_conf(inf)
    if check:
        file_num += 1
print("conf 파일 생성 완료")
print("생성한 conf 파일의 개수 :", file_num)
if len(error_code) > 0:
    print("다음 GB code는 conf.py를 생성하지 않았음. (디렉토리는 생성됨) 엑셀 파일을 재확인해주세요.")
    print(error_code)


