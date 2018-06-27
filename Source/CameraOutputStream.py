import io
import sys
import cv2
import skvideo.io
import numpy as np
import tkinter as tk
import skvideo.utils
from time import sleep
import subprocess as sp
from PIL import Image, ImageTk
from threading import Thread, Event
from imagesocket import ImageSocket
from queue import Queue, Empty, PriorityQueue

class tracker(object):
    def __init__(self, posX, posY):
        self.x = posX
        self.y = posY
        self.framesSinceLastMove = 0
        self.displayMsg = 'Awake'

    def calcDist(self, posX, posY):
        return (self.x-posX)**2 + (self.y-posY)**2

    def updatePos(self, dist, x, y):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
            
        if dist is not None and dist > 20:
            self.framesSinceLastMove = 0
            self.displayMsg = 'Awake'
        else:
            self.framesSinceLastMove += 1
            if self.framesSinceLastMove > 10*3: # 3 sec @10 fps
                self.displayMsg = 'Sleeping'

class EventTracker(object):
    def __init__(self, numberOfObj):
        self.numberOfObj = numberOfObj
        #self.trackers = [tracker(0,0)] * numberOfObj
        self.trackers = []
        for i in range(numberOfObj):
            self.trackers.append(tracker(0, 0))
            
        self.queue = PriorityQueue()
        self.lastFrameNum = 0

    def report(self, objCenters, frameNum):
        if frameNum != self.lastFrameNum+1:
            self.queue.put((frameNum, objCenters))

            # Keep poping the queue
            while True:
                top = self.queue.get()
                if top[0] == self.lastFrameNum+1:
                    self.track(top[1])
                    self.lastFrameNum += 1
                else:
                    self.queue.put(top)
                    break

        else:
            self.lastFrameNum += 1
            self.track(objCenters)

        #sys.stdout.write('\r')
        for i in range(len(self.trackers)):
            sys.stdout.write('Tracker %i: %s (%f, %f) ' % (i, self.trackers[i].displayMsg,
                                                             self.trackers[i].x, self.trackers[i].y))
        sys.stdout.write(' '*10)
        sys.stdout.write('\r')
        sys.stdout.flush()

            
    def track(self, centers):
        usedIndexes = []
        for x, y in centers:
            best = None
            bestIndex = None
            for i in range(len(self.trackers)):
                if i in usedIndexes:
                    continue
                
                dist = self.trackers[i].calcDist(x, y)
                if best is None:
                    best = dist
                    bestIndex = i
                else:
                    if dist < best:
                        best = dist
                        bestIndex = i

            if best is None:
                break

            self.trackers[bestIndex].updatePos(best, x, y)
            usedIndexes.append(bestIndex)
        unusedIndexes = [x for x in [0,1,2,3] if x not in usedIndexes]
        for i in unusedIndexes:
            self.trackers[i].updatePos(None, None, None)


