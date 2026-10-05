"""Reject poor input before alignment and embedding."""
import cv2
import numpy as np


def check_quality(frame: np.ndarray, face: np.ndarray, min_size: int, min_blur: float):
    x, y, width, height = face[:4]
    h, w = frame.shape[:2]
    if min(width, height) < min_size:
        raise ValueError("Move closer: the face is too small.")
    if x < 0 or y < 0 or x + width > w or y + height > h:
        raise ValueError("Keep your entire face inside the camera frame.")
    crop = frame[int(y):int(y + height), int(x):int(x + width)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    if cv2.Laplacian(gray, cv2.CV_64F).var() < min_blur:
        raise ValueError("Image is blurry. Hold still and improve lighting.")
    if gray.mean() < 35 or gray.mean() > 225:
        raise ValueError("Lighting is too dark or too bright.")


def head_offset(face: np.ndarray) -> float:
    """Nose displacement relative to eye midpoint, normalized by inter-eye distance.

    This is a rough pose proxy, not a calibrated 3D yaw angle or anti-spoof classifier.
    """
    eyes = np.asarray(face[4:8]).reshape(2, 2)
    nose = face[8:10]
    return float((nose[0] - eyes[:, 0].mean()) / max(np.linalg.norm(eyes[0] - eyes[1]), 1))
