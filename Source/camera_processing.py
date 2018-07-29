"""Defines the classes that are used for the post-processing of images generated
   from the picamera

   Author: Zachary Selk <zrselk@gmail.com>
   Github: www.github.com/zacharyselk
   Date  : June 2018

  Style-Guide: https://www.github.com/google/styleguide/blob/gh-pages/pyguide.md
"""

from queue import Empty
from queue import Queue
from RPi import GPIO
from threading import Event
from threading import Thread

import io
import cv2
import os
import random
import time

import numpy as np


class EventTracker(object):
    """Event tracking object.

    A class to classify and maintain the events detected from the frames passed
    to it.

    Attributes:
        x_pos (float) : The x position of the current frame.
        y_pos (float) : The y position of the current frame.
        event (str)   : The current event that has been classified.
    """

    def __init__(self, x_pos=0, y_pos=0):
        """Initialization.

        Args:
            x_pos (float, optional): The initial x position. Defaults to 0.
            y_pos (float, optional): The initial y position. Defaults to 0.
        """
        self.x_pos = x_pos  #: The center x position of the tracked object
        self.y_pos = y_pos  #: The center y position of the tracked object
        self.event = 'Awake'  #: A string of the current event
        self._frames_since_movement = 0  # How long it has been since movement

    def calc_dist2(self, x_pos, y_pos):
        """Calculate the squared euclidean distance.

        Calculates the squared euclidean distance between the current position
        and the new position passed.

        Args:
            x_pos (float): x position of the point to be measured.
            y_pos (float): y position of the point to be measured.

        Returns:
            The squared distance between the two points.
        """
        return (self.x_pos-x_pos)**2 + (self.y_pos-y_pos)**2

    def update(self, bounding_box):
        """Updates the tracking.

        Takes the next frame along with a bounding box of the object, and
        updates the event.

        Args:
            bounding_box: A tuple that describes the box ie.
            (top_left_x_pos, top_left_y_pos, top_right_x_pos, bottom_left_y_pos).

        Returns:
            None.
        """
        # Defines the (x, y) coordinates of the center fo the bounding box
        center_x = bounding_box[0] + (bounding_box[2] - bounding_box[0])/2
        center_y = bounding_box[1] + (bounding_box[3] - bounding_box[1])/2

        dist2 = self.calc_dist2(center_x, center_y)
        # If there was a movement of at least `thresh` pixels then the object
        #     is 'awake'
        thresh = 10
        if dist2 is not None and dist2 > thresh*thresh:
            self._frames_since_movement = 0
            self.event = 'Awake'
        else:
            self._frames_since_movement += 1
            if self._frames_since_movement > 2*3:  # 3 sec @2 fps
                self.event = 'Sleeping'

        # Update to new position
        self.x_pos = center_x
        self.y_pos = center_y

    def significant_movement(self, x_pos, y_pos, threshold=10):
        """Determines if movement is 'significant'.

        Measures to see if the distance between the current position and
        (x_pos, y_pos) is greater than `threshold`.

        Args:
            x_pos (float): x position of the point to be measured.
            y_pos (float): y position of the point to be measured.
            threshold (float, optional): The distance that is considered
            'significant'. Defaults to 10.

        Returns:
            Bool: True if distance is greater than `threshold`, False otherwise.
        """
        dist2 = self.calc_dist2(x_pos, y_pos)
        if dist2 is not None and dist2 > threshold*threshold:
            return True
        return False


