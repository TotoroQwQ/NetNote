import os
import xlrd

def getTemperature(contents):
    opTypes=["调高","调低","测温"]
    keywords=["温度","调温",""]
    results=[]
    for content in contents:
        if "温" in str(content):
            results.append(content)
    print(len(results),results)


path = "C:/Users/chens/Desktop/record"
files = os.listdir(path)
for index, file in enumerate(files):
    if index >= 1:
        break
    fileName = path+"/"+file
    excel = xlrd.open_workbook(fileName)
    sheet = excel.sheet_by_index(0)

    serverType = sheet.col(2)[4:]  # 服务类型2
    timeList = sheet.col(11)[4:]  # 服务日期11
    contents = sheet.col(4)[4:]  # 服务类容4
    locationList = sheet.col(3)[4:]  # 服务地点3

    # print(contents)
    getTemperature(contents)



