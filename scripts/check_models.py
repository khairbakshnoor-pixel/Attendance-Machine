"""Exercise the real detector and feature network without a camera or stored face."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import Settings
from face.recognizer import SFaceBackend


def main():
    backend = SFaceBackend(Settings())
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    assert backend.detector.detect(blank) == [], "Unexpected blank-frame detection"
    try:
        backend.extract(blank)
    except ValueError as exc:
        assert "No face" in str(exc)
    else:
        raise AssertionError("Blank image should not pass extraction")
    # Synthetic landmarks exercise alignment without enrolling a real person.
    synthetic = np.full((160, 160, 3), 127, dtype=np.uint8)
    landmarks = np.array([20, 20, 120, 120, 50, 60, 110, 60, 80, 85, 55, 115, 105, 115, .99], dtype=np.float32)
    aligned = backend.model.alignCrop(synthetic, landmarks)
    embedding = backend.model.feature(aligned)
    assert embedding.size == 128 and np.isfinite(embedding).all()
    print("PASS: real YuNet detection, no-face rejection, alignment, and SFace 128-dimensional inference.")
    print("This checks model execution only; it does not measure recognition accuracy or liveness.")


if __name__ == "__main__":
    main()