class Tracker(object):
    """Tracks an object when given a ROI (Region Of Interest).

    Tracks a ROI, using the KCF (Kernelized Correlation Filters) tracking
    algorithm, until tracking is lost.
    """
    def __init__(self):
        """Initilization.

        Sets variables with default values.
        """
        self.tracker = None    # Used to track an object
        self.tracking = False  # If we are currently tracking something
        self.num_of_objects = 0
        self.event_tracker = EventTracker()
        self.consecutive_frames_recived = 0

    def init_kcf_tracking(self, frame, bounding_box):
        """Creates a default KCF tracking object."""
        self.tracker = cv2.TrackerKCF_create()
        self.tracker.init(frame, bounding_box)
        self.tracking = True
        print('Tracking')

    def track(self, frame, bounding_box=None):
        """Decides if tracking should be done.

        Args:
            frame: The opencv image to be tracked.
            bounding_box: The ROI to track, only needed if this is the first
            time calling `track`. Defaults to None.

        TODO:
            This really needs to be intergrated better.
        """
        if self.tracking:
            frame = self.kcf_tracking(frame)
            self.consecutive_frames_recived = 0
        # If not tracking check to see if tracking can be reinitalized,
        # the object in question must be relitivly still for a couple of
        # before we (re)initalize tracking to make sure we know what the
        # object looks like
        else:
            self.consecutive_frames_recived += 1
            center_x = bounding_box[0] + (bounding_box[2] - bounding_box[0])/2
            center_y = bounding_box[1] + (bounding_box[3] - bounding_box[1])/2
            if self.event_tracker.significant_movement(center_x, center_y):
                self.consecutive_frames_recived = 0
            else:
                if self.consecutive_frames_recived > 6:
                    self.init_kcf_tracking(frame, bounding_box)
            self.event_tracker.x_pos = center_x
            self.event_tracker.y_pos = center_y

        return frame

    # Uses the KCF tracking from opencv to track an object
    def kcf_tracking(self, frame):
        """Progresses the object tracking.

        Takes a frame and attempts to track the original object using KCF
        tracking.

        Args:
            frame: The opencv image to be tracked.

        Returns:
            If tracking was successful returns the frame with a box draw on it,
            otherwise return the frame as is.
        """
        # Return if the tracker has not been initialized
        if self.tracker is None:
            return frame

        # Otherwise update the tracker with the current frame
        success, box = self.tracker.update(frame)

        # If the update was a success, get the bounding box returned and draw
        #     it on to the frame
        if success:
            point1 = (int(box[0]), int(box[1]))  # Vertex point
            # Point on opposite side of vertex point
            point2 = (int(box[0] + box[2]), int(box[1] + box[3]))
            cv2.rectangle(frame, point1, point2, (255, 0, 0), 2, 1)
            self.tracking = True
            self.event_tracker.update(box)
        # If the update was unsuccessful then we lost track of the object
        else:
            print('Lost')
            self.tracking = False
            #return None

        return frame