class VideoOutput(Thread):
    def __init__(self, filename, height, width, port):
        super(VideoOutput, self).__init__()
        self.maxSize = 32
        self.event = Event()
        self.queue = Queue(maxsize=self.maxSize)
        self.height = height
        self.width = width
        self.frameNum = 0
        self.filename = filename
        self.backgroundFrame = None
        self.eventTracker = EventTracker(4)
        self.blobParams = None
        self.blobDetector = None
        self.mog = None
        self.gmg = None
        self.kernel = None
        self.command = ['ffmpeg',
                        '-y',
                        '-f', 'rawvideo',
                        '-vcodec', 'rawvideo',
                        '-s', '720x480',
                        '-pix_fmt', 'gray',
                        '-r', '25',
                        '-i', '-',
                        '-an',
                        '-vcodec', 'mpeg',
                        'video.mp4']
        self.pipe = sp.Popen(self.command, stdin=sp.PIPE, stderr=sp.PIPE)
        #self.pipe.communicate()
        #self.fourcc = cv2.VideoWriter_fourcc('H', '2', '6', '4')
        #self.videoWriter = cv2.VideoWriter('video.mp4', self.fourcc, 20, (480, 720))
        #self.videoWriter = skvideo.io.LibAVWriter('video.mp4', inputdict={"-pix_fmt": "gray"})
        self.writeVideo = True
        #self.socket = ImageSocket()
        #self.socket1 = ImageSocket()
        #self.socket2 = ImageSocket()
        #self.socket3 = ImageSocket()
        #self.socket.startServer('142.66.96.249', port)
        # self.socket.startServer('142.66.96.249', 1130)
        # self.socket1.startServer('142.66.96.249', 1131)
        # self.socket2.startServer('142.66.96.249', 1132)
        # self.socket3.startServer('142.66.96.249', 1133)
        self.start()

    def write(self, buf):
        self.queue.put((buf, self.frameNum))
        self.frameNum += 1
        return len(buf)

    def run(self):
        while not self.event.wait(0):
            try:
                buf, num = self.queue.get(timeout=0.1)
            except Empty:
                pass
            else:
                if self.backgroundFrame is not None:
                    self.backgroundFrame = np.frombuffer(buf, dtype=np.uint8, count=self.width*self.height)
                    self.backgroundFrame = np.reshape(self.backgroundFrame, (self.height, self.width))
                    self.backgroundFrame = cv2.GaussianBlur(self.backgroundFrame, (5, 5), 0)

                #self.splitFrame(buf, self.frameNum)
                self.splitFrame(buf, num)
                #self.frameNum += 1
                self.queue.task_done()

                
    def cvWrite(self, frame, filename):
        if frame.ndim == 1:
            frame = np.reshape(frame, (self.height, self.width))
        cv2.imwrite(filename, frame)


    def cvWriteVideo(self, frame):
        if frame.ndim == 1:
            #print("Resahpe")
            #frame = np.reshape(frame, (self.height, self.width, 1))
            #frame = np.reshape(frame, (480, 720, 1))
            frame = skvideo.utils.vshape(frame)
        #cv2.cvtColor(frame, frame, cv2.COLOR_GRAY2RGB)
        #print(frame.shape)            
        #self.videoWriter.writeFrame(frame)
        #self.videoWriter.write(frame)
        for x in range(10):
            self.pipe.stdin.write(frame.tostring()[:-1].encode('utf-8'))
            print("Written")
        
    def splitFrame(self, buf, frameNum):
        #np_array = np.frombuffer(buf, dtype=np.uint8, count=self.width*self.height)

        #self.socket.sendNumpy(np.reshape(np_array, (self.height, self.width)))
        length = self.width * self.height
        if length == 0:
            length = len(buf)


        # Sends 1/3rd of the frames to the slave pi, and keeps 2/3rds locally to process
        # if(frameNum % 2 == 0):
        #     self.socket.send(buf,  length)
        # elif(frameNum % 16 == 4):
        #     self.socket1.send(buf, length)
        # elif(frameNum % 16 == 8):
        #     self.socket2.send(buf, length)
        # elif(frameNum % 16 == 12):
        #     self.socket3.send(buf, length)
        # else:
        image = np.frombuffer(buf, dtype=np.uint8, count=length)
        image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
        #image = cv2.GaussianBlur(image, (5,5), 0)
        frame, _ = self.backgroundFrameSub(image, 16, 300)
        #cv2.imwrite('testing.{}.jpg'.format(frameNum), image)
        #cv2.imwrite('testing.frame{}.jpg'.format(frameNum), frame)
        if self.writeVideo is True:
            try:
                self.cvWriteVideo(frame)
            except Exception as e:
                print(e)
        else:
            print("Done")
        if self.frameNum >= 900:
            self.writeVideo = False
            self.videoWriter.release()
            #self.videoWriter.close()
        self.frameNum += 1
        
        #print(self.ident)
        #if frameNum % 5 == 0:
        #gray, centers = self.backgroundFrameSub(np_array, threshold=10, minimum_area=300)
        #gray, centers = self.blobDetection(np_array, threshold=10, minimum_area=300)
        #gray, centers = self.mogSubtraction(np_array, threshold=16, minimum_area=300)
        #self.eventTracker.report(centers, frameNum)
        
        #self.cvWrite(np_array, '%s.%i.yuv.jpg' % (self.filename, frameNum))
        #self.cvWrite(gray, '%s.tracking.%i.yuv.jpg' % (self.filename, frameNum))


    def backgroundFrameSub(self, np_buffer, threshold, minimum_area):
        #frame = np.reshape(np_buffer, (self.height, self.width))
        frame = cv2.GaussianBlur(np_buffer, (5,5), 0)
        if self.backgroundFrame is None:
            self.backgroundFrame = frame
            
        frame = cv2.absdiff(frame, self.backgroundFrame)

        ret, frame = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)
        _, contours, hierarchy = cv2.findContours(frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        centers = []
        for contour in contours:
            if cv2.contourArea(contour) > minimum_area:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x,y), (x+w, y+h), (255, 255, 255), 2)

                m = cv2.moments(contour)
                centers.append(((m['m10'] / m['m00']), (m['m01'] / m['m00'])))
                
        return (frame, centers)


    def mogSubtraction(self, np_buffer, threshold, minimum_area):
        frame = np.reshape(np_buffer, (self.height, self.width))
        if self.mog is None:
            self.mog = cv2.createBackgroundSubtractorMOG2(varThreshold=threshold, detectShadows=False)

        frame = self.mog.apply(frame)
        _, contours, hierarchy = cv2.findContours(frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        centers = []
        for contour in contours:
            if cv2.contourArea(contour) > minimum_area:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x,y), (x+w, y+h), (255, 255, 255), 2)

                m = cv2.moments(contour)
                centers.append(((m['m10'] / m['m00']), (m['m01'] / m['m00'])))
                
        return (frame, centers)

    def gmgSubtraction(self, np_buffer, threshold, minimum_area):
        frame = np.reshape(np_buffer, (self.height, self.width))
        if self.kernel is None:
            self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        if self.gmg is None:
            self.gmg = cv2.bgsegm.createBackgroundSubtractorGMG()
            
        frame = self.gmg.apply(frame)
        frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, self.kernel)
        _, contours, hierarchy = cv2.findContours(frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        centers = []
        for contour in contours:
            if cv2.contourArea(contour) > minimum_area:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x,y), (x+w, y+h), (255, 255, 255), 2)

                m = cv2.moments(contour)
                centers.append(((m['m10'] / m['m00']), (m['m01'] / m['m00'])))
                
        return (frame, centers)

        
    def blobDetection(self, np_buffer, threshold, minimum_area):
        frame = np.reshape(np_buffer, (self.height, self.width))
        if self.blobParams is None:
            self.blobParams = cv2.SimpleBlobDetector_Params()
            self.blobParams.minThreshold = 10
            self.blobParams.maxThreshold = 200
            self.blobParams.filterByArea = True
            self.blobParams.minArea = minimum_area
            self.blobParams.filterByCircularity = True
            self.blobParams.minCircularity = 0.5
            self.blobParams.filterByConvexity = True
            self.blobParams.minConvexity = 0.5
            self.blobParams.filterByInertia = True
            self.blobParams.minInertiaRatio = 0.01
        if self.blobDetector is None:
            self.blobDetector = cv2.SimpleBlobDetector_create(self.blobParams)

        centers = []
        blobs = self.blobDetector.detect(frame)
        for blob in blobs:
            centers.append(blob.pt)

        frame = cv2.drawKeypoints(frame, blobs, np.array([]), (0,0,255))

        return (frame, centers)

    def flush(self):
        self.queue.join()

    def close(self):
        self.event.set()
        self.join()


