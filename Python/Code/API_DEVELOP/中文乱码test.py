import os,json

dir = './data'
tokenRecordFile = dir+'/data.json'
def loadRecords():
        """ 从文件读取以前保存得token数据 """
        try:
            if os.path.exists(tokenRecordFile):
                rfile = open(tokenRecordFile, "r")
                result=rfile.read()
                print(type(result),result)
                __TokenRecords = json.loads(result)
                print(__TokenRecords)
                __Users = [item['user'] for item in __TokenRecords["records"]]
                print(__Users)
        except Exception as e:
            print(e)

loadRecords()