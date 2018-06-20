#!/usr/bin/env python

import socket
import numpy as np
from io import BytesIO as StringIO


class ImageSocket():
    def __init__(self):
        self.address = 0
        self.port = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.type = None  # server or client

    # def __del__(self):
    #     if self.type is "client":
    #         self.endClient()
    #     if self.type is "server":
    #         self.endServer()
    #     print(self.id, 'closed')

    def startServer(self, address, port):
        self.type = "server"
        self.address = address
        self.port = port
        try:
            self.socket.connect((self.address, self.port))
            print('Connected to %s on port %s' % (self.address, self.port))
        except socket.error as e:
            print('Connection to %s on port %s failed: %s' % (self.address, self.port, e))
            return

    def endServer(self):
        self.socket.shutdown(1)
        self.socket.close()


    def send(self, buf):
        if self.type is not "server":
            print("Not setup as a server")
            return

        size = len(buf)
        byteValue = []
        byteValue.append(size  & 255)
        byteValue.append((size & (255 <<  8)) >>  8)
        byteValue.append((size & (255 << 16)) >> 16)
        byteValue.append((size & (255 << 24)) >> 24)
        buf = bytes(byteValue) + buf
        try:
            self.socket.sendall(out)
        except Exception:
            exit()
        
    def sendNumpy(self, image):
        if self.type is not "server":
            print("Not setup as a server")
            return

        if not isinstance(image, np.ndarray):
            print('not a valid numpy image')
            return
        f = StringIO()
        np.savez_compressed(f, frame=image)
        f.seek(0)
        out = f.read()

        size = len(f.getvalue())
        byteValue = []
        byteValue.append(size  & 255)
        byteValue.append((size & (255 <<  8)) >>  8)
        byteValue.append((size & (255 << 16)) >> 16)
        byteValue.append((size & (255 << 24)) >> 24)

        out = bytes(byteValue) + out
        try:
            self.socket.sendall(out)
        except Exception:
            exit()
        #print('image sent')

    def startClient(self, port):
        self.type = "client"
        self.address = ''
        self.port = port

        self.socket.bind((self.address, self.port))
        self.socket.listen(1)
        print('waiting for a connection...')
        self.client_connection, self.client_address = self.socket.accept()
        print('connected to ', self.client_address[0])

    def endClient(self):
        self.client_connection.shutdown(1)
        self.client_connection.close()

        
    def intToBytes(integer):
        bytesValue = []
        bytesValue.append(integer  & 255)
        bytesValue.append((integer & (255 <<  8)) >>  8)
        bytesValue.append((integer & (255 << 16)) >> 16)
        bytesValue.append((integer & (255 << 24)) >> 24)
        return bytes(bytesValue)
        
        
    def bytesToInt(byte):
        num  = byte[0]
        num += byte[1] << 8
        num += byte[2] << 16
        num += byte[3] << 24
        return num

    def recieve(self):
        if self.type is not "client":
            print("Not setup as a client")
            return

        length = None
        rows   = 0
        cols   = 0
        buf = bytes([])
        while True:
            data = self.client_connection.recv(1024)
            buf += data
            if len(buf) == length:
                break
            while True:
                if length is None:
                    cols = bytesToInt(buf[:4])
                    rows  = bytesToInt(buf[4:8])
                    length = rows*cols
                    buf = buf[8:]

                if len(buf) < length:
                    break
                # split off the full message from the remaining bytes
                # leave any remaining bytes in the buf!
                buf = buf[length:]
                length = None
                break
        image = np.frombuffer(buf, dtype=np.uint8, count=cols*rows)
        return image
        
        
    def recieveNumpy(self):
        if self.type is not "client":
            print("Not setup as a client")
            return

        length = None
        buf = bytes([])
        while True:
            data = self.client_connection.recv(1024)
            buf += data
            if len(buf) == length:
                break
            while True:
                if length is None:
                    # length  = buf[0]
                    # length += buf[1] << 8
                    # length += buf[2] << 16
                    # length += buf[3] << 24
                    length = bytesToInt(buf[:4])
                    buf = buf[4:]

                if len(buf) < length:
                    break
                # split off the full message from the remaining bytes
                # leave any remaining bytes in the buf!
                buf = buf[length:]
                length = None
                break
        final_image = np.load(StringIO(buf))['frame']
        #print('frame received')
        return final_image
