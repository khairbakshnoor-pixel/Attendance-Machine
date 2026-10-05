"""Download the exact official OpenCV Zoo models and verify their LFS SHA-256."""
import hashlib
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "face_detection_yunet_2023mar.onnx": ("face_detection_yunet", "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"),
    "face_recognition_sface_2021dec.onnx": ("face_recognition_sface", "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"),
}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    directory = ROOT / "models"
    directory.mkdir(exist_ok=True)
    for filename, (folder, expected) in MODELS.items():
        target = directory / filename
        if target.exists() and sha256(target) == expected:
            print(f"Verified {filename}")
            continue
        url = f"https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/{folder}/{filename}"
        temporary = target.with_suffix(".part")
        try:
            print(f"Downloading {filename}…", flush=True)
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            if sha256(temporary) != expected:
                raise ValueError(f"Checksum mismatch for {filename}; refusing to load.")
            temporary.replace(target)
            print(f"Verified {filename}")
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
