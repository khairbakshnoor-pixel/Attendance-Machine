"""Replaceable face backend: detection, aligned SFace embedding, cosine matching."""
from dataclasses import dataclass
from typing import Protocol
import cv2
import numpy as np

from config.settings import ROOT, Settings
from face.detector import YuNetDetector
from face.embeddings import normalize
from face.preprocessing import check_quality


class FaceBackend(Protocol):
    model_version: str

    def extract(self, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]: ...


class SFaceBackend:
    model_version = "opencv-sface-2021dec-128-v1"

    def __init__(self, settings: Settings):
        self.settings = settings
        directory = ROOT / "models"
        self.detector = YuNetDetector(directory / "face_detection_yunet_2023mar.onnx", settings.detection_threshold)
        model = directory / "face_recognition_sface_2021dec.onnx"
        if not model.is_file():
            raise ValueError("SFace model missing. Run: python scripts/download_models.py")
        self.model = cv2.FaceRecognizerSF.create(str(model), "")

    def extract(self, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        faces = self.detector.detect(frame)
        if not faces:
            raise ValueError("No face detected. Look toward the camera.")
        if len(faces) != 1:
            raise ValueError("Multiple faces detected. Only one person may use the kiosk at a time.")
        face = faces[0]
        check_quality(frame, face, self.settings.min_face_size, self.settings.min_blur_score)
        aligned = self.model.alignCrop(frame, face)
        return face, normalize(self.model.feature(aligned))


@dataclass(frozen=True)
class Match:
    user_id: int
    employee_id: str
    name: str
    score: float


def match_embedding(embedding: np.ndarray, gallery: list[dict], threshold: float, margin: float) -> Match | None:
    if not gallery:
        return None
    query = normalize(embedding)
    scores = np.asarray([float(query @ normalize(item["embedding"])) for item in gallery])
    order = np.argsort(scores)[::-1]
    best = int(order[0])
    if scores[best] < threshold:
        return None
    if len(order) > 1 and scores[best] - scores[order[1]] < margin:
        return None
    user = gallery[best]
    return Match(user["id"], user["employee_id"], user["name"], float(scores[best]))
