# inoon-bin_to_csv.py
# 실행파일과 같은 폴더에 있는 raw data bin file을 인식해 csv로 변환해줍니다.
# 편의를 위해 bin list를 출력하고 파일의 번호를 골라 csv로 바꿀 수 있게 했습니다.
# bin_to_csv(filename)만을 사용해도 상관없을듯합니다.

# 220714 업데이트 : bridge number가 8자리 숫자일 때만 정상작동하던 현상을 수정하였습니다.
# 220726 업데이트 : AC, DS의 경우, 데이터의 시간을 밀리세컨드까지 표기하도록 수정하였습니다. 다만 csv 파일에서 시간 셀 서식을 바꾸어야 시간이 제대로 보입니다.
# 220802 업데이트 : 그래프를 포함하는 엑셀 파일을 저장하는 기능을 추가하였습니다. 0802기준 아직 테스트 필요.

import pandas as pd
import openpyxl
from openpyxl import workbook, worksheet
from openpyxl.chart import Reference, LineChart
import matplotlib.pyplot as plt
import json
import requests
import sys
import datetime as dtime
from datetime import datetime
import os


raw_json = {}

# string bin_to_csv(filename)
# 파일 이름을 기반으로 파일에 접근하고 읽습니다. 이후 그 파일의 데이터를 csv 파일 형식으로 변환시켜줍니다.
# 변환이 완료되면 저장한 파일명을 return합니다.
def bin_to_csv(filename, mode):
    if "AC" in filename: type_name = "AC"
    elif "DI" in filename: type_name = "DI"
    elif "TP" in filename: type_name = "TP"
    elif "TI" in filename: type_name = "TI"
    elif "DS" in filename: type_name = "DS"
    else:
        print("ERROR : wrong AE type")
        input("Press enter to exit...")
        sys.exit(0)
    f = open(filename, 'rb')
    #print(filename)
    try:
        raw_json = json.loads(f.read().decode('utf_8'))
    except requests.JSONDecodeError as msg:
        print(F"ERROR : json decode has failed.\n please check the file.")
        sys.exit(0)
    except FileNotFoundError as msg:
        print(F"ERROR : there is no file.\n")
        sys.exit(0)
# file close    

    # 센서 종류와 관계없이 data가 list이므로 
    index_list = list()
    data_list = list()
    time_list = list() # 각각 csv파일의 1열, 2열, 3열에 삽입될 데이터

    start_time = datetime.strptime(raw_json["starttime"],"%Y-%m-%d %H:%M:%S") # 예 : 2022-06-09 09:30:00
    end_time = datetime.strptime(raw_json["endtime"],"%Y-%m-%d %H:%M:%S")

    measure_gap = end_time - start_time 
    measure_time = measure_gap.seconds+1 #통상의 경우 600초
    time_count = 0 # time index 기록용 count
    index_list = list(range(1, raw_json["count"]+1))

    if type_name == "AC" or type_name == "DS": # 1초에 여러 개의 데이터가 들어오는 센서의 경우 
        samplerate = raw_json["count"]//measure_time
        milli_count = 0
        for i in range(len(raw_json["data"])): # time쪽 잘 돌아가는지 잘 볼 것
            data_list.append(raw_json["data"][i])
            csv_file_time = datetime.strftime(start_time + dtime.timedelta(seconds = time_count) + dtime.timedelta(milliseconds = milli_count*10), "%H:%M:%S.%f")
            #print(f'csv_file_time : {csv_file_time}')
            time_list.append(csv_file_time)
            milli_count += 1
            if (i+1)%samplerate == 0:
                time_count +=1
                milli_count = 0

    else: # 1초에 1개의 데이터만 들어오는 경우
        samplerate = 1
        for i in range(len(raw_json["data"])): # time쪽 잘 돌아가는지 잘 볼 것
            data_list.append(raw_json["data"][i])
            csv_file_time = datetime.strftime(start_time + dtime.timedelta(seconds = time_count), "%H:%M:%S")
            time_list.append(csv_file_time) 
            time_count +=1  
            
    excel_frame = pd.DataFrame({"time":time_list, type_name:data_list}, index = index_list)

    if mode == "xlsx": # 그래프를 포함한 엑셀 파일로 받기로 결정했다면, 그에 따른 가공을 한다

        writer = pd.ExcelWriter(F"{filename[:len(filename)-4]}.xlsx", engine='xlsxwriter')
        
        excel_frame.to_excel(writer, sheet_name=type_name)
        writer.save() #1차저장

        #raw data를 기반으로 dataFrame을 생성한 후, 그래프를 그릴 준비를 한다

        wb = openpyxl.load_workbook(filename = F"./{filename[:len(filename)-4]}.xlsx")
        ws = wb[type_name]
        
        # 시트에서 데이터를 수집할 때는 index list의 길이를 기반으로 함
        sensorData = Reference(ws, range_string=F"{type_name}!C2:C{len(index_list)+1}") # 실제 센서 계측값
        timeData = Reference(ws, range_string=F"{type_name}!B2:B{len(index_list)+1}") # 센서 time

        chart = LineChart()
        chart.add_data(sensorData, titles_from_data = True)
        chart.set_categories(timeData) # x축을 시간으로 설정

        # 이하로는 그래프에 적히는 글씨 등에 대한 설정(cosmetic)
        chart.title = F'{type_name} data'
        chart.x_axis.title = 'time'
        chart.y_axis.title = type_name
        chart.legend.position = 'b'
        ## 그래프 작성 완료
        
        ws.add_chart(chart, "H1")
        wb.save(filename=F"{filename[:len(filename)-4]}.xlsx")

        return F"{filename[:len(filename)-4]}.xlsx"

        #일단 테스트해보자
    
    else: # 단순 csv파일로 받기로 결정했다면, 그에 따른 가공을 한다
        #print(excel_frame)
        excel_frame.to_csv(F"{filename[:len(filename)-4]}.csv", mode = "w")

        return F"{filename[:len(filename)-4]}.csv"

