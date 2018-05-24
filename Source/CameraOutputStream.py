import io

class CameraOutputStream():
    def __init__(self, camera, videoFile, logFileExtention):
        self.camera = camera
        self.videoFile = videoFile
        self.logFileExtention = logFileExtention
        self.videoStream = io.open(videoFile, 'wb')
        self.logStream = None
        if logFileExtention is not None:
            self.logStream = io.open(videoFile + logFileExtention, 'w')


    def write(self, buf):
        self.videoStream.write(buf)  # Write frame to the stream

        if self.logStream is not None:
            if self.camera.frame.complete and self.camera.frame.timestamp:
                self.logStream.write('%f\n' %(self.camera.frame.timestamp /\
                                              1000.0))  # Normalize the time then write it to the log stream


    def flush(self):
        self.videoStream.flush()

        if self.logStream is not None:
            self.logStream.flush()


    def close(self):
        self.videoStream.close()

        if self.logStream is not None:
            self.logStream.close()
