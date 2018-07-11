#!/home/pi/.virtualenvs/cv2/bin/python3

import cv2
import time
import argparse
import numpy as np
from threading import Thread
#from CameraOutputStream import CameraOutputStream
from camera_processing import VideoHandler


class Resolution():
    height = 0
    width  = 0

class Frame():
    complete = True
    timestamp = 0

class FauxCamera():
    framerate = 0
    resolution = Resolution()
    frame = Frame()

class PassFrame():
    def __init__(self, filename, framerate, resolution, output):
        self.filename = filename
        self.reader = cv2.VideoCapture(filename)
        self.camera = FauxCamera()
        self.camera.framerate = framerate
        self.camera.resolution.height = resolution[0]
        self.camera.resolution.width  = resolution[1]
        
        #self.tracking = CameraOutputStream(camera=self.camera, videoFile=output)
        self.tracking = VideoHandler(camera=self.camera, video_file=output)


    def sendFrame(self, buf):
        #self.tracking.camera.frame.timestamp = 
        self.tracking.write(buf)
        
    def readFrames(self):
        while self.reader.isOpened():
            ret, frame = self.reader.read()
            if not ret:
                break

            #print(frame.shape)
            #buf = np.reshape(frame, -1, 'A').astype(np.uint8).tobytes()
            cv2.imshow('Read', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            ret, buf = cv2.imencode('.png', frame)
            Thread(target=self.sendFrame, kwargs={'buf': buf}).start()
            time.sleep(1/self.camera.framerate)


        self.reader.release()
        self.tracking.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='The input video')
    parser.add_argument('-o', '--output', required=False, help='Video output file')
    parser.add_argument('-f', '--framerate', required=True, help='The video framerate')
    parser.add_argument('-v', '--height', required=True, help='The frame height')
    parser.add_argument('-w', '--width', required=True, help='The frame width')

    args = vars(parser.parse_args())

    filename  = args['input']
    fileout   = args['output']
    framerate = int(args['framerate'])
    resolution= (int(args['height']), int(args['width']))

    setup = PassFrame(filename, framerate, resolution, fileout)
    setup.readFrames()
    print("Done")
