'''
camera_processing.new.py
Copyright (C) 2018 - Zachary Selk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

"""Defines the classes that are used for the post-processing of images generated
   from the picamera

   Author: Zachary Selk <zrselk@gmail.com>
   Github: www.github.com/zacharyselk
   Date  : June 2018

  Style-Guide: https://www.github.com/google/styleguide/blob/gh-pages/pyguide.md
"""

from RPi import GPIO
from sleeping import MouseState
from sleeping import SleepState

import numpy as np

import cv2
import io
import os
import random
import time

class VideoProperties:
    """A struct to contain the properties of a video.
    
    Attributes:
       type: The video file type.
       height: The height of the video frames in pixels.
       width: The width of the video frames in pixels.
       framerate: The framerate of the video.
       file_name: The path name of the video (used for reading and writing to
           disk).
       color: True if the video is in color, False otherwise.
    """
    __slots__ = [
        'type',
        'height',
        'width',
        'framerate',
        'file_name',
        'color'
    ]

class VideoWriter(cv2.VideoWriter):
    """A small interface for cv2.VideoWriter.
    
    Provides some small functionallity to cv2.VideoWriter and acts as an,
    interface, using the VideoProperties struct for information, as well as
    setting some default values.

    Args:
        properties: A VideoProperties object, used for initialization 
            information.
        write_type: The file type to write the video as. Defaults to mp4.
        fourcc: The fourcc id of the write_type. Defaults to 0x00000021 for mp4.
    """
    def __init__(self, properties, write_type='mp4', fourcc=0x00000021):
        # Changes the file type to write_type
        file_name = properties.file_name.split('.')[:-1] + '.' + write_type
        if len(file_name) is 0:
            file_name = properties.file_name + '.' + write_type
        resolution = (properties.width, properties.height)
        
        super(cv2.VideoWriter, self).__init__(file_name, fourcc,
                                              properties.framerate,
                                              resolution, properties.color)

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
    def __init__(self, properties, track=True, tracking_fps=1):
        #super(VideoProcessing, self).__init__()
        self._frame_number = 0
        
        self.video_properties = properties
        self.track = track
        self.tracking_fps = tracking_fps
        self.last_frame = None
        self.last_box = None
        
        self.pinout = 3
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pinout, GPIO.OUT, initial=GPIO.LOW)

        self.tracking_filename = self.filename + '.tracking.log'
        self.tracking_stream = io.open(self.tracking_filename, 'w')
        self.video_writer = VideoWriter(properties)

    def process_frame(self, buf, image=None):
        """Decodes the buffer then manages the tracking.

        Args:
            buf: A buffer representing the image.
        """
        self._frame_number += 1
        if image is None:
            image = np.frombuffer(buf, dtype=np.uint8, count=len(buf))
            image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)

        if self._frame_number % round(self.framerate/self.tracking_fps) != 0  or self.track is False:
            self.write_tracking(self.last_box)
            self.cv_write_video(image)
            return

        frame, box = self.sequential_frame_subtraction(image, 16, 1000)
        if box is None:
            box = self.last_box

        if box == self.last_box:
            self.sleeping_state.run(MouseState.moving)
        else:
            self.sleeping_state.run(MouseState.still)
            
        if sleeping_state.current_state == SleepState.sleeping:
            self.write_tracking(box, sleeping=True)
            GPIO.output(self.pinout, GPIO.HIGH)
        else:
            self.write_tracking(box)
            GPIO.output(self.pinout, GPIO.LOW)
        
        cv2.imshow('Frame', frame.copy())
        cv2.imshow('Image', image.copy())
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return
        
        self.cv_write_video(image)
        self.last_box = box

    def sequential_frame_subtraction(self, np_buffer, threshold, minimum_area):
        frame = cv2.GaussianBlur(np_buffer, (3, 3), 0)        
        if self.last_frame is None:
            self.last_frame = frame

        tmp = cv2.absdiff(frame, self.last_frame)
        self.last_frame = frame
        frame = tmp
        
        _, frame = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)
        frame = cv2.dilate(frame, np.ones((5, 5), np.uint8), iterations=1)        
        _, contours, _ = cv2.findContours(frame, cv2.RETR_LIST,
                                          cv2.CHAIN_APPROX_SIMPLE)        
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

    def cv_write_video(self, frame):
        """Writes the frames of the video as a mp4 video using opencv.

        Args:
            frame: The frame to be written.
        """
        self.video_writer.write(frame)

    def write_tracking(self, box=None, sleeping=False):
        sleep = 1 if sleeping is True else 0
        if box is None:
            self.tracking_stream.write('-1,-1,-1,-1,{}\n'.format(sleep))
        else:
            self.tracking_stream.write('{},{},{},{},{}\n'.format(box[0],
                                                                 box[1],
                                                                 box[2],
                                                                 box[3],
                                                                 sleep))


    def flush(self):
        pass
    
    def close(self):
        """Closes the video stream and the worker queue"""
        print('Closing Stream')
        self.flush()
        self.video_writer.release()
        self._event.set()



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
            properties = VideoProperties()
            properties.file_tpye = self.file_type
            properties.height = self.height
            properties.width = self.width
            properties.framerate = self.framerate
            properties.file_name = self.video_file
            properties.color = False
            
            self.video = VideoProcessing(properties, tracking=self.tracking,
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
