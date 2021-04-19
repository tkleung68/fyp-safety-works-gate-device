import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import re
import datetime
import time
import os
from os import listdir
from os.path import isfile, join
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# video set-up
cap = cv2.VideoCapture(0)
font = cv2.FONT_HERSHEY_DUPLEX

# firebase set-up
cred = credentials.Certificate(
    "firebase/safety-works-316c4-firebase-adminsdk-287vn-1d4e891f0e.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


def transmiss(data):
    try:
        doc_ref = db.collection("equipment").document()
        doc_ref.set(data)
    except Exception as e:
        print(e)

    ID = ""
    try:

        doc_liveRef = db.collection("project").document(
            "DtviKY6dGOgGpgF4pZQ2").collection("worker")
        doc_live = doc_liveRef.where('user', '==', data['user']).stream()
        for doc in doc_live:
            # print(f'{doc.id} => {doc.to_dict()}')
            ID = doc.id
        if(ID == ""):
            doc_liveRef = db.collection("project").document(
                "DtviKY6dGOgGpgF4pZQ2").collection("worker").document()
            doc_liveRef.set({'user': data['user']})

        doc_liveRef = db.collection("project").document(
            "DtviKY6dGOgGpgF4pZQ2").collection("worker")
        doc_live = doc_liveRef.where('user', '==', data['user']).stream()

        if(data['result']):
            doc_liveRef = db.collection("project").document(
                "DtviKY6dGOgGpgF4pZQ2").collection("worker").document(ID)
            doc_liveRef.update({'equipment_dateTime': data['dateTime']})

    except Exception as e:
        print(e)


def checkLabel(path):
    # get files
    allresults = []
    try:
        allresults = [f for f in listdir(path) if isfile(join(path, f))]
    except:
        return 400

    for result in allresults:
        countHead = 0
        countHelmet = 0
        countPerson = 0
        try:
            resultFile = open(path + "/" + result, "r")
            # per one image
            for line in resultFile:
                if(line[0] == '0'):
                    countHead += 1
                elif(line[0] == '1'):
                    countHelmet += 1
                elif(line[0] == '2'):
                    countPerson += 1
        except:
            pass

        # detected a helmet
        if(countHelmet > 0):
            # no head and no other person
            if(countHead == 0 and countPerson == 0):
                return 200
    return 201


def checkEmail(email):
    if(re.search(regex, email)):
        return True
    return False


def auth(img):
    decodeedObjects = pyzbar.decode(img)
    ret = {"status": "", "message": ""}
    if(len(decodeedObjects) == 0):
        ret["status"] = 400
        ret["message"] = "Waiting for the Login QR code ..."
    elif(len(decodeedObjects) > 1):
        ret["status"] = 402
        ret["message"] = "Multiple QRcodes. Please try again."
    else:
        for obj in decodeedObjects:
            email = str(obj.data)
            if(checkEmail(email[2: -1])):

                ret["status"] = 200
                ret["message"] = "Sccessfully logined: {}".format(email[2: -1])
                ret['email'] = email
            else:
                ret["status"] = 401
                ret["message"] = "Wrong format"
    return ret


# flag , constants, variables
regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
FOLDER_PREFIX = "scannedPhoto/"

isScanned = False
email = ""

lockMessage = False
folderExists = False
currentFilePath = ""
currentFolderPath = ""
currentRecordTime = ""
count = 0
currentRecordTimestamp = 0
currentUser = ""
isProcessed = False
isSubmitted = False
oldTime = datetime.datetime.now()
time.sleep(5)


# main logic, UI
while True:
    _, frame = cap.read()
    # Decode from QRcode
    newTime = datetime.datetime.now()
    if(isScanned == False):
        if(newTime - oldTime).seconds >= 3:
            result = auth(frame)
            lockMessage = False

        if (result["status"] == 200):
            # has a email address
            cv2.rectangle(frame, (100, 90), (900, 90), (0, 255, 0), 50)
            cv2.putText(frame, result["message"],
                        (100, 100), font, 1, (255, 255, 255), 1)
            currentUser = result['email'][2:-1]
            isScanned = True
            oldTime = newTime

        elif(result["status"] > 200):
            # error

            cv2.rectangle(frame, (100, 90), (650, 90), (255, 255, 255), 50)
            cv2.putText(frame, result["message"],
                        (100, 100), font, 1, (116, 181, 254), 1)
            if(lockMessage == False):
                if(result["status"] != 400):
                    oldTime = newTime
                    lockMessage = True
            else:
                pass
    else:
        if(newTime - oldTime).seconds <= 1:
            cv2.rectangle(frame, (100, 90), (900, 90), (0, 255, 0), 50)
            cv2.putText(frame, result["message"],
                        (100, 100), font, 1, (255, 255, 255), 1)
        elif(newTime - oldTime).seconds <= 2:
            cv2.rectangle(frame, (100, 90), (950, 90), (0, 255, 0), 50)
            cv2.putText(frame, "Please show your face in front of the camera ... 3",
                        (100, 100), font, 1, (255, 255, 255), 1)
        elif(newTime - oldTime).seconds <= 3:
            cv2.rectangle(frame, (100, 90), (950, 90), (0, 255, 0), 50)
            cv2.putText(frame, "Please show your face in front of the camera ... 2",
                        (100, 100), font, 1, (255, 255, 255), 1)
        elif(newTime - oldTime).seconds <= 4:
            now_raw = datetime.datetime.now()
            now_str = now_raw.strftime("%Y-%m-%d_%H_%M_%S")
            currentRecordTimestamp = int(now_raw.timestamp())
            # 2021-04-13 01:05:47
            currentRecordDateTime = now_raw.strftime("%Y/%m/%d %H:%M:%S")

            if(folderExists == False):
                try:
                    currentRecordTime = now_str
                    os.mkdir(FOLDER_PREFIX + "/" + currentRecordTime)

                    folderExists = True
                    currentFolderPath = FOLDER_PREFIX + "/" + currentRecordTime
                except Exception as e:
                    print(e)
            else:
                currentFilePath = currentFolderPath + "/{}.jpg".format(now_str)
                cv2.imwrite(currentFilePath, frame)
                if(os.path.exists(currentFilePath)):
                    count += 1

            cv2.rectangle(frame, (100, 90), (950, 90), (0, 255, 0), 50)
            cv2.putText(frame, "Please show your face in front of the camera ... 1",
                        (100, 100), font, 1, (255, 255, 255), 1)

        elif(newTime - oldTime).seconds <= 16:

            if(folderExists == True):
                if(checkLabel("result/{}/labels".format(currentRecordTime)) == 400):
                    cv2.rectangle(frame, (100, 90), (950, 90), (0, 255, 0), 50)
                    cv2.putText(frame, "Waiting for the result",
                                (100, 100), font, 1, (255, 255, 255), 1)

                if(isProcessed == False):
                    os.system("python yolov5/detect.py --source {}  --weights 'yolov5/runs/train/helmet/weights/best.pt' --conf 0.5 --project result --name {} --save-txt".format(currentFolderPath, currentRecordTime))
                    isProcessed = True
                else:
                    # "/Users/samsam/Study/Year4/final year project/source/hardhat/result/2021-04-06_23_02_044" + "/labels"
                    # print(checkLabel("result/{}/labels".format(currentRecordTime)))
                    if(checkLabel("result/{}/labels".format(currentRecordTime)) == 200):
                        cv2.rectangle(frame, (100, 90),
                                      (900, 90), (0, 255, 0), 50)
                        cv2.putText(frame, "You have equipped helmet! ",
                                    (100, 100), font, 1, (255, 255, 255), 1)
                        if(isSubmitted == False):
                            # dummy = {"equipment": "123", "result": 1, "timestamp": 23456789, "user": "abc3328658@yajdisa.com"}
                            data = {"equipment": "helmet", "result": 1,
                                    "timestamp": currentRecordTimestamp, "user": currentUser, "dateTime": currentRecordDateTime}
                            transmiss(data)
                            isSubmitted = True
                    elif(checkLabel("result/{}/labels".format(currentRecordTime)) == 201):
                        cv2.rectangle(frame, (100, 90),
                                      (900, 90), (0, 255, 0), 50)
                        cv2.putText(frame, "Please adjust your position! ",
                                    (100, 100), font, 1, (255, 255, 255), 1)

                        if(isSubmitted == False):
                            # dummy = {"equipment": "123", "result": 1, "timestamp": 23456789, "user": "abc3328658@yajdisa.com"}
                            data = {"equipment": "helmet", "result": 0,
                                    "timestamp": currentRecordTimestamp, "user": currentUser, "dateTime": currentRecordDateTime}
                            transmiss(data)
                            isSubmitted = True

        else:
            count = 0
            folderExists = False
            isScanned = False
            isProcessed = False
            isSubmitted = False

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1)  # s will pause the video
    if key == ord('S') or key == ord('s'):
        break
    elif key == ord('R') or key == ord('r'):
        isScanned = False
