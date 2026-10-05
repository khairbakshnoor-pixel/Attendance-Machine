"""YuNet face detection with five landmarks."""
from pathlib import Path
import cv2
import numpy as np


class YuNetDetector:
    def __init__(self, model: Path, threshold: float):
        if not model.is_file():
            raise ValueError("Face models are missing. Run: python scripts/download_models.py")
        self.model = cv2.FaceDetectorYN.create(str(model), "", (320, 320), threshold, 0.3, 5000)

    def detect(self, frame: np.ndarray) -> list[np.ndarray]:
        height, width = frame.shape[:2]
        self.model.setInputSize((width, height))
        _, faces = self.model.detect(frame)
        return [] if faces is None else list(faces)
