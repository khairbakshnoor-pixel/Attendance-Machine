"""Exclusive local camera ownership with expiry for disconnected browser sessions."""
import threading
import time
import cv2


class Camera:
    def __init__(self, index: int):
        self.index = index
        self.capture = None
        self.owner = None
        self.last_read = 0.0
        self.lock = threading.RLock()

    def _close(self):
        if self.capture is not None:
            self.capture.release()
        self.capture, self.owner = None, None

    def read(self, owner: str):
        with self.lock:
            if self.owner != owner:
                if self.owner is not None and time.monotonic() - self.last_read < 8:
                    raise ValueError("The camera is in use by another session. Stop that session first.")
                self._close()
                self.capture = cv2.VideoCapture(self.index)
                self.owner = owner
                if not self.capture.isOpened():
                    self._close()
                    raise ValueError("Camera unavailable or permission denied. Check Windows camera privacy settings and CAMERA_INDEX.")
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.last_read = time.monotonic()
            ok, frame = self.capture.read()
            if not ok:
                self._close()
                raise ValueError("Cannot read the camera. Reconnect it and restart the preview.")
            return frame

    def release(self, owner: str):
        with self.lock:
            if self.owner == owner:
                self._close()

    def reap(self):
        with self.lock:
            if self.owner and time.monotonic() - self.last_read > 8:
                self._close()


def draw_face(frame, face):
    output = frame.copy()
    if face is not None:
        x, y, w, h = map(int, face[:4])
        cv2.rectangle(output, (x, y), (x + w, y + h), (90, 210, 80), 2)
    return output
