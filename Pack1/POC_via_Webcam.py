from __future__ import print_function
import sys
import cv2
import time
import os
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.uic import loadUi
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from P2.Auth import Auth

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


class WebCam(QDialog):
    def __init__(self):
        super(WebCam, self).__init__()
        loadUi('MyUi.ui', self)
        self.image = None
        self.frame_count = 0
        self.sec_count = 2
        self.VideoSizeInFrames = 20
        authInst = Auth(SCOPES)
        self.credentials = authInst.getCredentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.start_webcam()

    def start_webcam(self):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture_secondary = cv2.VideoCapture(1)
        self.capture_secondary.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture_secondary.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.imgSize = (640, 480)
        self.fps = 2.0
        self.createVW()
        self.timer = QTimer(self)
        self.t2 = QTimer(self)
        self.t2.timeout.connect(self.update_frame)
        self.timer.timeout.connect(self.motion_detect)
        self.timer.start(1)
        self.t2.start(1)


    def createVW(self):
        current_time = datetime.utcnow().strftime("_%M_%S")
        self.path="D:\Softwares\Eclipse\PythonIntro\Pack1\Media"+datetime.utcnow().strftime("\%Y\%m\%d\%H")
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.fileName = "Video" + current_time
        self.fileName += ".avi"
        self.VideoPath = os.path.join(self.path, self.fileName)
        self.writer_motion = cv2.VideoWriter(self.VideoPath, cv2.VideoWriter_fourcc(*"MJPG"), self.fps, self.imgSize)

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.image = cv2.flip(self.image, 1)
        self.displayImage(self.image, 1)

    def motion_detect(self):
        if self.frame_count == self.VideoSizeInFrames:
            self.save_clip()
            self.createVW()
            self.frame_count = 0
        ret, self.frame1 = self.capture.read()
        self.frame1 = cv2.flip(self.frame1, 1)
        time.sleep(0.1)
        ret, self.frame2 = self.capture.read()
        self.frame2 = cv2.flip(self.frame2, 1)
        img1 = cv2.absdiff(self.frame1, self.frame2)
        gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (21, 21), 0)
        ret, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        _, contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        save = False
        for c in contours:
            if cv2.contourArea(c) > 10000:
                save = True
                break;
        if save:
            self.frame_count += 1
            self.sec_count -= 1
            if self.sec_count == 0:
                current_time = datetime.utcnow().strftime("_%M_%S")
                _, self.sec_image = self.capture_secondary.read()
                iname = "SS"+current_time+".jpeg"
                self.imgPath = os.path.join(self.path, iname)
                self.sec_image = cv2.flip(self.sec_image,1)
                cv2.imwrite(self.imgPath, self.sec_image)
                self.uploadMedia(name=iname, path=self.imgPath, mimetype='image/jpeg')
                self.sec_count = 10
            self.saveImage(self.frame1, self.writer_motion, 1)

    def save_clip(self):
        self.writer_motion.release()
        mtype='video/x-msvideo'
        self.uploadMedia(name=self.fileName, path=self.VideoPath, mimetype=mtype)

    def saveImage(self, img, writer, ret):
        if ret == True:
            writer.write(img)

    def displayImage(self, img, win=1):
        qformat = QImage.Format_Indexed8

        if len(img.shape) == 3:
            if img.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888

        outimage = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        outimage = outimage.rgbSwapped()

        if win == 1:
            self.videoLabel.setPixmap(QPixmap.fromImage(outimage))
            self.videoLabel.setScaledContents(True)

    def uploadMedia(self, name, path, mimetype):
        file_metadata = {'name': name}
        media = MediaFileUpload(str(path), mimetype=mimetype)
        file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(name + " Upload Successful")

    def closeEvent(self, event):
        self.save_clip()
        self.capture_secondary.release()
        self.capture.release()
        super(WebCam, self).closeEvent(event)


app = QApplication(sys.argv)
window = WebCam()
window.setWindowTitle("Smart Video Surveillance")
window.show()
sys.exit(app.exec_())
