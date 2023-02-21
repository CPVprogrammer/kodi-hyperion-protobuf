'''
		Kodi -> Hyperion - protobuf
'''
import xbmc

import socket
import struct

from misc import log
from message_pb2 import HyperionRequest
from message_pb2 import HyperionReply
from message_pb2 import ColorRequest
from message_pb2 import ImageRequest
from message_pb2 import ClearRequest


class Hyperion():
    def __init__(self, kodi_settings):
        # get addon settings
        self.settings = kodi_settings
        self.img_width = self.settings.capture_width
        self.img_height = self.settings.capture_height

        # kodi
        self.first_capture = True

        # connect to hyperion
        self.socket_hyperion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_hyperion.settimeout(2)
        self.socket_connected = False
        self.connect_socket()


    def __del__(self):
        try:
            self.socket_hyperion.close()
        except:
            pass


    def connect_socket(self):
        ''' create a socket connection to hyperion
        '''
        try:
            log("hyperion address: "+ self.settings.address +" port: " +str(self.settings.port))
            self.socket_hyperion.connect((self.settings.address, self.settings.port))
            self.socket_connected = True
        except Exception as e:
            log("hyperion connection: "+ str(e))


    def capture(self):
        ''' capture an image from kodi and send to hyperion
        '''
        if self.first_capture:
            self.first_capture = False

        self.kodi_capture = xbmc.RenderCapture()
        self.kodi_capture.capture(self.img_width, self.img_height)

        # Format of captured image: 'BGRA'
        image_data = self.kodi_capture.getImage()

        if len(image_data) > 0:
            # BGRA --> RGB
            del image_data[3::4]
            image_data[0::3], image_data[2::3] = image_data[2::3], image_data[0::3]

            self.create_image(self.img_width, self.img_height, image_data, self.settings.priority, -1)

            #limit the maximum number of frames sent to hyperion
            xbmc.sleep(int(1. / self.settings.framerate * 1000))


    def create_image(self, width, height, data, priority, duration = -1):
        ''' Send an image to Hyperion
            - width    : width of the image
            - height   : height of the image
            - data     : image data (byte string containing 0xRRGGBB pixel values)
            - priority : the priority channel to use
            - duration : duration the leds should be set
        ''' 

        request = HyperionRequest()
        request.command = HyperionRequest.IMAGE
        imageRequest = request.Extensions[ImageRequest.imageRequest]
        imageRequest.imagewidth = width
        imageRequest.imageheight = height
        imageRequest.imagedata = bytes(data)
        imageRequest.priority = priority
        imageRequest.duration = duration

        self.send_recv_data(request)


    def create_clear(self, priority):
        ''' Clear the given priority channel
            priority: the priority channel to clear
        '''
        request = HyperionRequest()
        request.command = HyperionRequest.CLEAR
        clearRequest = request.Extensions[ClearRequest.clearRequest]
        clearRequest.priority = priority

        self.send_recv_data(request)


    def create_clearAll(self):
        ''' Clear all active priority channels
            https://docs.hyperion-project.org/en/api/guidelines.html#priority-guidelines
        '''
        request = HyperionRequest()
        request.command = HyperionRequest.CLEARALL

        self.send_recv_data(request)


    def create_color(self, color, priority, duration = -1):
        ''' Send a static color to Hyperion
            - color    : integer value with the color as 0x00RRGGBB
            - priority : the priority channel to use
            - duration : duration the leds should be set
        ''' 
        request = HyperionRequest()
        request.command = HyperionRequest.COLOR
        colorRequest = request.Extensions[ColorRequest.colorRequest]
        colorRequest.rgbColor = color
        colorRequest.priority = priority
        colorRequest.duration = duration

        self.send_recv_data(request)


    def send_recv_data(self, message):
        ''' send protobuf to hyperion
            recv reply from hyperion
        '''
        #print "send message to Hyperion (%d):\n%s" % (len(message.SerializeToString()), message)

        # send message to Hyperion server
        binaryRequest = message.SerializeToString()
        binarySize = struct.pack(">I", len(binaryRequest))
        self.socket_hyperion.sendall(binarySize)
        self.socket_hyperion.sendall(binaryRequest);
        
        # receive a reply from Hyperion server
        size = struct.unpack(">I", self.socket_hyperion.recv(4))[0]
        reply = HyperionReply()
        reply.ParseFromString(self.socket_hyperion.recv(size))
        
        # check the reply
        #print "Reply received:\n%s" % (reply)
        if not reply.success:
            raise RuntimeError("Hyperion server error: " + reply.error)