#class VideoProcessing(Thread):
class VideoProcessing:
    """Handles video processing

    Args:
        filename: The file name/path that the video or images will be written
        as. Note: if writing images. each one will have the frame number
        added to the name.
        height: The height of the video in pixels.
        width: The width of the video in pixels.
        framerate: The framerate of the video in frames per second.
        file_type: What type of encoding is used on the buffers that will be
        passed for decoding
    """
    def __init__(self, filename, height, width, framerate, file_type, tracking=True, tracking_fps=1):
        super(VideoProcessing, self).__init__()
        self._event = Event()
        self._tracker = Tracker()
        self._queue = Queue(maxsize=32)
        self._frame_number = 0
        self._count = 0
        
        self.filename = filename
        self.file_type = file_type
        self.framerate = framerate
        self.height = height
        self.width = width
        self.resolution = (width, height)
        self.tracking = tracking
        self.tracking_fps = tracking_fps
        self.background_frame = None
        self.last_frame = None
        self.last_box = None
        self.last_time = None
        self.time_not_moving = 0
        
        self.pinout = 3
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pinout, GPIO.OUT, initial=GPIO.LOW)
        self.timeout = False
        self.timeout_timer = 0

        # Object detection algorithm perameters
        self.blob_params = None
        self.blob_detector = None
        self.mog = None
        self.gmg = None
        self.kernel = None

        self.tracking_filename = self.filename + '.tracking.log'
        self.tracking_stream = io.open(self.tracking_filename, 'w')
        # Switches the filename's extension with .mp4
        self.mp4_filename = '.'.join(filename.split('.')[:-1]) + '.mp4'
        # 0x00000021 is just some codec that works (not sure what it is for sure)
        self.fourcc = 0x00000021
        self.write_in_color = False
        self.video_writer = cv2.VideoWriter(self.mp4_filename,
                                            self.fourcc,
                                            self.framerate,
                                            self.resolution,
                                            self.write_in_color)
        #self.start()

    def write(self, buf, image=None):
        """Handles then writes a frame buffer.

        Args:
            buf: The buffer (binary form) of a frame.

        Returns:
            Returns the length of the recieved buffer.
        """
        yuv = False
        if image is not None:
            yuv = True
        #self._queue.put((buf, self._frame_number, yuv))
        #self._frame_number += 1
        self.process_frame(buf=buf, image=image)

    def rename(self, new_name):
        """Changes the filename of the video"""
        new_name = new_name.replace(':', '\:')
        new_name = new_name.replace('&', '\&')
        new_name = new_name.replace('#', '\#')
        try:
            new_mp4_name = '.'.join(new_name.split('.')[:-1]) + '.mp4'
            os.rename(self.mp4_filename, new_mp4_name)
            self.mp4_filename = new_mp4_name
            new_tracking_name = '.'.join(new_name.split('.')[:-1]) + '.tracking.log'
            os.rename(self.tracking_filename, new_tracking_name)
            self.tracking_filename = new_tracking_name
        except:
            rand_num = str(random.randint(1, 1000000))
            new_mp4_name = '/'.join(self.mp4_filename.split('/')[:-1]) + '/recovedVideo' + rand_num + '.mp4'
            os.rename(self.mp4_filename, new_mp4_name)
            self.mp4_filename = new_mp4_name
            
            new_tracking_name = '/'.join(new_name.split('/')[:-1]) + '/recovedVideo' + rand_num + '.tracking.log'
            os.rename(self.tracking_filename, new_tracking_name)
            self.tracking_filename = new_tracking_name
            print('Error: could not use that name, name this video as %s' % new_mp4_name)

    def run(self):
        """Runs the processes that have been queued up.

        This function is called by the `threading` class.
        """
        while not self._event.wait(0):
            try:
                buf, _, yuv = self._queue.get(timeout=0.01)
            except Empty:
                pass
            else:
                if yuv is True:
                    self.process_frame(buf=None, image=buf)
                else:
                    self.process_frame(buf)
                self._queue.task_done()

    def cv_write_image(self, frame, file_type='.jpeg'):
        """Writes the frames of the video as images using opencv.

        Args:
            frame: The frame to be written.
            file_type: What encoding to use on the image. Defaults to jpeg.
        """
        # Add a unique number to the filename to prevent name collision
        name = '%s.%i.%s' % (self.filename, self._frame_number, file_type)
        cv2.imwrite(name, frame)

    def cv_write_video(self, frame):
        """Writes the frames of the video as a mp4 video using opencv.

        Args:
            frame: The frame to be written.
        """
        self.video_writer.write(frame)

    def write_tracking(self, box=None):
        if box is None:
            self.tracking_stream.write('-1,-1,-1,-1\n')
        else:
            self.tracking_stream.write('{},{},{},{}\n'.format(box[0], box[1], box[2], box[3]))

    def process_frame(self, buf, image=None):
        """Decodes the buffer then manages the tracking.

        Args:
            buf: A buffer representing the image.
        """
        current_time = time.time()
        self._frame_number += 1
        if image is None:
            image = np.frombuffer(buf, dtype=np.uint8, count=len(buf))
            image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
        #    pass
        # Need something better than this
        if self._frame_number % round(self.framerate/self.tracking_fps) != 0  or self.tracking is False:
            #if self.last_box is not None:                
            #    box = self.last_box
                #cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 255, 255), 2)

            self.write_tracking(self.last_box)
            #cv2.imshow('Image', image)
            self.cv_write_video(image)
            return

        frame, box = self.sequential_frame_subtraction(image, 16, 1000)
        #frame, box = self.background_frame_subtraction(image, 30, 1500)
        #frame, box = self.mog_subtraction(image, 30, 900)
        #frame, box = self.blob_detection(image, 900)
        #frame, box = self.gmg_subtraction(image, 2000)
        if box is None:
            box = self.last_box
            # if box is None:
            #     self.write_tracking()
            #     return
        # If we detected something then hand it to the tracker
        #if box is not None:
        #    image = self._tracker.track(image, box)
        if self.timeout is True:
            self.timeout_timer -= (time.time() - self.last_time)
            if self.timeout_timer <= 0:
                self.timeout = False
        elif self.time_not_moving >= 40:
            self.timeout = True
            self.timeout_timer = 120
            GPIO.output(self.pinout, GPIO.LOW)

        if box == self.last_box:
            if self.last_time is None:
                self.last_time = time.time()
                
            self.time_not_moving += time.time() - self.last_time
            if self.time_not_moving >= 20 and self.timeout is False:
                GPIO.output(self.pinout, GPIO.HIGH)
                
        else:
            self.time_not_moving = 0
            GPIO.output(self.pinout, GPIO.LOW)
            
        self.write_tracking(box)
        #cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 255, 255), 2)
        cv2.imshow('Frame', frame.copy())
        cv2.imshow('Image', image.copy())
        #cv2.waitKey(0)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return
        
        self.cv_write_video(image)
        self.last_box = box
        self.last_time = current_time

    def background_frame_subtraction(self, np_buffer, threshold, minimum_area):
        """Object detection using frame subtraction.

        Subtracts the first frame acquired from any proceding frame to detect
        any changes in the scene.

        Args:
            np_buffer: A numpy buffer of the image.
            threshold: The amount of change in pixel luminescence unitl a
            difference is detected.
            minimum_area: The minimum amount of area that is required for an
            object to be detected.

        Returns:
            (frame, box): A tuple containing both the thresholded frame and
            a bounding box of the detected object. If no object is detected,
            then box is None.
        """
        frame = cv2.GaussianBlur(np_buffer, (21, 21), 0)
        if self.background_frame is None or self._frame_number % 100 == 0:
            print('Setting Background')
            self.background_frame = frame

        frame = cv2.absdiff(frame, self.background_frame)

        _, frame = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)
        _, contours, _ = cv2.findContours(frame, cv2.RETR_LIST,
                                          cv2.CHAIN_APPROX_SIMPLE)
        box = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > minimum_area and area < 3500:
                x_pos, y_pos, width, height = cv2.boundingRect(contour)
                box = (x_pos, y_pos, x_pos+width, y_pos+height)

                # Draws a rectangle onto the image
                cv2.rectangle(frame, (x_pos, y_pos),
                              (x_pos+width, y_pos+height), (255, 255, 255), 2)
                break

        return (frame, box)

    def sequential_frame_subtraction(self, np_buffer, threshold, minimum_area):
        frame = cv2.GaussianBlur(np_buffer, (3, 3), 0)
        #frame = cv2.pyrDown(np_buffer)
        
        if self.last_frame is None:
            self.last_frame = frame

        
        tmp = cv2.absdiff(frame, self.last_frame)
        self.last_frame = frame
        frame = tmp
        #cv2.imshow('diff', frame)
        
        _, frame = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)
        frame = cv2.dilate(frame, np.ones((5, 5), np.uint8), iterations=1)        
        _, contours, _ = cv2.findContours(frame, cv2.RETR_LIST,
                                          cv2.CHAIN_APPROX_SIMPLE)
        
        # We only look at the first item in the list
        #
        #                        ^
        # TODO: Make this better |
        box = None
        for contour in contours:
            if cv2.contourArea(contour) > minimum_area:
                x_pos, y_pos, width, height = cv2.boundingRect(contour)
                box = (x_pos, y_pos, x_pos+width, y_pos+height)

                # Draws a rectangle onto the image
                cv2.rectangle(frame, (x_pos, y_pos),
                              (x_pos+width, y_pos+height), (255, 255, 255), 2)
                break

        return (frame, box)


    # Have not really used this
    def mog_subtraction(self, np_buffer, threshold, minimum_area):
        """Object detection using MOG subtraction.

        Uses the opencv implementation of MOG subtraction developed by
        Pakorn KaewTraKulPong and Richard Bowden.

        Args:
            np_buffer: A numpy buffer of the image.
            threshold: The amount of change in pixel luminescence unitl a
            difference is detected.
            minimum_area: The minimum amount of area that is required for an
            object to be detected.

        Returns:
            (frame, box): A tuple containing both the thresholded frame and
            a bounding box of the detected object. If no object is detected,
            then box is None.
        """
        if self.mog is None:
            self.mog = cv2.createBackgroundSubtractorMOG2(varThreshold=threshold,
                                                          detectShadows=False)

        frame = self.mog.apply(np_buffer)
        _, contours, _ = cv2.findContours(frame, cv2.RETR_LIST,
                                          cv2.CHAIN_APPROX_SIMPLE)

        box = None
        for contour in contours:
            if cv2.contourArea(contour) > minimum_area:
                x_pos, y_pos, width, height = cv2.boundingRect(contour)
                box = (x_pos, y_pos, x_pos+width, y_pos+height)
                cv2.rectangle(frame, (x_pos, y_pos),
                              (x_pos+width, y_pos+height), (255, 255, 255), 2)
                break


        return (frame, box)

    # Have not really used this
    def gmg_subtraction(self, np_buffer, minimum_area):
        """Object detection using GMG subtraction.

        Uses the opecnv implementation of GMG subtraction developed by
        Andrew Godbehere, Akihiro Matsukawa, and Ken Goldberg (GMG).

        Args:
            np_buffer: A numpy buffer of the image.
            minimum_area: The minimum amount of area that is required for an
            object to be detected.

        Returns:
            (frame, centers): A tuple containing both the thresholded frame as
            well as a list of tuples describing the center of each objected
            detected.
        """
        if self._count < 50:
            print(self._count)
        self._count += 1        
        frame = np.reshape(np_buffer, (self.height, self.width))
        #frame = cv2.GaussianBlur(frame, (7, 7), 0)        
        if self.kernel is None:
            self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        if self.gmg is None:
            self.gmg = cv2.bgsegm.createBackgroundSubtractorGMG(initializationFrames=100,
                                                                decisionThreshold=0.70)

        frame = self.gmg.apply(frame)
        frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, self.kernel)
        _, contours, _ = cv2.findContours(frame, cv2.RETR_LIST,
                                          cv2.CHAIN_APPROX_SIMPLE)

        # centers = []
        # for contour in contours:
        #     if cv2.contourArea(contour) > minimum_area:
        #         x_pos, y_pos, width, height = cv2.boundingRect(contour)
        #         cv2.rectangle(frame, (x_pos, y_pos),
        #                       (x_pos+width, y_pos+height), (255, 255, 255), 2)

        #         moments = cv2.moments(contour)
        #         centers.append(((moments['m10'] / moments['m00']),
        #                         (moments['m01'] / moments['m00'])))

        # return (frame, centers)

        box = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > minimum_area:
                x_pos, y_pos, width, height = cv2.boundingRect(contour)
                box = (x_pos, y_pos, x_pos+width, y_pos+height)
                cv2.rectangle(frame, (x_pos, y_pos),
                              (x_pos+width, y_pos+height), (255, 255, 255), 2)
                break


        return (frame, box)
        

    # Have not really used this
    def blob_detection(self, np_buffer, minimum_area):
        """Object detection by finding 'blobs' in the scene

        Uses the opencv implementation of blob detection to find convex 'blobs'
        in the scene.

        Args:
            np_buffer: A numpy buffer of the image.
            minimum_area: The minimum amount of area that is required for an
            object to be detected.

        Returns:
            (frame, centers): A tuple containing both the thresholded frame as
            well as a list of tuples describing the center of each objected
            detected.
        """
        frame = np.reshape(np_buffer, (self.height, self.width))
        if self.blob_params is None:
            self.blob_params = cv2.SimpleBlobDetector_Params()
            self.blob_params.minThreshold = 5
            self.blob_params.maxThreshold = 255
            self.blob_params.filterByArea = True
            self.blob_params.minArea = 30
            self.blob_params.filterByCircularity = True
            self.blob_params.minCircularity = 0.1
            self.blob_params.filterByConvexity = True
            self.blob_params.minConvexity = 0.1
            self.blob_params.filterByInertia = True
            self.blob_params.minInertiaRatio = 0.01
        if self.blob_detector is None:
            self.blob_detector = cv2.SimpleBlobDetector_create(self.blob_params)

        # centers = []
        # blobs = self.blob_detector.detect(frame)
        # for blob in blobs:
        #     centers.append(blob.pt)

        # frame = cv2.drawKeypoints(frame, blobs, np.array([]), (0, 0, 255))

        # return (frame, centers)

        box = None
        blobs = self.blob_detector.detect(frame)
        for blob in blobs:
            print("Blob")
            x_pos, y_pos, width, height = cv2.boundingRect(blob)
            box = (x_pos, y_pos, x_pos+width, y_pos+height)
            
            # Draws a rectangle onto the image
            cv2.rectangle(frame, (x_pos, y_pos),
                         (x_pos+width, y_pos+height), (255, 255, 255), 2)
            break

        return (frame, box)        

        
    def flush(self):
        """Flushes the worker queue"""
        self._queue.join()

    def close(self):
        """Closes the video stream and the worker queue"""
        print('Closing Stream')
        self.flush()
        self.video_writer.release()
        self._event.set()
        #self.join()


