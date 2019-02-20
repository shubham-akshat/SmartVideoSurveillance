from __future__ import print_function
import sys
import cv2
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.uic import loadUi
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from Pack1 import Auth

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


class WebCam(QDialog):
    def __init__(self):
        super(WebCam, self).__init__()
        loadUi('MyUi.ui', self)
        self.image = None
        self.count = 0
        self.sec_count = 2
        self.name_count = 0
        authInst = Auth.Auth(SCOPES)
        self.credentials = authInst.getCredentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.startButton.clicked.connect(self.start_webcam)
        self.stopButton.clicked.connect(self.stop_webcam)

    def start_webcam(self):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture_secondary = cv2.VideoCapture(1)
        self.capture_secondary.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture_secondary.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        current_date = datetime.utcnow().strftime("%Y%m%d")
        self.count += 1
        self.fileName = "Video" + current_date + "_" + str(self.count)
        self.fileName += ".avi"
        self.imgSize = (640, 480)
        self.fps = 2.0
        self.writer_motion = cv2.VideoWriter(self.fileName, cv2.VideoWriter_fourcc(*"MJPG"), self.fps, self.imgSize)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.timeout.connect(self.motion_detect)
        self.timer.start(1)

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.image = cv2.flip(self.image, 1)
        self.displayImage(self.image, 1)

    def motion_detect(self):
        ret, self.frame1 = self.capture.read()
        self.frame1 = cv2.flip(self.frame1, 1)
        time.sleep(0.25)
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
            self.sec_count-=1
            if (self.sec_count==0):
                current_time = time.time()
                _, self.sec_image = self.capture_secondary.read()
                iname="SS"+str(current_time)+".jpeg"
                self.sec_image = cv2.flip(self.sec_image,1)
                cv2.imwrite(iname,self.sec_image)
                self.uploadMedia(fname=iname, mimetype='image/jpeg')
                self.sec_count = 10
            self.saveImage(self.frame1, self.writer_motion, 1)

    def stop_webcam(self):
        self.timer.stop()
        mtype='video/x-msvideo'
        fname=str(self.fileName)
        self.uploadMedia(fname=fname, mimetype=mtype)

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

    def uploadMedia(self, fname, mimetype):
        file_metadata = {'name': fname}
        media = MediaFileUpload(fname, mimetype=mimetype)
        file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(fname+" Upload Successful")


app = QApplication(sys.argv)
window = WebCam()
window.setWindowTitle("Smart Video Surveillance")
window.show()
sys.exit(app.exec_())
