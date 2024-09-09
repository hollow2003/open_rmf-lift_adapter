import requests
import json
import urllib3
import socket
import time
from rmf_door_msgs.msg import DoorRequest
import uuid
import hashlib
import binascii
from Crypto.Cipher import AES
import base64
from urllib import parse
## Every robotId has unique token !! 

class LiftClientAPI:
    def __init__(self,appCode,appId,appSecret,test_robotId,projectId):
        self.aes = Aes_ECB(appSecret)
        ## Init encode and decode module
        count = 0
        self.appCode = appCode
        self.appId = appId
        self.appSecret = appSecret
        self.test_robotId = test_robotId
        self.projectId = projectId
        self.connected = True
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        while self.check_connection(self.test_robotId) == '':        
            ## Using get token api to check connection
            if count >= 5:
                print("Unable to connect to lift client API.")
                self.connected = False
                break
            else:
                print("Unable to connect to lift client API. Attempting to reconnect...")
                count += 1
            time.sleep(1)

    def check_connection(self,robotId):
        # Get token and store
        self.connection_data = {"requestId":"Null","sign":"Null","robotId":"Null","projectId":self.projectId,"timestamp":"Null"}
        self.connection_data["requestId"] = getUUID()
        self.connection_data["timestamp"] = int(round(time.time() * 1000))
        self.connection_data["robotId"] = robotId
        self.connection_data["sign"] = md5value(str(self.connection_data.get("projectId"))+str(self.connection_data.get("requestId"))+str(self.connection_data.get("robotId"))+str(self.connection_data.get("timestamp"))+self.appSecret)
        data = '{"requestId":"'+self.connection_data.get("requestId")+'","sign":"'+self.connection_data.get("sign")+'","robotId":"'+self.connection_data.get("robotId")+'","projectId":"'+self.connection_data.get("projectId")+'","timestamp":"'+str(self.connection_data.get("timestamp"))+'"}'
        endata = {"appId":self.appId,"encryptType":"0","encryptScript":self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)   
        try:
            res = requests.request("POST","https://api.yun-r.com/api/cloud/base/developerLogin", headers = self.headers, data = payload)
            res.raise_for_status()
            temp = json.loads(res.text)
            self.result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
            print(self.result)
            if self.result.get('success') == True:
                self.token = self.result.get('data').get('token')
                return self.token
            else:
                return ''
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"Connection Error: {e}")
            return ''
    
    def get_DeviceInfo(self,robotId,token):
        ## Get deviceinfo that this robot can control
        ## In this project every robot can control all lifts 
        ## Because of this this function is none of use
        self.get_DeviceInfo_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","appCode":self.appCode,"projectId":self.projectId}
        self.get_DeviceInfo_data["requestId"] = getUUID()
        self.get_DeviceInfo_data["timestamp"] = int(round(time.time() * 1000))
        self.get_DeviceInfo_data["robotId"] = robotId
        data = '{"requestId":"'+self.get_DeviceInfo_data.get("requestId")+'","robotId":"'+self.get_DeviceInfo_data.get("robotId")+'","timestamp":"'+str(self.get_DeviceInfo_data.get("timestamp"))+'","appCode":"'+self.get_DeviceInfo_data.get("appCode")+'","projectId":"'+self.get_DeviceInfo_data.get("projectId")+'"}'
        endata = {"token":token,"appId": self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            res = requests.request("POST", "https://api.yun-r.com/api/cloud/base/getDeviceInfo", headers = self.headers, data = payload)
            res.raise_for_status()
            temp = json.loads(res.text)
            result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
            print(result)
            if(result.get('success') == True):
                self.devices = result.get('data')
                return True
            else:
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"Connection Error: {e}")
            return False

    def call_lift(self,robotId,deviceUnique,token,fromFloor,toFloor):
        ## Post call lift request
        self.calllift_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","deviceUnique":"Null","fromFloor":"Null","toFloor":"Null","openTime":"90","appCode":self.appCode}
        ## Change the value of openTime (which means effect time that door open) to suit your situation
        self.calllift_data["requestId"] = getUUID()
        self.calllift_data["timestamp"] = int(round(time.time() * 1000))
        self.calllift_data["robotId"] = robotId
        self.calllift_data["deviceUnique"] = deviceUnique
        self.calllift_data["fromFloor"] = fromFloor
        self.calllift_data["toFloor"] = toFloor
        self.calllift_data["deviceUnique"] = deviceUnique
        data = '{"requestId":"'+self.calllift_data.get("requestId")+'","timestamp":"'+str(self.calllift_data.get("timestamp"))+'","robotId":"'+self.calllift_data.get("robotId")+'","deviceUnique":"'+self.calllift_data.get("deviceUnique")+'","appCode":"'+self.calllift_data.get("appCode")+'","fromFloor":"'+self.calllift_data.get("fromFloor")+'","toFloor":"'+self.calllift_data.get("toFloor")+'","openTime":"'+self.calllift_data.get("openTime")+'"}'
        endata = {"token":token,"appId": self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/elevator/callElevator", headers = self.headers, data = payload)
            if response :
                while(1):
                    temp = json.loads(response.text)
                    result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                    print(result)
                    if(result.get('success') == True):
                        return True
                    else:
                        print("Can't call the lift now")
                        return False
                        break
            else:
                print("Invalid response received")
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return False

    def callNoninductive_lift(self,robotId,deviceUnique,token,fromFloor,toFloor):
        ## Post call lift request
        self.calllift_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","deviceUnique":"Null","fromFloor":"Null","toFloor":"Null","openTime":"90","appCode":self.appCode}
        ## Change the value of openTime (which means effect time that door open) to suit your situation
        self.calllift_data["requestId"] = getUUID()
        self.calllift_data["timestamp"] = int(round(time.time() * 1000))
        self.calllift_data["robotId"] = robotId
        self.calllift_data["deviceUnique"] = deviceUnique
        self.calllift_data["fromFloor"] = fromFloor
        self.calllift_data["toFloor"] = toFloor
        self.calllift_data["deviceUnique"] = deviceUnique
        data = '{"requestId":"'+self.calllift_data.get("requestId")+'","timestamp":"'+str(self.calllift_data.get("timestamp"))+'","robotId":"'+self.calllift_data.get("robotId")+'","deviceUnique":"'+self.calllift_data.get("deviceUnique")+'","appCode":"'+self.calllift_data.get("appCode")+'","fromFloor":"'+self.calllift_data.get("fromFloor")+'","toFloor":"'+self.calllift_data.get("toFloor")+'","openTime":"'+self.calllift_data.get("openTime")+'"}'
        endata = {"token":token,"appId": self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/elevator/callNoninductiveElevator", headers = self.headers, data = payload)
            if response :
                while(1):
                    temp = json.loads(response.text)
                    result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                    print(result)
                    if(result.get('success') == True):
                        return True
                    else:
                        if(result.get('data').get('wait') != '0'):
                            print("Need to wait")
                            return False
                        else:
                            print("Can't call the lift")
                            return False
                            break
            else:
                print("Invalid response received")
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return False

    def extend_opentime(self,robotId,deviceUnique,token,position):
        ## Post extend open time request
        self.opendoor_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","deviceUnique":"Null","appCode":self.appCode,"position":"Null","effectiveTime":"90"}
        ## Change the value of effectiveTime to suit your situation
        self.opendoor_data["requestId"] = getUUID()
        self.opendoor_data["timestamp"] = int(round(time.time() * 1000))
        self.opendoor_data["robotId"]  = robotId
        self.opendoor_data["deviceUnique"] = deviceUnique
        self.opendoor_data["position"] = position
        data = '{"requestId":"'+self.opendoor_data.get("requestId")+'","timestamp":"'+str(self.opendoor_data.get("timestamp"))+'","robotId":"'+self.opendoor_data.get("robotId")+'","deviceUnique":"'+self.opendoor_data.get("deviceUnique")+'","appCode":"'+self.opendoor_data.get("appCode")+'","position":"'+self.opendoor_data.get("position")+'","effectiveTime":"90"}'
        endata = {"token":token,"appId": self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/elevator/sendOpenDoor", headers = self.headers, data = payload)
            if response :
                while(1):
                    temp = json.loads(response.text)
                    result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                    print(result)
                    if(result.get('success') == True):
                        return True
                    else:
                        return False 
            else:
                print("Invalid response received")
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return False
    
    def close(self,robotId,deviceUnique,token,position):
        # Post close door request
        self.closedoor_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","deviceUnique":"Null","appCode":self.appCode,"position":"Null","effectiveTime":"0"}
        self.closedoor_data["requestId"] = getUUID()
        self.closedoor_data["timestamp"] = int(round(time.time() * 1000))
        self.closedoor_data["robotId"] = robotId
        self.closedoor_data["deviceUnique"] = deviceUnique
        self.closedoor_data["position"] = position
        data = '{"requestId":"'+self.closedoor_data.get("requestId")+'","timestamp":"'+str(self.closedoor_data.get("timestamp"))+'","robotId":"'+self.closedoor_data.get("robotId")+'","deviceUnique":"'+self.closedoor_data.get("deviceUnique")+'","appCode":"'+self.closedoor_data.get("appCode")+'","position":"'+self.closedoor_data.get("position")+'","effectiveTime":"0"}'
        endata = {"token":token,"appId": self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/elevator/sendOpenDoor", headers = self.headers, data = payload)
            if response :
                while(1):
                    temp = json.loads(response.text)
                    result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                    print(result)
                    if(result.get('success') == True):
                        return True
                    else:
                        return False 
            else:
                print("Invalid response received")
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return False

    def get_Taskinfo(self,robotId,token):
        ## Get task's current state
        self.gettask_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","appCode":self.appCode}
        self.gettask_data["requestId"] = getUUID()
        self.gettask_data["timestamp"] = json.dumps(int(round(time.time() * 1000)))
        self.gettask_data["robotId"] = robotId
        data = '{"requestId":"'+self.gettask_data.get("requestId")+'","timestamp":"'+self.gettask_data.get("timestamp")+'","robotId":"'+self.gettask_data.get("robotId")+'","appCode":"'+self.gettask_data.get("appCode")+'"}'
        endata = {"token":token,"appId": self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/elevator/getTaskInfo", headers = self.headers, data = payload)
            if response:
                temp = json.loads(response.text)
                result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                print(result)
                if result.get('success') == True and result["data"] != '':
                    return result.get('data')
                else :
                    return 4
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return 4
    
    def cancel_Task(self,robotId,token):
        ## Post cancel task request
        self.canceltask_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","appCode":self.appCode}
        self.canceltask_data["requestId"] = getUUID()
        self.canceltask_data["timestamp"] = json.dumps(int(round(time.time() * 1000)))
        self.canceltask_data["robotId"] = robotId
        data = '{"requestId":"'+self.canceltask_data.get("requestId")+'","timestamp":"'+self.canceltask_data.get("timestamp")+'","robotId":"'+self.canceltask_data.get("robotId")+'","appCode":"'+self.canceltask_data.get("appCode")+'"}'
        endata = {"token":token,"appId": self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/elevator/cancelRobotTask", headers = self.headers, data = payload)
            if response:
                temp = json.loads(response.text)
                result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                print(result)
                if result.get('success') == True and result["data"] != '':
                    return True
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return False
    
    def get_Devicestate(self,robotId,token,deviceUnique):
        ## Get device's current state
        self.gettask_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","appCode":self.appCode,"deviceType": "1","deviceUnique" : ""}
        self.gettask_data["requestId"] = getUUID()
        self.gettask_data["timestamp"] = json.dumps(int(round(time.time() * 1000)))
        self.gettask_data["robotId"] = robotId
        self.gettask_data["deviceUnique"] = deviceUnique
        data = '{"requestId":"'+self.gettask_data.get("requestId")+'","timestamp":"'+self.gettask_data.get("timestamp")+'","robotId":"'+self.gettask_data.get("robotId")+'","appCode":"'+self.gettask_data.get("appCode")+'","deviceUnique":"'+self.gettask_data.get("deviceUnique")+'"}'
        endata = {"token":token,"appId":self.appId,"encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}
        payload = parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/base/getDeviceStatus", headers=self.headers, data=payload)
            if response:
                temp = json.loads(response.text)
                result = json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                print(result)
                if(result.get('success') == True):
                        print(result)
                        if result.get('data') != '':
                            return result.get('data')[0].get('floor')
                        else:
                            return 4
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return 4

def getUUID():
    ## Generate UUid
    return "".join(str(uuid.uuid4()).split("-")).upper()
    
def md5value(s):
    ## Calculate md5 value
    ## Used in generate sign
    return hashlib.md5(s.encode(encoding='utf-8')).hexdigest()

class Aes_ECB(object):
    def __init__(self,key):
        self.key = key
        self.MODE = AES.MODE_ECB
        self.BS = AES.block_size
        self.pad = lambda s: s + (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS)
        self.unpad = lambda s: s[0:-ord(s[-1])]

    def add_to_16(value):
        while len(value) % 16 != 0:
            value += '\0'
        return str.encode(value)  
        ## Return bytes


    def AES_encrypt(self, text):
        aes = AES.new(Aes_ECB.add_to_16(self.key), self.MODE)  
        ## Init encode module
        encrypted_text = str(base64.encodebytes(aes.encrypt(Aes_ECB.add_to_16(self.pad(text)))), encoding ='utf-8').replace('\n', '')     
        ## The 'replace' may be not neccessary
        ## In test it works with 'replace' 
        ## Encode and return bytes
        return encrypted_text

    def AES_decrypt(self, text):
        ## Init decode module
        aes = AES.new(Aes_ECB.add_to_16(self.key), self.MODE)
        base64_decrypted = base64.decodebytes(text.encode(encoding ='utf-8'))
        decrypted_text = self.unpad(aes.decrypt(base64_decrypted).decode('utf-8'))
        decrypted_code = decrypted_text.rstrip('\0')
        return decrypted_code
