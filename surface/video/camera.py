import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp

class Camera:
    def __init__(self, port):
        self._frame = None
        Gst.init(None)
        gst_str = f'udpsrc port={port} ! application/x-rtp ! rtpjitterbuffer ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,width=1280,height=720,format=RGB ! appsink name=appsink0'
        print(gst_str)
        self.pipeline = Gst.parse_launch(gst_str)
        self.appsink = self.pipeline.get_by_name('appsink0')
        self.appsink.set_property('emit-signals', True)
        self.appsink.set_property('max-buffers', 1)
        self.appsink.set_property('drop', True)
        self.appsink.set_property('sync', False)
        self.appsink.connect('new-sample', self.on_new_buffer)

        self.pipeline.set_state(Gst.State.PLAYING)

    def __del__(self):
        self.pipeline.set_state(Gst.State.NULL)

    def on_new_buffer(self, sink):
        sample = sink.emit('pull-sample')
        buffer = sample.get_buffer()
        self._frame = np.ndarray(
            shape=(720, 1280, 3),
            buffer=buffer.extract_dup(0, buffer.get_size()),
            dtype=np.uint8,
        )
        return Gst.FlowReturn.OK

    def get_frame(self) -> bytes:
        if self._frame is not None and self._frame.any():
            file_object = BytesIO()
            img = Image.fromarray(self._frame)
            img.save(file_object, 'JPEG')
            file_object.seek(0)
            return file_object.read()
        return b''

        