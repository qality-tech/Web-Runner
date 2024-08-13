import os
import time

import cv2


class Recorder:
    def __init__(self, config, web_driver):
        self.config = config
        self.resolution = (1920, 1080)
        self.codec = cv2.VideoWriter_fourcc(*"mp4v")
        self.fps = 20.0
        self.stopped = False
        self.out = None
        self.window_title = None
        self.web_driver = web_driver
        self.filename = None
        self.frame_path = None

    def start(self, filename):
        self.filename = filename
        self.frame_path = f'recordings/frame_{self.filename}.png'.replace('.mp4', '')
        directory_path = os.path.join(os.path.dirname(__file__), '..', '..', 'recordings')
        if self.config['DEFAULT'].get('RECORDING', False) in ['True', 'true', '1', True] \
                and not os.path.exists(directory_path):
            os.makedirs(directory_path)
        self.out = cv2.VideoWriter(os.path.join(directory_path, filename), self.codec, self.fps, self.resolution)
        self.render_loop()

    def render_loop(self):
        while not self.stopped:
            self.render_frame()
            if self.stopped:
                break
            time.sleep(1 / self.fps)
        self.out.release()

    def render_frame(self):
        # TODO: check if it is mandatory to save the image locally
        try:
            self.web_driver.current_driver.get_screenshot_as_file(os.path.join(os.path.dirname(__file__), '..', '..', self.frame_path))
            frame = cv2.imread(os.path.join(os.path.dirname(__file__), '..', '..', self.frame_path))
            resized_frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_AREA)
            self.out.write(resized_frame)
        except (Exception,):
            pass

    @staticmethod
    def blackout_exterior_region(frame, x1, y1, x2, y2):
        # make sure coordinates are within frame range
        x1 = min(max(0, x1), len(frame[0]))
        x2 = min(max(0, x2), len(frame[0]))
        y1 = min(max(0, y1), len(frame))
        y2 = min(max(0, y2), len(frame))

        # top and bottom
        for i in list(range(0, y1)) + list(range(y2, len(frame))):
            frame[i] = [[0, 0, 0] for _ in range(0, len(frame[i]))]

        # left and right
        for j in list(range(0, x1)) + list(range(x2, len(frame[0]))):
            for i in range(0, len(frame)):
                frame[i][j] = [0, 0, 0]
        return frame

    def stop(self):
        self.stopped = True
        self.send_recording()
        self.delete_files()

    def delete_files(self):
        # remove frame file
        try:
            os.remove(os.path.join(os.path.dirname(__file__), '..', '..', self.frame_path))
        except (Exception,):
            pass
        # remove recording file
        # directory_path = os.path.join(os.path.dirname(__file__), '..', '..', 'recordings')
        # os.remove(os.path.join(os.path.join(directory_path, self.filename)))

    def send_recording(self):
        pass