class VideoHandler(object):
    """Handles aquired frames from a video stream.

    This object acts as an interface for the picamera so that frames can be
    processed before being writen.

    Args:
        camera: An instance of the camera object from the picam library.
        video_file: The file name/path for writing video to.
        log_file_extension: The name to appened to the timestamp file.
    """
    def __init__(self, camera, video_file, log_file_extension='.timestamp.log', tracking=True, tracking_fps=1):
        self.camera = camera
        self.video_file = video_file
        self.log_file_extension = log_file_extension
        self.video_stream = io.open(video_file, 'wb')
        self.file_type = video_file.split('.')[-1]
        self.height = camera.resolution.height
        self.width = camera.resolution.width
        self.framerate = camera.framerate
        self.tracking = tracking
        self.tracking_fps = tracking_fps
        if self.file_type == 'yuv':
            self.height = (self.height + 15) // 16 * 16
            self.width = (self.width+31) // 32 * 32

        self.frame_count = 0
        if self.tracking is True:
            self.video = VideoProcessing(video_file, height=self.height,
                                         width=self.width, framerate=self.framerate,
                                         file_type=self.file_type,
                                         tracking=self.tracking,
                                         tracking_fps=self.tracking_fps)
        else:
            self.video = io.open(video_file, 'wb')

        self.log_file_name = video_file + log_file_extension
        self.log_stream = None
        if log_file_extension is not None:
            self.log_stream = io.open(self.log_file_name, 'w')


    def write(self, buf):
        """Writes the timestamps and handles the aquired buffer.

        This function is used as an interface for the picamera, allowing us to
        capture the frames from the camera for processing.

        Args:
            buf: A buffer of a newly aquired image.
        """
        if self.file_type == 'yuv':
            # The first portion of yuv is luminescence (grayscale)
            luminescence = np.frombuffer(buf, dtype=np.uint8,
                                         count=self.width*self.height)
            luminescence = np.resize(luminescence, (self.height, self.width))
            #buf = cv2.encode('png', luminescence)
            self.video.write(buf=None, image=luminescence)
        else:
            self.video.write(buf)
            
        timestamp = self.camera.frame.timestamp
        if self.log_stream is not None:
            if self.camera.frame.complete and timestamp:
                # Normalize the time then write it to the log stream
                self.log_stream.write('%f\n' %(timestamp / 1000.0))

        self.frame_count += 1

    def rename(self, new_name):
        """Changes the name of the saved video.

        Args:
            new_name: The new name that the file will be changed to.
        """
        # Let the video processing unit take care of it
        # os.rename(self.video_file, new_name)
        # new_log_name = new_name + self.log_file_extension
        # print(new_log_name)
        # os.rename(self.log_file_name, new_log_name)
        try:
            self.video.rename(new_name)
        except:
            pass
        
    def flush(self):
        """Flushes the writing streams."""
        self.video_stream.flush()
        if self.log_stream is not None:
            self.log_stream.flush()


    def close(self):
        """Closes the writing streams and the processing objects."""
        self.video.close()
        if self.log_stream is not None:
            self.log_stream.close()