# #### 함수부 끝 ####

file_list = os.listdir(os.getcwd()) # 현재 디렉토리에 있는 파일 리스트를 출력
file_list.sort()
not_bin_list = list()
mode = "csv"
for file in file_list:
    if file[13:16] == "ae." and ("AC" in file or "DI" in file or "TP" in file or "TI" in file or "DS" in file) and file[len(file)-4:] ==".bin":
        pass
    else:
        not_bin_list.append(file)

#print(not_bin_list)
if len(not_bin_list) != 0: # bin파일이 아닌 파일이 존재했다면 리스트에서 제외
    for file in not_bin_list:
        file_list.remove(file)

if len(file_list) == 0:
    print("ERROR : there is no file to convert")
    input("press enter to exit...\n")
    sys.exit(0)

while True:
    print("####bin file list####")
    for i in range(len(file_list)):
        print(F"No.{i+1} : {file_list[i]}")
    print("---------")
    print("please select what you want to convert to {1, 2}")
    print("1.csv file without graph")
    print("2.xlsx file with graph")
    input_mode = input()
    if input_mode == "1":
        print("1 => convert to csv file without graph")
        mode = "csv"
    elif input_mode == "2":
        print("2 => convert to xlsx file with graph")
        mode = "xlsx"
    else:
        print(F"{input_mode} => failed to recognize your input")
        print("default convert mode is 1.csv file without graph")
        print("1 => convert to csv file without graph")
        mode = "csv"
    
    input_command = input("do you want to convert all file? {Y, N}\n")
    if input_command == "Y" or input_command == "y":
        print("YES => converting all file...")
        print("---------")
        for i in range(len(file_list)):
            print(F"convert No.{i+1} file : {file_list[i]}")
            print("converting...")
            name = bin_to_csv(file_list[i], mode)
            print(F"csv file name : {name}")

        print("converting completed")
        input("press enter to exit...\n")
        sys.exit(0)

    print("NO => file select mode")
    input_number = input("enter the number of file which you want to convert to csv\n")
    try:
        input_number = int(input_number)
    except ValueError:
        print("ERROR : you should enter integer")
        print("please retry")
        print("---------")
        continue

    if input_number >= 1 and input_number <= len(file_list):
        print(F"selected file : {file_list[input_number-1]}")
        selected_file = file_list[input_number-1]
    else:
        print("ERROR : entered number is out of range")
        print("please retry")
        print("---------")
        continue

    #print(selected_file[:len(selected_file)-4]+".csv")

    if selected_file[:len(selected_file)-4]+".csv" in not_bin_list: # 이미 csv파일이 존재하는 경우, 한번 더 묻는다
        print("ALERT : csv file with same name already exists")
        print("file name :", selected_file[:len(selected_file)-4]+".csv")
        answer = input("do you really want to make csv file? {Y, N} \n")

        if answer == "Y" or answer == "y":
            print("YES => continue converting.")
            print("---------")
            break
        elif answer == "N" or answer == "n":
            print("NO => please enter other file number")
            print("---------")
            continue
        else:
            print("unknown input : consider input NO command")
            print("NO => please enter other file number")
            print("---------")
            continue

    else:
        break


print("converting...")
file_name = bin_to_csv(file_list[input_number-1], mode)
print(F"{mode} file name : ", file_name)
input("press any key to exit...\n")