class CameraYUVStream(object):
    def __init__(self, camera, videoFile, logFileExtention='.timestamp.log'):
        self.camera = camera
        self.logStream = None
        self.counter = 0

        width = (self.camera.resolution.width+31) // 32 * 32
        height = (self.camera.resolution.height+15) // 16 * 16
        self.video = VideoOutput(videoFile, height=height, width=width)
        
        if logFileExtention is not None:
            self.logStream = io.open(videoFile + logFileExtention, 'w')

            
    def write(self, buf):
        if self.logStream is not None:
            if self.camera.frame.complete and self.camera.frame.timestamp:
                self.logStream.write('%f\n' %(self.camera.frame.timestamp /\
                                              1000.0))  # Normalize the time then write it to the log stream
        #if self.counter == 0:
        self.video.write(buf)
        #self.counter = (self.counter+1) % 2

        
    def flush(self):
        if self.logStream is not None:
            self.logStream.flush()


    def close(self):
        if self.logStream is not None:
            self.logStream.close()
        self.video.close()


        
class CameraOutputStream(object):
    def __init__(self, camera, videoFile, logFileExtention, writeMotion=True, root=None):
        self.camera = camera
        self.videoFile = videoFile
        self.logFileExtention = logFileExtention
        self.videoStream = io.open(videoFile, 'wb')
        self.logStream = None
        self.fileType = videoFile.split('.')[-1]
        self.lastGreyFrame = None
        self.THRESHOLD = 25
        self.frameCount = 0
        self.heighest=0
        self.total=0
        self.count=0
        self.totalCount = 0
        self.lastFrame = None
        self.tempFrame = None
        self.staticEnv = None
        self.MIN_AREA = 20
        #self.video = VideoOutput(videoFile, height=camera.resolution.height,
        #                                    width=camera.resolution.width)
        self.video0 = VideoOutput(videoFile, height=0, width=0, port=1130)
        # self.video1 = VideoOutput(videoFile, height=0, width=0, port=1131)
        # self.video2 = VideoOutput(videoFile, height=0, width=0, port=1132)
        # self.video3 = VideoOutput(videoFile, height=0, width=0, port=1133)
        
        if logFileExtention is not None:
            self.logStream = io.open(videoFile + logFileExtention, 'w')

            
    def write_pbm(self, size, lst):
        self.heighests = 0
        self.count = 0
        self.total = 0
        ret = bytearray(str.encode('P5\n' + ' '.join(map(str, size)) + '\n')) # Header
        for i in range(0, len(lst), size[0]):
            row = lst[i:i+size[0]]
            reminder = len(lst) % 8
            for j in range(reminder):
                row.append(0)
                
            #s = ''
            #for j in row:
            #    if j >= self.THRESHOLD:
            #        s += '1'
            #    else:
            #        s += '0'
            #s += '0000000'
            #s = ''.join(map(str, row)) + '0000000'  # Pad the row
            for j in range(size[0]//8 + 1):
                self.count += 8
                self.total += row[j]
                if(row[j] > self.heighest):
                    self.heighest = row[j]
                    
                # total = ((int(row[j])+self.THRESHOLD)//256)
                # total += ((int(row[j+1])+self.THRESHOLD)//256) << 1
                # total += ((int(row[j+2])+self.THRESHOLD)//256) << 2
                # total += ((int(row[j+3])+self.THRESHOLD)//256) << 3
                # total += ((int(row[j+4])+self.THRESHOLD)//256) << 4
                # total += ((int(row[j+5])+self.THRESHOLD)//256) << 5
                # total += ((int(row[j+6])+self.THRESHOLD)//256) << 6
                # total += ((int(row[j+7])+self.THRESHOLD)//256) << 7                                
                
                # ret.append(total)
                print(row[j])
                ret.append(int(row[j]))
                ret.append(int(row[j+1]))
                ret.append(int(row[j+2]))
                ret.append(int(row[j+3]))
                ret.append(int(row[j+4]))
                ret.append(int(row[j+5]))
                ret.append(int(row[j+6]))
                ret.append(int(row[j+7]))
                #ret.append(int(s[j*8:(j+1)*8], base=2)) # From 8-bit string to base-10 int to btye

        print(self.heighest)
        print(self.total / self.count * 8)
        with open(self.videoFile+'.'+str(self.frameCount)+'.pgm', 'wb') as f:
            f.write(ret)
        self.frameCount += 1
        #return ret


    def write_p2(self, size, lst):
        with open(self.videoFile+'.'+str(self.frameCount)+'.pgm', 'w') as f:
            f.write('P2\n' + ' '.join(map(str, size)) + '\n')
            for i in range(size[1]):
                for j in range(size[0]):
                    f.write(str(lst[i*size[0] + j]) + ' ')
                f.write('\n')
        self.frameCount += 1


    def cv_write(self, size, lst, _format, modified):
        if lst is not None:
            if lst.ndim == 1:
                lst = np.reshape(lst, (size[1], size[0]))
            if modified:
                cv2.imwrite(self.videoFile+'.modified.'+str(self.frameCount)+'.'+_format, lst)
            else:
                cv2.imwrite(self.videoFile+'.'+str(self.frameCount)+'.'+_format, lst)
            self.frameCount += 1


    def get_movement(self, frame, size):
        frame = np.reshape(frame, (size[1], size[0]))
        self.tempFrame = frame
        if self.lastFrame is not None:
            frame = cv2.absdiff(frame, self.lastFrame)
            ret, frame = cv2.threshold(frame, self.THRESHOLD, 255, cv2.THRESH_BINARY)
        self.lastFrame = self.tempFrame
        return frame


    def env_diff(self, frame, size):
        frame = np.reshape(frame, (size[1], size[0]))
        frame = cv2.GaussianBlur(frame, (5, 5), 0) # Lots of work
        if self.staticEnv is None:
            self.staticEnv = frame
        frame = cv2.absdiff(frame, self.staticEnv)
        ret, frame = cv2.threshold(frame, self.THRESHOLD, 255, cv2.THRESH_BINARY)

        # Box
        (_, conts, h) = cv2.findContours(frame.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for obj in conts:
            if cv2.contourArea(obj) < self.MIN_AREA:
                continue
            (x, y, w, h) = cv2.boundingRect(obj)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (255, 255, 255), 2)
                                    

        return frame
    

    def getMotion(self, buf):
        if self.fileType == 'bgr':
            array = np.frombuffer(buf, dtype=np.uint8)
            image = np.reshape(array, (self.camera.resolution.height, self.camera.resolution.width, 3))
            grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            returnBuf = None
            if self.lastGreyFrame is not None:
                self.movement = cv2.absdiff(self.lastGreyFrame, grey)
                ret, self.movement = cv2.threshold(self.movement, self.THRESHOLD, 255, cv2.THRESH_BINARY)
                #returnBuf = np.reshape(self.movement, (self.camera.resolution.height * self.camera.resolution.width)).tobytes()
                self.lastGreyFrame = grey
                return True

            self.lastGreyFrame = grey
            return False
                

    def write(self, buf):        
        if self.fileType == 'yuv':
            fwidth = (self.camera.resolution.width+31) // 32 * 32
            fheight = (self.camera.resolution.height+15) // 16 * 16
            y = np.frombuffer(buf, dtype=np.uint8, count=fwidth*fheight)
            if self.totalCount % 2 != 10:
                #y = self.get_movement(y, (fwidth, fheight))
                x = self.env_diff(y, (fwidth, fheight))
                self.cv_write((fwidth, fheight), x, 'jpg', modified=True)
            self.cv_write((fwidth, fheight), y, 'jpg', modified=False)
            #self.videoStream.write(buf) Slower
        else:
            # if self.totalCount % 4 == 0:
            self.video0.write(buf)
            # elif self.totalCount % 4 == 1:
            #     self.video1.write(buf)
            # elif self.totalCount % 4 == 2:
            #     self.video2.write(buf)
            # else:
            #     self.video3.write(buf)
            
            #numpy_buf = np.frombuffer(buf, dtype=np.uint8)
            #img = cv2.imdecode(numpy_buf, cv2.IMREAD_COLOR)
            #cv2.imwrite('testing.jpg', img)
            #self.videoStream.write(buf)


        if self.logStream is not None:
            if self.camera.frame.complete and self.camera.frame.timestamp:
                self.logStream.write('%f\n' %(self.camera.frame.timestamp /\
                                              1000.0))  # Normalize the time then write it to the log stream
        
        self.totalCount += 1
    def flush(self):
        self.videoStream.flush()

        if self.logStream is not None:
            self.logStream.flush()


    def close(self):
        self.videoStream.close()
        if self.logStream is not None:
            self.logStream.close()
        self.sleep(1)
